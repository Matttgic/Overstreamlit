"""Notifications Telegram gratuites des nouveaux value bets.

Mise en place (5 minutes, gratuit) :
1. Dans Telegram, écrire à @BotFather -> /newbot -> récupérer le jeton (TELEGRAM_BOT_TOKEN).
2. Écrire un message à votre bot, puis ouvrir
   https://api.telegram.org/bot<JETON>/getUpdates pour lire votre « chat id ».
3. Ajouter les secrets GitHub TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID.
Sans ces secrets, rien n'est envoyé (aucune erreur).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import requests


def _fmt(v: dict) -> str:
    return (f"[{str(v.get('sport', '')).upper()}] {v['event']} ({v['league']})\n"
            f"➡️ {v['selection']} — {v['book']} à {v['odds']:.2f}\n"
            f"Cote juste {v['fair_odds']:.2f} · EV {100 * v['ev']:+.1f} % · mise {v['stake_pct']:.2f} %\n"
            f"Début : {v['start'][:16].replace('T', ' ')} UTC")


def send_new_value_bets(data: dict, state_file: Path, site_url: str | None = None) -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat:
        return 0
    sent = set(json.loads(state_file.read_text())) if state_file.exists() else set()
    new = [v for v in data.get("value_bets", [])
           if f"{v['event']}|{v['selection']}|{v['book']}" not in sent]
    n = 0
    for v in new[:10]:
        text = _fmt(v) + (f"\n{site_url}" if site_url else "")
        try:
            r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                              json={"chat_id": chat, "text": text}, timeout=20)
            if r.ok:
                sent.add(f"{v['event']}|{v['selection']}|{v['book']}")
                n += 1
        except requests.RequestException:
            break
    state_file.write_text(json.dumps(sorted(sent)[-500:]), encoding="utf-8")
    return n
