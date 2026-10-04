"""Buteurs football en direct : cote juste « si titulaire » pour les 5 grands championnats.

- Buts attendus des équipes : grille de scores calée sur Pinnacle (1N2 + plus/moins), voir
  `sportpred.models.score_grid` ;
- répartition entre les joueurs : modèle `sportpred.models.football_scorers` (Understat) ;
- composition probable : titularisations des 8 derniers matchs de l'équipe (les plus récents
  comptent davantage) ; cote donnée **si le joueur est titulaire** (composition officielle
  ~1 h avant le match) ; un joueur absent rend le pari remboursé chez les opérateurs.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from ..data import understat
from ..models import football_scorers as M
from ..models import score_grid as G
from .matching import norm, sim

ROOT = Path(__file__).resolve().parents[2]
MODEL_FILE = ROOT / "data" / "processed" / "football_scorer_model.json"
LEAGUE_MAP = {"England - Premier League": "EPL", "Spain - La Liga": "La_liga", "Germany - Bundesliga": "Bundesliga",
              "Italy - Serie A": "Serie_A", "France - Ligue 1": "Ligue_1"}
MODEL_MIN_EV = 0.12            # marge exigée face à la cote du modèle (Pinnacle ne cote pas les buteurs de football)
N_RECENT = 8                   # matchs récents de l'équipe pour la composition probable
DECAY = 0.7                    # poids du match j (0 = le plus récent) : DECAY ** j
MIN_P_START = 0.3


def season_of(now: pd.Timestamp) -> int:
    return now.year if now.month >= 7 else now.year - 1


def load_model(path: Path | None = None) -> tuple[M.Params, float]:
    d = json.loads((path or MODEL_FILE).read_text())
    p = M.Params(**d["params"])
    p.beta = np.array(d["beta"], float)
    p.priors = d["priors"]
    p.og_share = d["og_share"]
    return p, float(d["bench"])


def load_hist(now: pd.Timestamp, raw: Path = ROOT / "data" / "raw") -> pd.DataFrame:
    s = season_of(now)
    return understat.load(raw, seasons=[s - 1, s], refresh_current=True)


def upcoming(now: pd.Timestamp, horizon_hours: float = 48) -> pd.DataFrame:
    s = season_of(now)
    fx = pd.concat([understat.fixtures(understat.league_season(lg, s), lg, s) for lg in understat.LEAGUES],
                   ignore_index=True)
    fx["date"] = pd.to_datetime(fx["date"]).dt.tz_localize("UTC")
    return fx[(~fx["played"]) & (fx["date"] > now) & (fx["date"] < now + pd.Timedelta(hours=horizon_hours))]


def link_pinnacle(pin: pd.DataFrame, fx: pd.DataFrame, max_hours: float = 60.0) -> pd.DataFrame:
    """Matchs Pinnacle (5 grands championnats) ↔ calendrier Understat, avec λ et grille.
    Understat met des heures provisoires (ex. tous les matchs d'une journée à 13 h) : appariement
    sur les deux noms d'équipe, à ± 2,5 jours."""
    if pin.empty or fx.empty or "league" not in pin:
        return pd.DataFrame()
    rows = []
    soc = pin[pin["league"].isin(LEAGUE_MAP)]
    for ev, e in soc.groupby("event"):
        lg = LEAGUE_MAP[e["league"].iloc[0]]
        home, away, t = e["home"].iloc[0], e["away"].iloc[0], pd.Timestamp(e["start"].iloc[0])
        t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
        c = fx[(fx["league"] == lg) & ((fx["date"] - t).abs() <= pd.Timedelta(hours=max_hours))]
        if c.empty:
            continue
        sc = np.array([sim(home, h) + sim(away, a) for h, a in zip(c["home"], c["away"])])
        sc = sc - (c["date"] - t).abs().dt.total_seconds().to_numpy() / 86400 / 100    # départage : date proche
        if sc.max() < 1.5:
            continue
        f = c.iloc[int(sc.argmax())]
        ml = e[e["market"] == "moneyline"].set_index("selection")["fair_prob"]
        if not {home, away, "Nul"} <= set(ml.index):
            continue
        tot = e[(e["market"] == "total") & (e["selection"] == "Plus")]
        _, info = G.fit_grid(float(ml[home]), float(ml["Nul"]), total_lines=dict(zip(tot["line"], tot["fair_prob"])))
        rows.append({"event": ev, "start": t, "league": lg, "match_id": int(f["match_id"]),
                     "home_id": int(f["home_id"]), "away_id": int(f["away_id"]), "home": f["home"], "away": f["away"],
                     "lam_h": info["lam_h"], "lam_a": info["lam_a"], "rho": info["rho"]})
    return pd.DataFrame(rows)


ESPN_LEAGUE = {"EPL": "England - Premier League", "La_liga": "Spain - La Liga", "Bundesliga": "Germany - Bundesliga",
               "Serie_A": "Italy - Serie A", "Ligue_1": "France - Ligue 1"}


def espn_lineups(league: str, start: pd.Timestamp, home: str, away: str) -> dict | None:
    """Compositions officielles ESPN (publiées ~1 h avant le match) : {'home': [noms], 'away': [noms]}
    des titulaires, ou None si pas encore publiées / match introuvable."""
    import requests

    from . import results as R
    from .matching import match_events
    path = R.league_path(ESPN_LEAGUE.get(league, league))
    if not path:
        return None
    rows = []
    for dd in (-1, 0):
        rows += R.scoreboard(path, (start + pd.Timedelta(days=dd)).normalize())
    res = pd.DataFrame(rows).drop_duplicates("event_id") if rows else pd.DataFrame()
    if res.empty:
        return None
    m = match_events(pd.DataFrame({"event_id": ["p"], "start": [start], "home": [home], "away": [away]}), res, max_hours=3)
    if m.empty:
        return None
    try:
        s = requests.get(f"{R.ESPN}/{path}/summary", params={"event": m.iloc[0]["right_id"]}, timeout=20).json()
    except (requests.RequestException, ValueError):
        return None
    out = {}
    for t in s.get("rosters") or []:
        st = [(x.get("athlete") or {}).get("displayName") for x in t.get("roster") or [] if x.get("starter")]
        side = t.get("homeAway")
        if bool(m.iloc[0]["swapped"]):
            side = {"home": "away", "away": "home"}.get(side, side)
        if len(st) >= 11 and side in ("home", "away"):
            out[side] = [x for x in st if x]
    return out if len(out) == 2 else None


def _match_names(names: list[str], cands: pd.DataFrame) -> set[int]:
    """player_id des candidats correspondant aux noms ESPN (nom exact, sinon nom de famille unique)."""
    ids = set()
    k = cands["player"].map(norm)
    for n in names:
        nn = norm(n)
        hit = cands[k == nn]
        if hit.empty:
            last = nn.split()[-1] if nn else ""
            hit = cands[k.str.split().str[-1] == last] if last else hit
        if len(hit) == 1:
            ids.add(int(hit["player_id"].iloc[0]))
    return ids


def probable_players(hist: pd.DataFrame, team_id: int) -> pd.DataFrame:
    """Joueurs de l'équipe avec P(titulaire) d'après les N_RECENT derniers matchs."""
    h = hist[hist["team_id"] == team_id]
    games = (h.drop_duplicates("match_id").sort_values("date", ascending=False)["match_id"].head(N_RECENT).tolist())
    if not games:
        return pd.DataFrame()
    w = pd.Series(DECAY ** np.arange(len(games)), index=games)
    r = h[h["match_id"].isin(games)]
    st = r[r["starter"]].groupby("player_id")["match_id"].apply(lambda s: w.reindex(s).sum())
    ap = r.groupby("player_id")["match_id"].apply(lambda s: w.reindex(s).sum())
    out = pd.DataFrame({"p_start": (st / w.sum()).reindex(ap.index).fillna(0.0), "p_play": ap / w.sum()})
    # transferts : dernier club connu du joueur (tous clubs confondus)
    last = hist.sort_values("date").drop_duplicates("player_id", keep="last").set_index("player_id")["team_id"]
    out = out[last.reindex(out.index).to_numpy() == team_id]
    out["n_starts"] = r[r["starter"]].groupby("player_id").size().reindex(out.index).fillna(0).astype(int)
    out["n_games"] = len(games)
    return out.reset_index()


def predict(pin: pd.DataFrame, now: pd.Timestamp, hist: pd.DataFrame | None = None,
            fx: pd.DataFrame | None = None, lineups=None, lineup_hours: float = 2.5) -> pd.DataFrame:
    """Une ligne par joueur probable des matchs à venir couverts par Pinnacle.
    Compositions officielles (ESPN) lues pour les matchs des `lineup_hours` prochaines heures :
    titulaire annoncé -> P(titulaire) = 1, sinon 0 ; `lineups` = fonction de remplacement (tests)."""
    lineups = espn_lineups if lineups is None else lineups
    p, bench = load_model()
    hist = load_hist(now) if hist is None else hist
    if fx is None:                                   # calendrier sur la même fenêtre que les cotes Pinnacle
        last = pd.to_datetime(pin["start"], utc=True).max()
        fx = upcoming(now, max(48.0, (last - now).total_seconds() / 3600 + 6))
    games = link_pinnacle(pin, fx)
    if games.empty or hist.empty:
        return pd.DataFrame()
    fut, meta = [], []
    names = hist.drop_duplicates("player_id", keep="last").set_index("player_id")["player"]
    for g in games.itertuples():
        official = None
        if pd.Timestamp(g.start) - now <= pd.Timedelta(hours=lineup_hours):
            try:
                official = lineups(g.league, pd.Timestamp(g.start), g.home, g.away)
            except Exception as e:  # noqa: BLE001 — ESPN indisponible : composition probable
                print("composition ESPN illisible :", e)
        for side, tid, lam in (("home", g.home_id, g.lam_h), ("away", g.away_id, g.lam_a)):
            pl = probable_players(hist, tid)
            if pl.empty:
                continue
            pl["lineup"] = "probable"
            if official:
                ids = _match_names(official[side], pl.assign(player=pl["player_id"].map(names)))
                if len(ids) >= 9:                          # au moins 9 titulaires reconnus sur 11
                    pl["p_start"] = pl["player_id"].isin(ids).astype(float)
                    pl["lineup"] = "officielle"
            team = g.home if side == "home" else g.away
            for r in pl.itertuples():
                fut.append({"match_id": -(g.match_id * 2 + (side == "home")), "date": g.start.tz_localize(None),
                            "league": g.league, "season": season_of(now), "team_id": tid, "team": team,
                            "opp": g.away if side == "home" else g.home, "home": side == "home",
                            "player_id": r.player_id, "player": names.get(r.player_id), "position": None,
                            "time": 0, "is_future": True, "starter": False})
                meta.append({"player_id": r.player_id, "fid": -(g.match_id * 2 + (side == "home")),
                             "p_start": r.p_start, "n_starts": r.n_starts, "n_games": r.n_games,
                             "event": g.event, "start": g.start, "lam": lam, "lineup": r.lineup})
    if not fut:
        return pd.DataFrame()
    base = hist.assign(is_future=False)
    F = pd.DataFrame(fut)
    for c in base.columns:
        if c not in F:
            F[c] = 0
    P = M.prepare(pd.concat([base, F[base.columns]], ignore_index=True), p)
    P = P[P["is_future"]].merge(pd.DataFrame(meta), left_on=["player_id", "match_id"],
                                right_on=["player_id", "fid"], how="inner")
    if P.empty:
        return pd.DataFrame()
    g0 = P["grp_use"].where(P["grp_use"].isin(["D", "M", "A", "F"]), "M")
    mins = P["min_start_exp"].fillna(g0.map({k: p.priors[k]["min_start"] for k in ("D", "M", "A", "F")})).clip(20, 95)
    X = M.features(P, p, minutes=mins)
    X["e"] = np.exp(X[M.FEATURES].to_numpy(float) @ p.beta)
    X["xi"] = X.groupby("fid")["p_start"].rank(ascending=False, method="first") <= 10
    z = X[X["xi"]].groupby("fid")["e"].sum() * (1 + bench)
    X["share"] = X["e"] / X["fid"].map(z)
    X["model_prob"] = 1 - np.exp(-X["lam"] * (1 - p.og_share) * X["share"])
    X = X[X["p_start"] >= MIN_P_START].copy()
    X["k"] = X["player"].map(norm)
    cols = ["event", "start", "league", "team", "player", "player_id", "grp_use", "p_start", "n_starts", "n_games",
            "lam", "share", "model_prob", "np90", "pen_share", "k", "lineup"]
    return X[cols].rename(columns={"grp_use": "pos"}).sort_values(["start", "event", "model_prob"],
                                                                     ascending=[True, True, False])


# ------------------------------------------------------------------ comparaison avec les opérateurs
VB_MIN_P_START = 0.85          # « À jouer maintenant » seulement pour les titulaires quasi sûrs


def _p_line(model_prob, line):
    """P(au moins line + 0,5 buts) avec un nombre de buts de Poisson de moyenne μ = −ln(1 − p)."""
    mu = -np.log1p(-np.clip(np.asarray(model_prob, float), 1e-9, 0.999))
    k = int(np.floor(line)) + 1
    cdf = sum(np.exp(-mu) * mu ** j / math.factorial(j) for j in range(k))
    return 1 - cdf


def compare_books(pred: pd.DataFrame, books: pd.DataFrame, max_hours: float = 3.0) -> pd.DataFrame:
    """Cotes buteurs des opérateurs (colonnes book, ub_event_id, ub_event, start, player, line, odds)
    face à la cote juste « si titulaire » du modèle."""
    if pred is None or pred.empty or books is None or books.empty:
        return pd.DataFrame()
    books = books.assign(ub_event_id=books["ub_event_id"].astype(str))
    out = []
    evs = pred.drop_duplicates("event")[["event", "start"]]
    for (bk, ubid), g in books.groupby(["book", "ub_event_id"]):
        t = pd.Timestamp(g["start"].iloc[0])
        t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
        lab = re.split(r"\s+(?:vs|-|–)\s+", str(g["ub_event"].iloc[0]), maxsplit=1)
        c = evs[(pd.to_datetime(evs["start"], utc=True) - t).abs() <= pd.Timedelta(hours=max_hours)]
        if c.empty or len(lab) != 2:
            continue
        sc = [sim(lab[0], e.split(" - ")[0]) + sim(lab[1], e.split(" - ")[-1]) for e in c["event"]]
        if max(sc) < 1.5:
            continue
        event = c["event"].iloc[int(np.argmax(sc))]
        pe = pred[pred["event"] == event]
        pcols = ["k", "player_id", "team", "p_start", "model_prob"] + (["lineup"] if "lineup" in pe else [])
        x = g.assign(k=g["player"].map(norm)).merge(pe[pcols], on="k", how="inner")
        if x.empty:
            continue
        x["event"], x["start"] = event, t
        x["fair_prob"] = [_p_line(p, ln) for p, ln in zip(x["model_prob"], x["line"])]
        x["ev"] = x["fair_prob"] * x["odds"] - 1
        x["threshold"] = MODEL_MIN_EV
        out.append(x)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def book_value_bets(cmp: pd.DataFrame, max_odds: float = 10.0, min_odds: float = 1.15,
                    max_ev: float = 0.30) -> pd.DataFrame:
    if cmp is None or cmp.empty:
        return pd.DataFrame()
    v = cmp[(cmp["ev"] >= cmp["threshold"]) & (cmp["ev"] <= max_ev) & (cmp["odds"] <= max_odds) &
            (cmp["odds"] >= min_odds) & (cmp["p_start"] >= VB_MIN_P_START)].copy()
    if v.empty:
        return pd.DataFrame()
    cond = np.where(v.get("lineup", pd.Series("probable", index=v.index)) == "officielle", " (titulaire confirmé)", " (si titulaire)")
    lab = np.where(v["line"] == 0.5, v["player"] + " marque",
                   v["player"] + " : " + (v["line"] + 0.5).astype(int).astype(str) + "+ buts") + cond
    return pd.DataFrame({"sport": "football", "league": "Buteurs", "start": v["start"], "event": v["event"],
                         "market": "Buteur (si titulaire)", "selection": lab, "book": v["book"], "odds": v["odds"],
                         "fair_prob": v["fair_prob"], "fair_odds": 1 / v["fair_prob"], "ev": v["ev"], "pin_margin": np.nan,
                         "market_key": None, "player": v["player"], "stat": "Buts", "line": v["line"],
                         "source": "Modèle vs " + v["book"] + " (buteurs football)"})


# ------------------------------------------------------------------ suivi et bloc du site
def archive(pred: pd.DataFrame, arch: Path, now: pd.Timestamp) -> None:
    if pred.empty:
        return
    arch.mkdir(parents=True, exist_ok=True)
    f = arch / f"foot_buteurs_{now.strftime('%Y-%m-%d')}.csv.gz"
    a = pred[["event", "start", "league", "team", "player", "player_id", "p_start", "lam", "share", "model_prob"]].copy()
    a.insert(0, "captured_at", now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    a[["p_start", "lam", "share", "model_prob"]] = a[["p_start", "lam", "share", "model_prob"]].round(4)
    a.to_csv(f, mode="a", header=not f.exists(), index=False, compression="gzip")


def evaluate_archive(arch: Path, hist: pd.DataFrame) -> dict:
    """Bilan des cotes « si titulaire » archivées (dernier relevé avant le match), sur les
    joueurs effectivement titulaires (Understat)."""
    files = sorted(Path(arch).glob("foot_buteurs_*.csv.gz"))
    if not files or hist.empty:
        return {}
    a = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    a["captured_at"] = pd.to_datetime(a["captured_at"], utc=True)
    a["start"] = pd.to_datetime(a["start"], utc=True)
    a = a[a["captured_at"] < a["start"]].sort_values("captured_at").groupby(["event", "player_id"]).tail(1)
    h = hist[hist["starter"]][["player_id", "team", "date", "goals"]].copy()
    h["date"] = pd.to_datetime(h["date"]).dt.tz_localize("UTC")
    m = a.merge(h, on="player_id", how="inner")
    m = m[(m["date"] - m["start"]).abs() <= pd.Timedelta(hours=60)]
    if m.empty:
        return {"n_model": 0}
    y = (m["goals"] > 0).to_numpy(float)
    p = np.clip(m["model_prob"].to_numpy(float), 1e-6, 1 - 1e-6)
    return {"n_model": int(len(m)), "n_games": int(m["event"].nunique()),
            "ll_model": round(float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()), 4),
            "pred_mean": round(float(p.mean()), 4), "obs_mean": round(float(y.mean()), 4)}


def block(pin: pd.DataFrame, out_dir: Path, now: pd.Timestamp,
          books: pd.DataFrame | None = None) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """(bloc « Buteurs football » de today.json, prédictions, paris au-dessus du seuil)."""
    if pin.empty or "league" not in pin or not pin["league"].isin(LEAGUE_MAP).any():
        return {}, pd.DataFrame(), pd.DataFrame()
    hist = load_hist(now)
    pred = predict(pin, now, hist=hist)
    arch = out_dir / "archive"
    archive(pred, arch, now)
    suivi = evaluate_archive(arch, hist)
    if pred.empty:
        return {"rows": [], "suivi": suivi, "model_min_ev": MODEL_MIN_EV}, pred, pd.DataFrame()
    cmp, vb, rejected = pd.DataFrame(), pd.DataFrame(), {}
    if books is not None and not books.empty:
        try:
            from . import nhl_scorers as nhl_mod
            books, rejected = nhl_mod.drop_mixed_markets(books)
            cmp = compare_books(pred, books)
            cmp, odd = nhl_mod.drop_implausible(cmp)
            for bk, n in odd.items():
                rejected[bk] = rejected.get(bk, 0) + n
            vb = book_value_bets(cmp)
        except Exception as e:  # noqa: BLE001
            print("comparaison des cotes buteurs football impossible :", e)
    r = pred.copy()
    r["fair_odds"] = (1 / r["model_prob"]).round(2)
    r["min_odds"] = (r["fair_odds"] * (1 + MODEL_MIN_EV)).round(2)
    r["start"] = pd.to_datetime(r["start"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    r[["p_start", "model_prob"]] = r[["p_start", "model_prob"]].round(3)
    bmap = {}
    if not cmp.empty:
        for x in cmp[cmp["line"] == 0.5].sort_values("odds", ascending=False).itertuples():
            bmap.setdefault((x.event, int(x.player_id)), []).append(
                {"b": x.book, "o": float(x.odds), "hit": bool(x.ev >= x.threshold)})
    r["books"] = [bmap.get((e, int(p)), []) for e, p in zip(r["event"], r["player_id"])]
    if "lineup" not in r:
        r["lineup"] = "probable"
    cols = ["event", "start", "league", "team", "player", "pos", "p_start", "model_prob", "fair_odds", "min_odds", "books",
            "lineup"]
    summary = {"compared": int(len(cmp)), "value": int((cmp["ev"] >= cmp["threshold"]).sum()) if not cmp.empty else 0,
               "by_book": {bk: int(len(g)) for bk, g in cmp.groupby("book")} if not cmp.empty else {},
               "rejected": {k: int(v) for k, v in rejected.items()}}
    return {"rows": r[cols].replace({np.nan: None}).to_dict("records"), "suivi": suivi, "model_min_ev": MODEL_MIN_EV,
            "books": summary, "leagues": sorted(r["league"].map(understat.LEAGUES).unique().tolist())}, pred, vb



def settle(hist: list[dict], now: pd.Timestamp, uhist: pd.DataFrame) -> list[dict]:
    """Règle les paris buteurs football suivis (« si titulaire ») avec Understat :
    titulaire -> gagné / perdu ; entré en cours de jeu -> « non joué (pas titulaire) » (la règle
    du site était de ne jouer qu'une fois la titularisation connue) ; absent -> remboursé."""
    if uhist is None or uhist.empty:
        return hist
    d = pd.to_datetime(uhist["date"]).dt.tz_localize("UTC")
    for h in hist:
        if h.get("sport") != "football" or not h.get("stat") or h.get("result"):
            continue
        start = pd.Timestamp(h["start"])
        start = start.tz_localize("UTC") if start.tzinfo is None else start
        if now < start + pd.Timedelta(hours=4):
            continue
        day = uhist[(d - start).abs() <= pd.Timedelta(hours=48)]
        pid = h.get("player_id")
        rows = day[day["player_id"] == int(pid)] if pid not in (None, "") and pid == pid else day.iloc[0:0]
        if rows.empty:
            rows = day[day["player"].map(norm) == norm(h.get("player", ""))]
        if len(rows) == 1:
            r = rows.iloc[0]
            if not bool(r["starter"]):
                h["result"], h["profit_units"], h["status"] = "non joué (pas titulaire)", 0.0, "réglé"
                continue
            won = float(r["goals"]) > float(h["line"])
            h["result"] = "gagné" if won else "perdu"
            h["score"] = f"{int(r['goals'])} but(s)"
            h["profit_units"] = round(h["odds"] - 1, 3) if won else -1.0
            h["status"] = "réglé"
        elif now > start + pd.Timedelta(days=3):
            h["result"], h["profit_units"], h["status"] = "remboursé (n'a pas joué)", 0.0, "réglé"
    return hist
