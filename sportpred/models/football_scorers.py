"""Modèle buteurs football ancré sur le marché (même principe que le modèle NHL, S11).

1. Buts attendus de chaque équipe λ_T : tirés des cotes sans marge (1N2 + plus/moins de 2,5
   buts, deux lois de Poisson, `team_lambdas`). Les buts contre son camp (~3 %) ne comptent
   pour aucun buteur : λ_joueurs = λ_T × (1 − OG_SHARE).
2. Part de chaque joueur s_i (logit conditionnel, chaque but de l'équipe attribué au joueur i
   avec probabilité s_i = exp(η_i) / Σ_j exp(η_j), joueurs de champ ayant joué) :
       η_i = β·x_i,  x = [log(minutes/90), log(taux xG/90), finition, défenseur, milieu,
                          milieu offensif, nouveau]
   taux xG/90 = xG hors penalty par 90 min (moyenne pondérée décroissante des matchs
   précédents, ramenée vers la moyenne du poste) + part des penaltys de l'équipe tirés par le
   joueur × xG de penalty de l'équipe par match. Aucune information du match courant n'entre
   dans les variables (sauf les minutes, connues à l'avance quand on prend « si titulaire »).
3. P(i marque) = 1 − exp(−λ_joueurs × s_i) ; avant le match, minutes = minutes attendues
   quand le joueur est titulaire (cote « si titulaire »).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize
from scipy.stats import poisson

POS_GROUP = {"GK": "G", "DR": "D", "DC": "D", "DL": "D", "DMR": "M", "DMC": "M", "DML": "M",
             "MR": "M", "MC": "M", "ML": "M", "AMR": "A", "AMC": "A", "AML": "A", "FW": "F"}
FEATURES = ["l_min", "l_rate", "l_fin", "is_d", "is_m", "is_a", "new"]
OG_SHARE = 0.028           # part des buts marqués contre son camp (recalculée par `fit`)
PEN_XG = 0.76


@dataclass
class Params:
    hl_rate: float = 38.0      # demi-vie (matchs) des taux xG / buts
    hl_pen: float = 25.0       # demi-vie pour la part des penaltys
    hl_min: float = 6.0        # demi-vie pour les minutes quand titulaire (rôle actuel)
    k_min: float = 900.0       # minutes « fictives » au taux moyen du poste
    k_fin: float = 6.0         # buts « fictifs » pour la finition
    k_team_pen: float = 20.0   # matchs « fictifs » au taux de penaltys moyen
    beta: np.ndarray | None = None
    priors: dict = field(default_factory=dict)
    og_share: float = OG_SHARE


# ------------------------------------------------------------------ historique (sans fuite)
def _ewm_prev(df: pd.DataFrame, cols: list[str], hl: float, key: str | list[str] = "player_id") -> pd.DataFrame:
    """Sommes pondérées décroissantes des matchs PRÉCÉDENTS (poids 1, d, d², …)."""
    d = 0.5 ** (1 / hl)
    out = {}
    keys = [df[k] for k in ([key] if isinstance(key, str) else key)]
    g = df.groupby(keys, sort=False)
    for c in cols:
        m = g[c].transform(lambda s: s.ewm(halflife=hl, adjust=True).mean())
        n = g.cumcount() + 1
        w = (1 - d ** n) / (1 - d)                         # somme des poids jusqu'au match courant
        cum = m * w
        out[c] = cum.groupby(keys, sort=False).shift(1).fillna(0.0)
    return pd.DataFrame(out, index=df.index)


def prepare(df: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Ajoute les cumuls des matchs antérieurs de chaque joueur et de son équipe.
    Lignes `is_future` (matchs à venir, time = 0) : gardées, leurs cumuls couvrent tout
    l'historique du joueur (c'est ce qui sert aux prédictions)."""
    fut = df["is_future"].fillna(False).astype(bool) if "is_future" in df else pd.Series(False, index=df.index)
    df = df[(df["time"] > 0) | fut].copy()
    df["is_future"] = fut.loc[df.index]
    df["grp"] = df["position"].map(POS_GROUP)
    df = df.sort_values(["player_id", "date", "match_id"]).reset_index(drop=True)
    # poste habituel : dernier poste connu comme titulaire (le match courant compte s'il est titulaire)
    known = df["grp"].where(df["starter"])
    df["grp_prev"] = known.groupby(df["player_id"]).ffill().groupby(df["player_id"]).shift(1)
    # poste connu avant le match : celui des titularisations précédentes (sinon celui du jour)
    df["grp_use"] = df["grp_prev"].fillna(df["grp"].where(df["starter"])).fillna("M")
    df = df[(df["grp_use"] != "G") & (df["position"] != "GK")]
    df["n_prev"] = df.groupby("player_id").cumcount()
    df["np_goals"] = df["goals"] - df["pen_goals"]
    # penaltys de l'équipe pendant le match (approximation : pondérés par le temps joué)
    tp = df.groupby(["match_id", "team_id"])[["pen_att", "pen_xg"]].transform("sum")
    df["team_pen_att_on"] = tp["pen_att"] * (df["time"] / 90).clip(upper=1)
    long = _ewm_prev(df, ["time", "npxg", "np_goals"], p.hl_rate)
    df["S_min"], df["S_npxg"], df["S_npg"] = long["time"], long["npxg"], long["np_goals"]
    pen = _ewm_prev(df, ["pen_att", "team_pen_att_on"], p.hl_pen, key=["player_id", "team_id"])   # par club
    df["S_pen"], df["S_tpen"] = pen["pen_att"], pen["team_pen_att_on"]
    # minutes quand titulaire (rôle récent)
    st = df["time"].where(df["starter"])
    df["min_start_exp"] = (st.groupby(df["player_id"]).transform(lambda s: s.ewm(halflife=p.hl_min, ignore_na=True).mean())
                           .groupby(df["player_id"]).shift(1))
    # xG de penalty de l'équipe par match (antérieur, par équipe)
    tm = (df.groupby(["team_id", "date", "match_id"], as_index=False)["pen_xg"].sum()
          .sort_values(["team_id", "date", "match_id"]))
    tm["one"] = 1.0
    tw = _ewm_prev(tm, ["pen_xg", "one"], p.hl_pen, key="team_id")      # sommes décroissantes antérieures
    mu = tm["pen_xg"].mean()
    tm["team_pen_xg_exp"] = (tw["pen_xg"] + p.k_team_pen * mu) / (tw["one"] + p.k_team_pen)
    df = df.merge(tm[["match_id", "team_id", "team_pen_xg_exp"]], on=["match_id", "team_id"], how="left")
    return df


def fit_priors(df: pd.DataFrame) -> dict:
    pri = {}
    for g in ("D", "M", "A", "F"):
        x = df[df["grp_use"] == g]
        pri[g] = {"np90": 90 * x["npxg"].sum() / max(x["time"].sum(), 1),
                  "min_start": x.loc[x["starter"], "time"].mean()}
    pri["team_pen_xg"] = df.groupby(["match_id", "team_id"])["pen_xg"].sum().mean()
    return pri


def features(df: pd.DataFrame, p: Params, minutes: pd.Series | None = None) -> pd.DataFrame:
    """Variables du logit conditionnel. `minutes` : minutes jouées (apprentissage) ou attendues."""
    pri = p.priors
    g = df["grp_use"].where(df["grp_use"].isin(["D", "M", "A", "F"]), "M")
    np0 = g.map({k: pri[k]["np90"] for k in ("D", "M", "A", "F")}) / 90
    np90 = 90 * (df["S_npxg"] + p.k_min * np0) / (df["S_min"] + p.k_min)
    share = (df["S_pen"] / (df["S_tpen"] + 0.75)).clip(0, 1)
    tpen = df["team_pen_xg_exp"].fillna(pri["team_pen_xg"])
    rate = np90 + share * tpen
    fin = (df["S_npg"] + p.k_fin) / (df["S_npxg"] + p.k_fin)
    mins = (df["time"] if minutes is None else minutes).clip(lower=1)
    out = df.copy()
    out["np90"], out["pen_share"], out["rate90"] = np90, share, rate
    out["l_min"] = np.log(mins / 90)
    out["l_rate"] = np.log(rate.clip(lower=1e-3))
    out["l_fin"] = np.log(fin)
    out["is_d"] = (g == "D").astype(float)
    out["is_m"] = (g == "M").astype(float)
    out["is_a"] = (g == "A").astype(float)
    out["new"] = (df["n_prev"] < 5).astype(float)
    return out


# ------------------------------------------------------------------ logit conditionnel
def _groups(df: pd.DataFrame):
    key = df["match_id"].astype(np.int64) * 2 + df["home"].astype(np.int64)
    order = np.argsort(key.to_numpy(), kind="stable")
    k = key.to_numpy()[order]
    starts = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return order, starts


def _shares(eta: np.ndarray, starts: np.ndarray) -> np.ndarray:
    n = len(eta)
    gmax = np.maximum.reduceat(eta, starts)
    idx = np.repeat(np.arange(len(starts)), np.diff(np.r_[starts, n]))
    e = np.exp(eta - gmax[idx])
    return e / np.add.reduceat(e, starts)[idx]


def fit_beta(df: pd.DataFrame, ridge: float = 1.0) -> np.ndarray:
    order, starts = _groups(df)
    X = df[FEATURES].to_numpy(float)[order]
    y = df["goals"].to_numpy(float)[order]
    n = len(y)
    idx = np.repeat(np.arange(len(starts)), np.diff(np.r_[starts, n]))
    G = np.add.reduceat(y, starts)

    def nll(b):
        s = _shares(X @ b, starts)
        ll = (y * np.log(s)).sum()
        grad = X.T @ y - X.T @ (s * G[idx])
        return -ll + ridge * b @ b, -grad + 2 * ridge * b

    b0 = np.zeros(X.shape[1])
    b0[FEATURES.index("l_min")] = 1.0
    b0[FEATURES.index("l_rate")] = 1.0
    return minimize(nll, b0, jac=True, method="L-BFGS-B").x


def predict_shares(df: pd.DataFrame, beta: np.ndarray | None, col: str | None = None) -> np.ndarray:
    order, starts = _groups(df)
    eta = (np.log(df[col].to_numpy(float)[order].clip(1e-9)) if beta is None
           else df[FEATURES].to_numpy(float)[order] @ beta)
    s = _shares(eta, starts)
    out = np.empty_like(s)
    out[order] = s
    return out


# ------------------------------------------------------------------ buts attendus d'équipe
def team_lambdas(p_home: float, p_draw: float, p_over: float, line: float = 2.5) -> tuple[float, float]:
    """λ domicile / extérieur (Poisson indépendants) qui reproduisent P(over `line`) et
    P(victoire domicile) / P(victoire extérieur) sans marge (le nul sert de contrôle)."""
    def p_over_mu(mu):
        k = np.floor(line)
        if line == k:
            return poisson.sf(k, mu) / (1 - poisson.pmf(k, mu))
        return poisson.sf(k, mu)

    if not (p_over_mu(0.3) < p_over < p_over_mu(8.0)):
        return np.nan, np.nan
    mu = brentq(lambda m: p_over_mu(m) - p_over, 0.3, 8.0)
    ks = np.arange(0, 16)
    p_away = 1 - p_home - p_draw
    target = p_home / max(p_home + p_away, 1e-9)            # part de la victoire domicile hors nul

    def ratio(f):
        j = np.outer(poisson.pmf(ks, mu * f), poisson.pmf(ks, mu * (1 - f)))
        w, a = np.tril(j, -1).sum(), np.triu(j, 1).sum()
        return w / (w + a)

    if not (ratio(0.03) < target < ratio(0.97)):
        return np.nan, np.nan
    f = brentq(lambda x: ratio(x) - target, 0.03, 0.97)
    return mu * f, mu * (1 - f)


def p_score(lam_players: np.ndarray, share: np.ndarray) -> np.ndarray:
    return 1 - np.exp(-np.asarray(lam_players) * np.asarray(share))


def fit(df_prepared: pd.DataFrame, p: Params, train_mask: pd.Series) -> Params:
    """Estime les moyennes de poste et β sur les lignes `train_mask` (joueurs de champ)."""
    tr = df_prepared[train_mask & (df_prepared["grp_use"] != "G") & ~df_prepared["is_future"]]
    p.priors = fit_priors(tr)
    tg = tr.groupby(["match_id", "team_id"]).agg(g=("goals", "sum"), tg=("team_goals", "first"))
    p.og_share = float(1 - tg["g"].sum() / tg["tg"].sum())
    X = features(tr, p)
    p.beta = fit_beta(X)
    return p
