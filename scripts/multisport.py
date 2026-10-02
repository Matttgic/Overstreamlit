"""Évaluation multi-sports (tennis ATP/WTA, NBA, NHL, NFL, MLB, MMA).

Pour chaque sport :
1. Elo adapté au sport (paramètres raisonnables tirés de la littérature, NON optimisés
   sur la période de test) -> probabilité calibrée par régression logistique ré-estimée
   chaque saison sur le passé seulement.
2. Comparaison au marché (cotes sans marge, méthode power) : log-loss, Brier.
3. Test d'information : le modèle apporte-t-il quelque chose AU-DELÀ du marché ?
   (régression logistique sur logit(p_marché) + logit(p_modèle), walk-forward)
4. Stratégies à mise fixe : value vs modèle, value vs mélange, carte des biais par
   tranche de cotes, et (tennis) sharp Pinnacle/Betfair vs bookmakers soft.
Protocole dev/test identique au football : les seuils sont comparés sur la période dev,
la période test sert de validation.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportpred.backtest.metrics import bootstrap_roi  # noqa: E402
from sportpred.betting.odds import devig  # noqa: E402
from sportpred.data import other_sports as osp  # noqa: E402
from sportpred.models.team_elo import two_outcome_elo  # noqa: E402

warnings.filterwarnings("ignore")
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results" / "multisport"
OUT.mkdir(parents=True, exist_ok=True)

# paramètres Elo : valeurs usuelles (538, Kovalchik 2016), pas d'optimisation sur le test
SPORTS = {
    "tennis_atp": dict(loader=lambda: osp.load_tennis(RAW, "atp"), elo=dict(dynamic_k=True, surface_col="surface"),
                       split=2015),
    "tennis_wta": dict(loader=lambda: osp.load_tennis(RAW, "wta"), elo=dict(dynamic_k=True, surface_col="surface"),
                       split=2016),
    "nba": dict(loader=lambda: osp.load_nba(RAW), elo=dict(k=20, hfa=100, regress=0.25), split=2017),
    "nhl": dict(loader=lambda: osp.load_nhl(RAW), elo=dict(k=6, hfa=50, regress=0.3), split=2017),
    "nfl": dict(loader=lambda: osp.load_nfl(RAW), elo=dict(k=20, hfa=48, regress=0.33, margin_col="margin"),
                split=2016),
    "mlb": dict(loader=lambda: osp.load_mlb(RAW), elo=dict(k=4, hfa=24, regress=0.33), split=2016),
    "ufc": dict(loader=lambda: osp.load_ufc(RAW), elo=dict(dynamic_k=True), split=2018),
}


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def walk_forward_logreg(df, feats, target="home_win", min_seasons=2):
    out = pd.Series(np.nan, index=df.index)
    seasons = sorted(df["season"].unique())
    for i, s in enumerate(seasons):
        if i < min_seasons:
            continue
        tr = df[(df["season"] < s)].dropna(subset=feats)
        te = df[df["season"] == s].dropna(subset=feats)
        if len(tr) < 300 or len(te) == 0:
            continue
        m = LogisticRegression(C=1.0).fit(tr[feats].values, tr[target].values)
        out.loc[te.index] = m.predict_proba(te[feats].values)[:, 1]
    return out


def ll(p, y):
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))


def roi_stats(c):
    if len(c) == 0:
        return dict(n=0)
    pnl = np.where(c["won"], c["odds"] - 1, -1.0)
    lo, hi, p0 = bootstrap_roi(np.ones(len(c)), pnl, n_boot=1000)
    return dict(n=len(c), ROI=pnl.mean(), IC_bas=lo, IC_haut=hi, p_ROI_le0=p0, cote_moy=c["odds"].mean())


def candidates(df, pcol, oh, oa):
    a = pd.DataFrame({"season": df["season"], "p": df[pcol], "odds": df[oh], "won": df["home_win"]})
    b = pd.DataFrame({"season": df["season"], "p": 1 - df[pcol], "odds": df[oa], "won": ~df["home_win"]})
    c = pd.concat([a, b]).dropna()
    c["ev"] = c["p"] * c["odds"] - 1
    return c


def evaluate(name, cfg):
    df = cfg["loader"]()
    df = df.join(two_outcome_elo(df, **cfg["elo"]))
    ok = df[["odds_home", "odds_away"]].notna().all(axis=1)
    pm = np.full(len(df), np.nan)
    pm[ok.values] = devig(df.loc[ok, ["odds_home", "odds_away"]].values, "power")[:, 0]
    df["p_mkt"] = pm
    df["margin_mkt"] = 1 / df["odds_home"] + 1 / df["odds_away"] - 1
    feats = ["elo_diff"]
    if "elo_surf_diff" in df:
        feats.append("elo_surf_diff")
    if "rank_1" in df:
        df["log_rank_ratio"] = np.log(df["rank_2"].clip(1, 3000).fillna(1500)) - np.log(
            df["rank_1"].clip(1, 3000).fillna(1500))
        feats.append("log_rank_ratio")
    df["p_model"] = walk_forward_logreg(df, feats)
    df["lg_mkt"] = logit(df["p_mkt"])
    df["lg_model"] = logit(df["p_model"])
    df["p_blend"] = walk_forward_logreg(df.dropna(subset=["p_model", "p_mkt"]), ["lg_mkt", "lg_model"]) \
        .reindex(df.index)
    df["y"] = df["home_win"].astype(int)

    split = cfg["split"]
    rows_q, rows_s = [], []
    for per, m in {"dev": df["season"] < split, "test": df["season"] >= split}.items():
        d = df[m & df[["p_model", "p_mkt", "p_blend"]].notna().all(axis=1)]
        if len(d) == 0:
            continue
        rows_q.append({"sport": name, "période": per, "n": len(d),
                       "saisons": f"{d['season'].min()}-{d['season'].max()}",
                       "logloss_modèle": ll(d["p_model"], d["y"]), "logloss_marché": ll(d["p_mkt"], d["y"]),
                       "logloss_mélange": ll(d["p_blend"], d["y"]),
                       "brier_modèle": np.mean((d["p_model"] - d["y"]) ** 2),
                       "brier_marché": np.mean((d["p_mkt"] - d["y"]) ** 2),
                       "marge_moy": d["margin_mkt"].mean()})
        cm = candidates(d, "p_model", "odds_home", "odds_away")
        cb = candidates(d, "p_blend", "odds_home", "odds_away")
        for thr in (0.03, 0.05, 0.10):
            for label, c in (("modèle", cm), ("mélange", cb)):
                s = roi_stats(c[(c["ev"] >= thr) & (c["ev"] <= 0.5)])
                rows_s.append({"sport": name, "période": per, "stratégie": f"value {label} EV>={thr:.0%}", **s})
        # biais favori/outsider : tous les favoris / tous les outsiders
        allc = candidates(d.assign(p_one=0.5), "p_one", "odds_home", "odds_away")
        fav = allc[allc["odds"] < 2.0]
        dog = allc[allc["odds"] >= 2.0]
        for lab, c in (("tous les favoris (cote<2)", fav), ("tous les outsiders (cote>=2)", dog),
                       ("gros favoris (cote<1.3)", allc[allc["odds"] < 1.3]),
                       ("gros outsiders (cote>4)", allc[allc["odds"] > 4])):
            rows_s.append({"sport": name, "période": per, "stratégie": f"biais: {lab}", **roi_stats(c)})
        if "neutral" not in d or (d["neutral"] == 0).all():
            home = pd.DataFrame({"odds": d["odds_home"], "won": d["home_win"]}).dropna()
            away = pd.DataFrame({"odds": d["odds_away"], "won": ~d["home_win"]}).dropna()
            rows_s.append({"sport": name, "période": per, "stratégie": "biais: toujours domicile", **roi_stats(home)})
            rows_s.append({"sport": name, "période": per, "stratégie": "biais: toujours extérieur", **roi_stats(away)})
        # tennis : sharp (Pinnacle puis Betfair Exchange) contre bookmakers soft
        if "sharp_home" in d:
            okk = d[["sharp_home", "sharp_away"]].notna().all(axis=1)
            ds = d[okk].copy()
            ds["p_sharp"] = devig(ds[["sharp_home", "sharp_away"]].values, "power")[:, 0]
            for book in ("B365", "Max", "Avg"):
                c = candidates(ds, "p_sharp", f"{book}_home", f"{book}_away")
                for thr in (0.0, 0.02, 0.05):
                    s = roi_stats(c[(c["ev"] > thr) & (c["ev"] <= 0.3)])
                    rows_s.append({"sport": name, "période": per,
                                   "stratégie": f"sharp vs {book} EV>{thr:.0%}", **s})
        # NHL : valeur de la cote d'ouverture vs clôture (CLV)
        if "odds_home_open" in d:
            o = d.dropna(subset=["odds_home_open", "odds_home", "odds_away_open", "odds_away"])
            clo_fair = 1 / devig(o[["odds_home", "odds_away"]].values, "power")
            c = pd.DataFrame({"season": np.r_[o["season"], o["season"]],
                              "odds": np.r_[o["odds_home_open"], o["odds_away_open"]],
                              "won": np.r_[o["home_win"], ~o["home_win"]],
                              "clv": np.r_[o["odds_home_open"] / clo_fair[:, 0],
                                           o["odds_away_open"] / clo_fair[:, 1]] - 1})
            for lab, cc in (("ouverture: côté dont la cote va baisser (CLV>2%)", c[c["clv"] > 0.02]),
                            ("ouverture: côté dont la cote va monter (CLV<-2%)", c[c["clv"] < -0.02])):
                rows_s.append({"sport": name, "période": per, "stratégie": f"info: {lab}", **roi_stats(cc)})
    df.to_parquet(ROOT / "data" / "processed" / f"{name}_predictions.parquet", index=False)
    return pd.DataFrame(rows_q), pd.DataFrame(rows_s)


def main(only=None):
    qs, ss = [], []
    for name, cfg in SPORTS.items():
        if only and name not in only:
            continue
        q, s = evaluate(name, cfg)
        print(q.round(4).to_string(index=False))
        print(s.round(4).to_string(index=False))
        qs.append(q)
        ss.append(s)
    q = pd.concat(qs)
    s = pd.concat(ss)
    tag = "_".join(only) if only else "all"
    q.to_csv(OUT / f"qualite_{tag}.csv", index=False)
    s.to_csv(OUT / f"strategies_{tag}.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
