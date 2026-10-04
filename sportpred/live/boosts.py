"""Cotes boostées des opérateurs français : lecture, probabilité juste, verdict.

Une cote boostée n'a de valeur que si la cote proposée dépasse la cote juste. On traduit
le libellé (« Le PSG gagne et Dembélé marque », « Les deux équipes marquent », « Plus de 2,5
buts »…) en « jambes » élémentaires, puis :
- jambe unique cotée par Pinnacle (vainqueur, total, les deux marquent, combinés publiés par
  Pinnacle) : probabilité sans marge de Pinnacle ;
- football, plusieurs jambes ou joueur : grille des scores calée sur Pinnacle
  (`sportpred.models.score_grid`) et parts des buteurs (`football_scorers`, si titulaire) ;
- sinon : « non évaluable » (le libellé est affiché avec le gain de cote annoncé).

Sources : Unibet.fr (page publique /cotes-boostees, lue par GitHub) ; Winamax et Betclic
(lus par le téléphone, voir telephone/collecte_fr.py).
"""
from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

from ..models import score_grid as G
from . import unibet
from .matching import norm, sim

MIN_EV_PIN = 0.03          # référence Pinnacle directe
MIN_EV_MODEL = 0.08        # grille / modèle buteurs : marge d'erreur plus large
_ODDS_TXT = re.compile(r"\(\s*(?P<o>\d+[,.]\d+)\s*->\s*(?P<b>\d+[,.]\d+)\s*(?:/\s*mise max\s*(?P<m>\d+)\s*€?)?\s*\)", re.I)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = s.replace("’", "'")
    return re.sub(r"\s+", " ", s).strip()


def _num(x) -> float | None:
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ lecture Unibet
def unibet_boosts() -> pd.DataFrame:
    html = unibet._get(unibet.BASE + "/cotes-boostees")
    st = unibet._state(html) if html else None
    rows = []
    for ev in ((st or {}).get("BoostedBets") or {}).get("events") or []:
        sport = ((ev.get("path") or {}).get("sport") or {}).get("label")
        for g in ev.get("groupedMarkets") or []:
            for mk in g.get("markets") or []:
                if mk.get("suspended"):
                    continue
                txt = str(mk.get("description", ""))
                yes = [o for o in mk.get("outcomes") or [] if not o.get("hidden") and o.get("description") != "Non"]
                if not yes:
                    continue
                m = _ODDS_TXT.search(txt)
                rows.append({"book": "Unibet", "sport": sport, "event": ev.get("descDisplay") or ev.get("description"),
                             "start": pd.Timestamp(ev.get("parsedStart")) if ev.get("parsedStart") else pd.NaT,
                             "text": clean_text(txt), "raw": txt, "odds": _num(yes[0].get("price")),
                             "orig_odds": _num(m.group("o")) if m else None,
                             "max_stake": _num(m.group("m")) if m and m.group("m") else None})
    return pd.DataFrame(rows)


def clean_text(txt: str) -> str:
    t = _ODDS_TXT.sub("", str(txt))
    t = re.sub(r"^\s*(?:CB|Boost(?:\s+[A-Z]{2,4})?(?:\s+[A-Za-zÀ-ÿ'.]+)*)\s*-\s*", "", t)    # « CB - », « Boost DAL Mavericks - »
    t = re.sub(r"\s*-\s*\d+\s*Mins?\s*$", "", t, flags=re.I)
    return t.strip(" ?.")


# ------------------------------------------------------------------ libellé -> jambes
_LEGS = [
    ("btts", re.compile(r"^(?:les )?(?:deux|2) equipes (?:marquent|ont marque)(?: dans le match)?$")),
    ("draw", re.compile(r"^(?:match )?nul$")),
    ("over", re.compile(r"^(?:plus de|\+ ?de|\+) ?(?P<n>\d+(?:[,.]5)?) (?:buts?|points?|jeux|sets?|essais?)(?: dans le match)?$")),
    ("under", re.compile(r"^(?:moins de|\- ?de) ?(?P<n>\d+(?:[,.]5)?) (?:buts?|points?|jeux|sets?|essais?)(?: dans le match)?$")),
    ("atleast", re.compile(r"^au moins (?P<k>\d+) buts?(?: dans le match)?$")),
    ("win_nil", re.compile(r"^(?P<who>.+?) (?:gagne|s'impose|l'emporte) sans encaisser de buts?$")),
    ("margin", re.compile(r"^(?P<who>.+?) (?:gagne|s'impose|l'emporte) (?:avec|par) (?:au moins )?(?P<k>\d+) buts? d'ecart(?: ou (?:plus|\+))?$")),
    ("win", re.compile(r"^(?:victoire (?:de |du |des |d')(?P<who2>.+)|(?P<who>.+?) (?:gagne|s'impose|l'emporte|bat .+)(?: le match| la rencontre)?)$")),
    ("not_lose", re.compile(r"^(?P<who>.+?) ne perd pas$")),
    ("goals_k", re.compile(r"^(?P<who>.+?) marque (?:au moins )?(?P<k>\d+) buts?(?: ou (?:plus|\+))?(?: dans le match)?$")),
    ("double", re.compile(r"^(?P<who>.+?) (?:marque un|realise un|signe un) double$")),
    ("scores", re.compile(r"^(?P<who>.+?) (?:marque|buteur|est buteur|trouve le chemin des filets)(?: un but| au moins (?:un|1) but| 1 but ou (?:plus|\+))?(?: dans le match| a tout moment)?$")),
]


def parse_legs(text: str) -> list[dict] | None:
    """Jambes du libellé ; None si une partie n'est pas reconnue."""
    t = _fold(text)
    t = re.sub(r"^(?:le |la |l'|les )(?=[a-z])", "", t)
    parts = [p.strip(" .?!") for p in re.split(r"\s+(?:et|&)\s+", t) if p.strip(" .?!")]
    legs = []
    for p in parts:
        p = re.sub(r"^(?:le |la |l'|les )(?=[a-z])", "", p)
        for kind, rx in _LEGS:
            m = rx.match(p)
            if not m:
                continue
            d = {k: v for k, v in m.groupdict().items() if v is not None}
            leg = {"kind": kind, "who": (d.get("who") or d.get("who2") or "").strip()}
            if "n" in d:
                leg["line"] = float(d["n"].replace(",", "."))
            if "k" in d:
                leg["k"] = int(d["k"])
            legs.append(leg)
            break
        else:
            return None
    return legs or None


# ------------------------------------------------------------------ probabilité juste (football)
NICK = {"om": "marseille", "ol": "lyon", "losc": "lille", "asse": "saint etienne", "ogcn": "nice", "asm": "monaco",
        "barca": "barcelona", "real": "real madrid", "atletico": "atletico madrid", "city": "manchester city",
        "united": "manchester united", "man u": "manchester united", "juve": "juventus", "bayern": "bayern munchen",
        "bvb": "borussia dortmund", "gunners": "arsenal", "reds": "liverpool", "blues": "chelsea", "spurs": "tottenham",
        "parisiens": "psg", "paris": "psg", "marseillais": "marseille", "lyonnais": "lyon", "lillois": "lille",
        "lensois": "lens", "rennais": "rennes", "nicois": "nice", "monegasques": "monaco"}


def _resolve(who: str, home: str, away: str, players: pd.DataFrame) -> tuple[str, object] | None:
    """('team', 'h'|'a') ou ('player', ligne du joueur) ou None."""
    who = re.sub(r"^(?:le |la |l'|les )", "", _fold(who)).strip()
    who = NICK.get(who, who)
    w = norm(who)
    sh, sa = sim(who, home), sim(who, away)
    if max(sh, sa) >= 0.8:
        return ("team", "h" if sh >= sa else "a")
    if players is not None and not players.empty:
        toks = set(w.split())
        best, score = None, 0.0
        for r in players.itertuples():
            pk = str(r.k)
            s = 1.0 if pk == w else (0.9 if toks and toks <= set(pk.split()) else sim(who, r.player))
            if s > score:
                best, score = r, s
        if score >= 0.85:
            return ("player", best)
    return None


def price_football(legs: list[dict], ev: pd.DataFrame, players: pd.DataFrame | None, og: float = 0.028) -> dict | None:
    """Probabilité juste d'un combiné de jambes sur un match de football (lignes Pinnacle `ev`)."""
    home, away = ev["home"].iloc[0], ev["away"].iloc[0]
    ml = ev[ev["market"] == "moneyline"].set_index("selection")["fair_prob"]
    if not {home, away, "Nul"} <= set(ml.index):
        return None
    tot = ev[(ev["market"] == "total") & (ev["selection"] == "Plus")]
    g, _ = G.fit_grid(float(ml[home]), float(ml["Nul"]), total_lines=dict(zip(tot["line"], tot["fair_prob"])))
    conds, plegs, method, spec = [], [], "grille Pinnacle", []
    for lg in legs:
        k = lg["kind"]
        spec.append({"kind": k, **{x: lg[x] for x in ("line", "k") if x in lg}})
        if k == "btts":
            conds.append(lambda h, a: (h > 0) & (a > 0))
        elif k == "draw":
            conds.append(lambda h, a: h == a)
        elif k in ("over", "under", "atleast"):
            n = lg.get("line", lg.get("k", 0) - 0.5)
            conds.append((lambda n: (lambda h, a: h + a > n))(n) if k != "under" else (lambda n: (lambda h, a: h + a < n))(n))
        else:
            r = _resolve(lg["who"], home, away, players)
            if r is None:
                return None
            typ, x = r
            if typ == "team":
                side = x
                spec[-1]["side"] = side
                if k == "win":
                    conds.append(lambda h, a, s=side: h > a if s == "h" else a > h)
                elif k == "not_lose":
                    conds.append(lambda h, a, s=side: h >= a if s == "h" else a >= h)
                elif k == "win_nil":
                    conds.append(lambda h, a, s=side: (h > a) & (a == 0) if s == "h" else (a > h) & (h == 0))
                elif k == "margin":
                    conds.append(lambda h, a, s=side, m=lg["k"]: h - a >= m if s == "h" else a - h >= m)
                elif k in ("goals_k", "scores"):
                    kk = lg.get("k", 1)
                    conds.append(lambda h, a, s=side, kk=kk: h >= kk if s == "h" else a >= kk)
                else:
                    return None
            else:
                if k not in ("scores", "goals_k", "double"):
                    return None
                side = "h" if sim(x.team, home) >= sim(x.team, away) else "a"
                plegs.append((side, float(x.share), 2 if k == "double" else lg.get("k", 1)))
                spec[-1].update(side=side, player=x.player, player_id=int(x.player_id) if hasattr(x, "player_id") else None,
                                k=2 if k == "double" else lg.get("k", 1))
                method = "grille Pinnacle + modèle buteurs (si titulaire)"

    def cond(h, a):
        m = np.ones_like(h, dtype=bool)
        for c in conds:
            m &= c(h, a)
        return m
    p = G.players_prob(g, plegs, og=og, cond=cond) if plegs else G.ev_prob(g, cond)
    return {"fair_prob": p, "method": method, "legs": spec}


def pinnacle_direct(legs: list[dict], ev: pd.DataFrame) -> float | None:
    """Une seule jambe que Pinnacle cote directement (vainqueur, nul, total, les deux marquent)."""
    if len(legs) != 1:
        return None
    lg, home, away = legs[0], ev["home"].iloc[0], ev["away"].iloc[0]
    ml = ev[ev["market"] == "moneyline"].set_index("selection")["fair_prob"]
    if lg["kind"] == "win" and lg["who"]:
        r = _resolve(lg["who"], home, away, None)
        if r is not None:
            t = home if r[1] == "h" else away
            return float(ml[t]) if t in ml else None
    if lg["kind"] == "draw" and "Nul" in ml:
        return float(ml["Nul"])
    if lg["kind"] in ("over", "under"):
        r = ev[(ev["market"] == "total") & (ev["line"] == lg["line"]) &
               (ev["selection"] == ("Plus" if lg["kind"] == "over" else "Moins"))]
        return float(r["fair_prob"].iloc[0]) if len(r) else None
    if lg["kind"] == "btts":
        r = ev[(ev["market"] == "Team Props: Both Teams To Score?") & (ev["selection"] == "Yes")]
        return float(r["fair_prob"].iloc[0]) if len(r) else None
    return None


def pinnacle_combo(legs: list[dict], ev: pd.DataFrame) -> float | None:
    """Combinés que Pinnacle publie lui-même (marchés « Team Props ») : victoire + les deux
    marquent, victoire / nul + total, les deux marquent + total, écart, sans encaisser,
    nombre de buts d'une équipe."""
    home, away = ev["home"].iloc[0], ev["away"].iloc[0]

    def get(market, sel):
        r = ev[(ev["market"] == market) & (ev["selection"] == sel)]
        return float(r["fair_prob"].iloc[0]) if len(r) else None

    def team(lg):
        r = _resolve(lg["who"], home, away, None) if lg.get("who") else None
        return (home if r[1] == "h" else away) if r and r[0] == "team" else None

    kinds = sorted(lg["kind"] for lg in legs)
    by = {lg["kind"]: lg for lg in legs}
    if kinds == ["btts", "win"] and team(by["win"]):
        return get("Team Props: Both Teams To Score/Winner", f"Yes & {team(by['win'])}")
    if kinds == ["over", "win"] and by["over"].get("line") == 2.5 and team(by["win"]):
        return get("Team Props: Winner/Total Goals", f"{team(by['win'])} & Over 2.5")
    if kinds == ["under", "win"] and by["under"].get("line") == 2.5 and team(by["win"]):
        return get("Team Props: Winner/Total Goals", f"{team(by['win'])} & Under 2.5")
    if kinds == ["draw", "over"] and by["over"].get("line") == 2.5:
        return get("Team Props: Winner/Total Goals", "Draw & Over 2.5")
    if kinds == ["btts", "over"] and by["over"].get("line") == 2.5:
        return get("Team Props: Both Teams To Score/Total Goals", "Yes & Over 2.5")
    if len(legs) != 1:
        return None
    lg = legs[0]
    t = team(lg)
    if lg["kind"] == "win_nil" and t:
        return get(f"Team Props: {t} To Win to Nil?", "Yes")
    if lg["kind"] == "margin" and t:
        k = lg["k"]
        sels = [f"{t} By {j}" for j in range(k, 4)] + [f"{t} By 4+"]
        ps = [get("Team Props: Winning Margin", x) for x in sels]
        return float(sum(ps)) if k <= 4 and all(x is not None for x in ps) else None
    if lg["kind"] in ("goals_k", "scores") and t:
        k = lg.get("k", 1)
        r = ev[ev["market"] == f"Team Props: {t} Goals"]
        if len(r):
            ex = r.assign(n=pd.to_numeric(r["selection"].str.extract(r"(\d+)")[0], errors="coerce"))
            low = ex[ex["n"] < k]["fair_prob"].sum()
            return float(1 - low) if (ex["n"] < k).sum() == k else None
    return None


def find_event(b: dict, pin: pd.DataFrame, max_hours: float = 4.0) -> pd.DataFrame:
    """Lignes Pinnacle du match visé par le boost (heure ± `max_hours`, noms d'équipes)."""
    if pin.empty:
        return pin
    t = pd.Timestamp(b.get("start")) if b.get("start") is not None else pd.NaT
    cand = pin
    if pd.notna(t):
        t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
        cand = pin[(pd.to_datetime(pin["start"], utc=True) - t).abs() <= pd.Timedelta(hours=max_hours)]
    if cand.empty:
        return cand
    label = " ".join(str(b.get(k) or "") for k in ("event", "text"))
    best, score = None, 0.0
    for ev, e in cand.groupby("event"):
        s = max(sim(e["home"].iloc[0], w) for w in _words(label)) + max(sim(e["away"].iloc[0], w) for w in _words(label))
        if s > score:
            best, score = ev, s
    return cand[cand["event"] == best] if score >= 1.5 else cand.iloc[0:0]


def _words(label: str) -> list[str]:
    """Morceaux candidats (1 à 3 mots consécutifs) pour retrouver un nom d'équipe dans un texte."""
    w = re.findall(r"[A-Za-zÀ-ÿ0-9'.]+", label)
    return [" ".join(w[i:i + n]) for n in (1, 2, 3) for i in range(len(w) - n + 1)] or [label]


def evaluate(boosts: pd.DataFrame, pin: pd.DataFrame, foot_pred: pd.DataFrame | None = None) -> pd.DataFrame:
    """Ajoute fair_prob, fair_odds, ev, method, verdict à chaque boost."""
    out = []
    for b in boosts.to_dict("records"):
        res = {"fair_prob": None, "method": None, "reason": None}
        legs = parse_legs(b["text"])
        ev = find_event(b, pin)
        if legs is None:
            res["reason"] = "libellé non reconnu"
        elif ev.empty:
            res["reason"] = "match introuvable chez Pinnacle"
        else:
            direct = pinnacle_direct(legs, ev)
            if direct is None and str(ev["sport"].iloc[0]) == "football":
                direct = pinnacle_combo(legs, ev)
            spec = None
            if str(ev["sport"].iloc[0]) == "football":
                pl = foot_pred[foot_pred["event"] == ev["event"].iloc[0]] if foot_pred is not None and not foot_pred.empty else None
                rr = price_football(legs, ev, pl)
                spec = rr["legs"] if rr else None
            if direct is not None:
                res.update(fair_prob=direct, method="Pinnacle", legs=spec)
            elif str(ev["sport"].iloc[0]) == "football":
                pl = foot_pred[foot_pred["event"] == ev["event"].iloc[0]] if foot_pred is not None and not foot_pred.empty else None
                r = price_football(legs, ev, pl)
                if r:
                    res.update(r)
                else:
                    res["reason"] = "joueur ou équipe non reconnu"
            else:
                res["reason"] = "combiné hors football : pas encore évalué"
        if res["fair_prob"]:
            res["fair_odds"] = 1 / res["fair_prob"]
            res["ev"] = res["fair_prob"] * b["odds"] - 1
            thr = MIN_EV_PIN if res["method"] == "Pinnacle" else MIN_EV_MODEL
            res["verdict"] = "à jouer" if res["ev"] >= thr else ("limite" if res["ev"] >= 0 else "à éviter")
            res["pin_event"] = ev["event"].iloc[0]
            res["pin_league"], res["pin_sport"] = ev["league"].iloc[0], ev["sport"].iloc[0]
        out.append({**b, **res})
    return pd.DataFrame(out)


# ------------------------------------------------------------------ bloc du site
def block(pin: pd.DataFrame, foot_pred: pd.DataFrame | None = None,
          phone: pd.DataFrame | None = None) -> tuple[dict, pd.DataFrame]:
    """(bloc « Cotes boostées » de today.json, boosts au-dessus du seuil au format des paris)."""
    frames = []
    try:
        frames.append(unibet_boosts())
    except Exception as e:  # noqa: BLE001 — Unibet peut changer de format
        print("cotes boostées Unibet illisibles :", e)
    if phone is not None and not phone.empty:
        frames.append(phone)
    frames = [f for f in frames if f is not None and not f.empty]
    if not frames:
        return {"rows": [], "books": []}, pd.DataFrame()
    b = pd.concat(frames, ignore_index=True)
    b = b[b["odds"].notna()].drop_duplicates(["book", "text", "odds"])
    ev = evaluate(b, pin, foot_pred)
    rows = ev.copy()
    rows["start"] = pd.to_datetime(rows["start"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    for c in ("fair_prob", "fair_odds", "ev"):
        if c not in rows:
            rows[c] = np.nan
    rows = rows.sort_values(["ev"], ascending=False, na_position="last")
    cols = ["book", "sport", "event", "start", "text", "odds", "orig_odds", "max_stake", "fair_odds", "ev", "method",
            "verdict", "reason"]
    for c in cols:
        if c not in rows:
            rows[c] = None
    out = rows[cols].round({"fair_odds": 2, "ev": 4}).replace({np.nan: None}).to_dict("records")
    vb = ev[ev.get("verdict", pd.Series(dtype=str)) == "à jouer"].copy() if "verdict" in ev else pd.DataFrame()
    if not vb.empty:
        vb = pd.DataFrame({
            "sport": vb["pin_sport"], "league": vb["pin_league"], "start": vb["start"],
            "event": vb["pin_event"], "market": "Cote boostée", "selection": vb["text"], "book": vb["book"],
            "odds": vb["odds"], "fair_prob": vb["fair_prob"], "fair_odds": vb["fair_odds"], "ev": vb["ev"],
            "pin_margin": np.nan, "market_key": None, "max_stake": vb["max_stake"], "legs": vb.get("legs"),
            "source": "Cote boostée " + vb["book"] + " (" + vb["method"] + ")"})
    return {"rows": out, "books": sorted(b["book"].unique().tolist()),
            "n_eval": int(ev["fair_prob"].notna().sum()) if "fair_prob" in ev else 0}, vb



# ------------------------------------------------------------------ règlement
def _leg_ok(leg: dict, h: int, a: int, goals: dict) -> bool | None:
    """Jambe gagnée ? (score final h-a, buts des joueurs par player_id ; None = joueur absent)."""
    k, side = leg["kind"], leg.get("side")
    mine, other = (h, a) if side == "h" else (a, h)
    if k == "btts":
        return h > 0 and a > 0
    if k == "draw":
        return h == a
    if k in ("over", "atleast"):
        return h + a > leg.get("line", leg.get("k", 0) - 0.5)
    if k == "under":
        return h + a < leg["line"]
    if leg.get("player_id") is not None:
        g = goals.get(int(leg["player_id"]))
        return None if g is None else g >= leg.get("k", 1)
    if k == "win":
        return mine > other
    if k == "not_lose":
        return mine >= other
    if k == "win_nil":
        return mine > other and other == 0
    if k == "margin":
        return mine - other >= leg["k"]
    if k in ("goals_k", "scores"):
        return mine >= leg.get("k", 1)
    return None


def settle(hist: list[dict], now: pd.Timestamp, players: pd.DataFrame | None = None) -> list[dict]:
    """Règle les cotes boostées de football suivies (champ « legs ») : score ESPN, buteurs Understat."""
    from . import results as R
    from .matching import match_events
    for x in hist:
        if not x.get("legs") or x.get("result"):
            continue
        start = pd.Timestamp(x["start"])
        start = start.tz_localize("UTC") if start.tzinfo is None else start
        if now < start + pd.Timedelta(hours=3):
            continue
        path = R.league_path(x.get("league", ""))
        parts = str(x["event"]).split(" - ")
        rows = []
        if path and len(parts) == 2:
            for dd in (-1, 0, 1):
                rows += R.scoreboard(path, (start + pd.Timedelta(days=dd)).normalize())
        res = pd.DataFrame(rows).drop_duplicates("event_id") if rows else pd.DataFrame()
        m = match_events(pd.DataFrame({"event_id": ["p"], "start": [start], "home": [parts[0]], "away": [parts[-1]]}),
                         res, max_hours=6) if not res.empty else pd.DataFrame()
        if m.empty:
            if now > start + pd.Timedelta(days=3):
                x["result"] = "non réglé (résultat introuvable)"
            continue
        r = res[res["event_id"] == m.iloc[0]["right_id"]].iloc[0]
        if not r["completed"]:
            continue
        h, a = int(r["home_score"]), int(r["away_score"])
        if bool(m.iloc[0]["swapped"]):
            h, a = a, h
        goals = {}
        if players is not None and not players.empty:
            d = pd.to_datetime(players["date"]).dt.tz_localize("UTC")
            day = players[(d - start).abs() <= pd.Timedelta(hours=48)]
            goals = dict(zip(day["player_id"].astype(int), day["goals"].astype(int)))
        oks = [_leg_ok(lg, h, a, goals) for lg in x["legs"]]
        if any(o is None for o in oks):
            if now > start + pd.Timedelta(days=3):
                x["result"], x["profit_units"], x["status"] = "remboursé (joueur absent)", 0.0, "réglé"
            continue
        won = all(oks)
        x["result"] = "gagné" if won else "perdu"
        x["score"] = f"{h}-{a}"
        x["profit_units"] = round(x["odds"] - 1, 3) if won else -1.0
        x["status"] = "réglé"
    return hist
