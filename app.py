"""Overstreamlit — tableau de bord de la bibliothèque de prédiction sportive.

Lancer : streamlit run app.py
Mode robot (GitHub Actions) : python scripts/daily_scan.py
Aucune clé API n'est nécessaire.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sportpred.live import scanner as sc  # noqa: E402

st.set_page_config(page_title="Overstreamlit — value bets", layout="wide")
RES = ROOT / "results"
PICKS = ROOT / "picks"


@st.cache_data(ttl=3600, show_spinner="Téléchargement des matchs à venir…")
def fixtures():
    return sc.load_fixtures()


@st.cache_data(ttl=6 * 3600, show_spinner="Mise à jour du modèle Dixon-Coles…")
def dc_predictions(fx: pd.DataFrame):
    s = sc.current_season_code()
    y = int(s[:2])
    seasons = [f"{(y - 2) % 100:02d}{(y - 1) % 100:02d}", f"{(y - 1) % 100:02d}{y:02d}", s]
    res = sc.load_recent_results(seasons)
    return sc.dixon_coles_today(res, fx)


def csv(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


st.title("⚽🎾🏀 Overstreamlit — bibliothèque de stratégies de paris")
st.caption("Recherche reproductible, données gratuites, protocole walk-forward. "
           "Les paris sportifs comportent des risques : jouez de façon responsable (09 74 75 13 13).")

tab_scan, tab_suivi, tab_res, tab_lib = st.tabs(
    ["🎯 Value bets du jour", "📊 Suivi des paris", "🔬 Résultats de recherche", "📚 Bibliothèque"])

with tab_scan:
    c1, c2, c3, c4 = st.columns(4)
    min_ev = c1.slider("EV minimale", 0.0, 0.15, 0.03, 0.01, help="Espérance de gain minimale vs proba juste")
    books = c2.multiselect("Bookmakers (agréés ANJ)", ["B365", "BW"], default=["B365", "BW"])
    w = c3.slider("Poids du modèle Dixon-Coles", 0.0, 0.5, 0.0, 0.1,
                  help="0 = marché sharp seul (recommandé par le backtest)")
    bankroll = c4.number_input("Bankroll (€)", 50.0, 1e6, 1000.0, 50.0)
    if st.button("🔍 Scanner les matchs à venir", type="primary"):
        fx = fixtures()
        if w > 0:
            fx = fx.join(dc_predictions(fx))
        cfg = sc.ScanConfig(min_ev=min_ev, soft_books=books or ["B365"], model_weight=w, bankroll=bankroll)
        picks = sc.find_value(fx, cfg)
        st.write(f"**{len(fx)}** matchs à venir analysés, **{len(picks)}** value bets.")
        if len(picks):
            st.dataframe(picks, width="stretch", hide_index=True)
        st.info("Référence « juste » : Betfair Exchange sans marge (méthode power). "
                "Vérifiez la cote sur votre bookmaker français avant de miser : "
                "les cotes .fr peuvent être inférieures à celles du fichier.")

with tab_suivi:
    h = csv(PICKS / "history.csv")
    if h is None or h.empty:
        st.info("Pas encore d'historique : il sera créé par la GitHub Action quotidienne.")
    else:
        done = h[h["statut"] != "en attente"].copy()
        if len(done):
            mise, prof = done["mise_€"].sum(), done["profit_€"].sum()
            a, b, c = st.columns(3)
            a.metric("Paris réglés", len(done))
            b.metric("Profit", f"{prof:.2f} €")
            c.metric("ROI", f"{100 * prof / mise:.2f} %")
            done["cumul"] = done["profit_€"].cumsum()
            st.line_chart(done.set_index("date")["cumul"])
        st.dataframe(h.iloc[::-1], width="stretch", hide_index=True)
    old = csv(ROOT / "archives" / "historique_paris_ancien_systeme.csv")
    if old is not None:
        with st.expander("Ancien système (janvier-février 2026) — ROI −6,95 %, voir l'audit"):
            st.dataframe(old, width="stretch", hide_index=True)

with tab_res:
    st.subheader("Football : qualité des prédictions (RPS, plus bas = meilleur)")
    q = csv(RES / "football" / "qualite_predictions.csv")
    if q is not None:
        st.dataframe(q, width="stretch", hide_index=True)
    st.subheader("Football : meilleures stratégies (choisies sur 2012-2019, validées sur 2019-2026)")
    s = csv(RES / "football" / "selection_dev_validation_test.csv")
    if s is not None:
        st.dataframe(s, width="stretch", hide_index=True)
    for img in sorted((RES / "football").glob("*.png")):
        st.image(str(img), caption=img.stem)
    st.subheader("Autres sports (tennis, NBA, NHL, NFL, MLB, MMA)")
    for f in ("qualite_all.csv", "strategies_all.csv"):
        d = csv(RES / "multisport" / f)
        if d is not None:
            st.dataframe(d, width="stretch", hide_index=True)

with tab_lib:
    st.markdown((ROOT / "docs" / "00_INDEX.md").read_text(encoding="utf-8")
                if (ROOT / "docs" / "00_INDEX.md").exists() else "Documentation : dossier docs/")
