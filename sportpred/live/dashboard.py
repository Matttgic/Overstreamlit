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
from . import oddsapi, pinnacle
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
    """Compare les cotes FR (The Odds API) aux cotes justes Pinnacle, marché vainqueur/1N2."""
    if pin.empty or fr.empty:
        return pd.DataFrame()
    out = []
    pm = pin[(pin["market"] == "moneyline") & ~pin["is_prop"]]
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
                            "market_key": pr["market_key"].iloc[0], "source": "Pinnacle vs FR (The Odds API)",
                            "match_score": round(mm.score, 2)})
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


def watchlist(pin: pd.DataFrame, cfg: DashConfig, props: bool = False) -> pd.DataFrame:
    if pin.empty:
        return pin
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
    known = {(h["event"], h["selection"], h["book"]) for h in hist}
    for r in picks.itertuples():
        k = (r.event, r.selection, r.book)
        if k in known:
            continue
        hist.append({"detected_at": now.isoformat(), "sport": r.sport, "league": r.league,
                     "start": pd.Timestamp(r.start).isoformat(), "event": r.event, "market": r.market,
                     "selection": r.selection, "book": r.book, "odds": float(r.odds),
                     "fair_odds_at_pick": float(r.fair_odds), "fair_odds_last": float(r.fair_odds),
                     "ev_at_pick": float(r.ev), "market_key": r.market_key, "source": r.source,
                     "clv": None, "status": "en attente"})
    latest = {}
    if not pin.empty:
        for r in pin.itertuples():
            latest[(r.market_key, r.selection)] = r.fair_odds
    fd_fair = fd_fair or {}
    for h in hist:
        start = pd.Timestamp(h["start"])
        if start > now:
            fo = latest.get((h.get("market_key"), h["selection"])) if h.get("market_key") \
                else fd_fair.get((h["event"], h["selection"]))
            if fo and np.isfinite(fo) and now.isoformat() > h["detected_at"]:
                h["fair_odds_last"] = float(fo)
                h["last_seen"] = now.isoformat()
        # CLV seulement si la cote juste a été ré-observée après la détection du pari
        h["clv"] = round(h["odds"] / h["fair_odds_last"] - 1, 4) if h.get("last_seen") else None
        if start <= now and h["status"] == "en attente":
            h["status"] = "commencé (CLV figée)"
    return hist


def build(out_dir: Path, cfg: DashConfig | None = None, now: pd.Timestamp | None = None) -> dict:
    cfg = cfg or DashConfig()
    now = now or pd.Timestamp.now(tz="UTC")
    out_dir.mkdir(parents=True, exist_ok=True)
    pin = _upcoming(pinnacle.all_odds(), cfg, now)
    budget = oddsapi.Budget()
    fr = _upcoming(oddsapi.fr_odds(budget=budget), cfg, now)
    frames = [value_from_oddsapi(pin, fr, cfg), value_from_football_data(cfg)]
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
    hist_path.write_text(json.dumps(hist, ensure_ascii=False, indent=0), encoding="utf-8")

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
    data = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": cfg.__dict__,
        "sources": {"pinnacle_outcomes": int(len(pin)), "fr_odds_rows": int(len(fr)),
                    "odds_api_key": bool(oddsapi._key()), "odds_api_remaining": budget.remaining},
        "value_bets": rec(vb, ["sport", "league", "start", "event", "market", "selection", "book", "odds",
                               "fair_odds", "ev", "stake_pct", "stake_eur", "source"]),
        "watchlist": rec(wl, ["sport", "league", "start", "event", "market_label", "selection_label",
                              "fair_odds", "min_odds", "pin_odds"]),
        "props": rec(pr, ["sport", "league", "start", "event", "market_label", "selection_label",
                          "fair_odds", "min_odds", "pin_odds"]),
        "tracking": {"n_picks": len(hist), "n_closed": len(clvs), "n_with_clv": len(clv_any),
                     "clv_mean": round(float(np.mean(clvs)), 4) if clvs else None,
                     "clv_positive_share": round(float(np.mean([c > 0 for c in clvs])), 3) if clvs else None,
                     "recent": hist[-30:][::-1]},
    }
    (out_dir / "today.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data
