#!/usr/bin/env python3
"""Collecte des cotes Winamax et Betclic depuis un téléphone Android (Termux).

Pourquoi le téléphone : Winamax et Betclic bloquent tous les serveurs (GitHub, cloud),
mais pas une connexion française ordinaire (wifi ou 4G). Le téléphone télécharge donc
les pages et les dépose sur le dépôt GitHub ; tout le reste (lecture des cotes,
comparaison avec la cote juste, alertes) tourne sur GitHub.

Usage (dans Termux) :
    python collecte_fr.py           # collecte : cotes joueurs NHL Winamax + Betclic -> GitHub
    python collecte_fr.py sonde     # diagnostic : échantillon de pages NHL brutes

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
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
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
        "User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9", "Accept-Encoding": "gzip",
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


# ----------------------------------------------------------------------------- lecture des cotes
HORIZON_H = 30            # matchs qui commencent dans les 30 heures
MAX_MATCHES = 16          # par bookmaker et par passage
_WM_BETS = [(re.compile(r"^Buteur$"), "Buts", None),
            (re.compile(r"^Marque (\d+) buts? ou plus$"), "Buts", 1),
            (re.compile(r"^Points du joueur : (\d+) ou plus$"), "Points", 1),
            (re.compile(r"^Passes décisives du joueur : (\d+) ou plus$"), "Passes décisives", 1)]
_BC_BETS = [(re.compile(r"^Buteur$"), "Buts", None),
            (re.compile(r"^Le joueur inscrit (\d+) buts? ou \+"), "Buts", 1)]


def _iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def winamax_nhl_upcoming(state: dict, now: datetime, horizon_h: float = HORIZON_H) -> list[str]:
    """Matchs NHL pas encore commencés (PREMATCH) dans les `horizon_h` heures."""
    tours = state.get("tournaments") or {}
    nhl = {str(k) for k, t in tours.items() if isinstance(t, dict) and str(t.get("tournamentName", "")) == "NHL"}
    lo, hi = now.timestamp(), now.timestamp() + horizon_h * 3600
    ms = [m for m in (state.get("matches") or {}).values()
          if isinstance(m, dict) and str(m.get("tournamentId")) in nhl and m.get("status") == "PREMATCH"
          and lo < (m.get("matchStart") or 0) < hi]
    return [str(m["matchId"]) for m in sorted(ms, key=lambda m: m["matchStart"])]


def parse_winamax_match(state: dict, match_id: str) -> list[dict]:
    """Cotes joueurs d'une page de match Winamax (état PRELOADED_STATE)."""
    m = (state.get("matches") or {}).get(str(match_id))
    if not isinstance(m, dict):
        return []
    bets, outs, odds = state.get("bets") or {}, state.get("outcomes") or {}, state.get("odds") or {}
    start = _iso(datetime.fromtimestamp(m.get("matchStart") or 0, timezone.utc))
    rows = []
    for bid in m.get("bets") or []:
        b = bets.get(str(bid))
        if not isinstance(b, dict) or not b.get("available", True):
            continue
        title = str(b.get("betTitle", "")).strip()
        for pat, stat, grp in _WM_BETS:
            mm = pat.match(title)
            if not mm:
                continue
            k = int(mm.group(grp)) if grp else 1
            # paris joueurs Winamax : hors prolongation (précisé sur buteur, points, passes ;
            # « Marque N buts ou plus » n'a pas de texte d'aide : même règle)
            hlp = str(b.get("betTypeHelp", "")).lower()
            reg_only = not ("prolongation" in hlp and "inclus" in hlp)
            for oid in b.get("outcomes") or []:
                o, od = outs.get(str(oid)) or {}, odds.get(str(oid))
                try:
                    od = float(od)
                except (TypeError, ValueError):
                    continue
                if o.get("available", True) and od > 1 and o.get("label"):
                    rows.append({"book": "Winamax", "event": m.get("title"), "home": m.get("competitor1Name"),
                                 "away": m.get("competitor2Name"), "start": start, "stat": stat,
                                 "line": k - 0.5, "player": o["label"], "odds": od, "reg_only": reg_only})
            break
    return rows


def betclic_state(html: str) -> dict | None:
    m = re.search(r'<script id="ng-state" type="application/json">(.*?)</script>', html, re.S)
    try:
        return json.loads(m.group(1)) if m else None
    except ValueError:
        return None


def _betclic_payload(state: dict | None) -> dict:
    for k, v in (state or {}).items():
        if str(k).startswith("grpc:") and isinstance(v, dict):
            return (v.get("response") or {}).get("payload") or {}
    return {}


def _betclic_date(s: str) -> datetime:
    return datetime.fromisoformat(str(s)[:19]).replace(tzinfo=timezone.utc)


def _betclic_matches(o, out: list) -> list:
    """Tous les objets « match » (matchId + matchDateUtc) d'un état Betclic."""
    if isinstance(o, dict):
        if "matchId" in o and "matchDateUtc" in o:
            out.append(o)
        for v in o.values():
            _betclic_matches(v, out)
    elif isinstance(o, list):
        for v in o:
            _betclic_matches(v, out)
    return out


def _slug(name: str) -> str:
    """« Dallas Stars - St. Louis Blues » -> « dallas-stars-st-louis-blues » (adresses Betclic)."""
    txt = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", txt).strip("-")


BC_NHL = "/hockey-sur-glace-sice_hockey/nhl-c83"


def betclic_nhl_upcoming(html: str, now: datetime, horizon_h: float = HORIZON_H) -> list[str]:
    """Chemins des pages de match NHL pas encore commencés (page hockey et/ou page NHL, à la
    suite). La page n'a pas de lien pour tous les matchs de son état : adresse construite
    depuis le nom du match dans ce cas (même règle que les liens réels)."""
    found = {}
    for st in re.findall(r'<script id="ng-state" type="application/json">(.*?)</script>', html, re.S):
        try:
            state = json.loads(st)
        except ValueError:
            continue
        for m in _betclic_matches(state, []):
            try:
                t = _betclic_date(m["matchDateUtc"])
            except (KeyError, ValueError):
                continue
            if (str((m.get("competition") or {}).get("name")) == "NHL" and not m.get("isLive")
                    and now < t < now + timedelta(hours=horizon_h)):
                found.setdefault(str(m["matchId"]), (t, m.get("name")))
    links = dict((mid, path) for path, mid in
                 re.findall(r'href="(/[a-z0-9_\-]+/nhl-c\d+/[a-z0-9\-]+-m(\d+))"', html, re.I)[::-1])
    comp = re.search(r'href="(/[a-z0-9_\-]+/nhl-c\d+)/', html, re.I)
    order = sorted(found, key=lambda k: found[k][0])
    return [links.get(mid) or f"{comp.group(1) if comp else BC_NHL}/{_slug(found[mid][1])}-m{mid}"
            for mid in order if links.get(mid) or found[mid][1]]


def _selections(o, out: list) -> list:
    if isinstance(o, dict):
        if "betslipName" in o and "odds" in o:
            out.append(o)
            return out
        for v in o.values():
            _selections(v, out)
    elif isinstance(o, list):
        for v in o:
            _selections(v, out)
    return out


def parse_betclic_match(state: dict | None) -> list[dict]:
    """Cotes joueurs (onglet « Le Top » : Buteur, « Le joueur inscrit N buts ou + »)."""
    m = _betclic_payload(state).get("match") or {}
    if not m:
        return []
    names = [c.get("name") for c in m.get("contestants") or []]
    start = _iso(_betclic_date(m.get("matchDateUtc", "1970-01-01T00:00:00")))
    rows, seen = [], set()
    for sc in m.get("subCategories") or []:
        for mk in sc.get("markets") or []:
            name = str(mk.get("name", "")).strip()
            for pat, stat, grp in _BC_BETS:
                mm = pat.match(name)
                if not mm:
                    continue
                k = int(mm.group(grp)) if grp else 1
                for sel in _selections(mk, []):
                    key = (sel.get("id"), k)
                    if sel.get("status") != 1 or key in seen:
                        continue
                    seen.add(key)
                    try:
                        od = float(sel["odds"])
                    except (TypeError, ValueError):
                        continue
                    if od > 1:
                        rows.append({"book": "Betclic", "event": m.get("name"),
                                     "home": names[0] if names else None, "away": names[1] if len(names) > 1 else None,
                                     "start": start, "stat": stat, "line": k - 0.5, "player": sel.get("name"),
                                     "odds": od, "reg_only": "tps r" in name.lower()})   # buteur : prolongation incluse
                break
    return rows


def collecte(horizon_h: float = HORIZON_H, pause: float = 1.0) -> None:
    """Cotes joueurs NHL Winamax + Betclic -> cotes_fr.json.gz sur la branche cotes-telephone."""
    print("Vérification du jeton GitHub…")
    ensure_branch()
    now = datetime.now(timezone.utc)
    rows, stats, errors = [], {}, []

    st, _, data = http_get(f"{WINAMAX}/paris-sportifs/sports/4")
    state = extract_json_after(data.decode("utf-8", "ignore"), "PRELOADED_STATE") if st == 200 else None
    ids = winamax_nhl_upcoming(state or {}, now, horizon_h)
    if st != 200 or state is None:
        errors.append(f"winamax liste : {st}")
    n = 0
    for mid in ids[:MAX_MATCHES]:
        time.sleep(pause)
        st, _, data = http_get(f"{WINAMAX}/paris-sportifs/match/{mid}")
        s2 = extract_json_after(data.decode("utf-8", "ignore"), "PRELOADED_STATE") if st == 200 else None
        if s2 is None:
            errors.append(f"winamax match {mid} : {st}")
            continue
        r = parse_winamax_match(s2, mid)
        n += bool(r)
        rows += r
    stats["winamax"] = {"matchs": len(ids), "avec_joueurs": n, "cotes": sum(x["book"] == "Winamax" for x in rows)}
    print(f"  Winamax : {len(ids)} matchs NHL, {n} avec cotes joueurs, {stats['winamax']['cotes']} cotes")

    st, final, data = http_get(f"{BETCLIC}/hockey-sur-glace-s13")
    html = data.decode("utf-8", "ignore")
    base = re.match(r"https?://[^/]+", final or BETCLIC).group(0)        # m.betclic.fr sur téléphone
    comp = re.search(r'href="(/[a-z0-9_\-]+/nhl-c\d+)/', html, re.I)
    time.sleep(pause)                    # page NHL : tous les matchs à venir, pas seulement ceux du jour
    st2, _, data2 = http_get(base + (comp.group(1) if comp else BC_NHL))
    html2 = data2.decode("utf-8", "ignore") if st2 == 200 else ""
    paths = betclic_nhl_upcoming(html2 + html, now, horizon_h)
    if st != 200 and st2 != 200:
        errors.append(f"betclic liste : {st}/{st2}")
    n = 0
    for path in paths[:MAX_MATCHES]:
        time.sleep(pause)
        st, _, data = http_get(base + path)
        r = parse_betclic_match(betclic_state(data.decode("utf-8", "ignore"))) if st == 200 else []
        if st != 200:
            errors.append(f"betclic match {path[-20:]} : {st}")
        n += bool(r)
        rows += r
    stats["betclic"] = {"matchs": len(paths), "avec_joueurs": n, "cotes": sum(x["book"] == "Betclic" for x in rows)}
    print(f"  Betclic : {len(paths)} matchs NHL, {n} avec cotes joueurs, {stats['betclic']['cotes']} cotes")

    payload = {"version": 1, "at": _iso(now), "rows": rows, "stats": stats, "errors": errors}
    code = put_file("cotes_fr.json.gz", gzip.compress(json.dumps(payload, ensure_ascii=False).encode()),
                    f"Cotes téléphone {_iso(now)} : {len(rows)} cotes")
    print("Envoyé sur GitHub." if code in (200, 201) else "Échec de l'envoi sur GitHub.")
    if code in (200, 201):
        relance_site()
    for e in errors:
        print("  !", e)


def relance_site() -> None:
    """Demande à GitHub de mettre le site à jour tout de suite (les mises à jour programmées
    de GitHub sont souvent retardées ou sautées). Même jeton : droit « Contents : Read and write »."""
    st, out = gh("POST", f"/repos/{REPO}/dispatches", {"event_type": "cotes-telephone"})
    print("Mise à jour du site demandée." if st == 204
          else f"  ! mise à jour du site non demandée ({st}) : {out.get('message')}")


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
        last_final[0] = final
        time.sleep(1.5)
        return data
    last_final = [""]

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
    base = re.match(r"https?://[^/]+", last_final[0] or BETCLIC).group(0)   # m.betclic.fr sur téléphone
    comp = re.search(r'href="(/[a-z0-9_\-]+/nhl-c\d+)/', page, re.I)
    nhl = grab("betclic_nhl", base + (comp.group(1) if comp else BC_NHL))
    nhl = nhl.decode("utf-8", "ignore")
    now = datetime.now(timezone.utc)
    avant = betclic_nhl_upcoming(nhl + page, now, 48)                                 # pas commencés
    links = list(dict.fromkeys(re.findall(r'href="(/[a-z0-9_\-]+/nhl-c\d+/[a-z0-9\-]+-m\d+)"', nhl + page, re.I)))
    report["betclic_links"] = links[:30]
    report["betclic_avant_match"] = avant[:30]
    for k, path in enumerate(avant[:max_matches]):
        grab(f"betclic_avant_match_{k}", base + path)

    print("Envoi sur GitHub (branche cotes-telephone) :")
    files["sonde/rapport.json"] = json.dumps(report, indent=1, ensure_ascii=False).encode()
    ok = sum(put_file(p, c, f"Sonde téléphone {stamp} : {p}") in (200, 201) for p, c in files.items())
    print(f"  {ok}/{len(files)} fichiers déposés. Merci ! Vous pouvez prévenir Claude.")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "sonde":
        sonde()
    elif arg in ("", "collecte"):
        collecte()
    else:
        print(__doc__)
