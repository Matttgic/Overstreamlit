"""Moteur de backtest : simulation d'une stratégie de paris sur l'historique.

Principe (anti-biais) :
1. Les probabilités doivent avoir été produites HORS-ÉCHANTILLON (walk-forward).
2. On ne parie qu'à des cotes réellement disponibles AVANT le match
   (cotes d'« ouverture » football-data = relevées le vendredi / mardi).
3. La bankroll est mise à jour jour par jour : tous les paris d'une même journée sont
   dimensionnés avec la bankroll du matin (pas de réinvestissement intra-journée).
4. On mesure la CLV contre la cote de clôture Pinnacle sans marge.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..betting.kelly import kelly_fraction
from .metrics import summarize_bets


def candidate_bets(df: pd.DataFrame, prob_cols: list[str], odds_cols: list[str],
                   won_cols: list[str], close_fair_cols: list[str] | None = None,
                   labels: list[str] | None = None) -> pd.DataFrame:
    """Transforme un tableau match x issues en tableau de paris candidats (format long)."""
    parts = []
    labels = labels or [str(i) for i in range(len(prob_cols))]
    for i, (pc, oc, wc) in enumerate(zip(prob_cols, odds_cols, won_cols)):
        d = pd.DataFrame({
            "date": df["Date"].values,
            "match": (df["HomeTeam"] + " - " + df["AwayTeam"]).values,
            "league": df["League"].values,
            "selection": labels[i],
            "p": df[pc].values,
            "odds": df[oc].values,
            "won": df[wc].values.astype(bool),
        }, index=df.index)
        if close_fair_cols is not None:
            d["close_fair_odds"] = df[close_fair_cols[i]].values
        parts.append(d)
    c = pd.concat(parts)
    c["ev"] = c["p"] * c["odds"] - 1.0
    if "close_fair_odds" in c:
        c["clv"] = c["odds"] / c["close_fair_odds"] - 1.0
    return c.dropna(subset=["p", "odds"]).sort_values("date", kind="stable")


def simulate(bets: pd.DataFrame, staking: str = "flat", bankroll0: float = 1000.0,
             flat_frac: float = 0.01, kelly_frac: float = 0.25, cap: float = 0.05,
             max_daily_exposure: float = 0.5, one_per_match: bool = True) -> tuple[pd.DataFrame, dict]:
    """Simule la bankroll. `bets` doit déjà être filtré (paris sélectionnés)."""
    b = bets.copy()
    if one_per_match and len(b):
        b = b.sort_values("ev", ascending=False).drop_duplicates(["date", "match"]) \
             .sort_values("date", kind="stable")
    bank = bankroll0
    stakes, banks = [], []
    for d, day in b.groupby("date", sort=True):
        if staking == "flat":
            s = np.full(len(day), flat_frac * bankroll0)          # mise fixe en euros
        elif staking == "flat_pct":
            s = np.full(len(day), flat_frac * bank)               # % de la bankroll courante
        elif staking == "kelly":
            s = np.minimum(kelly_frac * kelly_fraction(day["p"].values, day["odds"].values),
                           cap) * bank
        else:
            raise ValueError(staking)
        tot = s.sum()
        if tot > max_daily_exposure * bank and tot > 0:
            s *= max_daily_exposure * bank / tot
        pnl = np.where(day["won"].values, s * (day["odds"].values - 1), -s)
        bank += pnl.sum()
        stakes.append(pd.Series(s, index=day.index))
        banks.append(pd.Series(bank, index=day.index))
        if bank <= 1:
            break
    if not stakes:
        return b.iloc[0:0], {"n_paris": 0}
    # b est trié par date : les journées traitées correspondent aux premières lignes
    b = b.iloc[:sum(len(x) for x in stakes)].copy()
    b["stake"] = pd.concat(stakes).values
    b["bankroll"] = pd.concat(banks).values
    b = b[b["stake"] > 0]
    return b, summarize_bets(b, bankroll0)


def season_breakdown(bets: pd.DataFrame, season_col: str = "season") -> pd.DataFrame:
    if season_col not in bets:
        bets = bets.assign(season=pd.to_datetime(bets["date"]).dt.year)
    g = bets.groupby(season_col)
    pnl = np.where(bets["won"], bets["stake"] * (bets["odds"] - 1), -bets["stake"])
    bets = bets.assign(pnl=pnl)
    g = bets.groupby(season_col)
    return pd.DataFrame({"n": g.size(), "mise": g["stake"].sum(), "profit": g["pnl"].sum(),
                         "ROI": g["pnl"].sum() / g["stake"].sum()})
