"""Évaluation et ajustement du modèle buteurs NHL (sportpred/models/nhl_scorers.py).

Protocole (aucune information postérieure au match n'entre dans une prédiction) :
- historique joueur : moyennes décroissantes des matchs précédents uniquement ;
- réglage des demi-vies et du rétrécissement : ajustement 2011-12 → 2015-16, validation
  2016-17 → 2017-18 ;
- test hors échantillon : 2018-19 → 2025-26, β ajusté sur 2011-12 → 2017-18 seulement ;
- test « ancré marché » : 2018-19 → 2021-22 (cotes de clôture SBR : vainqueur + total).
Le modèle final (β réajusté sur 2011-12 → 2025-26) est enregistré dans
data/processed/nhl_scorer_model.json pour l'usage quotidien.

Usage : python scripts/nhl_buteurs.py   (télécharge l'historique NHL au premier lancement)
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportpred.data import nhl_players  # noqa: E402
from sportpred.data.other_sports import american_to_decimal  # noqa: E402
from sportpred.models import nhl_scorers as M  # noqa: E402

RAW = ROOT / "data" / "raw"
OUT_MD = ROOT / "docs" / "resultats" / "nhl_buteurs.md"
OUT_MODEL = ROOT / "data" / "processed" / "nhl_scorer_model.json"
SEASONS = [y * 10000 + y + 1 for y in range(2010, 2027)]
FIT, VAL = (20112012, 20152016), (20162017, 20172018)
DEV, TEST = (20112012, 20172018), (20182019, 20252026)

SBR_TEAMS = {"Ducks": "ANA", "Coyotes": "ARI", "Phoenix": "ARI", "Arizonas": "ARI", "Bruins": "BOS",
             "Sabres": "BUF", "Hurricanes": "CAR", "Blue Jackets": "CBJ", "Flames": "CGY",
             "Blackhawks": "CHI", "Avalanche": "COL", "Stars": "DAL", "Red Wings": "DET", "Oilers": "EDM",
             "Panthers": "FLA", "Kings": "LAK", "Wild": "MIN", "Canadiens": "MTL", "Devils": "NJD",
             "Predators": "NSH", "Islanders": "NYI", "NY Islanders": "NYI", "Rangers": "NYR",
             "Senators": "OTT", "Flyers": "PHI", "Penguins": "PIT", "Kraken": "SEA", "SeattleKraken": "SEA",
             "Sharks": "SJS", "St.Louis": "STL", "Lightning": "TBL", "Tampa": "TBL", "Tampa Bay": "TBL",
             "Maple Leafs": "TOR", "Canucks": "VAN", "Golden Knights": "VGK", "Jets": "WPG",
             "WinnipegJets": "WPG", "Capitals": "WSH"}


def between(df, a, b):
    return df[(df["season"] >= a) & (df["season"] <= b)]


def ll_per_goal(df, share):
    """Log-vraisemblance moyenne par but (attribution au bon buteur)."""
    m = df["goals"].to_numpy() > 0
    return float((df["goals"].to_numpy()[m] * np.log(share[m])).sum() / df["goals"].sum())


def scores(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {"log_loss": float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()),
            "brier": float(((p - y) ** 2).mean())}


def team_goals(df):
    key = df["game_id"].astype(np.int64) * 2 + df["home"].astype(np.int64)
    return df.groupby(key)["goals"].transform("sum").to_numpy()


def build(raw_df, p: M.ShareParams, priors=None):
    h = M.add_history(raw_df, p)
    p.priors = priors or M.fit_priors(between(h, *FIT))
    return M.features(h, p)


def tune(raw_df):
    rows = []
    for hl_long, hl_short in itertools.product((15, 25, 41, 82), (2, 3, 5, 10)):
        p = M.ShareParams(hl_long=hl_long, hl_short=hl_short)
        h = M.add_history(raw_df, p)
        p.priors = M.fit_priors(between(h, *FIT))
        for k_toi, k_shots in itertools.product((150, 300, 600), (50, 100, 150, 300)):
            p.k_toi, p.k_shots = k_toi, k_shots
            f = M.features(h, p)
            fit, val = between(f, *FIT), between(f, *VAL)
            beta = M.fit_beta(fit)
            rows.append({"hl_long": hl_long, "hl_short": hl_short, "k_toi": k_toi, "k_shots": k_shots,
                         "val_ll_per_goal": ll_per_goal(val, M.predict_shares(val, beta))})
    return pd.DataFrame(rows).sort_values("val_ll_per_goal", ascending=False)


def sbr_lambdas() -> pd.DataFrame:
    s = pd.DataFrame(json.load(open(RAW / "nhl" / "nhl_sbr.json")))
    s = s[(s["home_team"].astype(str) != "0") & (s["away_team"].astype(str) != "0")]
    oh, oa = american_to_decimal(s["home_close_ml"]), american_to_decimal(s["away_close_ml"])
    ph = (1 / oh) / (1 / oh + 1 / oa)
    oo = pd.to_numeric(s["close_over_under_odds"], errors="coerce").to_numpy(float)
    ok = (np.abs(oo) >= 100) & (np.abs(oo) <= 200)
    po = np.where(ok, 1 / american_to_decimal(np.where(ok, oo, -110)) / 1.045, 0.5).clip(0.3, 0.7)
    line = pd.to_numeric(s["close_over_under"], errors="coerce").to_numpy(float)
    lam = [M.team_lambdas(a, b, c) if np.isfinite(a) and c >= 4 else (np.nan, np.nan)
           for a, b, c in zip(ph, po, line)]
    out = pd.DataFrame({"date": pd.to_datetime(s["date"].astype(int).astype(str), format="%Y%m%d"),
                        "home_team": s["home_team"].map(SBR_TEAMS), "away_team": s["away_team"].map(SBR_TEAMS),
                        "lam_home": [x[0] for x in lam], "lam_away": [x[1] for x in lam]})
    return out.dropna().drop_duplicates(["date", "home_team", "away_team"])


def attach_market(f: pd.DataFrame, lam: pd.DataFrame) -> pd.DataFrame:
    g = f[["game_id", "date", "team", "opp", "home"]].copy()
    g["home_team"] = np.where(g["home"], g["team"], g["opp"])
    g["away_team"] = np.where(g["home"], g["opp"], g["team"])
    g = g.merge(lam, on=["date", "home_team", "away_team"], how="left")
    f = f.copy()
    f["lam_mkt"] = np.where(g["home"], g["lam_home"], g["lam_away"])
    return f


def calib_table(y, p, bins=(0, .05, .1, .15, .2, .25, .3, .35, .4, .5, 1)):
    c = pd.cut(p, bins)
    t = pd.DataFrame({"y": y, "p": p, "c": c}).groupby("c", observed=True).agg(
        n=("y", "size"), predit=("p", "mean"), observe=("y", "mean"))
    return t


def fmt_pct(x):
    return f"{100 * x:.1f} %"


def main():
    raw_df = nhl_players.load(RAW, SEASONS, refresh_current=True)
    raw_df = raw_df[raw_df["season"] <= TEST[1]]                 # saison en cours : pas évaluée
    print("joueur-matchs :", len(raw_df))

    grid = tune(raw_df)
    best = grid.iloc[0].to_dict()
    print(grid.head(8).to_string())
    p = M.ShareParams(hl_long=best["hl_long"], hl_short=best["hl_short"], k_toi=best["k_toi"],
                      k_shots=best["k_shots"])
    f = build(raw_df, p)
    dev, test = between(f, *DEV), between(f, *TEST).copy()
    beta = M.fit_beta(dev)
    print("beta", dict(zip(M.FEATURES, beta.round(3))))

    # ------------------------------------------------ test conditionnel au nombre de buts
    G = team_goals(test)
    y = (test["goals"].to_numpy() > 0).astype(float)
    n_team = pd.Series(1.0, index=test.index).groupby(
        test["game_id"].astype(np.int64) * 2 + test["home"].astype(np.int64)).transform("size").to_numpy()
    test["S_goals_p1"] = test["S_goals"] + 0.5
    shares = {
        "Uniforme (1/18)": 1 / n_team,
        "Buts récents (pondérés)": M.predict_shares(test, None, "S_goals_p1"),
        "Temps × tirs/min × réussite (sans β)": M.predict_shares(test, None, "r_simple"),
        "Modèle (logit conditionnel)": M.predict_shares(test, beta),
    }
    cond = []
    for name, s in shares.items():
        sc = scores(y, M.p_score_given_goals(G, s))
        cond.append({"modèle": name, "logvrais_par_but": ll_per_goal(test, s), **sc})
    cond = pd.DataFrame(cond)
    print(cond.to_string())

    # ------------------------------------------------ test ancré marché (2018-19 → 2021-22)
    lam = sbr_lambdas()
    fm = attach_market(between(f, 20112012, 20212022), lam)
    s_all = M.predict_shares(fm, beta)
    fm["share"] = s_all
    dev_m = fm[(fm["season"] <= DEV[1]) & fm["lam_mkt"].notna()]
    G_dev = dev_m.groupby(dev_m["game_id"].astype(np.int64) * 2 + dev_m["home"].astype(np.int64))
    tg = G_dev.agg(goals=("goals", "sum"), lam=("lam_mkt", "first"))
    so_adj = float(tg["goals"].sum() / tg["lam"].sum())             # buts « joueurs » / λ marché
    tm = fm[(fm["season"] >= TEST[0]) & fm["lam_mkt"].notna()].copy()
    ym = (tm["goals"].to_numpy() > 0).astype(float)
    nt = tm.groupby(tm["game_id"].astype(np.int64) * 2 + tm["home"].astype(np.int64))["goals"].transform("size")
    lam_avg = float(tg["goals"].mean())                              # λ moyen (sans marché), dev
    variants = {
        "λ marché + part uniforme": M.p_score(tm["lam_mkt"] * so_adj, 1 / nt),
        "λ moyen ligue + part modèle": M.p_score(lam_avg, tm["share"]),
        "λ marché + part modèle": M.p_score(tm["lam_mkt"] * so_adj, tm["share"]),
    }
    mkt = pd.DataFrame([{"variante": k, **scores(ym, np.asarray(v))}
                        for k, v in variants.items()])
    print("so_adj", so_adj, "couverture", tm["game_id"].nunique(), "matchs")
    print(mkt.to_string())
    p_main = np.asarray(variants["λ marché + part modèle"])
    cal = calib_table(ym, p_main)
    top = p_main >= 0.2
    top_sc = {k: scores(ym[top], np.asarray(v)[top]) for k, v in variants.items()}

    # ------------------------------------------------ modèle final pour l'usage quotidien
    full = between(f, DEV[0], TEST[1])
    beta_full = M.fit_beta(full)
    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    OUT_MODEL.write_text(json.dumps({
        "params": {k: float(best[k]) for k in ("hl_long", "hl_short", "k_toi", "k_shots")},
        "beta": dict(zip(M.FEATURES, map(float, beta_full))), "priors": p.priors, "so_adj": so_adj,
        "trained_on": f"{DEV[0]}-{TEST[1]}"}, indent=1), encoding="utf-8")

    write_md(grid, best, beta, cond, mkt, so_adj, tm, cal, top_sc, int(top.sum()), beta_full)


def write_md(grid, best, beta, cond, mkt, so_adj, tm, cal, top_sc, n_top, beta_full):
    L = ["# Modèle buteurs NHL : résultats (généré par `scripts/nhl_buteurs.py`)", "",
         "Modèle : `sportpred/models/nhl_scorers.py`. Buts attendus de l'équipe tirés du marché, "
         "seule la répartition entre joueurs est modélisée (logit conditionnel).", "",
         "## 1. Réglage (ajustement 2011-12 → 2015-16, validation 2016-17 → 2017-18)", "",
         "| demi-vie longue | demi-vie temps de jeu | k minutes | k tirs | log-vrais. / but (valid.) |",
         "|---|---|---|---|---|"]
    for r in grid.head(6).itertuples():
        L.append(f"| {r.hl_long:g} | {r.hl_short:g} | {r.k_toi:g} | {r.k_shots:g} | {r.val_ll_per_goal:.4f} |")
    L += ["", f"Retenu : demi-vie {best['hl_long']:g} matchs (tirs, buts), {best['hl_short']:g} matchs "
          f"(temps de jeu), rétrécissement {best['k_toi']:g} minutes / {best['k_shots']:g} tirs.", "",
          "Coefficients β (ajustés sur 2011-12 → 2017-18) :", "",
          "| variable | β | sens |", "|---|---|---|"]
    sens = {"l_toi": "log temps de jeu attendu", "l_pp": "log temps en supériorité",
            "l_spm": "log tirs par minute (rétréci)", "l_sh": "log réussite au tir (rétrécie)",
            "is_d": "défenseur", "new": "moins de 10 matchs d'historique"}
    for k, b in zip(M.FEATURES, beta):
        L.append(f"| `{k}` | {b:+.3f} | {sens[k]} |")
    L += ["", "## 2. Test hors échantillon 2018-19 → 2025-26, sachant le nombre de buts de l'équipe", "",
          "P(joueur marque | l'équipe marque G buts) = 1 − (1 − part)^G. Mesure la qualité de la "
          "**répartition** seule.", "",
          "| répartition | log-vrais. / but | log-loss | Brier |", "|---|---|---|---|"]
    for r in cond.itertuples():
        L.append(f"| {r[1]} | {r.logvrais_par_but:.4f} | {r.log_loss:.4f} | {r.brier:.4f} |")
    L += ["", f"## 3. Test ancré marché 2018-19 → 2021-22 ({tm['game_id'].nunique()} matchs, "
          f"{len(tm)} joueur-matchs)", "",
          "λ équipe = cotes de clôture (vainqueur + total, sans marge, deux lois de Poisson). "
          f"Facteur buts « joueurs » / λ marché (tirs au but exclus) estimé sur 2011-12 → 2017-18 : "
          f"{so_adj:.3f}.", "", "| variante | log-loss | Brier |", "|---|---|---|"]
    for r in mkt.itertuples():
        L.append(f"| {r.variante} | {r.log_loss:.4f} | {r.brier:.4f} |")
    L += ["", f"Joueurs à P ≥ 20 % (ceux que les bookmakers proposent en priorité, n = {n_top}) :", "",
          "| variante | log-loss | Brier |", "|---|---|---|"]
    for k, v in top_sc.items():
        L.append(f"| {k} | {v['log_loss']:.4f} | {v['brier']:.4f} |")
    L += ["", "Calibration (λ marché + part modèle) :", "", "| tranche | n | prédit | observé |",
          "|---|---|---|---|"]
    for idx, r in cal.iterrows():
        L.append(f"| {idx} | {int(r['n'])} | {fmt_pct(r['predit'])} | {fmt_pct(r['observe'])} |")
    L += ["", "## 4. Modèle de production", "",
          "β réajusté sur 2011-12 → 2025-26, enregistré dans `data/processed/nhl_scorer_model.json` :", "",
          "| variable | β |", "|---|---|"]
    for k, b in zip(M.FEATURES, beta_full):
        L.append(f"| `{k}` | {b:+.3f} |")
    L += ["", "## 5. Limites", "",
          "- Aucun historique gratuit de cotes buteurs : la comparaison avec Pinnacle se construit "
          "jour après jour (archive `dashboard-data`, voir docs/12). Tant qu'elle n'a pas montré "
          "que le modèle apporte quelque chose **en plus** de Pinnacle, il reste indicatif.",
          "- Composition d'équipe : en direct, l'alignement est estimé (dernier match / effectif), "
          "pas lu sur la feuille de match ; un joueur absent fausse sa ligne et un peu les autres.",
          "- Gardien adverse, rencontres consécutives (back-to-back) et blessures en cours de match "
          "ne sont pas modélisés : ils passent par λ (le marché les intègre) mais pas par les parts.", ""]
    OUT_MD.write_text("\n".join(L), encoding="utf-8")
    print("écrit", OUT_MD)


if __name__ == "__main__":
    main()
