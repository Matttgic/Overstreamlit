"""Scan quotidien : value bets du jour + règlement des paris passés.

Usage : python scripts/daily_scan.py [--bankroll 1000] [--min-ev 0.03] [--model-weight 0]

Écrit :
- picks/latest.csv   : paris recommandés pour les prochains jours
- picks/history.csv  : historique complet (statut en attente / gagné / perdu)
- picks/bilan.md     : bilan (ROI, CLV indicative, nombre de paris)

Aucune clé API n'est nécessaire (données football-data.co.uk).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportpred.live import scanner as sc  # noqa: E402

PICKS = ROOT / "picks"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bankroll", type=float, default=1000.0)
    ap.add_argument("--min-ev", type=float, default=0.03)
    ap.add_argument("--model-weight", type=float, default=0.0)
    ap.add_argument("--books", default="B365,BW")
    a = ap.parse_args()
    cfg = sc.ScanConfig(min_ev=a.min_ev, model_weight=a.model_weight, bankroll=a.bankroll,
                        soft_books=a.books.split(","))
    PICKS.mkdir(exist_ok=True)

    fx = sc.load_fixtures()
    s = sc.current_season_code()
    prev = f"{(int(s[:2]) - 1) % 100:02d}{int(s[:2]):02d}"
    prev2 = f"{(int(s[:2]) - 2) % 100:02d}{(int(s[:2]) - 1) % 100:02d}"
    results = sc.load_recent_results([prev2, prev, s])
    if cfg.model_weight > 0:
        dc = sc.dixon_coles_today(results, fx)
        fx = fx.join(dc)
    picks = sc.find_value(fx, cfg)
    picks.to_csv(PICKS / "latest.csv", index=False)
    print(f"{len(fx)} matchs à venir, {len(picks)} value bets")
    if len(picks):
        print(picks.to_string(index=False))

    hist_path = PICKS / "history.csv"
    hist = pd.read_csv(hist_path) if hist_path.exists() else pd.DataFrame()
    if len(picks):
        new = picks.assign(**{"statut": "en attente", "profit_€": 0.0, "date": picks["date"].astype(str)})
        hist = pd.concat([hist, new], ignore_index=True)
        hist = hist.drop_duplicates(["date", "match", "selection"], keep="first")
    hist = sc.settle(hist, results)
    if len(hist):
        hist.to_csv(hist_path, index=False)
        done = hist[hist["statut"] != "en attente"]
        lines = ["# Bilan du scanner (paris réels proposés, suivi automatique)", ""]
        if len(done):
            mise = done["mise_€"].sum()
            prof = done["profit_€"].sum()
            lines += [f"- Paris réglés : {len(done)}", f"- Mises : {mise:.2f} €",
                      f"- Profit : {prof:.2f} €", f"- ROI : {100 * prof / mise:.2f} %",
                      f"- EV moyenne annoncée : {100 * done['ev'].mean():.2f} %",
                      f"- En attente : {(hist['statut'] == 'en attente').sum()}"]
        else:
            lines.append("Aucun pari réglé pour l'instant.")
        (PICKS / "bilan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
