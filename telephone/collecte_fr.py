#!/usr/bin/env python3
"""Collecte des cotes Winamax et Betclic depuis un téléphone Android (Termux).

Pourquoi le téléphone : Winamax et Betclic bloquent tous les serveurs (GitHub, cloud),
mais pas une connexion française ordinaire (wifi ou 4G). Le téléphone télécharge donc
les pages et les dépose sur le dépôt GitHub ; tout le reste (lecture des cotes,
comparaison avec la cote juste, alertes) tourne sur GitHub.

Usage (dans Termux) :
    python collecte_fr.py sonde     # une seule fois : échantillon de pages NHL pour régler la lecture

Le jeton GitHub est lu dans ~/.overstreamlit_token (jamais affiché, jamais envoyé
ailleurs qu'à api.github.com). Il doit avoir uniquement l'accès « Contents : Read and
write » sur le dépôt Overstreamlit. Les fichiers sont déposés sur la branche
« cotes-telephone » (créée au premier passage), jamais sur « main ».

Aucune dépendance : Python standard uniquement (pkg install python).
"""
from __future__ import annotations

import base64
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = "Matttgic/Overstreamlit"
BRANCH = "cotes-telephone"
TOKEN_FILE = Path.home() / ".overstreamlit_token"
UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0.0.0 Mobile Safari/537.36")
WINAMAX = "https://www.winamax.fr"
BETCLIC = "https://www.betclic.fr"


# ----------------------------------------------------------------------------- réseau
def http_get(url: str, timeout: int = 30) -> tuple[int, str, bytes]:
    """(statut, adresse finale, contenu) ; ne lève pas d'exception."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            return r.status, r.geturl(), data
    except urllib.error.HTTPError as e:
        return e.code, url, e.read() or b""
    except Exception as e:  # noqa: BLE001 — réseau du téléphone : on note et on continue
        return 0, url, str(e).encode()


def extract_json_after(text: str, marker: str) -> dict | None:
    """Premier objet JSON qui suit `marker` dans une page (ex. « PRELOADED_STATE »)."""
    i = text.find(marker)
    if i < 0:
        return None
    j = text.find("{", i)
    if j < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[j:])
        return obj if isinstance(obj, dict) else None
    except ValueError:
        return None


# ----------------------------------------------------------------------------- GitHub
def _token() -> str:
    if not TOKEN_FILE.exists():
        sys.exit(f"Jeton introuvable : créez {TOKEN_FILE} (voir telephone/README.md).")
    return TOKEN_FILE.read_text().strip()


def gh(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"https://api.github.com{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {_token()}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "overstreamlit-telephone"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"message": raw[:200].decode(errors="ignore")}


def ensure_branch() -> None:
    st, _ = gh("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}")
    if st == 200:
        return
    st, main = gh("GET", f"/repos/{REPO}/git/ref/heads/main")
    if st != 200:
        sys.exit(f"Accès au dépôt refusé ({st}) : vérifiez le jeton (droit Contents : Read and write).")
    st, out = gh("POST", f"/repos/{REPO}/git/refs",
                 {"ref": f"refs/heads/{BRANCH}", "sha": main["object"]["sha"]})
    if st not in (200, 201):
        sys.exit(f"Création de la branche {BRANCH} impossible ({st}) : {out.get('message')}")


def put_file(path: str, content: bytes, message: str) -> int:
    st, cur = gh("GET", f"/repos/{REPO}/contents/{path}?ref={BRANCH}")
    body = {"message": message, "branch": BRANCH, "content": base64.b64encode(content).decode()}
    if st == 200 and isinstance(cur, dict) and cur.get("sha"):
        body["sha"] = cur["sha"]
    st, out = gh("PUT", f"/repos/{REPO}/contents/{path}", body)
    if st not in (200, 201):
        print(f"  ! envoi de {path} refusé ({st}) : {out.get('message')}")
    return st


# ----------------------------------------------------------------------------- sonde
def _winamax_nhl_matches(state: dict) -> list[str]:
    """Identifiants des matchs NHL à venir dans l'état PRELOADED_STATE de Winamax."""
    tours = state.get("tournaments") or {}
    nhl = {str(k) for k, t in tours.items() if isinstance(t, dict) and "NHL" in str(t.get("tournamentName", ""))}
    ms = [m for m in (state.get("matches") or {}).values()
          if isinstance(m, dict) and str(m.get("tournamentId")) in nhl]
    ms.sort(key=lambda m: m.get("matchStart") or 0)
    return [str(m.get("matchId")) for m in ms if m.get("matchId")]


def sonde(max_matches: int = 3) -> None:
    """Dépose un échantillon de pages (gzip) dans sonde/ sur la branche cotes-telephone."""
    print("Vérification du jeton GitHub…")
    ensure_branch()                      # échoue tout de suite si le jeton est absent ou insuffisant
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    files, report = {}, {"at": stamp, "pages": []}

    def grab(name: str, url: str) -> bytes:
        st, final, data = http_get(url)
        report["pages"].append({"name": name, "url": url, "final_url": final, "status": st, "bytes": len(data)})
        print(f"  {st} {len(data) // 1024:>6} Ko  {name}")
        if data:
            files[f"sonde/{name}.gz"] = gzip.compress(data)
        time.sleep(1.5)
        return data

    print("Winamax :")
    page = grab("winamax_hockey", f"{WINAMAX}/paris-sportifs/sports/4").decode("utf-8", "ignore")
    state = extract_json_after(page, "PRELOADED_STATE") or {}
    ids = _winamax_nhl_matches(state)
    if not ids:                          # page d'accueil des paris : liste des sports et des matchs
        home = grab("winamax_accueil", f"{WINAMAX}/paris-sportifs").decode("utf-8", "ignore")
        st2 = extract_json_after(home, "PRELOADED_STATE") or {}
        report["winamax_sports"] = {k: v.get("sportName") for k, v in (st2.get("sports") or {}).items()
                                    if isinstance(v, dict)}
        ids = _winamax_nhl_matches(st2) or re.findall(r"/paris-sportifs/match/(\d+)", page + home)
    report["winamax_nhl_ids"] = ids[:20]
    for mid in list(dict.fromkeys(ids))[:max_matches]:
        grab(f"winamax_match_{mid}", f"{WINAMAX}/paris-sportifs/match/{mid}")

    print("Betclic :")
    page = grab("betclic_hockey", f"{BETCLIC}/hockey-sur-glace-s13").decode("utf-8", "ignore")
    links = list(dict.fromkeys(re.findall(r'href="(/hockey-sur-glace-s13/[^"]*nhl[^"]*-m\d+)"', page, re.I)))
    comp = re.findall(r'href="(/hockey-sur-glace-s13/[^"]*nhl[^"]*-c\d+)"', page, re.I)
    if comp:
        cpage = grab("betclic_nhl", BETCLIC + comp[0]).decode("utf-8", "ignore")
        links += [u for u in dict.fromkeys(re.findall(r'href="(/hockey-sur-glace-s13/[^"]*-m\d+)"', cpage))
                  if u not in links]
    report["betclic_links"] = links[:20]
    for k, path in enumerate(links[:max_matches]):
        grab(f"betclic_match_{k}", BETCLIC + path)
    grab("betclic_api_events", "https://offer.cdn.betclic.fr/api/pub/v4/events?application=2&countrycode=fr"
                               "&language=fr&sitecode=frfr&sportIds=13&limit=50")

    print("Envoi sur GitHub (branche cotes-telephone) :")
    files["sonde/rapport.json"] = json.dumps(report, indent=1, ensure_ascii=False).encode()
    ok = sum(put_file(p, c, f"Sonde téléphone {stamp} : {p}") in (200, 201) for p, c in files.items())
    print(f"  {ok}/{len(files)} fichiers déposés. Merci ! Vous pouvez prévenir Claude.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sonde":
        sonde()
    else:
        print(__doc__)
