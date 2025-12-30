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

# Correction : Gestion robuste de la clé API
API_KEY = os.getenv("FOOT_API_KEY")
if not API_KEY:
    try:
        API_KEY = st.secrets["FOOT_API_KEY"]
    except:
        API_KEY = None

BASE_URL = "https://v3.football.api-sports.io"
BANKROLL = 1000
LIGUES = {"Angleterre": 39, "France": 61, "Espagne": 140, "Italie": 135, "Allemagne": 78}

# --- FONCTIONS MOTEUR ---
@st.cache_data(ttl=86400)
def get_all_ratings():
    ratings = {}
    # Génération simplifiée des URLs pour les 5 ligues sur 2 saisons
    codes = ["E0", "F1", "SP1", "I1", "D1"]
    saisons = ["2425", "2324"]
    for s in saisons:
        for c in codes:
            url = f"https://www.football-data.co.uk/mmz4281/{s}/{c}.csv"
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

def predict_over_25(home, away, ratings):
    lh, la = ratings[home]['att_h']*ratings[away]['def_a']*1.1, ratings[away]['att_a']*ratings[home]['def_h']
    prob_matrix = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            p = poisson.pmf(i, lh) * poisson.pmf(j, la)
            if i==0 and j==0: p *= 0.9
            prob_matrix[i, j] = p
    return 1 - (prob_matrix[0,0]+prob_matrix[1,0]+prob_matrix[0,1]+prob_matrix[1,1]+prob_matrix[2,0]+prob_matrix[0,2])

def log_bet(fid, date, match, cote, mise, proba):
    file = 'historique_paris.csv'
    new_data = pd.DataFrame([[fid, date, match, cote, mise, f"{proba:.1%}", 0]], 
                            columns=['FID', 'Date', 'Match', 'Cote', 'Mise', 'Proba', 'Statut'])
    if not os.path.isfile(file): new_data.to_csv(file, index=False)
    else: new_data.to_csv(file, mode='a', header=False, index=False)

def update_results_auto():
    file = 'historique_paris.csv'
    if not os.path.isfile(file): return False
    df = pd.read_csv(file)
    updated = False
    for idx, row in df[df['Statut'] == 0].iterrows():
        try:
            res = requests.get(f"{BASE_URL}/fixtures", headers={'x-apisports-key': API_KEY}, params={'id': int(row['FID'])}).json().get('response', [])
            if res and res[0]['fixture']['status']['short'] == 'FT':
                total = res[0]['goals']['home'] + res[0]['goals']['away']
                df.at[idx, 'Statut'] = 1 if total > 2.5 else 2
                updated = True
        except: continue
    if updated: df.to_csv(file, index=False)
    return updated

# --- INTERFACE ---
st.title("⚽ FootPredictor Pro")
if not API_KEY:
    st.error("❌ Clé API introuvable. Configure FOOT_API_KEY dans les secrets.")
    st.stop()

tab1, tab2 = st.tabs(["🔍 Scan", "📊 Bilan"])

with tab1:
    if st.button("🚀 Lancer le Scan Europe"):
        ratings = get_all_ratings()
        date_now = datetime.now().strftime("%Y-%m-%d")
        for pays, l_id in LIGUES.items():
            st.write(f"Analyse {pays}...")
            try:
                odds = requests.get(f"{BASE_URL}/odds", headers={'x-apisports-key': API_KEY}, params={'league': l_id, 'season': 2025, 'date': date_now, 'bet': 5}).json().get('response', [])
                fixs = requests.get(f"{BASE_URL}/fixtures", headers={'x-apisports-key': API_KEY}, params={'league': l_id, 'season': 2025, 'date': date_now}).json().get('response', [])
                f_map = {f['fixture']['id']: (f['teams']['home']['name'], f['teams']['away']['name']) for f in fixs}
                for item in odds:
                    fid = item['fixture']['id']
                    if fid in f_map:
                        h_raw, a_raw = f_map[fid]
                        h_m = difflib.get_close_matches(h_raw, ratings.keys(), n=1, cutoff=0.4)
                        a_m = difflib.get_close_matches(a_raw, ratings.keys(), n=1, cutoff=0.4)
                        if h_m and a_m:
                            cote = next((float(v['odd']) for b in item['bookmakers'] for bet in b['bets'] if bet['id']==5 for v in bet['values'] if v['value']=='Over 2.5'), None)
                            if cote:
                                p = predict_over_25(h_m[0], a_m[0], ratings)
                                edge = p - (1/cote)
                                if edge >= 0.05:
                                    mise = round(BANKROLL * ((p*cote-1)/(cote-1)) * 0.25, 2)
                                    st.success(f"✅ {h_m[0]} vs {a_m[0]} | Cote: {cote}")
                                    log_bet(fid, date_now, f"{h_m[0]} vs {a_m[0]}", cote, min(mise, 20), p)
            except: continue

with tab2:
    if st.button("🔄 Actualiser les scores"):
        if update_results_auto(): st.rerun()
    if os.path.exists('historique_paris.csv'):
        df = pd.read_csv('historique_paris.csv')
        st.dataframe(df)
        clos = df[df['Statut'].isin([1, 2])]
        if not clos.empty:
            profit = sum([(r['Mise']*r['Cote']-r['Mise']) if r['Statut']==1 else -r['Mise'] for _,r in clos.iterrows()])
            st.metric("Profit Net", f"{profit:.2f}€")
