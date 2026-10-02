#!/usr/bin/env python3
"""Snippets testés le 2026-10-02 depuis le conteneur (proxy HTTPS, IP hors France).
- sbr_season(sport, season)  : archive SportsbookReviewsOnline (NBA/NHL/NFL HTML, MLB xlsx) -> 1 ligne par match
- espn_odds(sport, league, date): cotes ESPN core API (multi-bookmakers, open/close récents)
- understat_league(league, year): xG Understat via endpoint AJAX
- tennis_data(tour, year)    : miroir GitHub tennis-data.co.uk (B365/PS/Max/Avg/BFE)
Dépendances: requests pandas lxml openpyxl
"""
import io, requests, pandas as pd
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

def tennis_data(tour="atp", year=2025):
    """tour='atp' (2000-2026) ou 'wta' (2007-2026)."""
    u = f"https://raw.githubusercontent.com/nick-benelli/Tennis-Data-Pipeline/main/data/raw/uk/{tour}/uk_{tour}_singles_raw_{year}.csv"
    df = pd.read_csv(u, encoding_errors="replace")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", format="mixed")
    return df

def sbr_season(sport="nba", season="2021-22"):
    """sport in nba|nhl|nfl (HTML, season '2021-22') ou mlb (xlsx, season '2021').
    Retourne 1 ligne par match (visiteur V + domicile H appariés). Colonnes brutes SBR suffixées _v/_h."""
    if sport == "mlb":
        u = f"https://www.sportsbookreviewsonline.com/wp-content/uploads/sportsbookreviewsonline_com_737/mlb-odds-{season}.xlsx"
        raw = pd.read_excel(io.BytesIO(requests.get(u, headers=UA, timeout=60).content))
    else:
        u = f"https://www.sportsbookreviewsonline.com/scoresoddsarchives/{sport}-odds-{season}"
        t = pd.read_html(io.StringIO(requests.get(u, headers=UA, timeout=60).text))[0]
        raw = t.iloc[1:].copy(); raw.columns = [str(c) for c in t.iloc[0]]
    raw = raw.reset_index(drop=True)
    # lignes N (neutre) : la 1re du couple joue le rôle de V
    v, h = raw.iloc[0::2].reset_index(drop=True), raw.iloc[1::2].reset_index(drop=True)
    return v.add_suffix("_v").join(h.add_suffix("_h"))

def espn_scoreboard(sport="basketball", league="nba", date="20250115"):
    u = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
    return requests.get(u, params={"dates": date}, headers=UA, timeout=30).json().get("events", [])

def espn_odds(sport="basketball", league="nba", date="20250115"):
    """Une ligne par (match, bookmaker). Profondeur: NBA ~2015+, NFL ~2015+, NHL ~2019+, MLB ~2010+ (partiel),
    soccer (eng.1, fra.1...) ~2019+. open/close structurés surtout depuis 2023."""
    rows = []
    for ev in espn_scoreboard(sport, league, date):
        eid = ev["id"]
        u = f"https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{eid}/competitions/{eid}/odds"
        for it in requests.get(u, headers=UA, timeout=30).json().get("items", []):
            h, a = it.get("homeTeamOdds", {}) or {}, it.get("awayTeamOdds", {}) or {}
            def ml(side, k):
                x = side.get(k)
                return x.get("moneyLine", {}).get("american") if isinstance(x, dict) else None
            rows.append({"event_id": eid, "name": ev.get("name"), "date": ev.get("date"),
                         "book": (it.get("provider") or {}).get("name"), "details": it.get("details"),
                         "spread": it.get("spread"), "total": it.get("overUnder"),
                         "ml_home": h.get("moneyLine"), "ml_away": a.get("moneyLine"),
                         "ml_home_open": ml(h, "open"), "ml_home_close": ml(h, "close"),
                         "ml_away_open": ml(a, "open"), "ml_away_close": ml(a, "close")})
    return pd.DataFrame(rows)

def understat_league(league="EPL", year=2024):
    """league: EPL, La_liga, Bundesliga, Serie_A, Ligue_1, RFPL ; year = année de début de saison.
    ATTENTION: robots.txt d'Understat = Disallow: / -> usage personnel, très faible fréquence."""
    r = requests.get(f"https://understat.com/getLeagueData/{league}/{year}",
                     headers={**UA, "X-Requested-With": "XMLHttpRequest"}, timeout=30)
    d = r.json()  # requests décompresse le gzip
    matches = pd.json_normalize(d["dates"])
    return matches, d["teams"], pd.DataFrame(d["players"])

if __name__ == "__main__":
    print(tennis_data("atp", 2025)[["Date", "Winner", "Loser", "B365W", "PSW", "AvgW", "BFEW"]].head(3))
    print(sbr_season("nhl", "2022-23").iloc[:2, :12])
    print(espn_odds("hockey", "nhl", "20240115").head(5))
    m, _, _ = understat_league("Ligue_1", 2024); print(m[["datetime", "h.title", "a.title", "xG.h", "xG.a"]].head(3))
