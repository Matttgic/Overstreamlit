"""Cotes joueurs NHL d'Unibet.fr (opérateur agréé ANJ), lues sur les pages publiques du site.

Aucune API gratuite ne fournit les cotes « paris joueurs » des opérateurs français (The Odds
API : vainqueur et totaux seulement ; Kambi ne sert pas l'offre Unibet France). Les pages de
match d'Unibet.fr contiennent l'état de l'application (balise JSON « serverApp-state ») avec
toutes les cotes ; la page de la NHL liste les matchs (données structurées JSON-LD).

Marchés lus (ouverts le jour du match) : « Nombre de Buts - Joueur - Match (Hors TAB) »,
« Nombre de Points - Joueur », « Nombre de Passes décisives - Joueur ». Une issue
« Joueur k+ » équivaut à « plus de k − 0,5 » (ex. « 1+ » buts = buteur).

Usage volontairement léger : une page de liste + une page par match des prochaines heures,
une seconde d'intervalle, 9 fois par jour. Si le site bloque ou change de format, les
fonctions renvoient un tableau vide et le tableau de bord continue sans Unibet.
"""
from __future__ import annotations

import json
import re
import time

import pandas as pd
import requests

BASE = "https://www.unibet.fr"
NHL_LIST = "/paris-hockey-sur-glace/etats-unis/nhl"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")
STATS = {"Nombre de Buts - Joueur": "Buts", "Nombre de Points - Joueur": "Points",
         "Nombre de Passes décisives - Joueur": "Passes décisives"}
_OUTCOME = re.compile(r"^(?P<player>.+?)\s+(?P<k>\d+)\+$")


def _get(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
    except requests.RequestException:
        return None
    return r.text if r.status_code == 200 else None


def _state(html: str) -> dict | None:
    m = re.search(r'<script id="serverApp-state" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        return None
    raw = (m.group(1).replace("&q;", '"').replace("&s;", "'").replace("&l;", "<")
           .replace("&g;", ">").replace("&a;", "&"))
    try:
        return json.loads(raw)
    except ValueError:
        return None


def list_events(path: str = NHL_LIST) -> pd.DataFrame:
    """Matchs de la page `path` : event_id, name, start (UTC), url."""
    html = _get(BASE + path)
    if not html:
        return pd.DataFrame()
    rows = []
    for block in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
        try:
            j = json.loads(block)
        except ValueError:
            continue
        for e in (j if isinstance(j, list) else [j]):
            if not isinstance(e, dict) or e.get("@type") != "SportsEvent" or not e.get("url"):
                continue
            m = re.search(r"/(\d+)/[^/]+$", e["url"])
            try:      # heure de Paris, sans fuseau dans la page
                start = pd.Timestamp(e["startDate"]).tz_localize("Europe/Paris").tz_convert("UTC")
            except (ValueError, TypeError, KeyError):
                continue
            if m:
                rows.append({"event_id": int(m.group(1)), "name": e.get("name", ""), "start": start, "url": e["url"]})
    return pd.DataFrame(rows).drop_duplicates("event_id") if rows else pd.DataFrame()


def parse_player_props(state: dict) -> pd.DataFrame:
    """Issues « Joueur k+ » des marchés joueurs d'une page de match (état serverApp-state)."""
    rows = []
    for ev in (state or {}).get("EventsDetail", {}).get("events", []):
        for g in ev.get("groupedMarkets", []):
            stat = next((v for k, v in STATS.items() if str(g.get("description", "")).startswith(k)), None)
            if stat is None or "Tiers" in str(g.get("description", "")):
                continue
            for mk in g.get("markets", []):
                if mk.get("suspended"):
                    continue
                for o in mk.get("outcomes", []):
                    m = _OUTCOME.match(str(o.get("description", "")).strip())
                    if not m or o.get("suspended") or o.get("hidden"):
                        continue
                    try:
                        odds = float(str(o["price"]).replace(",", "."))
                    except (KeyError, ValueError):
                        continue
                    rows.append({"ub_event_id": int(ev["id"]), "ub_event": ev.get("description", ""),
                                 "start": pd.Timestamp(ev.get("parsedStart")), "stat": stat,
                                 "player": m.group("player"), "line": int(m.group("k")) - 0.5, "odds": odds})
    return pd.DataFrame(rows)


def nhl_player_odds(now: pd.Timestamp, horizon_hours: float = 36, max_events: int = 16,
                    pause: float = 1.0) -> pd.DataFrame:
    """Cotes joueurs Unibet.fr des matchs NHL qui commencent dans les `horizon_hours` heures."""
    ev = list_events()
    if ev.empty:
        return pd.DataFrame()
    ev = ev[(ev["start"] > now) & (ev["start"] < now + pd.Timedelta(hours=horizon_hours))]
    frames = []
    for url in ev.sort_values("start")["url"].head(max_events):
        html = _get(url)
        st = _state(html) if html else None
        if st:
            frames.append(parse_player_props(st))
        time.sleep(pause)
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
