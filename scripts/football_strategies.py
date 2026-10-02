"""Évaluation de toutes les stratégies football sur l'historique (protocole honnête).

Protocole :
- Période de DÉVELOPPEMENT : saisons 2012/13 -> 2018/19 (choix des paramètres)
- Période de TEST          : saisons 2019/20 -> 2026/27 (jamais utilisée pour choisir)
- Mise fixe de 1 unité pour comparer les ROI ; CLV mesurée contre la clôture Pinnacle
  (ou Betfair Exchange quand Pinnacle n'est plus disponible).
- Le nombre total de configurations testées est reporté (risque de tests multiples).

Sorties : results/football/*.csv, *.md et graphiques PNG.
"""
from __future__ import annotations

import itertools
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportpred import strategies as st  # noqa: E402
from sportpred.backtest.engine import season_breakdown, simulate  # noqa: E402
from sportpred.backtest.metrics import bootstrap_roi, score_table  # noqa: E402
from sportpred.betting.odds import devig  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT / "results" / "football"
OUT.mkdir(parents=True, exist_ok=True)
DEV = (2012, 2018)
TEST = (2019, 2026)
# EV > 30 % = quasi toujours une erreur de cote (« palpable error ») que le bookmaker
# annulerait : on exclut ces paris pour ne pas gonfler artificiellement le ROI.
MAX_EV = 0.30


def load(tag: str = "main"):
    df = pd.read_parquet(ROOT / "data" / "processed" / f"football_{tag}_predictions.parquet")
    # marché Betfair Exchange (référence « sharp » après la disparition de Pinnacle)
    for name, cols in {"bfe": ("BFEH", "BFED", "BFEA"), "bfec": ("BFECH", "BFECD", "BFECA")}.items():
        if all(c in df for c in cols):
            o = df[list(cols)].values
            ok = ~np.isnan(o).any(axis=1)
            p = np.full(o.shape, np.nan)
            p[ok] = devig(o[ok], "power")
            df[[f"mk_{name}_ph", f"mk_{name}_pd", f"mk_{name}_pa"]] = p
            df[[f"fair_{name}_H", f"fair_{name}_D", f"fair_{name}_A"]] = 1 / p
    # proxy « bookmakers français » : meilleure cote entre bwin et bet365 (tous deux agréés
    # ANJ ; bet365 seulement depuis mai 2026) — approximation, les cotes .fr peuvent différer
    for o in st.OUT:
        df[f"FR{o}"] = df[[f"B365{o}", f"BW{o}"]].max(axis=1, skipna=True)
    # référence de clôture « sharp » : Pinnacle si dispo, sinon Betfair Exchange
    for o in st.OUT:
        df[f"fair_sharpc_{o}"] = df[f"fair_psc_{o}"].fillna(df.get(f"fair_bfec_{o}"))
    for s in ("ph", "pd", "pa"):
        df[f"mk_sharp_{s}"] = df[f"mk_ps_{s}"].fillna(df.get(f"mk_bfe_{s}"))
    return df


def period(c: pd.DataFrame, p) -> pd.DataFrame:
    return c[(c["season"] >= p[0]) & (c["season"] <= p[1])]


def stats(c: pd.DataFrame) -> dict:
    if len(c) == 0:
        return {"n": 0}
    pnl = np.where(c["won"], c["odds"] - 1, -1.0)
    lo, hi, p0 = bootstrap_roi(np.ones(len(c)), pnl, n_boot=1000)
    r = {"n": len(c), "ROI": pnl.mean(), "IC_bas": lo, "IC_haut": hi, "p(ROI<=0)": p0,
         "cote_moy": c["odds"].mean(), "réussite": c["won"].mean()}
    if "clv" in c and c["clv"].notna().any():
        r["CLV"] = c["clv"].mean()
    return r


# ---------------------------------------------------------------- 1. qualité
def prediction_quality(df):
    models = {"Elo (logit ordonné)": "elo", "Pi-ratings": "pi", "Dixon-Coles": "dc",
              "LightGBM (sans cotes)": "gbm", "LightGBM hybride (+cotes moy.)": "gbmh",
              "Marché : moyenne bookmakers (ouverture)": "mk_avg",
              "Marché : Pinnacle ouverture": "mk_ps", "Marché : Pinnacle clôture": "mk_psc"}
    rows = []
    for per_name, p in {"dev 2012-2019": DEV, "test 2019-2026": TEST}.items():
        d = df[(df["SeasonKey"] >= p[0]) & (df["SeasonKey"] <= p[1])]
        cols = {k: [f"{v}_ph", f"{v}_pd", f"{v}_pa"] for k, v in models.items()}
        m = np.ones(len(d), bool)
        for c in cols.values():
            m &= d[c].notna().all(axis=1).values
        d = d[m]
        t = score_table({k: d[c].values.astype(float) for k, c in cols.items()}, d["y"].values)
        t.insert(0, "période", per_name)
        rows.append(t)
    res = pd.concat(rows)
    res.to_csv(OUT / "qualite_predictions.csv")
    return res


def quality_by_league(df):
    d = df[(df["SeasonKey"] >= 2012) & df[["mk_psc_ph", "dc_ph", "gbm_ph", "mk_ps_ph"]].notna().all(axis=1)]
    rows = []
    from sportpred.backtest.metrics import rps
    for lg, g in d.groupby("League"):
        r = {"league": lg, "n": len(g)}
        for k in ("dc", "gbm", "mk_avg", "mk_ps", "mk_psc"):
            r[k] = rps(g[[f"{k}_ph", f"{k}_pd", f"{k}_pa"]].values, g["y"].values).mean()
        r["marge_moy_ouverture"] = g["mk_avg_margin"].mean()
        rows.append(r)
    res = pd.DataFrame(rows).set_index("league").sort_values("mk_psc")
    res.to_csv(OUT / "qualite_par_championnat.csv")
    return res


# ---------------------------------------------------------------- 2. biais
def bias_map(df):
    d = df[df["SeasonKey"] >= 2012]
    bands = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 1000]
    rows = []
    for book in ("PSC", "PS", "Avg", "Max", "B365", "BW"):
        for o in st.OUT:
            col = f"{book}{o}"
            if col not in d:
                continue
            x = d[[col, f"won_{o}"]].dropna()
            x["band"] = pd.cut(x[col], bands)
            for b, g in x.groupby("band", observed=True):
                pnl = np.where(g[f"won_{o}"], g[col] - 1, -1)
                rows.append({"cotes": book, "issue": o, "tranche": str(b), "n": len(g),
                             "ROI": pnl.mean(), "erreur_type": pnl.std() / np.sqrt(len(g))})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "carte_des_biais.csv", index=False)
    return res


# ---------------------------------------------------------------- 3. grille
def strategy_grid(df):
    configs = []
    # (a) value betting sur modèle
    for prob, book, ev, mo in itertools.product(["dc", "elo", "pi", "gbm", "gbmh"],
                                                ["Avg", "Max", "BW", "PS", "FR"],
                                                [0.02, 0.05, 0.10], [3.5, 10.0]):
        configs.append(dict(famille="modèle", prob=prob, book=book, min_ev=ev, max_odds=mo))
    # (b) sharp vs soft : proba Pinnacle/Betfair ouverture contre bookmakers « soft »
    for book, ev, mo in itertools.product(["Max", "FR", "BW", "B365", "WH", "IW", "VC", "Avg", "1XB"],
                                          [0.0, 0.02, 0.05], [3.5, 10.0]):
        configs.append(dict(famille="sharp", prob="mk_sharp", book=book, min_ev=ev, max_odds=mo))
    # (b') sharp = Betfair Exchange (seule référence sharp restante depuis fin 2025)
    for book, ev, mo in itertools.product(["Max", "FR", "BW", "B365", "Avg"],
                                          [0.0, 0.02, 0.05], [3.5, 10.0]):
        configs.append(dict(famille="sharp_betfair", prob="mk_bfe", book=book, min_ev=ev,
                            max_odds=mo))
    # (c) consensus Kaunitz
    for book, ev, mo in itertools.product(["Max", "FR", "B365", "BW"], [0.0, 0.02, 0.05], [3.5, 10.0]):
        configs.append(dict(famille="consensus", prob="kz", book=book, min_ev=ev, max_odds=mo))
        configs.append(dict(famille="consensus", prob="mk_avg", book=book, min_ev=ev, max_odds=mo))
    # (d) hybrides modèle + marché sharp
    for prob, book, ev, mo in itertools.product(["hyb_gbm20", "hyb_gbm40", "hyb_dc20", "hyb_dc40"],
                                                ["Max", "FR", "PS"], [0.02, 0.05], [3.5, 10.0]):
        configs.append(dict(famille="hybride", prob=prob, book=book, min_ev=ev, max_odds=mo))

    df = st.kaunitz_probs(df, 0.034, "Avg", "kz")
    for m, w in [("gbm", 0.2), ("gbm", 0.4), ("dc", 0.2), ("dc", 0.4)]:
        df = st.logit_blend(df, m, "sharp", w, f"hyb_{m}{int(w*100)}")

    cache = {}
    rows = []
    for cfg in configs:
        key = (cfg["prob"], cfg["book"])
        if key not in cache:
            cache[key] = st.candidates_1x2(df, cfg["prob"], cfg["book"], close_ref="sharpc")
        c = cache[key]
        if c.empty:
            continue
        sel = st.select_value(c, min_ev=cfg["min_ev"], max_ev=MAX_EV, max_odds=cfg["max_odds"])
        sel = sel.sort_values("ev", ascending=False).drop_duplicates(["date", "match"])
        r = dict(cfg)
        for pn, p in {"dev": DEV, "test": TEST}.items():
            for k, v in stats(period(sel, p)).items():
                r[f"{pn}_{k}"] = v
        rows.append(r)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "grille_strategies_1x2.csv", index=False)
    return res, df


def ou_grid(df):
    rows = []
    for prob, book, ev in itertools.product(["dc_over25", "gbmou_p", "mk_ou_p_over"],
                                            ["Avg", "Max", "B365", "P"], [0.02, 0.05, 0.10]):
        c = st.candidates_ou(df, prob, book, close_ref="ou_pc")
        if c.empty:
            continue
        sel = st.select_value(c, min_ev=ev, max_ev=MAX_EV)
        r = {"prob": prob, "book": book, "min_ev": ev}
        for pn, p in {"dev": DEV, "test": TEST}.items():
            for k, v in stats(period(sel, p)).items():
                r[f"{pn}_{k}"] = v
        rows.append(r)
    # réplique de l'ancien système (Over 2.5 seulement, edge p - 1/cote >= 5 %, cotes B365)
    c = st.candidates_ou(df, "dc_over25", "B365", close_ref="ou_pc")
    c = c[(c["selection"] == "Over2.5") & (c["p"] - 1 / c["odds"] >= 0.05)]
    r = {"prob": "ANCIEN SYSTÈME (DC, Over seul, edge>=5pts)", "book": "B365", "min_ev": None}
    for pn, p in {"dev": DEV, "test": TEST}.items():
        for k, v in stats(period(c, p)).items():
            r[f"{pn}_{k}"] = v
    rows.append(r)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "grille_strategies_over_under.csv", index=False)
    return res


# ---------------------------------------------------------------- 4. sélection
def select_and_validate(grid: pd.DataFrame, min_n: int = 300) -> pd.DataFrame:
    permanent = ["Max", "FR", "B365", "BW", "Avg", "PS"]
    g = grid[(grid["dev_n"] >= min_n) & grid["book"].isin(permanent)].copy()
    g["critère_dev"] = g["dev_ROI"]
    top = g.sort_values("critère_dev", ascending=False).groupby("famille").head(3)
    top = top.sort_values("critère_dev", ascending=False)
    top.to_csv(OUT / "selection_dev_validation_test.csv", index=False)
    return top


def staking_comparison(df, prob, book, min_ev, max_odds, label):
    c = st.candidates_1x2(df, prob, book, close_ref="sharpc")
    sel = st.select_value(c, min_ev=min_ev, max_ev=MAX_EV, max_odds=max_odds)
    sel = period(sel, TEST)
    rows, curves = [], {}
    for name, kw in {"mise fixe 1%": dict(staking="flat", flat_frac=0.01),
                     "1% bankroll courante": dict(staking="flat_pct", flat_frac=0.01),
                     "Kelly 1/10": dict(staking="kelly", kelly_frac=0.1),
                     "Kelly 1/4": dict(staking="kelly", kelly_frac=0.25),
                     "Kelly 1/2": dict(staking="kelly", kelly_frac=0.5),
                     "Kelly complet": dict(staking="kelly", kelly_frac=1.0, cap=0.2)}.items():
        b, s = simulate(sel, bankroll0=1000, max_stake=100.0, **kw)
        s["staking"] = name
        rows.append(s)
        curves[name] = b[["date", "bankroll"]]
    res = pd.DataFrame(rows).set_index("staking")
    res.to_csv(OUT / f"staking_{label}.csv")
    return res, curves


def plot_curves(curves: dict, path: Path, title: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5))
    for k, v in curves.items():
        if len(v):
            ax.plot(pd.to_datetime(v["date"]), v["bankroll"], label=k, lw=1.2)
    ax.axhline(1000, color="grey", lw=0.8, ls="--")
    ax.set_yscale("log")
    ax.set_title(title)
    ax.set_ylabel("Bankroll (€, échelle log)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def cumulative_plot(sel_dict: dict, path: Path, title: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5))
    for k, c in sel_dict.items():
        if len(c) == 0:
            continue
        c = c.sort_values("date")
        pnl = np.where(c["won"], c["odds"] - 1, -1.0).cumsum()
        ax.plot(pd.to_datetime(c["date"]), pnl, label=f"{k} (n={len(c)})", lw=1.1)
    ax.axhline(0, color="grey", lw=0.8)
    ax.axvline(pd.Timestamp("2019-07-01"), color="red", lw=0.8, ls=":")
    ax.text(pd.Timestamp("2019-08-01"), ax.get_ylim()[1] * 0.9, "début TEST", color="red", fontsize=8)
    ax.set_title(title)
    ax.set_ylabel("Profit cumulé (unités, mise fixe 1)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def league_breakdown(df, prob, book, min_ev, max_odds, label):
    c = st.candidates_1x2(df, prob, book, close_ref="sharpc")
    sel = st.select_value(c, min_ev=min_ev, max_ev=MAX_EV, max_odds=max_odds)
    sel = sel.sort_values("ev", ascending=False).drop_duplicates(["date", "match"])
    sel = sel[sel["season"] >= DEV[0]]
    rows = []
    for lg, g in sel.groupby("league"):
        r = {"league": lg}
        r.update(stats(g))
        rows.append(r)
    res = pd.DataFrame(rows).set_index("league").sort_values("ROI", ascending=False)
    res.to_csv(OUT / f"par_championnat_{label}.csv")
    sb = season_breakdown(sel.assign(stake=1.0))
    sb.to_csv(OUT / f"par_saison_{label}.csv")
    return res, sb


def main():
    global OUT
    t0 = time.time()
    tag = sys.argv[1] if len(sys.argv) > 1 else "main"
    if tag != "main":
        OUT = ROOT / "results" / f"football_{tag}"
        OUT.mkdir(parents=True, exist_ok=True)
    df = load(tag)
    print("chargé", df.shape, f"{time.time()-t0:.0f}s")
    q = prediction_quality(df)
    print(q.round(4).to_string())
    ql = quality_by_league(df)
    print(ql.round(4).to_string())
    bm = bias_map(df)
    print(bm[bm.cotes.isin(["PSC", "Avg"])].round(3).to_string())
    grid, df2 = strategy_grid(df)
    print("configs 1X2 :", len(grid), f"{time.time()-t0:.0f}s")
    ou = ou_grid(df)
    print(ou.round(3).to_string())
    top = select_and_validate(grid)
    cols = ["famille", "prob", "book", "min_ev", "max_odds", "dev_n", "dev_ROI", "dev_CLV",
            "test_n", "test_ROI", "test_IC_bas", "test_IC_haut", "test_CLV"]
    print(top[cols].round(4).to_string())
    json.dump({"n_configs_1x2": int(len(grid)), "n_configs_ou": int(len(ou))},
              open(OUT / "meta.json", "w"))

    # analyses détaillées des meilleures configurations de chaque famille (choisies sur dev)
    best = {}
    # bookmakers présents sur toute la période (IW, VC, WH, LB disparaissent des données)
    permanent = ["Max", "FR", "B365", "BW", "Avg", "PS"]
    for fam in ("sharp", "consensus", "modèle", "hybride"):
        g = grid[(grid["famille"] == fam) & (grid["dev_n"] >= 300) & grid["book"].isin(permanent)]
        if len(g):
            best[fam] = g.sort_values("dev_ROI", ascending=False).iloc[0]
    curves_sel = {}
    for fam, r in best.items():
        label = f"{fam}_{r['prob']}_{r['book']}_ev{r['min_ev']}_max{r['max_odds']}"
        res, curves = staking_comparison(df2, r["prob"], r["book"], r["min_ev"], r["max_odds"], label)
        print(label)
        print(res.round(3).to_string())
        plot_curves(curves, OUT / f"bankroll_{fam}.png", f"Football — {label} — période test")
        league_breakdown(df2, r["prob"], r["book"], r["min_ev"], r["max_odds"], label)
        c = st.candidates_1x2(df2, r["prob"], r["book"], close_ref="sharpc")
        sel = st.select_value(c, min_ev=r["min_ev"], max_ev=MAX_EV, max_odds=r["max_odds"])
        sel = sel.sort_values("ev", ascending=False).drop_duplicates(["date", "match"])
        curves_sel[f"{fam}: {r['prob']} vs {r['book']} EV>={r['min_ev']}"] = sel[sel["season"] >= DEV[0]]
    # stratégie « réaliste France » : sharp vs FR (bet365/bwin), mêmes paramètres que sharp
    if "sharp" in best:
        r = best["sharp"]
        c = st.candidates_1x2(df2, "mk_sharp", "FR", close_ref="sharpc")
        sel = st.select_value(c, min_ev=r["min_ev"], max_ev=MAX_EV, max_odds=r["max_odds"])
        sel = sel.sort_values("ev", ascending=False).drop_duplicates(["date", "match"])
        curves_sel[f"sharp: mk_sharp vs FR (bet365/bwin) EV>={r['min_ev']}"] = sel[sel["season"] >= DEV[0]]
    cumulative_plot(curves_sel, OUT / "profit_cumule_familles.png",
                    "Football 2012-2026 — meilleure config de chaque famille (choisie sur 2012-2019)")
    print(f"fini {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
