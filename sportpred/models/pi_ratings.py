"""Pi-ratings (Constantinou & Fenton, 2013, JQAS 9(1)).

Chaque équipe a une note « domicile » et une note « extérieur ». La différence de buts
attendue face à un adversaire moyen est psi(R) = sign(R)·(b^{|R|/c} - 1). Après chaque
match, l'erreur entre écart de buts observé et attendu met à jour les notes
(taux d'apprentissage λ, report croisé domicile/extérieur γ).

Hubáček et al. (2019) et Yeung et al. (2023) ont montré que les pi-ratings sont parmi
les meilleures caractéristiques pour la prédiction (Soccer Prediction Challenge).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _psi(r, b, c):
    return np.sign(r) * (b ** (np.abs(r) / c) - 1.0)


def pi_ratings(df: pd.DataFrame, lam: float = 0.035, gamma: float = 0.7, b: float = 10.0,
               c: float = 3.0, group_col: str | None = "Country", max_gd: int | None = None,
               home="HomeTeam", away="AwayTeam", hg="FTHG", ag="FTAG",
               date="Date") -> pd.DataFrame:
    order = df.sort_values(date, kind="stable").index
    RH: dict = {}
    RA: dict = {}
    pos = {ix: i for i, ix in enumerate(df.index)}
    out = np.zeros((len(df), 5))
    H, A = df[home].values, df[away].values
    G = df[group_col].values if group_col else np.zeros(len(df))
    GH, GA = df[hg].values, df[ag].values

    for ix in order:
        i = pos[ix]
        h, a = (G[i], H[i]), (G[i], A[i])
        rhh, rha = RH.get(h, 0.0), RA.get(h, 0.0)
        rah, raa = RH.get(a, 0.0), RA.get(a, 0.0)
        exp_gd = _psi(rhh, b, c) - _psi(raa, b, c)
        out[i] = [rhh, rha, rah, raa, exp_gd]
        gd = GH[i] - GA[i]
        if max_gd is not None:
            gd = np.clip(gd, -max_gd, max_gd)
        e = abs(gd - exp_gd)
        we = c * np.log10(1.0 + e)
        wh = we if gd > exp_gd else -we
        wa = -wh
        new_rhh = rhh + wh * lam
        new_rha = rha + (new_rhh - rhh) * gamma
        new_raa = raa + wa * lam
        new_rah = rah + (new_raa - raa) * gamma
        RH[h], RA[h] = new_rhh, new_rha
        RH[a], RA[a] = new_rah, new_raa

    return pd.DataFrame(out, index=df.index,
                        columns=["pi_hh", "pi_ha", "pi_ah", "pi_aa", "pi_gd"])
