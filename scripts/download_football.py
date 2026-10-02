"""Télécharge et normalise toutes les données football-data.co.uk.

Usage : python scripts/download_football.py [--first 2005] [--last 2025]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sportpred.data import football_data as fd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=2005)
    ap.add_argument("--last", type=int, default=2025)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    raw = ROOT / "data" / "raw" / "football"
    files = fd.download_main(raw, seasons=fd.season_codes(a.first, a.last), force=a.force)
    print(f"{len(files)} fichiers principaux")
    extra = fd.download_extra(raw, force=a.force)
    print(f"{len(extra)} fichiers extra")
    paths = fd.build_dataset(raw, ROOT / "data" / "processed")
    print(paths)
