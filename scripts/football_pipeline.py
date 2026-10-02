"""Pipeline football complet : notes + modèles walk-forward -> prédictions hors-échantillon.

Produit data/processed/football_predictions.parquet avec, pour chaque match :
- probabilités marché (Pinnacle ouverture/clôture, moyenne, max…) sans marge
- Elo, pi-ratings (+ calibration logit ordonné saison par saison)
- Dixon-Coles (ré-estimé chaque semaine, fenêtre 3 ans)
- LightGBM (ré-entraîné chaque saison) : version « pure » (sans cotes) et « hybride »

Usage : python scripts/football_pipeline.py [--which main|extra] [--workers 4]
"""
from __future__ import annotations

import argparse
import sys
import time
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportpred.features import add_basics, add_market_probs, team_form  # noqa: E402
from sportpred.models import dixon_coles as dcm  # noqa: E402
from sportpred.models.elo import football_elo  # noqa: E402
from sportpred.models.ordered import OrderedLogit  # noqa: E402
from sportpred.models.pi_ratings import pi_ratings  # noqa: E402

warnings.filterwarnings("ignore")
PROC = ROOT / "data" / "processed"


def _dc_group(args):
    g, refit_days = args
    return dcm.walk_forward(g, group_col="Country", refit_days=refit_days)


def season_walk_forward_ordered(df: pd.DataFrame, xcol: str, prefix: str, min_seasons: int = 2):
    """Calibre score -> 1N2 avec un logit ordonné ré-estimé à chaque saison (passé seul)."""
    out = pd.DataFrame(index=df.index, columns=[f"{prefix}_ph", f"{prefix}_pd", f"{prefix}_pa"],
                       dtype=float)
    seasons = sorted(df["SeasonKey"].unique())
    for i, s in enumerate(seasons):
        if i < min_seasons:
            continue
        tr = df[(df["SeasonKey"] < s) & (df["SeasonKey"] >= seasons[max(0, i - 6)])]
        te = df[df["SeasonKey"] == s]
        m = OrderedLogit().fit(tr[xcol].values, tr["y"].values)
        out.loc[te.index] = m.predict_proba(te[xcol].values)
    return out


FEATS_BASE = ["elo_diff", "elo_h", "elo_a", "pi_gd", "pi_hh", "pi_ha", "pi_ah", "pi_aa",
              "dc_ph", "dc_pd", "dc_pa", "dc_lambda", "dc_mu", "dc_over25"]


def lgbm_walk_forward(df: pd.DataFrame, feats: list[str], prefix: str, target: str = "y",
                      n_class: int = 3, first_season: int = 2008, train_seasons: int = 8):
    import lightgbm as lgb
    cols = [f"{prefix}_ph", f"{prefix}_pd", f"{prefix}_pa"] if n_class == 3 else [f"{prefix}_p"]
    out = pd.DataFrame(index=df.index, columns=cols, dtype=float)
    params = dict(objective="multiclass" if n_class == 3 else "binary",
                  num_class=n_class if n_class == 3 else 1, learning_rate=0.03,
                  num_leaves=15, min_data_in_leaf=200, feature_fraction=0.7,
                  bagging_fraction=0.8, bagging_freq=1, lambda_l2=5.0, verbose=-1,
                  num_threads=4)
    for s in sorted(df["SeasonKey"].unique()):
        if s < first_season:
            continue
        tr = df[(df["SeasonKey"] < s) & (df["SeasonKey"] >= s - train_seasons)].dropna(subset=feats)
        te = df[df["SeasonKey"] == s]
        if len(tr) < 2000 or len(te) == 0:
            continue
        # validation interne = dernière saison d'entraînement (early stopping honnête)
        va = tr[tr["SeasonKey"] == s - 1]
        tr2 = tr[tr["SeasonKey"] < s - 1]
        dtr = lgb.Dataset(tr2[feats], tr2[target])
        dva = lgb.Dataset(va[feats], va[target])
        m = lgb.train(params, dtr, 2000, valid_sets=[dva],
                      callbacks=[lgb.early_stopping(100, verbose=False)])
        # ré-entraînement sur tout le passé avec le nb d'itérations trouvé
        m = lgb.train(params, lgb.Dataset(tr[feats], tr[target]), max(m.best_iteration, 50))
        p = m.predict(te[feats])
        out.loc[te.index] = p if n_class == 3 else p.reshape(-1, 1)
    return out


def run(which: str = "main", workers: int = 4, refit_days: int = 7, countries: str = ""):
    t0 = time.time()
    df = pd.read_parquet(PROC / f"football_{which}.parquet")
    if which == "extra":
        df["Country"] = df["League"]
        df["SeasonKey"] = df["Season"].astype(int)
    df = add_basics(df) if which == "main" else _basics_extra(df)
    tag = which
    if countries:
        df = df[df["Country"].isin(countries.split(","))]
        tag = f"{which}_{countries.replace(',', '')}"

    if which == "main":
        df["SeasonKey"] = 2000 + df["Season"].str[:2].astype(int)
    df = add_market_probs(df)
    print(f"[{time.time()-t0:.0f}s] marché ok, {len(df)} matchs")

    df = df.join(football_elo(df, k=20, hfa=65, group_col="Country"))
    df = df.join(pi_ratings(df, group_col="Country"))
    print(f"[{time.time()-t0:.0f}s] elo + pi ok")

    cache = PROC / f"cache_dixon_coles_{tag}_{refit_days}d.parquet"
    if cache.exists() and len(pd.read_parquet(cache, columns=["dc_ph"])) > 0:
        dc = pd.read_parquet(cache)
        dc.index = dc.pop("_idx").values
    else:
        groups = [(g, refit_days) for _, g in df.groupby("Country")]
        with Pool(workers) as pool:
            dc = pd.concat(pool.map(_dc_group, groups))
        dc.assign(_idx=dc.index).to_parquet(cache, index=False)
    df = df.join(dc)
    print(f"[{time.time()-t0:.0f}s] dixon-coles ok ({dc['dc_ph'].notna().sum()} prédictions)")

    df = df.join(season_walk_forward_ordered(df, "elo_diff", "elo"))
    df = df.join(season_walk_forward_ordered(df, "pi_gd", "pi"))
    print(f"[{time.time()-t0:.0f}s] calibrations ok")

    if which == "main":
        df = df.join(team_form(df))
        form = [c for c in df.columns if c.startswith(("h_", "a_")) and ("ew" in c or c.endswith(
            ("rest_days", "n_played")))]
        df["league_code"] = df["League"].astype("category").cat.codes
        feats = FEATS_BASE + form + ["league_code"]
        df = df.join(lgbm_walk_forward(df, feats, "gbm"))
        print(f"[{time.time()-t0:.0f}s] gbm pur ok")
        mk = ["mk_avg_ph", "mk_avg_pd", "mk_avg_pa", "mk_avg_margin"]
        df = df.join(lgbm_walk_forward(df, feats + mk, "gbmh", first_season=2010))
        print(f"[{time.time()-t0:.0f}s] gbm hybride ok")
        df = df.join(lgbm_walk_forward(df, feats, "gbmou", target="over25", n_class=2))
        print(f"[{time.time()-t0:.0f}s] gbm over/under ok")

    out = PROC / f"football_{tag}_predictions.parquet"
    df.to_parquet(out, index=False)
    print(f"[{time.time()-t0:.0f}s] écrit {out}")
    return df


def _basics_extra(df):
    df = df.copy()
    gd = df["FTHG"] - df["FTAG"]
    df["y"] = np.where(gd > 0, 0, np.where(gd == 0, 1, 2))
    df["over25"] = (df["FTHG"] + df["FTAG"] > 2.5).astype(int)
    for k, v in {"won_H": 0, "won_D": 1, "won_A": 2}.items():
        df[k] = df["y"] == v
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", default="main")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--refit-days", type=int, default=7)
    ap.add_argument("--countries", default="", help="ex. F,SC pour un test rapide")
    a = ap.parse_args()
    run(a.which, a.workers, a.refit_days, a.countries)
