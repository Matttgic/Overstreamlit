"""Construit les données du tableau de bord « quoi parier aujourd'hui ».

Sorties (JSON, lues par site/index.html) :
- value_bets : paris où un bookmaker agréé ANJ paie plus que la cote juste (EV ≥ seuil) ;
- watchlist  : pour chaque issue des prochaines 36 h, la cote juste Pinnacle et la
               « cote minimum à prendre » (à comparer soi-même dans son appli) ;
- props      : idem pour les paris joueurs publiés par Pinnacle (buteurs NHL, points NBA…) ;
- history    : paris proposés, avec CLV (cote prise / dernière cote juste avant le match).

Sources : Pinnacle (référence sharp, sans clé), football-data.co.uk (bet365, bwin,
Betfair Exchange — football), The Odds API (Betclic, Winamax, Unibet, PMU, NetBet —
optionnel, clé gratuite). Aucune source payante.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..betting.kelly import kelly_fraction
from . import nhl_scorers as nhl_mod
from . import fr_phone, oddsapi, pinnacle, unibet
from . import results as results_mod
from . import scanner as fd_scanner
from .matching import match_events


@dataclass
class DashConfig:
    min_ev: float = 0.03
    max_ev: float = 0.30
    max_odds: float = 10.0
    min_odds: float = 1.15
    kelly_frac: float = 0.25
    kelly_cap: float = 0.02
    bankroll: float = 1000.0
    horizon_hours: float = 36.0
    max_pin_margin: float = 0.08     # marché Pinnacle trop margé = référence peu fiable


def _stake(p, o, cfg):
    f = float(kelly_fraction(p, o)) * cfg.kelly_frac
    return round(100 * min(f, cfg.kelly_cap), 2)


def _upcoming(df: pd.DataFrame, cfg: DashConfig, now: pd.Timestamp) -> pd.DataFrame:
    if df.empty:
        return df
    return df[(df["start"] > now) & (df["start"] < now + pd.Timedelta(hours=cfg.horizon_hours))]


def value_from_oddsapi(pin: pd.DataFrame, fr: pd.DataFrame, cfg: DashConfig) -> pd.DataFrame:
    """Compare les cotes FR (The Odds API) aux cotes justes Pinnacle : vainqueur/1N2 et,
    si relevés, totaux (même ligne exacte seulement)."""
    if pin.empty or fr.empty:
        return pd.DataFrame()
    out = []
    unit = pin["unit"] if "unit" in pin else pd.Series(None, index=pin.index)
    # en tennis, Pinnacle publie un second « match » en jeux : on l'exclut de l'appariement
    pm = pin[(pin["market"] == "moneyline") & ~pin["is_prop"] & (unit.fillna("") != "jeux")]
    ptot = pin[(pin["market"] == "total") & ~pin["is_prop"]].assign(_unit=unit.fillna(""))
    for sport, frs in fr.groupby("sport"):
        ps = pm[pm["sport"] == sport]
        if ps.empty:
            continue
        m = match_events(frs[["event_id", "start", "home", "away"]], ps[["event_id", "start", "home", "away"]],
                         swap_ok=sport in ("tennis", "mma"))
        for mm in m.itertuples():
            fe = frs[frs["event_id"] == mm.left_id]
            pe = ps[ps["event_id"] == mm.right_id]
            h_fr, a_fr = fe["home"].iloc[0], fe["away"].iloc[0]
            h_p, a_p = pe["home"].iloc[0], pe["away"].iloc[0]
            mapping = {h_fr: (a_p if mm.swapped else h_p), a_fr: (h_p if mm.swapped else a_p), "Nul": "Nul"}
            # totaux : Odds API « Over/Under » + ligne <-> Pinnacle « Plus/Moins » même ligne
            # (tennis : totaux en jeux, publiés par Pinnacle sur le match « (Games) »)
            ev_name, ev_start = pe["event"].iloc[0], pe["start"].iloc[0]
            pt = ptot[(ptot["start"] == ev_start) & (ptot["event"] == ev_name)]
            pt = pt[pt["_unit"] == ("jeux" if sport == "tennis" else "")]
            ft = fe[fe["market"] == "total"].sort_values("odds", ascending=False) \
                .drop_duplicates(["selection", "line"])
            for r in ft.itertuples():
                sel = {"Over": "Plus", "Under": "Moins"}.get(r.selection)
                pr = pt[(pt["selection"] == sel) & (pt["line"] == r.line)]
                if pr.empty or sel is None:
                    continue
                p = float(pr["fair_prob"].iloc[0])
                out.append({"sport": sport, "league": pe["league"].iloc[0], "start": ev_start, "event": ev_name,
                            "market": "Total" + (" de jeux" if sport == "tennis" else ""),
                            "selection": f"{sel} {r.line:g}", "book": r.book, "odds": r.odds,
                            "fair_odds": round(1 / p, 3), "fair_prob": p, "ev": p * r.odds - 1,
                            "pin_margin": float(pr["pin_margin"].iloc[0]), "market_key": pr["market_key"].iloc[0],
                            "pin_selection": sel, "source": "Pinnacle vs FR (The Odds API)",
                            "match_score": round(mm.score, 2)})
            # même marché seulement : hockey et handball sont publiés en 1N2 temps réglementaire
            # (avec « Nul ») par la plupart des opérateurs FR, en 2 issues par Pinnacle
            fe = fe[fe["market"] == "moneyline"]
            pin_draw = bool((pe["selection"] == "Nul").any())
            draw_books = set(fe.loc[fe["selection"] == "Nul", "book"])
            fe = fe[fe["book"].isin(draw_books) == pin_draw]
            best = fe.sort_values("odds", ascending=False).drop_duplicates("selection")
            for r in best.itertuples():
                pr = pe[pe["selection"] == mapping.get(r.selection)]
                if pr.empty:
                    continue
                p = float(pr["fair_prob"].iloc[0])
                ev = p * r.odds - 1
                out.append({"sport": sport, "league": pe["league"].iloc[0], "start": pe["start"].iloc[0],
                            "event": pe["event"].iloc[0], "market": "Vainqueur / 1N2",
                            "selection": mapping[r.selection], "book": r.book, "odds": r.odds,
                            "fair_odds": round(1 / p, 3), "fair_prob": p, "ev": ev,
                            "pin_margin": float(pr["pin_margin"].iloc[0]),
                            "market_key": pr["market_key"].iloc[0], "pin_selection": mapping[r.selection],
                            "source": "Pinnacle vs FR (The Odds API)", "match_score": round(mm.score, 2)})
    return pd.DataFrame(out)


def value_from_football_data(cfg: DashConfig) -> pd.DataFrame:
    """Football : Betfair Exchange (juste) vs bet365 / bwin (agréés ANJ) — fichier fixtures."""
    try:
        fx = fd_scanner.load_fixtures()
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    picks = fd_scanner.find_value(fx, fd_scanner.ScanConfig(min_ev=cfg.min_ev, max_ev=cfg.max_ev,
                                                            max_odds=cfg.max_odds))
    if picks.empty:
        return picks
    names = {"H": "domicile", "D": "Nul", "A": "extérieur"}
    start = pd.to_datetime(picks["date"].astype(str) + " " + picks["heure"].fillna("12:00").astype(str),
                           errors="coerce").dt.tz_localize("Europe/London").dt.tz_convert("UTC")
    return pd.DataFrame({
        "sport": "football", "league": picks["league"], "start": start, "event": picks["match"],
        "market": "1N2", "selection": [f"{names[s]} ({m.split(' - ')[0] if s == 'H' else m.split(' - ')[-1] if s == 'A' else 'nul'})"
                                       for s, m in zip(picks["selection"], picks["match"])],
        "book": picks["bookmaker"].map({"B365": "bet365", "BW": "bwin"}), "odds": picks["cote"],
        "fair_odds": picks["cote_juste"], "fair_prob": picks["p_juste"], "ev": picks["ev"],
        "pin_margin": np.nan, "market_key": None, "source": "Betfair Exchange vs bet365/bwin (football-data)",
        "match_score": 1.0})


PROP_STATS = [("Total Shots On Goal", "Tirs cadrés"), ("Total Goals", "Buts"), ("Total Points", "Points"),
              ("Total Assists", "Passes décisives"), ("Total Saves", "Arrêts"), ("Total Rebounds", "Rebonds"),
              ("Total Threes", "Paniers à 3 points"), ("Total 3 Point FG", "Paniers à 3 points"),
              ("Pts+Rebs+Asts", "Points + rebonds + passes"), ("Total Steals", "Interceptions"),
              ("Total Blocks", "Contres"), ("Total Hits", "Mises en échec"), ("Total Strikeouts", "Retraits au bâton")]


def props_table(pin: pd.DataFrame, cfg: DashConfig) -> pd.DataFrame:
    """Paris joueurs Pinnacle (« Player Props ») avec libellés lisibles et cote minimum."""
    if pin.empty:
        return pin
    w = pin[pin["is_prop"] & pin["market"].str.startswith("Player Props:")].copy()
    w = w[(w["pin_margin"] <= cfg.max_pin_margin + 0.02) & (w["fair_odds"] >= 1.05)]
    if w.empty:
        return w
    desc = w["market"].str.replace("Player Props: ", "", regex=False)
    players, stats = [], []
    for d in desc:
        for en, fr in PROP_STATS:
            if d.endswith(en):
                players.append(d[: -len(en)].strip())
                stats.append(fr)
                break
        else:
            players.append(d)
            stats.append("")
    w["player"], w["stat"] = players, stats
    goal_yes = (w["stat"] == "Buts") & (w["line"] == 0.5)
    w = w[~(goal_yes & (w["selection"] == "Under"))]          # « buteur » : on garde le « oui »
    goal_yes = (w["stat"] == "Buts") & (w["line"] == 0.5)
    w["market_label"] = w["player"] + " — " + w["stat"].where(w["stat"] != "", "stat")
    w["market_label"] = w["market_label"].where(~goal_yes, w["player"] + " — Buteur")
    w["selection_label"] = [("Marque (au moins 1 but)" if g else
                             f"{'Plus' if s_ == 'Over' else 'Moins'} de {l:g}")
                            for g, s_, l in zip(goal_yes, w["selection"], w["line"])]
    w["min_odds"] = (w["fair_odds"] * (1 + cfg.min_ev)).round(2)
    return w.sort_values(["start", "event", "player", "stat", "selection"])


def watchlist(pin: pd.DataFrame, cfg: DashConfig, props: bool = False) -> pd.DataFrame:
    if pin.empty:
        return pin
    if props:
        return props_table(pin, cfg)
    w = pin[pin["is_prop"] == props].copy()
    if not props:
        w = w[w["market"].isin(["moneyline", "total"])]
    w = w[(w["pin_margin"] <= cfg.max_pin_margin) & (w["fair_odds"] >= 1.05)]
    w["min_odds"] = (w["fair_odds"] * (1 + cfg.min_ev)).round(2)
    w["market_label"] = w["market"].map({"moneyline": "Vainqueur / 1N2", "total": "Total (plus/moins)"}) \
        .fillna(w["market"])
    if "unit" in w:
        tennis_tot = (w["sport"] == "tennis") & (w["market"] == "total")
        w.loc[tennis_tot, "market_label"] = np.where(w.loc[tennis_tot, "unit"] == "jeux", "Total de jeux",
                                                     "Total de sets")
        w = w[~((w["sport"] == "tennis") & (w["market"] == "moneyline") & (w["unit"] == "jeux"))]
    unit = w["unit"] if "unit" in w else pd.Series(None, index=w.index)
    w["selection_label"] = [
        f"{s} {l:g}{' ' + u if isinstance(u, str) and u else ''}" if m == "total" and pd.notna(l) else str(s)
        for s, l, m, u in zip(w["selection"], w["line"], w["market"], unit)]
    return w.sort_values(["start", "event"])


def football_data_fair_table() -> dict:
    """Cote juste Betfair Exchange actuelle de chaque issue du fichier fixtures (football)."""
    try:
        fx = fd_scanner.load_fixtures()
    except Exception:  # noqa: BLE001
        return {}
    from ..betting.odds import devig
    fx = fx.dropna(subset=["BFEH", "BFED", "BFEA"])
    if fx.empty:
        return {}
    p = devig(fx[["BFEH", "BFED", "BFEA"]].values, "power")
    out = {}
    for (h, a), row in zip(zip(fx["HomeTeam"], fx["AwayTeam"]), p):
        ev = f"{h} - {a}"
        out[(ev, f"domicile ({h})")] = 1 / row[0]
        out[(ev, "Nul (nul)")] = 1 / row[1]
        out[(ev, f"extérieur ({a})")] = 1 / row[2]
    return out


def update_history(hist: list[dict], picks: pd.DataFrame, pin: pd.DataFrame,
                   now: pd.Timestamp, fd_fair: dict | None = None) -> list[dict]:
    """Ajoute les nouveaux paris et met à jour la CLV des paris dont le match n'a pas commencé."""
    # faux value bets du 02/10/2026 (1N2 temps réglementaire FR comparé au vainqueur Pinnacle
    # en hockey/handball, corrigé dans value_from_oddsapi) : retirés du suivi
    hist = [h for h in hist if not (h.get("source") == "Pinnacle vs FR (The Odds API)"
                                    and h.get("sport") in ("hockey", "handball")
                                    and h.get("market") == "Vainqueur / 1N2"
                                    and h["detected_at"] < "2026-10-02T21")]
    known = {(h["event"], h["selection"], h["book"]) for h in hist}
    for r in picks.itertuples():
        k = (r.event, r.selection, r.book)
        if k in known:
            continue
        hist.append({"detected_at": now.isoformat(), "sport": r.sport, "league": r.league,
                     "start": pd.Timestamp(r.start).isoformat(), "event": r.event, "market": r.market,
                     "selection": r.selection, "book": r.book, "odds": float(r.odds),
                     "fair_odds_at_pick": float(r.fair_odds), "fair_odds_last": float(r.fair_odds),
                     "pin_selection": getattr(r, "pin_selection", None) if isinstance(
                         getattr(r, "pin_selection", None), str) else r.selection,
                     "ev_at_pick": float(r.ev), "market_key": r.market_key if isinstance(r.market_key, str) else None,
                     "source": r.source,
                     "stake_pct": float(getattr(r, "stake_pct", 0) or 0),
                     "clv": None, "status": "en attente"})
        for k in ("player", "stat", "line", "player_id", "reg_only"):   # paris joueurs (opérateurs FR)
            v = getattr(r, k, None)
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                hist[-1][k] = (int(v) if k == "player_id" else float(v) if k == "line"
                               else bool(v) if k == "reg_only" else v)
    latest = {}
    if not pin.empty:
        for r in pin.itertuples():
            latest[(r.market_key, r.selection)] = r.fair_odds
    fd_fair = fd_fair or {}
    for h in hist:
        start = pd.Timestamp(h["start"])
        if start > now:
            fo = latest.get((h.get("market_key"), h.get("pin_selection") or h["selection"])) if h.get("market_key") \
                else fd_fair.get((h["event"], h["selection"]))
            if fo and np.isfinite(fo) and now.isoformat() > h["detected_at"]:
                h["fair_odds_last"] = float(fo)
                h["last_seen"] = now.isoformat()
        # CLV seulement si la cote juste a été ré-observée après la détection du pari
        h["clv"] = round(h["odds"] / h["fair_odds_last"] - 1, 4) if h.get("last_seen") else None
        if start <= now and h["status"] == "en attente":
            h["status"] = "commencé (CLV figée)"
    return hist


def load_fr_odds(out_dir: Path, now: pd.Timestamp, budget: "oddsapi.Budget",
                 max_age_hours: float = 6.0) -> tuple[pd.DataFrame, str | None]:
    """Cotes FR via The Odds API, réglées par variables d'environnement :

    - ODDS_API_HOURS : heures UTC d'appel (« 7,13,17 ») ou « all » (à chaque passage) ;
    - ODDS_API_MAX_CALLS : nombre max de sports interrogés par passage ;
    - ODDS_API_MARKETS : « h2h » (1 crédit/sport) ou « h2h,totals » (2 crédits/sport) ;
    - ODDS_API_RESERVE : crédits à ne jamais entamer.
    Défauts prudents (offre gratuite 500/mois) : 7,13,17 / 5 / h2h / 0 -> ~15 crédits/jour.
    Hors des heures d'appel, réutilise le dernier relevé s'il a moins de `max_age_hours`.
    """
    import os
    cache = out_dir / "fr_odds_cache.json"
    hours_env = os.environ.get("ODDS_API_HOURS", "7,13,17").strip().lower()
    hours = set(range(24)) if hours_env in ("all", "*") else \
        {int(h) for h in hours_env.split(",") if h.strip()}
    max_calls = int(os.environ.get("ODDS_API_MAX_CALLS", "5"))
    markets = os.environ.get("ODDS_API_MARKETS", "h2h").strip() or "h2h"
    reserve = int(os.environ.get("ODDS_API_RESERVE", "0"))
    if oddsapi._key() and (now.hour in hours or not cache.exists()):
        fr = oddsapi.fr_odds(max_calls=max_calls, markets=markets, budget=budget, reserve=reserve)
        if not fr.empty:
            cache.write_text(json.dumps({"at": now.isoformat(), "rows": fr.assign(
                start=fr["start"].astype(str)).to_dict("records")}), encoding="utf-8")
            return fr, now.isoformat()
    if cache.exists():
        c = json.loads(cache.read_text())
        if now - pd.Timestamp(c["at"]) < pd.Timedelta(hours=max_age_hours):
            fr = pd.DataFrame(c["rows"])
            if not fr.empty:
                fr["start"] = pd.to_datetime(fr["start"], utc=True)
            return fr, c["at"]
    return pd.DataFrame(), None


def archive_odds(pin: pd.DataFrame, out_dir: Path, now: pd.Timestamp) -> None:
    """Archive les cotes Pinnacle (marchés principaux + paris joueurs) : un fichier gzip
    par jour, une ligne par issue et par relevé. Aucun historique gratuit de cotes de
    paris joueurs n'existe : cette archive permettra de futurs backtests (CLV, props)."""
    if pin.empty:
        return
    keep = pin[(pin["market"].isin(["moneyline", "total"])) | pin["market"].str.startswith("Player Props:")]
    a = keep[["sport", "league", "start", "event", "market", "selection", "line", "pin_odds", "fair_odds"]].copy()
    a.insert(0, "captured_at", now.strftime("%Y-%m-%dT%H:%MZ"))
    a["pin_odds"] = a["pin_odds"].round(3)
    a["fair_odds"] = a["fair_odds"].round(3)
    d = out_dir / "archive"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"pinnacle_{now.strftime('%Y-%m-%d')}.csv.gz"
    a.to_csv(f, mode="a", header=not f.exists(), index=False, compression="gzip")


NHL_MODEL_MIN_EV = nhl_mod.MODEL_MIN_EV   # marge exigée quand seule la cote du modèle sert de référence


def nhl_block(pin: pd.DataFrame, out_dir: Path, now: pd.Timestamp,
              cfg: DashConfig) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Buteurs NHL : tous les joueurs des matchs du jour, cote juste Pinnacle si elle existe,
    sinon cote du modèle (marge exigée plus large) ; cotes joueurs Unibet.fr (lues par GitHub)
    et Winamax / Betclic (envoyées par le téléphone) comparées automatiquement ; archive et
    bilan modèle vs Pinnacle.

    Renvoie (bloc pour today.json, paris joueurs au-dessus du seuil, feuilles de match NHL)."""
    empty = ({}, pd.DataFrame(), pd.DataFrame())
    if pin.empty or "league" not in pin or not (pin["league"] == "NHL").any():
        return empty
    hist, pred = pd.DataFrame(), pd.DataFrame()
    try:
        hist = nhl_mod.load_hist(now)
        pred = nhl_mod.predict(pin, now, hist=hist)
    except Exception as e:  # noqa: BLE001 — l'API NHL ne doit pas bloquer le tableau
        print("modèle buteurs NHL indisponible :", e)   # Unibet reste comparé à Pinnacle
    arch = out_dir / "archive"
    frames, phone_meta = [], {"status": "non lu"}
    try:
        ub = unibet.nhl_player_odds(now, min(cfg.horizon_hours, 20))   # marchés joueurs : jour du match
        if not ub.empty:
            arch.mkdir(parents=True, exist_ok=True)
            fu = arch / f"unibet_nhl_joueurs_{now.strftime('%Y-%m-%d')}.csv.gz"
            ub.assign(captured_at=now.strftime("%Y-%m-%dT%H:%MZ")).to_csv(
                fu, mode="a", header=not fu.exists(), index=False, compression="gzip")
            frames.append(ub.assign(book="Unibet", reg_only=False))
    except Exception as e:  # noqa: BLE001 — Unibet peut bloquer ou changer de format
        print("cotes joueurs Unibet indisponibles :", e)
    try:                                       # Winamax + Betclic, envoyés par le téléphone
        ph, phone_meta = fr_phone.load(now)
        if not ph.empty:
            frames.append(ph)
            state_f = out_dir / "fr_phone_state.json"
            last = json.loads(state_f.read_text()).get("last_at") if state_f.exists() else None
            if phone_meta.get("at") != last:      # une seule copie par collecte du téléphone
                arch.mkdir(parents=True, exist_ok=True)
                fp = arch / f"fr_telephone_{now.strftime('%Y-%m-%d')}.csv.gz"
                ph.drop(columns=["ub_event_id", "ub_event"]).assign(captured_at=phone_meta.get("at")).to_csv(
                    fp, mode="a", header=not fp.exists(), index=False, compression="gzip")
                state_f.write_text(json.dumps({"last_at": phone_meta.get("at")}))
        print("téléphone (Winamax, Betclic) :", phone_meta.get("status"), phone_meta.get("at"), len(ph), "cotes")
    except Exception as e:  # noqa: BLE001
        print("cotes du téléphone illisibles :", e)
    b_cmp, b_vb, mixed = pd.DataFrame(), pd.DataFrame(), {}
    try:
        allb = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        allb, mixed = nhl_mod.drop_mixed_markets(allb)      # marchés mélangés à la lecture -> écartés
        for bk, n in mixed.items():
            print(f"{bk} : cotes joueurs écartées sur {n} match(s) (même joueur, deux cotes sur la même ligne)")
        b_cmp = nhl_mod.compare_book_props(allb, pin, pred, cfg.min_ev)
        b_cmp, odd = nhl_mod.drop_implausible(b_cmp)          # cotes au-dessus de la cote juste en médiane
        for bk, n in odd.items():
            print(f"{bk} : cotes joueurs écartées sur {n} match(s) (écart médian à la cote juste > +5 %)")
            mixed[bk] = mixed.get(bk, 0) + n
        b_vb = nhl_mod.book_value_bets(b_cmp, cfg.max_odds, cfg.min_odds, cfg.max_ev, cfg.max_pin_margin + 0.02)
        for bk, g in (b_cmp.groupby("book") if not b_cmp.empty else []):
            print(f"{bk} joueurs NHL : {len(g)} cotes comparées, {int((g['ev'] >= g['threshold']).sum())} au-dessus du seuil")
    except Exception as e:  # noqa: BLE001
        print("comparaison des cotes joueurs impossible :", e)
    suivi = {}
    if not pred.empty:
        try:
            cmp = nhl_mod.compare_with_pinnacle(pin, pred)
        except Exception as e:  # noqa: BLE001 — ne doit jamais bloquer tout le tableau
            print("comparaison modèle / Pinnacle impossible :", e)
            cmp = pd.DataFrame()
        pred = pred.merge(cmp[["event", "prop_name", "pin_prob"]].drop_duplicates(["event", "prop_name"]),
                          on=["event", "prop_name"], how="left") if not cmp.empty else pred.assign(pin_prob=np.nan)
        a = pred[["event", "start", "game_id", "team", "player_id", "name", "lam", "share", "model_prob",
                  "pin_prob"]].copy()
        a.insert(0, "captured_at", now.strftime("%Y-%m-%dT%H:%MZ"))
        a[["lam", "share", "model_prob", "pin_prob"]] = a[["lam", "share", "model_prob", "pin_prob"]].round(4)
        arch.mkdir(parents=True, exist_ok=True)
        f = arch / f"nhl_buteurs_{now.strftime('%Y-%m-%d')}.csv.gz"
        a.to_csv(f, mode="a", header=not f.exists(), index=False, compression="gzip")
    try:
        suivi = nhl_mod.evaluate_archive(arch, hist)
    except Exception as e:  # noqa: BLE001
        print("bilan buteurs NHL impossible :", e)
    def summ(c: pd.DataFrame) -> dict:
        return {"compared": int(len(c)), "value": int((c["ev"] >= c["threshold"]).sum()) if not c.empty else 0,
                "ev_median": round(float(c["ev"].median()), 4) if not c.empty else None}
    books_summary = {**summ(b_cmp), "by_book": {bk: summ(g) for bk, g in b_cmp.groupby("book")} if not b_cmp.empty
                     else {}, "phone": {k: phone_meta.get(k) for k in ("status", "at", "stats")},
                     "rejected": {bk: int(n) for bk, n in mixed.items()}}
    if pred.empty:
        return {"rows": [], "suivi": suivi, "model_min_ev": NHL_MODEL_MIN_EV, "books": books_summary}, b_vb, hist
    has_pin = pred["pin_prob"].notna()
    r = pred[(pred["model_prob"] >= 1 / cfg.max_odds) | has_pin].copy()
    has_pin = r["pin_prob"].notna()
    r["fair_odds"] = np.where(has_pin, 1 / r["pin_prob"], 1 / r["model_prob"]).round(2)
    r["min_odds"] = (r["fair_odds"] * np.where(has_pin, 1 + cfg.min_ev, 1 + NHL_MODEL_MIN_EV)).round(2)
    r["ref"] = np.where(has_pin, "Pinnacle", "modèle")
    r["start"] = pd.to_datetime(r["start"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    books_map = {}                             # cotes « marque » des opérateurs face à chaque joueur
    if not b_cmp.empty:
        g = b_cmp[(b_cmp["stat"] == "Buts") & (b_cmp["line"] == 0.5)].dropna(subset=["player_id"])
        for x in g.sort_values("odds", ascending=False).itertuples():
            books_map.setdefault((x.event, int(x.player_id)), []).append(
                {"b": x.book, "o": float(x.odds), "hit": bool(x.ev >= x.threshold), "reg": bool(x.reg_only)})
    r["books"] = [books_map.get((e, int(p)), []) for e, p in zip(r["event"], r["player_id"])]
    cols = ["event", "match", "start", "team", "name", "model_prob", "pin_prob", "fair_odds", "min_odds", "ref",
            "lineup", "books"]
    r = r.sort_values(["start", "event", "model_prob"], ascending=[True, True, False])[cols]
    r[["model_prob", "pin_prob"]] = r[["model_prob", "pin_prob"]].round(4)
    block = {"rows": r.replace({np.nan: None}).to_dict("records"), "suivi": suivi,
             "model_min_ev": NHL_MODEL_MIN_EV, "books": books_summary}
    return block, b_vb, hist


def json_safe(o):
    """Remplace NaN / infini par None (JSON strict : sinon le navigateur rejette tout le fichier)."""
    if isinstance(o, float):
        return o if np.isfinite(o) else None
    if isinstance(o, dict):
        return {k: json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [json_safe(v) for v in o]
    if isinstance(o, np.generic):
        return json_safe(o.item())
    return o


def build(out_dir: Path, cfg: DashConfig | None = None, now: pd.Timestamp | None = None) -> dict:
    cfg = cfg or DashConfig()
    now = now or pd.Timestamp.now(tz="UTC")
    out_dir.mkdir(parents=True, exist_ok=True)
    pin = _upcoming(pinnacle.all_odds(), cfg, now)
    try:
        archive_odds(pin, out_dir, now)
    except Exception as e:  # noqa: BLE001
        print("archivage impossible :", e)
    budget = oddsapi.Budget()
    fr, fr_at = load_fr_odds(out_dir, now, budget)
    fr = _upcoming(fr, cfg, now)
    try:
        nhl, nhl_vb, nhl_hist = nhl_block(pin, out_dir, now, cfg)
    except Exception as e:  # noqa: BLE001 — le bloc NHL ne doit jamais empêcher la mise à jour du site
        print("bloc NHL indisponible :", e)
        nhl, nhl_vb, nhl_hist = {}, pd.DataFrame(), pd.DataFrame()
    frames = [value_from_oddsapi(pin, fr, cfg), value_from_football_data(cfg), nhl_vb]
    vb = pd.concat([f for f in frames if not f.empty], ignore_index=True) if any(
        not f.empty for f in frames) else pd.DataFrame()
    if not vb.empty:
        vb = vb[(vb["ev"] >= cfg.min_ev) & (vb["ev"] <= cfg.max_ev) & (vb["odds"] <= cfg.max_odds)
                & (vb["odds"] >= cfg.min_odds) & ~(vb["pin_margin"] > cfg.max_pin_margin)]
        vb = vb.sort_values("ev", ascending=False).drop_duplicates(["event", "market"])
        vb["stake_pct"] = [_stake(p, o, cfg) for p, o in zip(vb["fair_prob"], vb["odds"])]
        vb["stake_eur"] = (vb["stake_pct"] / 100 * cfg.bankroll).round(2)
        vb = vb.sort_values("start")
    wl = watchlist(pin, cfg)
    pr = watchlist(pin, cfg, props=True)

    hist_path = out_dir / "history.json"
    hist = json.loads(hist_path.read_text()) if hist_path.exists() else []
    hist = update_history(hist, vb if not vb.empty else pd.DataFrame(columns=["event"]), pin, now,
                          football_data_fair_table())
    try:
        hist = results_mod.settle(hist, now)
    except Exception as e:  # noqa: BLE001 — un échec ESPN ne doit pas bloquer le tableau
        print("règlement ESPN impossible :", e)
    try:
        hist = nhl_mod.settle_player_props(hist, nhl_hist, now)
    except Exception as e:  # noqa: BLE001
        print("règlement des paris joueurs impossible :", e)
    hist = json_safe(hist)
    hist_path.write_text(json.dumps(hist, ensure_ascii=False, indent=0, allow_nan=False), encoding="utf-8")

    def rec(df, cols):
        if df is None or df.empty:
            return []
        d = df[[c for c in cols if c in df]].copy()
        if "start" in d:
            d["start"] = pd.to_datetime(d["start"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        d = d.replace({np.nan: None})
        return d.to_dict("records")

    clvs = [h["clv"] for h in hist if h.get("clv") is not None and h["status"] != "en attente"]
    clv_any = [h["clv"] for h in hist if h.get("clv") is not None]
    settled = [h["profit_units"] for h in hist if h.get("profit_units") is not None]
    data = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": cfg.__dict__,
        "sources": {"pinnacle_outcomes": int(len(pin)), "fr_odds_rows": int(len(fr)), "fr_odds_at": fr_at,
                    "odds_api_key": bool(oddsapi._key()), "odds_api_remaining": budget.remaining},
        "value_bets": rec(vb, ["sport", "league", "start", "event", "market", "selection", "book", "odds",
                               "fair_odds", "ev", "stake_pct", "stake_eur", "source"]),
        "watchlist": rec(wl, ["sport", "league", "start", "event", "market_label", "selection_label",
                              "fair_odds", "min_odds", "pin_odds"]),
        "props": rec(pr, ["sport", "league", "start", "event", "market_label", "selection_label",
                          "fair_odds", "min_odds", "pin_odds"]),
        "nhl_buteurs": nhl,
        "tracking": {"n_picks": len(hist), "n_closed": len(clvs), "n_with_clv": len(clv_any),
                     "n_settled": len(settled), "profit_units": round(sum(settled), 2) if settled else None,
                     "roi_flat": round(sum(settled) / len(settled), 4) if settled else None,
                     "clv_mean": round(float(np.mean(clvs)), 4) if clvs else None,
                     "clv_positive_share": round(float(np.mean([c > 0 for c in clvs])), 3) if clvs else None,
                     "recent": hist[-30:][::-1]},
    }
    data = json_safe(data)
    (out_dir / "today.json").write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return data
