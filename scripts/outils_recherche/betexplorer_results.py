#!/usr/bin/env python3
"""Parse a Betexplorer 'results' page (static HTML) -> DataFrame(match, score, odds..., date).
Usage: python3 betexplorer_results.py https://www.betexplorer.com/handball/france/starligue-2024-2025/results/
Respecter robots.txt (pas de ?year=, pas de /bookmaker/) et limiter la cadence (>= 3-5 s entre requêtes)."""
import sys, re, requests, pandas as pd
from bs4 import BeautifulSoup
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def parse(url):
    soup = BeautifulSoup(requests.get(url, headers=UA, timeout=30).text, "lxml")
    rows, rnd = [], None
    for tr in soup.select("table.table-main tr"):
        th = tr.find("th")
        if th is not None:
            rnd = th.get_text(strip=True); continue
        a = tr.select_one("td a.in-match")
        if not a: continue
        tds = tr.find_all("td")
        odds = []
        for td in tr.select("td.table-main__odds"):  # la cote gagnante est dans un <span data-odd> imbriqué
            el = td if td.get("data-odd") else td.select_one("[data-odd]")
            odds.append(float(el["data-odd"]) if el is not None and el.get("data-odd") else None)
        # NB: la page statique ne montre que la dernière phase/les derniers tours ; les autres phases
        # sont accessibles via les liens de 'stage' de la page (pas via ?year=, interdit par robots.txt).
        rows.append({"round": rnd, "match": a.get_text(" ", strip=True), "href": a.get("href"),
                     "score": tr.select_one("td.h-text-center a, td.h-text-center").get_text(strip=True) if tr.select_one("td.h-text-center") else None,
                     **{f"odd_{i+1}": o for i, o in enumerate(odds)}, "date": (tr.select_one("td.h-text-right") or tds[-1]).get_text(strip=True)})
    return pd.DataFrame(rows)
if __name__ == "__main__":
    df = parse(sys.argv[1]); print(df.shape); print(df.head(8).to_string())
