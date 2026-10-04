"""Cotes joueurs Winamax et Betclic envoyées par le téléphone de l'utilisateur.

Winamax et Betclic bloquent tous les serveurs ; le téléphone (Termux, `telephone/collecte_fr.py`)
lit leurs pages depuis la connexion de l'utilisateur et dépose `cotes_fr.json.gz` sur la
branche `cotes-telephone` du dépôt. Ce module le relit (dépôt public : pas de jeton) et le met
au format des cotes Unibet (`sportpred.live.unibet`) pour la comparaison commune
(`nhl_scorers.compare_book_props`).
"""
from __future__ import annotations

import gzip
import json

import pandas as pd
import requests

RAW = "https://raw.githubusercontent.com/Matttgic/Overstreamlit/cotes-telephone/cotes_fr.json.gz"


def parse(payload: dict, now: pd.Timestamp, max_age_hours: float = 4.0) -> tuple[pd.DataFrame, dict]:
    """(cotes au format comparaison, état de la collecte : status, at, stats, errors)."""
    meta = {"status": "ok", "at": payload.get("at"), "stats": payload.get("stats") or {},
            "errors": (payload.get("errors") or [])[:10]}
    try:
        at = pd.Timestamp(payload.get("at"))
        at = at.tz_localize("UTC") if at.tzinfo is None else at.tz_convert("UTC")
    except (TypeError, ValueError):
        return pd.DataFrame(), {**meta, "status": "date illisible"}
    if now - at > pd.Timedelta(hours=max_age_hours):
        return pd.DataFrame(), {**meta, "status": "trop ancien"}
    df = pd.DataFrame(payload.get("rows") or [])
    need = {"book", "event", "start", "stat", "line", "player", "odds"}
    if df.empty or not need.issubset(df.columns):
        return pd.DataFrame(), {**meta, "status": "aucune cote"}
    df["start"] = pd.to_datetime(df["start"], utc=True)
    df = df[df["start"] > now]
    df["reg_only"] = df["reg_only"].fillna(False).astype(bool) if "reg_only" in df else False
    df["ub_event_id"] = df["book"] + "|" + df["event"].astype(str) + "|" + df["start"].astype(str)
    df["ub_event"] = df["event"]
    return df.reset_index(drop=True), meta


def load(now: pd.Timestamp, url: str = RAW, max_age_hours: float = 4.0) -> tuple[pd.DataFrame, dict]:
    try:
        r = requests.get(url, timeout=20)
    except requests.RequestException as e:
        return pd.DataFrame(), {"status": f"inaccessible ({type(e).__name__})"}
    if r.status_code == 404:
        return pd.DataFrame(), {"status": "pas encore de collecte"}
    if r.status_code != 200:
        return pd.DataFrame(), {"status": f"erreur {r.status_code}"}
    try:
        payload = json.loads(gzip.decompress(r.content))
    except (OSError, ValueError):
        return pd.DataFrame(), {"status": "fichier illisible"}
    rows = [x for x in payload.get("rows") or [] if x.get("sport", "hockey") == "hockey"]   # NHL seulement
    return parse({**payload, "rows": rows}, now, max_age_hours)


def load_boosts(now: pd.Timestamp, url: str = RAW, max_age_hours: float = 6.0) -> pd.DataFrame:
    """Cotes boostées Winamax / Betclic envoyées par le téléphone (champ « boosts » du fichier)."""
    try:
        r = requests.get(url, timeout=20)
        payload = json.loads(gzip.decompress(r.content)) if r.status_code == 200 else {}
    except (requests.RequestException, OSError, ValueError):
        return pd.DataFrame()
    try:
        at = pd.Timestamp(payload.get("at"))
        at = at.tz_localize("UTC") if at.tzinfo is None else at.tz_convert("UTC")
    except (TypeError, ValueError):
        return pd.DataFrame()
    b = pd.DataFrame(payload.get("boosts") or [])
    if b.empty or now - at > pd.Timedelta(hours=max_age_hours) or not {"book", "text", "odds"} <= set(b.columns):
        return pd.DataFrame()
    b["start"] = pd.to_datetime(b.get("start"), utc=True, errors="coerce")
    return b[(b["start"].isna()) | (b["start"] > now)].reset_index(drop=True)


def load_football(now: pd.Timestamp, url: str = RAW, max_age_hours: float = 6.0) -> pd.DataFrame:
    """Cotes buteurs football Winamax / Betclic du téléphone (lignes « sport » = football)."""
    try:
        r = requests.get(url, timeout=20)
        payload = json.loads(gzip.decompress(r.content)) if r.status_code == 200 else {}
    except (requests.RequestException, OSError, ValueError):
        return pd.DataFrame()
    rows = [x for x in payload.get("rows") or [] if x.get("sport") == "football"]
    if not rows:
        return pd.DataFrame()
    df, meta = parse({**payload, "rows": rows}, now, max_age_hours)
    return df
