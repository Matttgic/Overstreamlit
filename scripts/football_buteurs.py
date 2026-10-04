"""Évaluation et ajustement du modèle buteurs football (sportpred/models/football_scorers.py).

Protocole (aucune information postérieure au match n'entre dans une prédiction) :
- données : Understat, 5 grands championnats, 2018-19 → 2026-27 (joueur par match) ;
- variables : moyennes décroissantes des matchs précédents uniquement ;
- β et moyennes de poste ajustés sur 2019-20 → 2022-23, test 2023-24 → 2026-27 ;
- buts attendus des équipes : cotes de clôture sans marge (football-data.co.uk : Pinnacle,
  sinon moyenne du marché), 1N2 + plus/moins de 2,5 buts.
Le modèle final (β réajusté sur toutes les saisons) est enregistré dans
data/processed/football_scorer_model.json pour l'usage quotidien.

Usage : python scripts/football_buteurs.py   (télécharge Understat au premier lancement, ~1 h)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportpred.data import understat  # noqa: E402
from sportpred.live.matching import sim  # noqa: E402
from sportpred.models import football_scorers as M  # noqa: E402

DIV = {"EPL": "E0", "La_liga": "SP1", "Bundesliga": "D1", "Serie_A": "I1", "Ligue_1": "F1"}
TRAIN = (2019, 2022)
TEST = (2023, 2026)
OUT_MD = ROOT / "docs" / "resultats" / "football_buteurs.md"
OUT_JSON = ROOT / "data" / "processed" / "football_scorer_model.json"


# ------------------------------------------------------------------ cotes de clôture
def _devig(*odds):
    inv = np.array([1 / np.asarray(o, float) for o in odds])
    return inv / inv.sum(axis=0)


def fd_market() -> pd.DataFrame:
    fd = pd.read_parquet(ROOT / "data" / "processed" / "football_main.parquet")
    fd = fd[fd["Div"].isin(DIV.values())].copy()
    h = fd["PSCH"].where(fd["PSCH"].notna() & fd["PSCA"].notna(), fd.get("AvgCH"))
    d = fd["PSCD"].where(fd["PSCH"].notna() & fd["PSCA"].notna(), fd.get("AvgCD"))
    a = fd["PSCA"].where(fd["PSCH"].notna() & fd["PSCA"].notna(), fd.get("AvgCA"))
    o = fd["PC>2.5"].where(fd["PC>2.5"].notna() & fd["PC<2.5"].notna(), fd.get("AvgC>2.5"))
    u = fd["PC<2.5"].where(fd["PC>2.5"].notna() & fd["PC<2.5"].notna(), fd.get("AvgC<2.5"))
    ph, pdr, pa = _devig(h, d, a)
    po, _ = _devig(o, u)
    fd["p_home"], fd["p_draw"], fd["p_over"] = ph, pdr, po
    fd = fd[np.isfinite(fd["p_home"]) & np.isfinite(fd["p_over"])]
    lams = [M.team_lambdas(x, y, z) for x, y, z in zip(fd["p_home"], fd["p_draw"], fd["p_over"])]
    fd["lam_h"], fd["lam_a"] = [x[0] for x in lams], [x[1] for x in lams]
    return fd[["Div", "Date", "HomeTeam", "AwayTeam", "lam_h", "lam_a"]].dropna()


def link_market(df: pd.DataFrame, fd: pd.DataFrame) -> pd.DataFrame:
    """λ de chaque équipe-match Understat (rapprochement date ± 1 jour + noms, puis vote)."""
    fx = (df[df["home"]].groupby("match_id").agg(date=("date", "first"), league=("league", "first"),
                                                 home=("team", "first"), away=("opp", "first")).reset_index())
    fx["day"] = fx["date"].dt.normalize()
    fd = fd.assign(day=pd.to_datetime(fd["Date"]).dt.normalize())
    votes = {}
    for lg, g in fx.groupby("league"):
        f = fd[fd["Div"] == DIV[lg]]
        by_day = {k: v for k, v in f.groupby("day")}
        for r in g.itertuples():
            cands = pd.concat([by_day.get(r.day + pd.Timedelta(days=k), f.iloc[0:0]) for k in (-1, 0, 1)])
            if cands.empty:
                continue
            sc = [sim(r.home, x) + sim(r.away, y) for x, y in zip(cands["HomeTeam"], cands["AwayTeam"])]
            best = cands.iloc[int(np.argmax(sc))]
            if max(sc) >= 1.0:
                votes.setdefault((lg, r.home), {}).setdefault(best["HomeTeam"], 0)
                votes[(lg, r.home)][best["HomeTeam"]] += 1
    alias = {k: max(v, key=v.get) for k, v in votes.items()}
    fx["fd_home"] = [alias.get((lg, h)) for lg, h in zip(fx["league"], fx["home"])]
    fx["fd_away"] = [alias.get((lg, a)) for lg, a in zip(fx["league"], fx["away"])]
    m = fx.merge(fd, left_on=["fd_home", "fd_away"], right_on=["HomeTeam", "AwayTeam"], how="inner")
    m = m[(m["day_x"] - m["day_y"]).abs() <= pd.Timedelta(days=2)]
    lam = pd.concat([m[["match_id", "lam_h"]].assign(home=True).rename(columns={"lam_h": "lam"}),
                     m[["match_id", "lam_a"]].assign(home=False).rename(columns={"lam_a": "lam"})])
    return df.merge(lam.drop_duplicates(["match_id", "home"]), on=["match_id", "home"], how="left")


# ------------------------------------------------------------------ mesures
def ll_per_goal(df, share):
    y = df["goals"].to_numpy(float)
    return float(-(y * np.log(np.clip(share, 1e-12, 1))).sum() / y.sum())


def scores(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))), float(np.mean((p - y) ** 2))


def calib(y, p, bins=(0, .05, .1, .15, .2, .25, .3, .4, .5, .7, 1)):
    t = pd.DataFrame({"y": y, "p": p, "b": pd.cut(p, bins)})
    return t.groupby("b", observed=True).agg(n=("y", "size"), pred=("p", "mean"), obs=("y", "mean"))


def prematch_shares(X: pd.DataFrame, p: M.Params, bench: float) -> np.ndarray:
    """Parts « si titulaire » : titulaires réels avec leurs minutes ATTENDUES quand titulaires,
    remplaçants résumés par la masse moyenne du banc (`bench`, en part des titulaires)."""
    st = X[X["starter"]].copy()
    g = st["grp_use"].where(st["grp_use"].isin(["D", "M", "A", "F"]), "M")
    m0 = g.map({k: p.priors[k]["min_start"] for k in ("D", "M", "A", "F")})
    mins = st["min_start_exp"].fillna(m0).clip(20, 95)
    F = M.features(st, p, minutes=mins)
    e = np.exp(F[M.FEATURES].to_numpy(float) @ p.beta)
    z = pd.Series(e, index=F.index).groupby([F["match_id"], F["home"]]).transform("sum") * (1 + bench)
    return F.assign(share_pre=e / z.to_numpy())


def tune(df: pd.DataFrame, mk: pd.DataFrame) -> tuple[M.Params, list]:
    """Demi-vie et rétrécissements choisis sur 2019-20 → 2020-21 (ajustement) / 2021-22 →
    2022-23 (validation), critère : log-loss « buteur » avec λ de clôture."""
    grid = []
    for hl in (20.0, 38.0, 76.0):
        P = link_market(M.prepare(df, M.Params(hl_rate=hl)), mk)
        P = P[~P["is_future"]]
        tr, va = P["season"].between(2019, 2020), P["season"].between(2021, 2022)
        for k_min in (450.0, 900.0, 1800.0):
            for k_fin in (3.0, 6.0, 12.0):
                p = M.Params(hl_rate=hl, k_min=k_min, k_fin=k_fin)
                M.fit(P, p, tr)
                X = M.features(P[va], p)
                X = X[X["lam"].notna()]
                s = M.predict_shares(X, p.beta)
                y = (X["goals"] >= 1).to_numpy(float)
                ll = scores(y, M.p_score(X["lam"].to_numpy() * (1 - p.og_share), s))[0]
                grid.append({"hl_rate": hl, "k_min": k_min, "k_fin": k_fin, "ll": ll, "ll_goal": ll_per_goal(X, s)})
                print(grid[-1], flush=True)
    best = min(grid, key=lambda g: g["ll"])
    return M.Params(hl_rate=best["hl_rate"], k_min=best["k_min"], k_fin=best["k_fin"]), grid


def main():
    df = understat.load(ROOT / "data" / "raw", seasons=list(range(2018, 2027)), refresh_current=False)
    print("lignes joueur-match :", len(df))
    mk = fd_market()
    p, grid = tune(df, mk)
    print("réglage retenu :", p.hl_rate, p.k_min, p.k_fin)
    P = M.prepare(df, p)
    P = link_market(P, mk)
    print("équipes-matchs avec λ :", P.drop_duplicates(["match_id", "home"])["lam"].notna().mean().round(3))
    P = P[~P["is_future"]]
    tr = P["season"].between(*TRAIN)
    te = P["season"].between(*TEST)
    M.fit(P, p, tr)
    beta_train = p.beta.copy()
    X = M.features(P[te], p)
    s_model = M.predict_shares(X, p.beta)
    s_min = M.predict_shares(X.assign(_m=X["time"]), None, "_m")
    s_naive = M.predict_shares(X.assign(_r=X["time"] * X["rate90"]), None, "_r")
    cond = {"modèle": ll_per_goal(X, s_model), "minutes × xG/90 (sans β)": ll_per_goal(X, s_naive),
            "minutes seulement": ll_per_goal(X, s_min)}
    # anytime avec λ de clôture (minutes réelles)
    k = X["lam"].notna().to_numpy()
    y = (X["goals"] >= 1).to_numpy(float)[k]
    lamp = X["lam"].to_numpy()[k] * (1 - p.og_share)
    mkt = {name: scores(y, M.p_score(lamp, s[k])) for name, s in
          (("modèle", s_model), ("minutes × xG/90", s_naive), ("minutes seulement", s_min))}
    cal_any = calib(y, M.p_score(lamp, s_model[k]))
    # « si titulaire » : minutes attendues, banc moyen
    Xtr = M.features(P[tr], p)
    s_tr = M.predict_shares(Xtr, p.beta)
    tot = pd.Series(s_tr).groupby([Xtr["match_id"].to_numpy(), Xtr["starter"].to_numpy()]).sum().unstack()
    bench = float((tot[False] / tot[True]).median())
    S = prematch_shares(X, p, bench)
    S = S[S["lam"].notna()]
    ys = (S["goals"] >= 1).to_numpy(float)
    ps = M.p_score(S["lam"].to_numpy() * (1 - p.og_share), S["share_pre"].to_numpy())
    pre = scores(ys, ps)
    cal_pre = calib(ys, ps)
    by_grp = (pd.DataFrame({"g": S["grp_use"].to_numpy(), "y": ys, "p": ps}).groupby("g")
              .agg(n=("y", "size"), pred=("p", "mean"), obs=("y", "mean")))
    by_league = (pd.DataFrame({"l": S["league"].to_numpy(), "y": ys, "p": ps}).groupby("l")
                 .agg(n=("y", "size"), pred=("p", "mean"), obs=("y", "mean")))
    # modèle final : toutes les saisons
    M.fit(P, p, P["season"] >= TRAIN[0])
    OUT_JSON.write_text(json.dumps({
        "features": M.FEATURES, "beta": [round(float(b), 5) for b in p.beta],
        "beta_train": [round(float(b), 5) for b in beta_train],
        "priors": p.priors, "og_share": round(p.og_share, 5), "bench": round(bench, 4),
        "params": {k: getattr(p, k) for k in ("hl_rate", "hl_pen", "hl_min", "k_min", "k_fin")},
        "test": {"logloss_si_titulaire": round(pre[0], 5), "n": int(len(ys))}}, indent=1))
    write_md(cond, mkt, cal_any, pre, cal_pre, by_grp, by_league, beta_train, p, bench, len(X), int(k.sum()), len(ys), grid)
    print(open(OUT_MD).read())


def _pct(x):
    return f"{100 * x:.1f} %"


def write_md(cond, mk, cal_any, pre, cal_pre, by_grp, by_league, beta_train, p, bench, n_te, n_mk, n_pre, grid):
    names = {"l_min": "log(minutes / 90)", "l_rate": "log(xG/90 attendu, penaltys compris)",
             "l_fin": "log(finition : buts / xG, rétréci)", "is_d": "défenseur", "is_m": "milieu",
             "is_a": "milieu offensif / ailier", "new": "moins de 5 matchs d'historique"}
    L = ["# Modèle buteurs football : résultats", "",
         "> Généré par `scripts/football_buteurs.py`. Données Understat (5 grands championnats),",
         "> apprentissage 2019-20 → 2022-23, **test hors échantillon 2023-24 → 2026-27** ;",
         "> buts attendus des équipes tirés des cotes de clôture sans marge (football-data.co.uk).", "",
         "## 1. Répartition des buts d'une équipe entre ses joueurs (sachant le nombre de buts)", "",
         f"Log-loss par but (plus bas = mieux), {n_te:,} lignes joueur-match :".replace(",", " "), "",
         "| Méthode | Log-loss |", "|---|---|"]
    L += [f"| {k} | {v:.4f} |" for k, v in cond.items()]
    L += ["", "Coefficients (β, appris sur 2019-20 → 2022-23) :", "", "| Variable | β |", "|---|---|"]
    L += [f"| {names[f]} | {b:+.3f} |" for f, b in zip(M.FEATURES, beta_train)]
    L += ["", "## 2. Probabilité de marquer (minutes réelles, λ de clôture)", "",
          f"{n_mk:,} joueurs-matchs :".replace(",", " "), "", "| Méthode | Log-loss | Brier |", "|---|---|---|"]
    L += [f"| {k} | {v[0]:.4f} | {v[1]:.4f} |" for k, v in mk.items()]
    L += ["", "Calibration (modèle) :", "", "| Prédit (tranche) | Joueurs | Prédit | Observé |", "|---|---|---|---|"]
    L += [f"| {i} | {int(r.n)} | {_pct(r.pred)} | {_pct(r.obs)} |" for i, r in cal_any.iterrows()]
    L += ["", "## 3. Cote « si titulaire » (ce que le site affiche)", "",
          "Titulaires réels, minutes **attendues** quand ils sont titulaires (rôle récent), remplaçants",
          f"résumés par la masse moyenne du banc ({_pct(bench)} des titulaires) ; {n_pre:,} titulaires.".replace(",", " "),
          f"Log-loss {pre[0]:.4f}, Brier {pre[1]:.4f}.", "",
          "| Prédit (tranche) | Joueurs | Prédit | Observé |", "|---|---|---|---|"]
    L += [f"| {i} | {int(r.n)} | {_pct(r.pred)} | {_pct(r.obs)} |" for i, r in cal_pre.iterrows()]
    L += ["", "Par poste habituel :", "", "| Poste | Joueurs | Prédit | Observé |", "|---|---|---|---|"]
    lab = {"D": "défenseurs", "M": "milieux", "A": "milieux offensifs / ailiers", "F": "attaquants"}
    L += [f"| {lab.get(i, i)} | {int(r.n)} | {_pct(r.pred)} | {_pct(r.obs)} |" for i, r in by_grp.iterrows()]
    L += ["", "Par championnat :", "", "| Championnat | Joueurs | Prédit | Observé |", "|---|---|---|---|"]
    L += [f"| {understat.LEAGUES.get(i, i)} | {int(r.n)} | {_pct(r.pred)} | {_pct(r.obs)} |" for i, r in by_league.iterrows()]
    L += ["", f"Buts contre son camp : {_pct(p.og_share)} des buts (aucun buteur crédité).", "",
          "## 4. Réglage (ajustement 2019-20 → 2020-21, validation 2021-22 → 2022-23)", "",
          f"Retenu : demi-vie {p.hl_rate:g} matchs, {p.k_min:g} minutes fictives au taux du poste, "
          f"{p.k_fin:g} buts fictifs pour la finition.", "",
          "| Demi-vie | Minutes fictives | Buts fictifs | Log-loss buteur | Log-loss par but |", "|---|---|---|---|---|"]
    L += [f"| {g['hl_rate']:g} | {g['k_min']:g} | {g['k_fin']:g} | {g['ll']:.5f} | {g['ll_goal']:.4f} |"
          for g in sorted(grid, key=lambda g: g["ll"])[:10]]
    L += [""]
    OUT_MD.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
