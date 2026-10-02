"""Télécharge les données gratuites (résultats + cotes) des autres sports autorisés ANJ.

Sources vérifiées le 02/10/2026 (voir docs/03_sources_de_donnees.md) :
- Tennis ATP 2000-2026 / WTA 2007-2026 : miroir GitHub de tennis-data.co.uk
- NBA 2016-2026 : wippa-studios/wippa-nba-data (cotes décimales de clôture)
- NBA / NHL / MLB 2011-2022 : flancast90/sportsbookreview-scraper (archive SBR, JSON)
- NFL 1999-2026 : nflverse/nfldata games.csv (spread, total, moneyline)
- MLB 2006-2024 : Hugging Face Oronto (Oddsportal)
- MMA (UFC) 2010-2026 : shortlikeafox/ultimate_ufc_dataset
- Football international 1872-2026 : martj42/international_results (sans cotes)
- Rugby (Top 14, Premiership, URC…) : transientlunatic/Rugby-Data (sans cotes)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
GH = "https://raw.githubusercontent.com"

SOURCES = {
    "tennis/atp": [(f"{GH}/nick-benelli/Tennis-Data-Pipeline/main/data/raw/uk/atp/uk_atp_singles_raw_{y}.csv",
                    f"atp_{y}.csv") for y in range(2000, 2027)],
    "tennis/wta": [(f"{GH}/nick-benelli/Tennis-Data-Pipeline/main/data/raw/uk/wta/uk_wta_singles_raw_{y}.csv",
                    f"wta_{y}.csv") for y in range(2007, 2027)],
    "nba": [(f"{GH}/wippa-studios/wippa-nba-data/main/seasons/{y}-{y + 1}/nba_{y}-{y + 1}_results_odds.csv",
             f"nba_{y}.csv") for y in range(2016, 2026)]
    + [(f"{GH}/flancast90/sportsbookreview-scraper/main/data/nba_archive_10Y.json", "nba_sbr.json")],
    "nhl": [(f"{GH}/flancast90/sportsbookreview-scraper/main/data/nhl_archive_10Y.json", "nhl_sbr.json")],
    "mlb": [(f"{GH}/flancast90/sportsbookreview-scraper/main/data/mlb_archive_10Y.json", "mlb_sbr.json"),
            ("https://huggingface.co/datasets/Oronto/baseball-stats-cleaned_oddsportal_mlb/resolve/main/"
             "data/train-00000-of-00001.parquet", "mlb_oddsportal.parquet")],
    "nfl": [(f"{GH}/nflverse/nfldata/master/data/games.csv", "games.csv")],
    "mma": [(f"{GH}/shortlikeafox/ultimate_ufc_dataset/master/ufc-master.csv", "ufc-master.csv")],
    "international": [(f"{GH}/martj42/international_results/master/results.csv", "results.csv")],
}


def get(url: str, dest: Path, retries: int = 4) -> bool:
    for i in range(retries):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 404:
                return False
            r.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.content)
            return True
        except requests.RequestException:
            time.sleep(2 ** (i + 1))
    return False


def main(only: list[str] | None = None, force: bool = False):
    for key, files in SOURCES.items():
        if only and key.split("/")[0] not in only:
            continue
        ok = 0
        for url, name in files:
            dest = RAW / key / name
            if dest.exists() and not force and dest.stat().st_size > 0:
                ok += 1
                continue
            ok += get(url, dest)
        print(f"{key}: {ok}/{len(files)} fichiers")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
