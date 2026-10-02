"""Appariement prudent d'événements entre deux sources de cotes.

Leçon de l'ancien système : une correspondance floue trop permissive (difflib, seuil 0,4)
a associé « Sunderland » à « Salernitana ». Ici on exige :
1. des heures de début proches (± `max_hours`) ;
2. une similarité élevée pour LES DEUX équipes/joueurs (après normalisation) ;
3. une correspondance UNIQUE (si deux candidats sont proches, on abandonne).
Mieux vaut rater un match que parier sur le mauvais.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd

STOP = {"fc", "cf", "sc", "ac", "afc", "as", "ss", "ssc", "us", "rc", "sv", "vfb", "vfl", "tsg", "fk",
        "sk", "bk", "if", "cd", "ud", "sd", "rcd", "de", "la", "le", "les", "the", "club", "calcio",
        "1.", "1", "04", "05", "09", "96", "1899", "1846", "1907", "1910", "1913"}
ALIASES = {
    "paris saint germain": "psg", "paris sg": "psg", "man city": "manchester city",
    "man united": "manchester united", "man utd": "manchester united", "nottm forest": "nottingham forest",
    "nott'm forest": "nottingham forest", "wolves": "wolverhampton wanderers",
    "spurs": "tottenham hotspur", "tottenham": "tottenham hotspur", "inter": "inter milan",
    "internazionale": "inter milan", "bayern munich": "bayern munchen", "bayern münchen": "bayern munchen",
    "athletic bilbao": "athletic club", "ath bilbao": "athletic club", "ath madrid": "atletico madrid",
    "atletico de madrid": "atletico madrid", "sociedad": "real sociedad", "betis": "real betis",
    "m'gladbach": "borussia monchengladbach", "monchengladbach": "borussia monchengladbach",
    "dortmund": "borussia dortmund", "leverkusen": "bayer leverkusen", "ein frankfurt": "eintracht frankfurt",
    "st etienne": "saint etienne", "olympique lyonnais": "lyon", "olympique de marseille": "marseille",
}


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9' ]+", " ", s).strip()
    s = ALIASES.get(s, s)
    toks = [t for t in s.split() if t not in STOP]
    return " ".join(toks) if toks else s


def sim(a: str, b: str) -> float:
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ta, tb = set(a.split()), set(b.split())
    jacc = len(ta & tb) / len(ta | tb)
    # un nom contenu dans l'autre (« lens » / « rc lens ») : forte similarité
    contain = 0.9 if (a in b or b in a) and min(len(a), len(b)) >= 4 else 0.0
    return max(SequenceMatcher(None, a, b).ratio(), jacc, contain)


def match_events(left: pd.DataFrame, right: pd.DataFrame, max_hours: float = 3.0,
                 min_sim: float = 0.8, margin: float = 0.1, swap_ok: bool = False) -> pd.DataFrame:
    """Apparie left(event_id, start, home, away) à right(event_id, start, home, away).

    Retourne un DataFrame left_id, right_id, score. `swap_ok=True` autorise l'inversion
    domicile/extérieur (tennis, MMA : pas de notion de domicile).
    """
    rows = []
    R = right.drop_duplicates("event_id")
    for l in left.drop_duplicates("event_id").itertuples():
        cand = R[(R["start"] - l.start).abs() <= pd.Timedelta(hours=max_hours)]
        scored = []
        for r in cand.itertuples():
            s1 = min(sim(l.home, r.home), sim(l.away, r.away))
            s2 = min(sim(l.home, r.away), sim(l.away, r.home)) if swap_ok else 0.0
            scored.append((max(s1, s2), r.event_id, s2 > s1))
        scored.sort(reverse=True)
        if not scored or scored[0][0] < min_sim:
            continue
        if len(scored) > 1 and scored[1][0] > scored[0][0] - margin:
            continue  # ambigu : on s'abstient
        rows.append({"left_id": l.event_id, "right_id": scored[0][1], "score": scored[0][0],
                     "swapped": scored[0][2]})
    return pd.DataFrame(rows, columns=["left_id", "right_id", "score", "swapped"])
