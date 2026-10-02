"""Elo des sélections nationales (méthode eloratings.net) — 1872-2026.

Compétitions ANJ concernées : Coupe du monde, Euro, Ligue des nations, qualifications,
Copa América, CAN… (voir docs/01_reglementation_ANJ.md).
K selon l'importance du match (60 Coupe du monde, 50 tournois continentaux, 40
qualifications/Ligue des nations, 20 amicaux), avantage du terrain 100 points sauf
terrain neutre, multiplicateur d'écart de buts. Les probabilités 1N2 viennent d'un
logit ordonné ré-estimé chaque année sur les 10 années précédentes.
Sortie : results/international/ (qualité des prédictions + classement Elo actuel).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportpred.backtest.metrics import score_table  # noqa: E402
from sportpred.models.elo import goal_multiplier  # noqa: E402
from sportpred.models.ordered import OrderedLogit  # noqa: E402

OUT = ROOT / "results" / "international"
OUT.mkdir(parents=True, exist_ok=True)


def k_factor(t: str) -> float:
    t = t.lower()
    if t == "fifa world cup":
        return 60
    if any(s in t for s in ("euro", "copa am", "african cup of nations", "asian cup", "gold cup",
                            "confederations")) and "qualification" not in t:
        return 50
    if "qualification" in t or "nations league" in t:
        return 40
    if t == "friendly":
        return 20
    return 30


def main():
    r = pd.read_csv(ROOT / "data" / "raw" / "international" / "results.csv").dropna(subset=["home_score"])
    r["date"] = pd.to_datetime(r["date"])
    r = r.sort_values("date", kind="stable").reset_index(drop=True)
    R: dict = {}
    pre = np.zeros((len(r), 2))
    for i, row in enumerate(r.itertuples(index=False)):
        rh, ra = R.get(row.home_team, 1500.0), R.get(row.away_team, 1500.0)
        hfa = 0.0 if row.neutral else 100.0
        pre[i] = [rh, ra]
        e = 1 / (1 + 10 ** (-(rh + hfa - ra) / 400))
        gd = row.home_score - row.away_score
        res = 1.0 if gd > 0 else 0.5 if gd == 0 else 0.0
        d = k_factor(row.tournament) * goal_multiplier(gd) * (res - e)
        R[row.home_team] = rh + d
        R[row.away_team] = ra - d
    r["elo_h"], r["elo_a"] = pre[:, 0], pre[:, 1]
    r["diff"] = r["elo_h"] - r["elo_a"] + np.where(r["neutral"], 0, 100)
    gd = r["home_score"] - r["away_score"]
    r["y"] = np.where(gd > 0, 0, np.where(gd == 0, 1, 2))
    r["year"] = r["date"].dt.year
    probs = np.full((len(r), 3), np.nan)
    for y in range(1990, r["year"].max() + 1):
        tr = r[(r["year"] < y) & (r["year"] >= y - 10)]
        te = r["year"] == y
        if te.sum() == 0:
            continue
        m = OrderedLogit().fit(tr["diff"].values, tr["y"].values)
        probs[te.values] = m.predict_proba(r.loc[te, "diff"].values)
    m = (r["year"] >= 2010).values & ~np.isnan(probs).any(axis=1)
    base = np.tile(np.bincount(r.loc[r["year"] < 2010, "y"], minlength=3) / (r["year"] < 2010).sum(), (m.sum(), 1))
    tab = score_table({"Elo sélections": probs[m], "fréquences de base": base}, r.loc[m, "y"].values)
    comp = r.loc[m, "tournament"].values
    for t in ("FIFA World Cup", "UEFA Euro", "UEFA Nations League"):
        mm = comp == t
        if mm.sum() > 50:
            tab.loc[f"Elo — {t}"] = score_table({"x": probs[m][mm]}, r.loc[m, "y"].values[mm]).iloc[0]
    tab.to_csv(OUT / "qualite_elo_selections.csv")
    print(tab.round(4).to_string())
    last = r["date"].max() - pd.Timedelta(days=4 * 365)
    active = set(r.loc[r["date"] >= last, "home_team"]) | set(r.loc[r["date"] >= last, "away_team"])
    rank = pd.Series({t: v for t, v in R.items() if t in active}).sort_values(ascending=False)
    rank = rank.round(0).rename("elo").to_frame()
    rank.index.name = "sélection"
    rank.to_csv(OUT / "classement_elo_actuel.csv")
    print(rank.head(25).to_string())


if __name__ == "__main__":
    main()
