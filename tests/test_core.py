"""Tests unitaires des briques de base (exécuter : pytest -q)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import approx_fprime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sportpred.backtest.engine import simulate  # noqa: E402
from sportpred.backtest.metrics import brier, log_loss, rps  # noqa: E402
from sportpred.betting.kelly import kelly_fraction, simultaneous_kelly  # noqa: E402
from sportpred.betting.odds import DEVIG, devig, overround  # noqa: E402
from sportpred.models.dixon_coles import DixonColes  # noqa: E402
from sportpred.models.elo import binary_elo, football_elo  # noqa: E402
from sportpred.models.ordered import OrderedLogit  # noqa: E402
from sportpred.models.pi_ratings import pi_ratings  # noqa: E402

ODDS = np.array([[1.5, 4.2, 7.0], [2.6, 3.3, 2.9], [1.9, 3.6, 4.5]])


@pytest.mark.parametrize("method", list(DEVIG))
def test_devig_sums_to_one(method):
    p = devig(ODDS, method)
    assert np.allclose(p.sum(axis=1), 1.0)
    assert (p > 0).all()
    # l'ordre des probabilités suit l'ordre inverse des cotes
    assert (np.argsort(p, axis=1) == np.argsort(-ODDS, axis=1)).all()


def test_devig_nan_rows():
    o = np.array([[1.8, np.nan, 2.0]])
    for m in DEVIG:
        assert np.isnan(devig(o, m)).all()


def test_power_and_shin_correct_favourite_longshot():
    # power et Shin attribuent PLUS de proba au favori que la méthode multiplicative
    pm = devig(ODDS[:1], "multiplicative")[0]
    for m in ("power", "shin"):
        assert devig(ODDS[:1], m)[0][0] > pm[0]
        assert devig(ODDS[:1], m)[0][2] < pm[2]


def test_overround():
    assert overround([[2.0, 2.0]])[0] == pytest.approx(1.0)


def test_kelly():
    assert kelly_fraction(0.5, 2.0) == pytest.approx(0.0)
    assert kelly_fraction(0.6, 2.0) == pytest.approx(0.2)
    assert kelly_fraction(0.3, 2.0) == 0.0
    f = simultaneous_kelly(np.array([0.6, 0.6]), np.array([2.0, 2.0]))
    assert (f > 0).all() and f.sum() < 0.4  # moins que 2 x Kelly individuel


def test_rps_known_values():
    # Constantinou & Fenton (2012) : prédiction parfaite -> 0
    assert rps(np.array([[1.0, 0, 0]]), np.array([0]))[0] == 0.0
    # p=(1/3,1/3,1/3), victoire domicile -> ((1/3-1)^2 + (2/3-1)^2)/2 = 0.2778
    assert rps(np.array([[1 / 3, 1 / 3, 1 / 3]]), np.array([0]))[0] == pytest.approx(0.27778, 1e-4)
    # RPS sensible à l'ordre : (0.1,0.2,0.7) vs résultat H est pire que (0.1,0.7,0.2)
    a = rps(np.array([[0.1, 0.2, 0.7]]), np.array([0]))[0]
    b = rps(np.array([[0.1, 0.7, 0.2]]), np.array([0]))[0]
    assert a > b
    assert log_loss(np.array([[0.5, 0.25, 0.25]]), np.array([0]))[0] == pytest.approx(np.log(2))
    assert brier(np.array([[1.0, 0, 0]]), np.array([0]))[0] == 0.0


def _toy_matches(n=600, seed=0):
    rng = np.random.default_rng(seed)
    teams = [f"T{i}" for i in range(12)]
    strength = dict(zip(teams, rng.normal(0, 0.3, len(teams))))
    rows = []
    d0 = pd.Timestamp("2020-01-01")
    for k in range(n):
        h, a = rng.choice(teams, 2, replace=False)
        lam = np.exp(0.2 + 0.25 + strength[h] - strength[a])
        mu = np.exp(0.2 + strength[a] - strength[h])
        rows.append([d0 + pd.Timedelta(days=k // 6), h, a, rng.poisson(lam), rng.poisson(mu)])
    df = pd.DataFrame(rows, columns=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    df["Country"] = "X"
    df["Season"] = "2020"
    return df, strength


def test_dixon_coles_gradient_and_recovery():
    df, strength = _toy_matches(1500)
    m = DixonColes(xi=0.0).fit(df.HomeTeam, df.AwayTeam, df.FTHG, df.FTAG, np.zeros(len(df)))
    assert m.converged
    th = np.random.default_rng(1).normal(0, 0.1, 2 * len(m.teams) + 3)
    th[-1] = 0.03
    num = approx_fprime(th, lambda t: m._objective(t)[0], 1e-6)
    ana = m._objective(th)[1]
    assert np.max(np.abs(num - ana)) < 1e-2 * max(1, np.max(np.abs(ana)))
    # les forces estimées sont corrélées aux vraies forces
    est = np.array([m.att[t] + m.def_[t] for t in m.teams])
    true = np.array([2 * strength[t] for t in m.teams])
    assert np.corrcoef(est, true)[0, 1] > 0.8
    p = m.predict(["T0"], ["T1"])
    assert p[["dc_ph", "dc_pd", "dc_pa"]].sum(axis=1).iloc[0] == pytest.approx(1.0)


def test_ratings_use_only_past():
    """La note avant-match ne doit pas dépendre du résultat du match lui-même."""
    df, _ = _toy_matches(300)
    e1 = football_elo(df)
    p1 = pi_ratings(df)
    df2 = df.copy()
    last = df2.index[-1]
    df2.loc[last, "FTHG"] = 9   # on change le résultat du dernier match
    e2 = football_elo(df2)
    p2 = pi_ratings(df2)
    assert e1.loc[last, "elo_h"] == e2.loc[last, "elo_h"]
    assert p1.loc[last, "pi_gd"] == p2.loc[last, "pi_gd"]


def test_binary_elo_and_ordered_logit():
    df = pd.DataFrame({"date": pd.date_range("2020", periods=200), "winner": ["A"] * 150 + ["B"] * 50,
                       "loser": ["B"] * 150 + ["A"] * 50})
    r = binary_elo(df)
    assert r["p_elo"].iloc[0] == pytest.approx(0.5)
    assert r["elo_w"].iloc[149] > r["elo_l"].iloc[149]
    x = np.random.default_rng(0).normal(0, 1, 3000)
    y = np.where(x + np.random.default_rng(1).logistic(0, 1, 3000) > 0.5, 0,
                 np.where(x + np.random.default_rng(2).logistic(0, 1, 3000) > -0.5, 1, 2))
    p = OrderedLogit().fit(x, y).predict_proba(np.array([-2.0, 0.0, 2.0]))
    assert np.allclose(p.sum(axis=1), 1)
    assert p[2, 0] > p[0, 0]


def test_simulate_flat_and_kelly():
    bets = pd.DataFrame({"date": pd.to_datetime(["2020-01-01"] * 2 + ["2020-01-02"]),
                         "match": ["a", "b", "c"], "p": [0.6, 0.6, 0.6], "odds": [2.0] * 3,
                         "won": [True, False, True], "ev": [0.2] * 3})
    b, s = simulate(bets, staking="flat", flat_frac=0.01)
    assert s["profit"] == pytest.approx(10.0)
    b, s = simulate(bets, staking="kelly", kelly_frac=0.5, cap=0.5)
    assert s["n_paris"] == 3 and s["bankroll_finale"] > 1000


def test_scanner_find_value_and_settle():
    from sportpred.live import scanner as sc
    fx = pd.DataFrame({"Date": pd.to_datetime(["2026-10-03", "2026-10-03"]), "Time": ["15:00", "17:00"],
                       "League": ["E0", "F1"], "HomeTeam": ["A", "C"], "AwayTeam": ["B", "D"],
                       "BFEH": [2.0, 1.5], "BFED": [3.6, 4.2], "BFEA": [4.2, 7.0],
                       "B365H": [2.25, 1.45], "B365D": [3.4, 4.0], "B365A": [3.9, 6.5],
                       "BWH": [2.1, 1.44], "BWD": [3.4, 4.0], "BWA": [4.0, 6.0]})
    picks = sc.find_value(fx, sc.ScanConfig(min_ev=0.03))
    assert len(picks) == 1                       # seul A-B (H à 2,25 > cote juste ~2,08)
    r = picks.iloc[0]
    assert r["selection"] == "H" and r["bookmaker"] == "B365" and r["ev"] > 0.03
    assert 0 < r["mise_%"] <= 2.0
    hist = picks.assign(statut="en attente", **{"profit_€": 0.0}, date=picks["date"].astype(str))
    res = pd.DataFrame({"Date": pd.to_datetime(["2026-10-03"]), "HomeTeam": ["A"], "AwayTeam": ["B"],
                        "FTHG": [1], "FTAG": [0], "BFECH": [1.95], "BFECD": [3.7], "BFECA": [4.4]})
    h = sc.settle(hist, res)
    assert h.loc[0, "statut"] == "gagné" and h.loc[0, "clv"] > 0


def test_matching_is_strict():
    from sportpred.live.matching import match_events, sim
    assert sim("Paris Saint-Germain", "Paris Saint Germain") >= 0.95
    assert sim("Paris SG", "Paris Saint-Germain") >= 0.95
    assert sim("Sunderland", "Salernitana") < 0.8          # le bug de l'ancien système
    t = pd.Timestamp("2026-10-10T18:45:00Z")
    left = pd.DataFrame({"event_id": ["x"], "start": [t], "home": ["Paris Saint Germain"], "away": ["Le Mans FC"]})
    right = pd.DataFrame({"event_id": [1, 2], "start": [t, t], "home": ["Paris Saint-Germain", "Lens"],
                          "away": ["Le Mans", "Lille"]})
    m = match_events(left, right)
    assert len(m) == 1 and m.iloc[0]["right_id"] == 1
    far = right.assign(start=t + pd.Timedelta(hours=30))
    assert match_events(left, far).empty                   # heures trop différentes


def test_oddsapi_parse_and_value():
    from sportpred.live import oddsapi
    from sportpred.live.dashboard import DashConfig, value_from_oddsapi
    t = "2026-10-10T18:45:00Z"
    payload = [{"id": "e1", "commence_time": t, "home_team": "Paris Saint Germain", "away_team": "Le Mans",
                "bookmakers": [{"key": "winamax_fr", "markets": [{"key": "h2h", "outcomes": [
                    {"name": "Paris Saint Germain", "price": 1.20}, {"name": "Le Mans", "price": 15.0},
                    {"name": "Draw", "price": 7.5}]}]},
                               {"key": "pinnacle", "markets": []}]}]
    fr = pd.DataFrame(oddsapi.parse_odds(payload, "soccer_france_ligue_one"))
    assert set(fr["book"]) == {"Winamax"} and len(fr) == 3
    pin = pd.DataFrame({"event_id": [9] * 3, "start": [pd.Timestamp(t)] * 3, "event": ["PSG - Le Mans"] * 3,
                        "home": ["Paris Saint-Germain"] * 3, "away": ["Le Mans"] * 3, "market": ["moneyline"] * 3,
                        "selection": ["Paris Saint-Germain", "Le Mans", "Nul"], "fair_prob": [0.80, 0.08, 0.12],
                        "pin_margin": [0.03] * 3, "market_key": ["k"] * 3, "is_prop": [False] * 3,
                        "sport": ["football"] * 3, "league": ["France - Ligue 1"] * 3})
    v = value_from_oddsapi(pin, fr, DashConfig())
    lm = v[v["selection"] == "Le Mans"].iloc[0]
    assert abs(lm["ev"] - (0.08 * 15 - 1)) < 1e-9 and lm["book"] == "Winamax"


def test_results_pick_side_and_settle(monkeypatch):
    from sportpred.live import results as rs
    assert rs._pick_side({"selection": "domicile (Auxerre)"}, "Auxerre", "Brest") == "home"
    assert rs._pick_side({"selection": "Nul"}, "Auxerre", "Brest") == "draw"
    assert rs._pick_side({"selection": "Vancouver Canucks"}, "Colorado Avalanche", "Vancouver Canucks") == "away"
    fake = [{"event_id": "1", "start": pd.Timestamp("2026-09-20T13:00Z"), "home": "AJ Auxerre", "away": "Brest",
             "completed": True, "winner": "home", "home_score": "2", "away_score": "1"}]
    monkeypatch.setattr(rs, "scoreboard", lambda path, day: fake)
    h = [{"event": "Auxerre - Brest", "league": "F1", "sport": "football", "start": "2026-09-20T13:00:00+00:00",
          "selection": "Nul", "odds": 3.4, "status": "commencé (CLV figée)"}]
    out = rs.settle(h, pd.Timestamp("2026-09-21T12:00Z"))
    assert out[0]["result"] == "perdu" and out[0]["profit_units"] == -1.0


def test_oddsapi_totals_value_and_settlement(monkeypatch):
    from sportpred.live import oddsapi
    from sportpred.live import results as rs
    from sportpred.live.dashboard import DashConfig, value_from_oddsapi
    t = "2026-10-10T18:45:00Z"
    payload = [{"id": "e1", "commence_time": t, "home_team": "Lens", "away_team": "Lille",
                "bookmakers": [{"key": "betclic_fr", "markets": [
                    {"key": "h2h", "outcomes": [{"name": "Lens", "price": 2.6}, {"name": "Lille", "price": 2.9},
                                                {"name": "Draw", "price": 3.2}]},
                    {"key": "totals", "outcomes": [{"name": "Over", "price": 2.20, "point": 2.5},
                                                   {"name": "Under", "price": 1.62, "point": 2.5}]}]}]}]
    fr = pd.DataFrame(oddsapi.parse_odds(payload, "soccer_france_ligue_one"))
    st = pd.Timestamp(t)
    base = dict(event_id=7, start=st, event="Lens - Lille", home="Lens", away="Lille", is_prop=False,
                sport="football", league="France - Ligue 1", pin_margin=0.03)
    pin = pd.DataFrame([dict(base, market="moneyline", selection=s, line=None, fair_prob=p, market_key="m")
                        for s, p in (("Lens", 0.38), ("Lille", 0.33), ("Nul", 0.29))] +
                       [dict(base, market="total", selection=s, line=2.5, fair_prob=p, market_key="t")
                        for s, p in (("Plus", 0.50), ("Moins", 0.50))])
    v = value_from_oddsapi(pin, fr, DashConfig())
    over = v[v["selection"] == "Plus 2.5"].iloc[0]
    assert over["book"] == "Betclic" and abs(over["ev"] - (0.5 * 2.2 - 1)) < 1e-9
    assert over["pin_selection"] == "Plus"
    fake = [{"event_id": "1", "start": st, "home": "RC Lens", "away": "Lille OSC", "completed": True,
             "winner": "home", "home_score": "2", "away_score": "1"}]
    monkeypatch.setattr(rs, "scoreboard", lambda path, day: fake)
    h = [{"event": "Lens - Lille", "league": "France - Ligue 1", "sport": "football", "start": t,
          "selection": "Plus 2.5", "odds": 2.2, "status": "commencé (CLV figée)"}]
    out = rs.settle(h, st + pd.Timedelta(days=1))
    assert out[0]["result"] == "gagné" and out[0]["profit_units"] == 1.2
