"""Modèle de Dixon & Coles (1997) avec pondération temporelle.

Buts domicile ~ Poisson(λ), buts extérieur ~ Poisson(μ) avec
    log λ = m + h + att[dom] - def[ext]
    log μ = m     + att[ext] - def[dom]
et une correction τ(x, y, λ, μ, ρ) des scores faibles (0-0, 1-0, 0-1, 1-1).
Les matchs sont pondérés par exp(-ξ·âge_en_jours) (Dixon & Coles : ξ ≈ 0.0065 par
demi-semaine ≈ 0.0019 par jour).

Implémentation : log-vraisemblance + gradient analytique, L-BFGS-B, pénalité ridge
légère sur att/def (identifiabilité + rétrécissement des équipes à peu de matchs).
Ajustement « walk-forward » : ré-estimation périodique en n'utilisant QUE les matchs
passés, puis prédiction des matchs à venir jusqu'à la ré-estimation suivante.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson


class DixonColes:
    def __init__(self, xi: float = 0.0019, reg: float = 1.0, max_goals: int = 10):
        self.xi = xi
        self.reg = reg
        self.max_goals = max_goals
        self.teams: list = []
        self.params = None

    # ------------------------------------------------------------------ fit
    def fit(self, home, away, hg, ag, days_ago, init: dict | None = None):
        teams = sorted(set(home) | set(away))
        idx = {t: i for i, t in enumerate(teams)}
        hi = np.array([idx[t] for t in home])
        ai = np.array([idx[t] for t in away])
        x = np.asarray(hg, float)
        y = np.asarray(ag, float)
        w = np.exp(-self.xi * np.asarray(days_ago, float))
        n = len(teams)
        m00 = (x == 0) & (y == 0)
        m01 = (x == 0) & (y == 1)
        m10 = (x == 1) & (y == 0)
        m11 = (x == 1) & (y == 1)
        reg = self.reg

        def f(theta):
            att = theta[:n]
            dfn = theta[n:2 * n]
            hadv, mu0, rho = theta[2 * n], theta[2 * n + 1], theta[2 * n + 2]
            ll_ = mu0 + hadv + att[hi] - dfn[ai]
            lm_ = mu0 + att[ai] - dfn[hi]
            lam = np.exp(ll_)
            mu = np.exp(lm_)
            tau = np.ones_like(lam)
            tau[m00] = 1 - lam[m00] * mu[m00] * rho
            tau[m01] = 1 + lam[m01] * rho
            tau[m10] = 1 + mu[m10] * rho
            tau[m11] = 1 - rho
            tau = np.maximum(tau, 1e-10)
            ll = w * (x * ll_ - lam + y * lm_ - mu + np.log(tau))
            # dérivées de log τ
            dt_l = np.zeros_like(lam)
            dt_m = np.zeros_like(lam)
            dt_r = np.zeros_like(lam)
            dt_l[m00] = -mu[m00] * rho / tau[m00]
            dt_m[m00] = -lam[m00] * rho / tau[m00]
            dt_r[m00] = -lam[m00] * mu[m00] / tau[m00]
            dt_l[m01] = rho / tau[m01]
            dt_r[m01] = lam[m01] / tau[m01]
            dt_m[m10] = rho / tau[m10]
            dt_r[m10] = mu[m10] / tau[m10]
            dt_r[m11] = -1.0 / tau[m11]
            g_l = w * (x - lam + lam * dt_l)   # d/d log λ
            g_m = w * (y - mu + mu * dt_m)     # d/d log μ
            g_att = np.bincount(hi, g_l, n) + np.bincount(ai, g_m, n)
            g_def = -np.bincount(ai, g_l, n) - np.bincount(hi, g_m, n)
            grad = np.concatenate([g_att - reg * att, g_def - reg * dfn,
                                   [g_l.sum(), g_l.sum() + g_m.sum(), np.sum(w * dt_r)]])
            obj = ll.sum() - 0.5 * reg * (np.sum(att ** 2) + np.sum(dfn ** 2))
            return -obj, -grad

        self._objective = f
        theta0 = np.zeros(2 * n + 3)
        theta0[2 * n] = 0.25
        theta0[2 * n + 1] = 0.1
        theta0[2 * n + 2] = -0.05
        if init is not None:
            for t, i in idx.items():
                if t in init.get("att", {}):
                    theta0[i] = init["att"][t]
                    theta0[n + i] = init["def"][t]
            theta0[2 * n:] = [init["home"], init["mu"], init["rho"]]
        bounds = [(None, None)] * (2 * n + 2) + [(-0.25, 0.25)]
        res = minimize(f, theta0, jac=True, method="L-BFGS-B", bounds=bounds,
                       options={"maxiter": 500})
        th = res.x
        self.converged = bool(res.success)
        self.teams = teams
        self.att = dict(zip(teams, th[:n]))
        self.def_ = dict(zip(teams, th[n:2 * n]))
        self.home, self.mu, self.rho = th[2 * n], th[2 * n + 1], th[2 * n + 2]
        self.params = {"att": self.att, "def": self.def_, "home": self.home,
                       "mu": self.mu, "rho": self.rho}
        return self

    # -------------------------------------------------------------- predict
    def expected_goals(self, home, away):
        ah = np.array([self.att.get(t, 0.0) for t in home])
        dh = np.array([self.def_.get(t, 0.0) for t in home])
        aa = np.array([self.att.get(t, 0.0) for t in away])
        da = np.array([self.def_.get(t, 0.0) for t in away])
        lam = np.exp(self.mu + self.home + ah - da)
        mu = np.exp(self.mu + aa - dh)
        return lam, mu

    def score_matrix(self, lam: float, mu: float) -> np.ndarray:
        g = np.arange(self.max_goals + 1)
        m = np.outer(poisson.pmf(g, lam), poisson.pmf(g, mu))
        r = self.rho
        m[0, 0] *= max(1 - lam * mu * r, 1e-10)
        m[0, 1] *= 1 + lam * r
        m[1, 0] *= 1 + mu * r
        m[1, 1] *= 1 - r
        return m / m.sum()

    def predict(self, home, away) -> pd.DataFrame:
        lam, mu = self.expected_goals(home, away)
        rows = []
        for l_, m_ in zip(lam, mu):
            m = self.score_matrix(l_, m_)
            tot = np.add.outer(np.arange(m.shape[0]), np.arange(m.shape[1]))
            rows.append([np.tril(m, -1).sum(), np.trace(m), np.triu(m, 1).sum(),
                         m[tot > 2.5].sum(), 1 - m[0, :].sum() - m[:, 0].sum() + m[0, 0],
                         l_, m_])
        return pd.DataFrame(rows, columns=["dc_ph", "dc_pd", "dc_pa", "dc_over25", "dc_btts",
                                           "dc_lambda", "dc_mu"])


def walk_forward(df: pd.DataFrame, group_col: str = "Country", refit_days: int = 7,
                 window_days: int = 3 * 365, xi: float = 0.0019, reg: float = 1.0,
                 min_train: int = 300, verbose: bool = False) -> pd.DataFrame:
    """Prédictions Dixon-Coles hors-échantillon pour chaque match de df.

    Pour chaque groupe (pays), on ré-estime le modèle tous les `refit_days` jours sur la
    fenêtre glissante [t - window_days, t) et on prédit les matchs de [t, t + refit_days).
    """
    out = []
    for grp, g in df.groupby(group_col):
        g = g.sort_values("Date")
        dates = g["Date"].values
        start = g["Date"].min() + pd.Timedelta(days=180)
        t = start
        end = g["Date"].max() + pd.Timedelta(days=1)
        init = None
        while t <= end:
            t_next = t + pd.Timedelta(days=refit_days)
            test = g[(g["Date"] >= t) & (g["Date"] < t_next)]
            if len(test):
                train = g[(g["Date"] < t) & (g["Date"] >= t - pd.Timedelta(days=window_days))]
                if len(train) >= min_train:
                    m = DixonColes(xi=xi, reg=reg).fit(
                        train["HomeTeam"].values, train["AwayTeam"].values,
                        train["FTHG"].values, train["FTAG"].values,
                        (t - train["Date"]).dt.days.values, init=init)
                    init = m.params
                    p = m.predict(test["HomeTeam"].values, test["AwayTeam"].values)
                    p.index = test.index
                    # équipes inconnues -> prédiction non fiable, on la marque
                    known = set(m.teams)
                    p["dc_known"] = [(h in known and a in known) for h, a in
                                     zip(test["HomeTeam"], test["AwayTeam"])]
                    out.append(p)
            t = t_next
        if verbose:
            print(grp, "ok")
    _ = dates
    return pd.concat(out).sort_index() if out else pd.DataFrame()
