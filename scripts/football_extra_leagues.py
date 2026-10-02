"""Test de robustesse sur 16 championnats « extra » (cotes de clôture uniquement).

Échantillon indépendant de celui utilisé pour concevoir les stratégies : Argentine,
Autriche, Brésil, Chine, Danemark, Finlande, Irlande, Japon, Mexique, Norvège, Pologne,
Roumanie, Russie, Suède, Suisse, MLS. 2012-2026, ~63 000 matchs.

Stratégie testée : probabilité juste = clôture Pinnacle sans marge (puis Betfair
Exchange quand Pinnacle disparaît), pari à la meilleure cote de clôture (MaxC) ou à
bet365 (B365C) quand EV > seuil. Plus la carte du biais favori/outsider (AvgC).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportpred.backtest.metrics import bootstrap_roi  # noqa: E402
from sportpred.betting.odds import devig  # noqa: E402

OUT = ROOT / "results" / "football"
OUT.mkdir(parents=True, exist_ok=True)


def stats(pnl):
    pnl = np.asarray(pnl)
    if len(pnl) == 0:
        return dict(n=0)
    lo, hi, p0 = bootstrap_roi(np.ones(len(pnl)), pnl, n_boot=1000)
    return dict(n=len(pnl), ROI=pnl.mean(), IC_bas=lo, IC_haut=hi, p_ROI_le0=p0)


def main():
    df = pd.read_parquet(ROOT / "data" / "processed" / "football_extra.parquet")
    gd = df["FTHG"] - df["FTAG"]
    df["y"] = np.where(gd > 0, 0, np.where(gd == 0, 1, 2))
    df["year"] = df["Date"].dt.year
    sh = df[["PSCH", "PSCD", "PSCA"]].copy()
    bfe = df[["BFECH", "BFECD", "BFECA"]].values if "BFECH" in df else None
    if bfe is not None:
        for j, c in enumerate(sh.columns):
            sh[c] = sh[c].fillna(pd.Series(bfe[:, j], index=df.index))
    ok = sh.notna().all(axis=1).values
    p = np.full((len(df), 3), np.nan)
    p[ok] = devig(sh.values[ok], "power")
    rows = []
    for book in ("MaxC", "B365C", "AvgC"):
        cols = [f"{book}H", f"{book}D", f"{book}A"]
        if not all(c in df for c in cols):
            continue
        o = df[cols].values
        ev = p * o - 1
        for thr in (0.0, 0.02, 0.05):
            for per, m in {"2012-2018": df["year"] <= 2018, "2019-2026": df["year"] >= 2019}.items():
                sel = (ev > thr) & (ev <= 0.3) & m.values[:, None]
                # un pari par match : l'issue de plus forte EV
                evm = np.where(sel, ev, -np.inf)
                j = evm.argmax(axis=1)
                has = np.isfinite(evm.max(axis=1))
                won = (df["y"].values == j)[has]
                odds = o[has, j[has]]
                rows.append({"cote_jouée": book, "EV>": thr, "période": per,
                             **stats(np.where(won, odds - 1, -1.0))})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "extra_leagues_sharp_vs_soft.csv", index=False)
    print(res.round(4).to_string(index=False))
    # par championnat (MaxC, EV>2 %)
    o = df[["MaxCH", "MaxCD", "MaxCA"]].values
    ev = p * o - 1
    sel = (ev > 0.02) & (ev <= 0.3)
    evm = np.where(sel, ev, -np.inf)
    j = evm.argmax(axis=1)
    has = np.isfinite(evm.max(axis=1))
    d = pd.DataFrame({"league": df["League"].values[has],
                      "pnl": np.where(df["y"].values[has] == j[has], o[has, j[has]] - 1, -1.0)})
    by = d.groupby("league")["pnl"].agg(["size", "mean"]).rename(columns={"size": "n", "mean": "ROI"})
    by.to_csv(OUT / "extra_leagues_par_championnat.csv")
    print(by.round(4).to_string())


if __name__ == "__main__":
    main()
