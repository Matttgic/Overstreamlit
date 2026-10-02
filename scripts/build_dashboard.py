"""Génère site/data/today.json et site/data/history.json (tableau de bord quotidien).

Usage : python scripts/build_dashboard.py [--min-ev 0.03] [--bankroll 1000]
Optionnel : variable d'environnement THE_ODDS_API_KEY (clé gratuite the-odds-api.com)
pour comparer automatiquement les cotes Betclic/Winamax/Unibet/PMU/NetBet.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sportpred.live.dashboard import DashConfig, build  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-ev", type=float, default=0.03)
    ap.add_argument("--bankroll", type=float, default=1000.0)
    ap.add_argument("--out", default=str(ROOT / "site" / "data"))
    a = ap.parse_args()
    d = build(Path(a.out), DashConfig(min_ev=a.min_ev, bankroll=a.bankroll))
    print(f"{d['generated_at']} | cotes Pinnacle : {d['sources']['pinnacle_outcomes']} | "
          f"cotes FR : {d['sources']['fr_odds_rows']} | value bets : {len(d['value_bets'])} | "
          f"à surveiller : {len(d['watchlist'])} | props : {len(d['props'])}")
    for v in d["value_bets"][:20]:
        print(f"  {v['start']} {v['event']:<40} {v['selection']:<28} {v['book']:<8} {v['odds']:.2f} "
              f"(juste {v['fair_odds']:.2f}, EV {100*v['ev']:+.1f} %, mise {v['stake_pct']} %)")
