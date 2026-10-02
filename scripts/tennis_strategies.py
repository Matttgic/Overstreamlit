"""Tennis : analyse approfondie de la stratégie « sharp vs meilleure cote ».

- probabilité juste = Pinnacle sans marge (puis Betfair Exchange après 02/2026) ;
- pari sur la meilleure cote du marché (Max), ou sur bet365 seul (proxy « un seul
  bookmaker agréé ANJ » : bet365 est agréé en France depuis mai 2026) ;
- ventilation par année, par tour (ATP/WTA), par surface, par tranche de cote ;
- simulation de bankroll (mise fixe, Kelly 1/4 et 1/2) sur la période de test.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportpred.backtest.engine import simulate  # noqa: E402
from sportpred.backtest.metrics import bootstrap_roi  # noqa: E402
from sportpred.betting.odds import devig  # noqa: E402

OUT = ROOT / "results" / "multisport"
SPLIT = {"ATP": 2015, "WTA": 2016}


def candidates(df: pd.DataFrame, book: str) -> pd.DataFrame:
    d = df.dropna(subset=["sharp_home", "sharp_away", f"{book}_home", f"{book}_away"]).copy()
    p = devig(d[["sharp_home", "sharp_away"]].values, "power")
    parts = []
    for side, j, won in (("home", 0, d["home_win"].values), ("away", 1, ~d["home_win"].values)):
        parts.append(pd.DataFrame({"date": d["date"].values, "match": (d["home"] + " - " + d["away"]).values,
                                   "season": d["season"].values, "tour": d["tour"].values,
                                   "surface": d["surface"].values, "p": p[:, j],
                                   "odds": d[f"{book}_{side}"].values, "won": won}))
    c = pd.concat(parts, ignore_index=True)
    c["ev"] = c["p"] * c["odds"] - 1
    return c


def stats(c):
    if len(c) == 0:
        return dict(n=0)
    pnl = np.where(c["won"], c["odds"] - 1, -1.0)
    lo, hi, p0 = bootstrap_roi(np.ones(len(c)), pnl, n_boot=1000)
    return dict(n=len(c), ROI=pnl.mean(), IC_bas=lo, IC_haut=hi, p_ROI_le0=p0)


def main():
    frames = []
    for tour in ("atp", "wta"):
        d = pd.read_parquet(ROOT / "data" / "processed" / f"tennis_{tour}_predictions.parquet")
        d["tour"] = tour.upper()
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    rows = []
    sel_all = {}
    for book in ("Max", "B365", "Avg"):
        c = candidates(df, book)
        c = c[(c["ev"] > 0.02) & (c["ev"] <= 0.3)]
        c = c.sort_values("ev", ascending=False).drop_duplicates(["date", "match"]).sort_values("date")
        c["test"] = c.apply(lambda r: r["season"] >= SPLIT[r["tour"]], axis=1)
        sel_all[book] = c
        for (tour, test), g in c.groupby(["tour", "test"]):
            rows.append({"cote": book, "tour": tour, "période": "test" if test else "dev", **stats(g)})
        if book == "Max":
            for y, g in c.groupby("season"):
                rows.append({"cote": book, "tour": "ATP+WTA", "période": f"année {y}", **stats(g)})
            for s, g in c[c["test"]].groupby("surface"):
                rows.append({"cote": book, "tour": "ATP+WTA", "période": f"test, surface {s}", **stats(g)})
            bands = pd.cut(c["odds"], [1, 1.5, 2, 3, 5, 100])
            for b, g in c[c["test"]].groupby(bands, observed=True):
                rows.append({"cote": book, "tour": "ATP+WTA", "période": f"test, cotes {b}", **stats(g)})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "tennis_sharp_vs_soft_detail.csv", index=False)
    print(res.round(4).to_string(index=False))

    # simulation de bankroll sur la période test (Max, EV>2 %)
    t = sel_all["Max"][sel_all["Max"]["test"]].copy()
    srows = []
    curves = {}
    # mise plafonnée à 50 € : ordre de grandeur des limites appliquées aux gagnants
    for name, kw in {"mise fixe 10 €": dict(staking="flat", flat_frac=0.01),
                     "Kelly 1/4 (plafond 2 %, max 50 €)": dict(staking="kelly", kelly_frac=0.25, cap=0.02),
                     "Kelly 1/2 (plafond 5 %, max 50 €)": dict(staking="kelly", kelly_frac=0.5, cap=0.05)}.items():
        b, s = simulate(t, bankroll0=1000, max_daily_exposure=0.3, max_stake=50.0, **kw)
        srows.append({"staking": name, **s})
        curves[name] = b[["date", "bankroll"]]
    st = pd.DataFrame(srows)
    st.to_csv(OUT / "staking_tennis_sharp_vs_max.csv", index=False)
    print(st.round(3).to_string(index=False))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5))
    for k, v in curves.items():
        ax.plot(pd.to_datetime(v["date"]), v["bankroll"], label=k, lw=1.2)
    ax.set_yscale("log")
    ax.axhline(1000, color="grey", ls="--", lw=0.8)
    ax.set_title("Tennis ATP+WTA — Pinnacle/Betfair juste vs meilleure cote (EV>2 %), période test")
    ax.set_ylabel("Bankroll (€, log)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "tennis_bankroll_test.png", dpi=110)


if __name__ == "__main__":
    main()
