"""Génère les rapports Markdown de docs/resultats/ à partir des CSV de results/.

Les chiffres des documents de synthèse proviennent de ces tableaux : relancer ce script
après chaque backtest garantit que la documentation reflète exactement les calculs.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
DOC = ROOT / "docs" / "resultats"
DOC.mkdir(parents=True, exist_ok=True)

PCT = {"ROI", "IC_bas", "IC_haut", "CLV", "réussite", "taux_reussite", "p(ROI<=0)", "p_ROI_le0",
       "%_CLV>0", "CLV_moy", "ROI_IC95_bas", "ROI_IC95_haut", "max_drawdown", "marge_moy",
       "marge_moy_ouverture", "accuracy", "erreur_type"}


def fmt(df: pd.DataFrame, pct_cols=None, digits=4) -> str:
    d = df.copy()
    for c in d.columns:
        base = c.split("_", 1)[1] if c.startswith(("dev_", "test_")) else c
        if pd.api.types.is_float_dtype(d[c]):
            if (pct_cols and c in pct_cols) or base in PCT:
                d[c] = d[c].map(lambda v: "" if pd.isna(v) else f"{100 * v:+.2f} %"
                                if base in ("ROI", "IC_bas", "IC_haut", "CLV", "CLV_moy") else f"{100 * v:.1f} %")
            elif base in ("n", "dev_n", "test_n"):
                d[c] = d[c].map(lambda v: "" if pd.isna(v) else f"{int(v)}")
            else:
                d[c] = d[c].map(lambda v: "" if pd.isna(v) else f"{v:.{digits}f}")
    return d.to_markdown(index=False)


def read(p: Path):
    return pd.read_csv(p) if p.exists() else None


def football():
    f = RES / "football"
    out = ["# Résultats détaillés — football (généré automatiquement)", "",
           "> Fichier produit par `scripts/build_reports.py` à partir de `results/football/`. "
           "Ne pas éditer à la main.", ""]
    meta = f / "meta.json"
    if meta.exists():
        m = json.loads(meta.read_text())
        out += [f"Nombre de configurations testées : 1N2 = **{m.get('n_configs_1x2')}**, "
                f"Over/Under = **{m.get('n_configs_ou')}** (à garder en tête : tests multiples).", ""]
    sections = [
        ("1. Qualité des prédictions (mêmes matchs pour tous les modèles)", "qualite_predictions.csv", None),
        ("2. Qualité par championnat (RPS, 2012-2026)", "qualite_par_championnat.csv", None),
        ("3. Sélection sur la période dev (2012-2019) et validation sur test (2019-2026)",
         "selection_dev_validation_test.csv", None),
    ]
    for title, file, _ in sections:
        d = read(f / file)
        if d is not None:
            out += [f"## {title}", "", fmt(d), ""]
    g = read(f / "grille_strategies_1x2.csv")
    if g is not None:
        out += ["## 4. Grille complète 1N2 — meilleures configurations par famille (classées sur dev)", ""]
        cols = ["famille", "prob", "book", "min_ev", "max_odds", "dev_n", "dev_ROI", "dev_IC_bas",
                "dev_IC_haut", "dev_CLV", "test_n", "test_ROI", "test_IC_bas", "test_IC_haut", "test_CLV"]
        cols = [c for c in cols if c in g]
        for fam, gg in g.groupby("famille"):
            key = "dev_ROI" if gg["dev_n"].fillna(0).max() > 0 else "test_ROI"
            gg = gg[(gg["dev_n"].fillna(0) >= 200) | (key == "test_ROI")]
            out += [f"### Famille « {fam} »", "", fmt(gg.sort_values(key, ascending=False)[cols].head(8)), ""]
    ou = read(f / "grille_strategies_over_under.csv")
    if ou is not None:
        out += ["## 5. Over/Under 2.5", "", fmt(ou), ""]
    b = read(f / "carte_des_biais.csv")
    if b is not None:
        out += ["## 6. Carte des biais : ROI en pariant systématiquement une issue par tranche de cote "
                "(2012-2026)", ""]
        piv = b.pivot_table(index=["issue", "tranche"], columns="cotes", values="ROI").reset_index()
        out += [fmt(piv, pct_cols=set(piv.columns) - {"issue", "tranche"}), ""]
    for p in sorted(f.glob("staking_*.csv")):
        out += [f"## Gestion de mise — {p.stem.replace('staking_', '')} (période test)", "", fmt(read(p)), ""]
    for p in sorted(f.glob("par_championnat_*.csv")):
        out += [f"## Par championnat — {p.stem.replace('par_championnat_', '')} (2012-2026)", "",
                fmt(read(p)), ""]
    for p in sorted(f.glob("par_saison_*.csv")):
        out += [f"## Par saison — {p.stem.replace('par_saison_', '')}", "", fmt(read(p)), ""]
    for name, title in (("extra_leagues_sharp_vs_soft.csv", "Championnats extra (échantillon indépendant)"),
                        ("extra_leagues_par_championnat.csv", "Championnats extra — par championnat (MaxC, EV>2 %)")):
        d = read(f / name)
        if d is not None:
            out += [f"## {title}", "", fmt(d), ""]
    (DOC / "football.md").write_text("\n".join(out), encoding="utf-8")


def multisport():
    f = RES / "multisport"
    out = ["# Résultats détaillés — tennis, NBA, NHL, NFL, MLB, MMA (généré automatiquement)", "",
           "> Fichier produit par `scripts/build_reports.py` à partir de `results/multisport/`.", ""]
    q = read(f / "qualite_all.csv")
    if q is not None:
        out += ["## 1. Qualité des probabilités : modèle Elo vs marché vs mélange", "", fmt(q), ""]
    s = read(f / "strategies_all.csv")
    if s is not None:
        for sport, g in s.groupby("sport", sort=False):
            out += [f"## {sport}", "", fmt(g.drop(columns="sport")), ""]
    for p in sorted(f.glob("staking_*.csv")):
        out += [f"## Gestion de mise — {p.stem.replace('staking_', '')}", "", fmt(read(p)), ""]
    (DOC / "autres_sports.md").write_text("\n".join(out), encoding="utf-8")


def international():
    f = RES / "international"
    q = read(f / "qualite_elo_selections.csv")
    r = read(f / "classement_elo_actuel.csv")
    out = ["# Sélections nationales — Elo (généré automatiquement)", ""]
    if q is not None:
        out += ["## Qualité des prédictions 2010-2026", "", fmt(q), ""]
    if r is not None:
        out += ["## Classement Elo actuel (top 40)", "", r.head(40).to_markdown(index=False), ""]
    (DOC / "international.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    football()
    multisport()
    international()
    print("rapports écrits dans", DOC)
