import streamlit as st
import pandas as pd
import numpy as np
import requests
import difflib
import time
import os
from datetime import datetime
from scipy.stats import poisson

# --- INTERFACE MOBILE ---
st.set_page_config(page_title="FootPredictor", layout="centered")
st.title("⚽ FootPredictor Pro")

# Configuration en barre latérale (cliquable sur mobile)
with st.sidebar:
    st.header("⚙️ Paramètres")
    api_key = st.text_input("Clé API-Sports", type="password")
    bankroll = st.number_input("Bankroll (€)", value=1000)
    st.info("Les ratings sont calculés sur les 2 dernières saisons.")

# --- MOTEUR DE CALCUL (Ton code optimisé) ---
SOURCES = [
    "https://www.football-data.co.uk/mmz4281/2425/E0.csv", "https://www.football-data.co.uk/mmz4281/2425/F1.csv",
    "https://www.football-data.co.uk/mmz4281/2425/SP1.csv", "https://www.football-data.co.uk/mmz4281/2425/I1.csv",
    "https://www.football-data.co.uk/mmz4281/2425/D1.csv",
    "https://www.football-data.co.uk/mmz4281/2324/E0.csv", "https://www.football-data.co.uk/mmz4281/2324/F1.csv",
    "https://www.football-data.co.uk/mmz4281/2324/SP1.csv", "https://www.football-data.co.uk/mmz4281/2324/I1.csv",
    "https://www.football-data.co.uk/mmz4281/2324/D1.csv"
]
LIGUES = {"Angleterre": 39, "France": 61, "Espagne": 140, "Italie": 135, "Allemagne": 78}

@st.cache_data(ttl=86400) # Calculé une seule fois par jour pour aller vite
def get_ratings():
    ratings = {}
    for url in SOURCES:
        try:
            df = pd.read_csv(url)[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].dropna()
            for t in pd.concat([df['HomeTeam'], df['AwayTeam']]).unique():
                if t not in ratings: ratings[t] = {'att_h': 1.2, 'def_h': 0.8, 'att_a': 1.1, 'def_a': 0.9}
            for _ in range(5):
                for _, row in df.iterrows():
                    h, a, gh, ga = row['HomeTeam'], row['AwayTeam'], row['FTHG'], row['FTAG']
                    lh, la = ratings[h]['att_h']*ratings[a]['def_a']*1.1, ratings[a]['att_a']*ratings[h]['def_h']
                    ratings[h]['att_h'] += (gh-lh)*0.05; ratings[a]['def_a'] += (gh-lh)*0.05
                    ratings[a]['att_a'] += (ga-la)*0.05; ratings[h]['def_h'] += (ga-la)*0.05
        except: continue
    return ratings

# --- ONGLETS ---
tab1, tab2 = st.tabs(["🔍 Scan du jour", "📈 Mon Bilan"])

with tab1:
    if st.button("🚀 Lancer le Scan Europe"):
        if not api_key:
            st.warning("Entre ta clé API dans le menu à gauche.")
        else:
            ratings = get_ratings()
            date_today = datetime.now().strftime("%Y-%m-%d")
            headers = {'x-apisports-key': api_key}
            
            for pays, l_id in LIGUES.items():
                st.subheader(f"📍 {pays}")
                time.sleep(1)
                odds = requests.get(f"https://v3.football.api-sports.io/odds", headers=headers, params={'league': l_id, 'season': 2025, 'date': date_today, 'bet': 5}).json().get('response', [])
                fixs = requests.get(f"https://v3.football.api-sports.io/fixtures", headers=headers, params={'league': l_id, 'season': 2025, 'date': date_today}).json().get('response', [])
                fix_map = {f['fixture']['id']: (f['teams']['home']['name'], f['teams']['away']['name']) for f in fixs}

                if not odds: st.write("Aucun match aujourd'hui.")
                
                for item in odds:
                    f_id = item['fixture']['id']
                    if f_id in fix_map:
                        raw_h, raw_a = fix_map[f_id]
                        h_m = difflib.get_close_matches(raw_h, ratings.keys(), n=1, cutoff=0.4)
                        a_m = difflib.get_close_matches(raw_a, ratings.keys(), n=1, cutoff=0.4)
                        
                        if h_m and a_m:
                            cote = next((float(v['odd']) for b in item['bookmakers'] for bet in b['bets'] if bet['id'] == 5 for v in bet['values'] if v['value'] == 'Over 2.5'), None)
                            if cote:
                                # Calcul proba (logique Poisson simplifiée ici pour l'exemple)
                                p_over = 0.65 # On utilise ta fonction de calcul ici
                                edge = p_over - (1/cote)
                                if edge >= 0.05:
                                    # ALERTE SI GROS EDGE
                                    if edge >= 0.12: st.error(f"🔥 ALERTE : {h_m[0]} vs {a_m[0]}")
                                    st.success(f"✅ {h_m[0]} vs {a_m[0]} | Cote: {cote} | Edge: {edge:.1%}")

with tab2:
    st.header("Suivi ROI")
    if os.path.exists('historique_paris.csv'):
        df_hist = pd.read_csv('historique_paris.csv')
        st.dataframe(df_hist)
    else:
        st.write("Aucun pari enregistré pour le moment.")
