"""Modèle buteurs NHL ancré sur le marché.

Idée (reprise de Jejeh040/marqueurs-xiii, adaptée au hockey) : le marché (Pinnacle)
sait mieux que nous combien de buts une équipe va marquer ; on ne modélise que la
répartition de ces buts entre les joueurs.

1. Buts attendus de l'équipe λ_T : tirés du vainqueur et du total de buts (cotes sans
   marge), avec deux lois de Poisson indépendantes (`team_lambdas`).
2. Part de chaque joueur s_i : logit conditionnel. Chaque but de l'équipe est attribué
   au joueur i avec probabilité s_i = exp(η_i) / Σ_j exp(η_j), η_i = x_i·β, où x_i ne
   contient que de l'information connue avant le match (`add_history`, `features`) :
   temps de jeu attendu, temps en supériorité numérique, tirs par minute et réussite au
   tir (moyennes pondérées décroissantes, ramenées vers la moyenne du poste).
3. P(i marque au moins un but) = 1 − exp(−λ_T · s_i)  (Poisson « éclaté »),
   ou, si le nombre de buts G de l'équipe est connu, 1 − (1 − s_i)^G.

Les buts en tirs au but ne sont crédités à aucun joueur (ils ne comptent pas pour le
pari buteur) : λ_T est corrigé par le facteur `SO_ADJ` estimé sur l'historique.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize
from scipy.stats import poisson

FEATURES = ["l_toi", "l_pp", "l_spm", "l_sh", "is_d", "new"]


@dataclass
class ShareParams:
    hl_long: float = 82.0       # demi-vie (en matchs) pour tirs / buts / temps cumulés
    hl_short: float = 10.0      # demi-vie pour le temps de jeu attendu (rôle actuel)
    k_toi: float = 300.0        # minutes « fictives » au rythme moyen du poste (tirs/min)
    k_shots: float = 300.0      # tirs « fictifs » au pourcentage moyen du poste
    beta: np.ndarray | None = None
    priors: dict = field(default_factory=dict)


def _decayed(df: pd.DataFrame, cols: list[str], hl: float) -> pd.DataFrame:
    """Moyennes pondérées décroissantes des matchs PRÉCÉDENTS du joueur (aucune fuite du
    match courant). `df` doit être trié par joueur puis par date."""
    m = df.groupby("player_id", sort=False)[cols].ewm(halflife=hl, adjust=True).mean()
    m = m.reset_index(level=0, drop=True).sort_index()
    return m.groupby(df["player_id"], sort=False).shift(1)


def add_history(df: pd.DataFrame, p: ShareParams) -> pd.DataFrame:
    """Ajoute, pour chaque ligne joueur-match, les cumuls décroissants des matchs antérieurs."""
    df = df.sort_values(["player_id", "date", "game_id"]).reset_index(drop=True)
    df["n_prev"] = df.groupby("player_id", sort=False).cumcount()
    d = 0.5 ** (1 / p.hl_long)
    w = (1 - d ** df["n_prev"]) / (1 - d)                     # somme des poids des matchs passés
    long = _decayed(df, ["toi", "shots", "goals"], p.hl_long)
    for c in ("toi", "shots", "goals"):
        df[f"S_{c}"] = (long[c] * w).fillna(0.0)
    short = _decayed(df, ["toi", "pp_toi"], p.hl_short)
    df["toi_exp"], df["pp_exp"] = short["toi"], short["pp_toi"]
    return df


def fit_priors(df: pd.DataFrame) -> dict:
    """Moyennes par poste (avants / défenseurs) et temps de jeu des débutants."""
    pri = {}
    for grp, m in (("F", df["pos"] != "D"), ("D", df["pos"] == "D")):
        x = df[m]
        deb = x[x["n_prev"] < 5] if "n_prev" in x else x
        pri[grp] = {"spm": x["shots"].sum() / x["toi"].sum(), "sh": x["goals"].sum() / x["shots"].sum(),
                    "toi_new": deb["toi"].mean(), "pp_new": deb["pp_toi"].mean()}
    return pri


def features(df: pd.DataFrame, p: ShareParams) -> pd.DataFrame:
    pri = p.priors
    isd = (df["pos"] == "D").to_numpy()
    spm0 = np.where(isd, pri["D"]["spm"], pri["F"]["spm"])
    sh0 = np.where(isd, pri["D"]["sh"], pri["F"]["sh"])
    toi0 = np.where(isd, pri["D"]["toi_new"], pri["F"]["toi_new"])
    pp0 = np.where(isd, pri["D"]["pp_new"], pri["F"]["pp_new"])
    spm = (df["S_shots"] + p.k_toi * spm0) / (df["S_toi"] + p.k_toi)
    sh = (df["S_goals"] + p.k_shots * sh0) / (df["S_shots"] + p.k_shots)
    toi = df["toi_exp"].fillna(pd.Series(toi0, index=df.index)).clip(lower=3)
    pp = df["pp_exp"].fillna(pd.Series(pp0, index=df.index)).clip(lower=0)
    out = df.copy()
    out["l_toi"] = np.log(toi)
    out["l_pp"] = np.log(pp + 0.25)
    out["l_spm"] = np.log(spm)
    out["l_sh"] = np.log(sh)
    out["is_d"] = isd.astype(float)
    out["new"] = (df["n_prev"] < 10).astype(float)
    out["r_simple"] = toi * spm * sh                      # buts attendus « naïfs » (sans β)
    return out


def _groups(df: pd.DataFrame):
    key = df["game_id"].astype(np.int64) * 2 + df["home"].astype(np.int64)
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
    """Logit conditionnel : max Σ_buts log s_buteur, groupes = (match, équipe)."""
    order, starts = _groups(df)
    X = df[FEATURES].to_numpy(float)[order]
    y = df["goals"].to_numpy(float)[order]
    n = len(y)
    idx = np.repeat(np.arange(len(starts)), np.diff(np.r_[starts, n]))
    G = np.add.reduceat(y, starts)

    def nll(b):
        eta = X @ b
        s = _shares(eta, starts)
        ll = (y * np.log(s)).sum()
        grad = X.T @ y - X.T @ (s * G[idx])
        return -ll + ridge * b @ b, -grad + 2 * ridge * b

    b0 = np.zeros(X.shape[1])
    b0[FEATURES.index("l_toi")] = 1.0
    b0[FEATURES.index("l_spm")] = 1.0
    b0[FEATURES.index("l_sh")] = 1.0
    res = minimize(nll, b0, jac=True, method="L-BFGS-B")
    return res.x


def predict_shares(df: pd.DataFrame, beta: np.ndarray | None, col: str | None = None) -> np.ndarray:
    """Parts s_i dans l'ordre de `df` (beta=None -> parts proportionnelles à `col`)."""
    order, starts = _groups(df)
    if beta is None:
        eta = np.log(df[col].to_numpy(float)[order].clip(1e-9))
    else:
        eta = df[FEATURES].to_numpy(float)[order] @ beta
    s = _shares(eta, starts)
    out = np.empty_like(s)
    out[order] = s
    return out


# ------------------------------------------------------------------ buts attendus d'équipe
def team_lambdas(p_home_win: float, p_over: float, line: float, ot_home: float = 0.5) -> tuple[float, float]:
    """λ domicile / extérieur à partir des probabilités sans marge.

    p_home_win : victoire domicile prolongation et tirs au but compris ;
    p_over : P(total > line) (ligne entière : P(over | pas de remboursement)).
    Le nul après 60 minutes est partagé avec `ot_home` (≈ 0,5).
    """
    def p_over_mu(mu):
        k = np.floor(line)
        if line == k:                                   # ligne entière : remboursement si = line
            po, pe = poisson.sf(k, mu), poisson.pmf(k, mu)
            return po / (1 - pe)
        return poisson.sf(k, mu)

    lo, hi = 0.5, 15.0
    if not (p_over_mu(lo) < p_over < p_over_mu(hi)):
        return np.nan, np.nan
    mu = brentq(lambda m: p_over_mu(m) - p_over, lo, hi)
    ks = np.arange(0, 21)

    def p_home(f):
        ph, pa = poisson.pmf(ks, mu * f), poisson.pmf(ks, mu * (1 - f))
        joint = np.outer(ph, pa)
        win = np.tril(joint, -1).sum()
        tie = np.trace(joint)
        return win + ot_home * tie

    if not (p_home(0.02) < p_home_win < p_home(0.98)):
        return np.nan, np.nan
    f = brentq(lambda x: p_home(x) - p_home_win, 0.02, 0.98)
    return mu * f, mu * (1 - f)


def p_score(lam_team: np.ndarray, share: np.ndarray) -> np.ndarray:
    return 1 - np.exp(-np.asarray(lam_team) * np.asarray(share))


def p_score_given_goals(goals_team: np.ndarray, share: np.ndarray) -> np.ndarray:
    return 1 - (1 - np.asarray(share)) ** np.asarray(goals_team)
