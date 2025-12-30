import streamlit as st
import pandas as pd
import numpy as np
import requests
import difflib
import time
import os
from datetime import datetime
from scipy.stats import poisson

# --- CONFIGURATION & SECRETS ---
st.set_page_config(page_title="FootPredictor Pro", layout="centered")
# Récupère la clé depuis GitHub Secrets ou Streamlit Secrets
API_KEY = st.secrets.get("FOOT_API_KEY") or os.getenv("FOOT_API_KEY")
BASE_URL = "https://v3.football.api-sports.io"
BANKROLL = 1000

SOURCES = [
    "https://www.football-data.co.uk/mmz4281/2425/E0.csv", "https://www.football-data.co.uk/mmz4281/2425/F1.csv",
    "https://www.football-data.co.uk/mmz4281/2425/SP1.csv", "https://www.football-data.co.uk/mmz4281/2425/I1.csv",
    "https://www.football-data.co.uk/mmz4281/2425/D1.csv",
    "https://www.football-data.co.uk/mmz4281/2324/E0.csv", "https://www.football-data.co.uk/mmz4281/2324/F1.csv",
    "https://www.football-data.co.uk/mmz4281/2324/SP1.csv", "https://www.football-data.co.uk/mmz4281/2324/I1.csv",
    "https://www.football-data.co.uk/mmz4281/2324/D1.csv"
]
LIGUES = {"Angleterre": 39, "France": 61, "Espagne": 140, "Italie": 135, "Allemagne": 78}

# --- FONCTIONS MOTEUR ---
@st.cache_data(ttl=86400)
def get_all_ratings():
    ratings = {}
    for url in SOURCES:
        try:
            df = pd.read_csv(url)[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].dropna()
            for t in pd.concat([df['HomeTeam'], df['AwayTeam']]).unique():
                if t not in ratings: ratings[t] = {'att_h': 1.2, 'def_h': 0.8, 'att_a': 1.1, 'def_a': 0.9}
            for _ in range(5):
                for _, row in df.iterrows():
                    h, a, gh, ga = row['HomeTeam'], row['AwayTeam'], row['FTHG'], row['FTAG']
                    lh, la = ratings[h]['att_h']*ratings[a]['def_a']*1.10, ratings[a]['att_a']*ratings[h]['def_h']
                    ratings[h]['att_h'] += (gh-lh)*0.05; ratings[a]['def_a'] += (gh-lh)*0.05
                    ratings[a]['att_a'] += (ga-la)*0.05; ratings[h]['def_h'] += (ga-la)*0.05
        except: continue
    return ratings

def predict_over_25(home, away, ratings):
    lh, la = ratings[home]['att_h']*ratings[away]['def_a']*1.10, ratings[away]['att_a']*ratings[home]['def_h']
    prob_matrix = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            p = poisson.pmf(i, lh) * poisson.pmf(j, la)
            if i==0 and j==0: p *= 0.9
            prob_matrix[i, j] = p
    return 1 - (prob_matrix[0,0]+prob_matrix[1,0]+prob_matrix[0,1]+prob_matrix[1,1]+prob_matrix[2,0]+prob_matrix[0,2])

def log_bet(match, cote, mise, proba):
    file = 'historique_paris.csv'
    new_data = pd.DataFrame([[datetime.now().strftime('%Y-%m-%d'), match, cote, mise, f"{proba:.1%}", 0]], 
                            columns=['Date', 'Match', 'Cote', 'Mise', 'Proba', 'Statut'])
    if not os.path.isfile(file):
        new_data.to_csv(file, index=False)
    else:
        new_data.to_csv(file, mode='a', header=False, index=False)

# --- INTERFACE STREAMLIT ---
st.title("⚽ FootPredictor Pro")

if not API_KEY:
    st.error("❌ Clé API manquante. Configure 'FOOT_API_KEY' dans les secrets.")
    st.stop()

tab1, tab2 = st.tabs(["🔍 Scan du jour", "📊 Stats & ROI"])

with tab1:
    if st.button("🚀 Lancer le Scan Europe"):
        ratings = get_all_ratings()
        date_today = datetime.now().strftime("%Y-%m-%d")
        headers = {'x-apisports-key': API_KEY}
        
        found_any = False
        for pays, l_id in LIGUES.items():
            st.write(f"**Analyse {pays}...**")
            time.sleep(1) # Respect Rate Limit
            
            odds = requests.get(f"{BASE_URL}/odds", headers=headers, params={'league': l_id, 'season': 2025, 'date': date_today, 'bet': 5}).json().get('response', [])
            fixs = requests.get(f"{BASE_URL}/fixtures", headers=headers, params={'league': l_id, 'season': 2025, 'date': date_today}).json().get('response', [])
            fix_map = {f['fixture']['id']: (f['teams']['home']['name'], f['teams']['away']['name']) for f in fixs}

            for item in odds:
                f_id = item['fixture']['id']
                if f_id in fix_map:
                    raw_h, raw_a = fix_map[f_id]
                    h_m = difflib.get_close_matches(raw_h, ratings.keys(), n=1, cutoff=0.4)
                    a_m = difflib.get_close_matches(raw_a, ratings.keys(), n=1, cutoff=0.4)
                    
                    if h_m and a_m:
                        cote = next((float(v['odd']) for b in item['bookmakers'] for bet in b['bets'] if bet['id'] == 5 for v in bet['values'] if v['value'] == 'Over 2.5'), None)
                        if cote:
                            p_over = predict_over_25(h_m[0], a_m[0], ratings)
                            edge = p_over - (1/cote)
                            if edge >= 0.05:
                                found_any = True
                                f_kelly = ((p_over * cote) - 1) / (cote - 1)
                                mise = round(BANKROLL * min(f_kelly * 0.25, 0.02), 2)
                                
                                # Affichage Alerte si Edge > 10%
                                if edge >= 0.10:
                                    st.error(f"🔥 ALERTE : {h_m[0]} vs {a_m[0]} | Cote: {cote} | Edge: {edge:.1%}")
                                else:
                                    st.success(f"✅ {h_m[0]} vs {a_m[0]} | Cote: {cote} | Mise: {mise}€")
                                
                                log_bet(f"{h_m[0]} vs {a_m[0]}", cote, mise, p_over)
        if not found_any:
            st.info("Aucune value trouvée aujourd'hui.")

with tab2:
    if os.path.exists('historique_paris.csv'):
        df = pd.read_csv('historique_paris.csv')
        st.subheader("Historique des paris")
        st.dataframe(df)
        
        # Stats rapides
        clos = df[df['Statut'].isin([1, 2])]
        if len(clos) > 0:
            profit = sum([(r['Mise']*r['Cote'] - r['Mise']) if r['Statut']==1 else -r['Mise'] for _, r in clos.iterrows()])
            roi = (profit / clos['Mise'].sum()) * 100
            st.metric("Profit Total", f"{profit:.2f}€", delta=f"{roi:.2f}% ROI")
        else:
            st.write("En attente de résultats (Statut 0 -> 1 ou 2)")
    else:
        st.write("Aucun historique pour le moment.")
