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


def test_oddsapi_hockey_3way_not_compared_to_2way():
    """NHL : 1N2 temps réglementaire (avec « Nul ») chez Betclic vs vainqueur prolongations
    comprises chez Pinnacle -> marchés différents, pas de comparaison (faux +22 %)."""
    from sportpred.live import oddsapi
    from sportpred.live.dashboard import DashConfig, value_from_oddsapi
    t = "2026-10-02T22:40:00Z"
    payload = [{"id": "e1", "commence_time": t, "home_team": "Detroit Red Wings", "away_team": "New York Rangers",
                "bookmakers": [
                    {"key": "betclic_fr", "markets": [{"key": "h2h", "outcomes": [
                        {"name": "Detroit Red Wings", "price": 2.23}, {"name": "New York Rangers", "price": 2.68},
                        {"name": "Draw", "price": 4.05}]}]},
                    {"key": "netbet_fr", "markets": [{"key": "h2h", "outcomes": [
                        {"name": "Detroit Red Wings", "price": 1.67}, {"name": "New York Rangers", "price": 1.95}]}]}]}]
    fr = pd.DataFrame(oddsapi.parse_odds(payload, "icehockey_nhl"))
    base = dict(event_id=3, start=pd.Timestamp(t), event="Detroit Red Wings - New York Rangers",
                home="Detroit Red Wings", away="New York Rangers", is_prop=False, sport="hockey", league="NHL",
                market="moneyline", line=None, pin_margin=0.03, market_key="m")
    pin = pd.DataFrame([dict(base, selection=s, fair_prob=p)
                        for s, p in (("Detroit Red Wings", 0.546), ("New York Rangers", 0.454))])
    v = value_from_oddsapi(pin, fr, DashConfig())
    assert set(v["book"]) == {"NetBet"}                     # Betclic (3 issues) écarté
    assert v["ev"].max() < 0


def test_nhl_team_lambdas_round_trip():
    """λ domicile/extérieur retrouvés à partir de P(victoire) et P(plus de 5,5 buts)."""
    import numpy as np
    from scipy.stats import poisson
    from sportpred.models.nhl_scorers import team_lambdas
    lh, la = 3.4, 2.6
    k = np.arange(25)
    joint = np.outer(poisson.pmf(k, lh), poisson.pmf(k, la))
    p_home = np.tril(joint, -1).sum() + 0.5 * np.trace(joint)
    p_over = poisson.sf(5, lh + la)
    h, a = team_lambdas(p_home, p_over, 5.5)
    assert abs(h - lh) < 1e-3 and abs(a - la) < 1e-3
    h6, a6 = team_lambdas(0.5, 0.5, 6.0)                       # ligne entière (remboursement à 6)
    assert abs(h6 - a6) < 1e-6 and 5.5 < h6 + a6 < 6.5


def _nhl_games(n_games=40):
    """Petit historique synthétique : 2 équipes, 3 joueurs chacune, un joueur qui tire beaucoup."""
    import numpy as np
    rng = np.random.default_rng(0)
    rows = []
    for g in range(n_games):
        for team, home, base in (("AAA", True, 0), ("BBB", False, 10)):
            for j, (pos, toi, shots_mu) in enumerate((("C", 20, 4.0), ("L", 15, 1.5), ("D", 22, 1.0))):
                shots = int(rng.poisson(shots_mu))
                rows.append({"game_id": 1000 + g, "date": pd.Timestamp("2025-10-01") + pd.Timedelta(days=2 * g),
                             "season": 20252026, "team": team, "opp": "BBB" if home else "AAA", "home": home,
                             "player_id": base + j, "name": f"P{base + j}", "pos": pos,
                             "goals": int(rng.binomial(shots, 0.12)), "pp_goals": 0, "ot_goals": 0,
                             "shots": shots, "toi": float(toi), "pp_toi": 2.0 if j == 0 else 0.0, "sh_toi": 0.0})
    return pd.DataFrame(rows)


def test_nhl_history_no_leak_and_shares():
    import numpy as np
    from sportpred.models import nhl_scorers as M
    df = _nhl_games()
    p = M.ShareParams(hl_long=10, hl_short=3)
    h = M.add_history(df, p)
    one = h[h["player_id"] == 0].sort_values("date").reset_index(drop=True)
    d = 0.5 ** (1 / 10)
    for t in (1, 5, 12):                                      # cumul pondéré des matchs < t seulement
        expect = sum(one.loc[i, "goals"] * d ** (t - 1 - i) for i in range(t))
        assert abs(one.loc[t, "S_goals"] - expect) < 1e-9
    assert one.loc[0, "S_goals"] == 0 and np.isnan(one.loc[0, "toi_exp"])
    p.priors = M.fit_priors(h)
    f = M.features(h, p)
    beta = M.fit_beta(f, ridge=0.1)
    s = M.predict_shares(f, beta)
    key = f["game_id"] * 2 + f["home"].astype(int)
    assert np.allclose(pd.Series(s).groupby(key.values).sum(), 1.0)
    late = f["date"] > f["date"].quantile(0.5)
    assert s[late & (f["player_id"] == 0)].mean() > s[late & (f["player_id"] == 1)].mean()   # gros tireur
    assert abs(M.p_score_given_goals(2, 0.5) - 0.75) < 1e-12 and abs(M.p_score(1.0, 0.5) - (1 - np.exp(-0.5))) < 1e-12


def test_nhl_find_player_and_evaluate_archive(tmp_path):
    from sportpred.live import nhl_scorers as L
    ros = pd.DataFrame({"player_id": [1, 2, 3], "name": ["Tim Stützle", "Brady Tkachuk", "Matthew Tkachuk"],
                        "pos": ["C", "L", "L"]})
    assert L._find("Tim Stutzle", ros) == 1                    # accents
    assert L._find("Brady Tkachuk", ros) == 2
    assert L._find("Tkachuk", ros) is None                     # ambigu : on s'abstient
    a = pd.DataFrame({
        "captured_at": ["2026-10-03T17:00Z", "2026-10-03T21:00Z", "2026-10-03T23:30Z", "2026-10-03T21:00Z"],
        "event": ["X - Y"] * 4, "start": ["2026-10-03T23:00:00Z"] * 4, "game_id": [7, 7, 7, 7],
        "team": ["X"] * 4, "player_id": [1, 1, 1, 9], "name": ["A", "A", "A", "Scratch"],
        "lam": [3.0] * 4, "share": [0.1] * 4, "model_prob": [0.10, 0.30, 0.99, 0.2], "pin_prob": [None, 0.25, 0.5, None]})
    (tmp_path / "x").mkdir()
    a.to_csv(tmp_path / "x" / "nhl_buteurs_2026-10-03.csv.gz", index=False, compression="gzip")
    hist = pd.DataFrame({"game_id": [7], "player_id": [1], "goals": [1]})   # le joueur 9 n'a pas joué
    r = L.evaluate_archive(tmp_path / "x", hist)
    import math
    assert r["n_model"] == 1 and r["n_both"] == 1                # dernier relevé AVANT le match (0,30)
    assert abs(r["ll_model"] + math.log(0.30)) < 1e-3 and abs(r["ll_pinnacle"] + math.log(0.25)) < 1e-3


def test_nhl_predict_back_to_back_offline(monkeypatch):
    """Bout en bout sans réseau : une équipe qui joue deux soirs de suite garde les mêmes
    caractéristiques de joueurs pour ses deux matchs, et Pinnacle sert à apparier les props."""
    import numpy as np
    from sportpred.live import nhl_scorers as L
    hist = _nhl_games(30)
    now = pd.Timestamp("2025-12-15T12:00Z")
    t1, t2 = now + pd.Timedelta(hours=10), now + pd.Timedelta(hours=34)
    sched = pd.DataFrame({"game_id": [1, 2], "season": [20252026] * 2, "start": [t1, t2],
                          "home_abbr": ["AAA", "CCC"], "away_abbr": ["BBB", "AAA"],
                          "home_name": ["Alpha Aces", "Gamma Gulls"], "away_name": ["Beta Bears", "Alpha Aces"]})
    ros = {"AAA": pd.DataFrame({"player_id": [0, 1, 2], "name": ["P0", "P1", "P2"], "pos": ["C", "L", "D"]}),
           "BBB": pd.DataFrame({"player_id": [10, 11, 12], "name": ["P10", "P11", "P12"], "pos": ["C", "L", "D"]}),
           "CCC": pd.DataFrame({"player_id": [20, 21, 22], "name": ["Zed One", "Zed Two", "Zed Three"],
                                "pos": ["C", "L", "D"]})}
    monkeypatch.setattr(L, "schedule", lambda day: sched)
    monkeypatch.setattr(L, "roster", lambda abbr: ros[abbr])

    def ev(eid, start, home, away, ph):
        base = dict(event_id=eid, start=start, event=f"{home} - {away}", home=home, away=away, league="NHL",
                    sport="hockey", is_prop=False, line=np.nan, pin_margin=0.03)
        return [dict(base, market="moneyline", selection=home, fair_prob=ph),
                dict(base, market="moneyline", selection=away, fair_prob=1 - ph),
                dict(base, market="total", selection="Plus", line=5.5, fair_prob=0.5),
                dict(base, market="total", selection="Moins", line=5.5, fair_prob=0.5),
                dict(base, market="Player Props: P0 Total Goals", selection="Over", line=0.5, fair_prob=0.4,
                     is_prop=True, fair_odds=2.5)]
    pin = pd.DataFrame(ev(101, t1, "Alpha Aces", "Beta Bears", 0.55) + ev(102, t2, "Gamma Gulls", "Alpha Aces", 0.5))
    pred = L.predict(pin, now, hist=hist)
    p0 = pred[pred["player_id"] == 0].set_index("game_id")
    assert set(p0.index) == {1, 2}
    # mêmes coéquipiers dans les deux matchs -> même part (l'ancien code écrasait le 2e match)
    assert np.isclose(p0.loc[1, "share"], p0.loc[2, "share"])
    assert pred.groupby(["game_id", "team"])["share"].sum().round(9).eq(1).all()
    assert (p0["prop_name"] == "P0").all() and set(pred["match"]) == {"AAA-BBB", "CCC-AAA"}
    cmp = L.compare_with_pinnacle(pin, pred)
    assert len(cmp) == 2 and cmp["pin_prob"].eq(0.4).all()


def test_unibet_parse_events_and_player_props(monkeypatch):
    from sportpred.live import unibet
    html = ('<script type="application/ld+json">[{"@type":"SportsEvent","startDate":"2026-10-04T01:00:00",'
            '"name":"PIT Penguins vs MON Canadiens","url":"https://www.unibet.fr/paris-hockey-sur-glace/etats-unis/nhl/'
            '3383086/pit-penguins-vs-mon-canadiens"}]</script>')
    monkeypatch.setattr(unibet, "_get", lambda url: html)
    ev = unibet.list_events()
    assert ev.iloc[0]["event_id"] == 3383086
    assert ev.iloc[0]["start"] == pd.Timestamp("2026-10-03T23:00:00Z")          # heure de Paris -> UTC
    out = lambda d, p, susp=False: {"description": d, "price": p, "suspended": susp}  # noqa: E731
    state = {"EventsDetail": {"events": [{"id": 1, "description": "A vs B", "parsedStart": "2026-10-03T23:00:00.000Z",
             "groupedMarkets": [
                 {"description": "Nombre de Buts - Joueur - Match (Hors TAB)", "markets": [
                     {"outcomes": [out("Sidney Crosby 1+", "2,90"), out("Sidney Crosby 2+", "11,00"),
                                   out("Kris Letang 1+", "9,00", susp=True)]}]},
                 {"description": "Buteurs - Tiers Temps", "markets": [{"outcomes": [out("Sidney Crosby 1+", "7,00")]}]},
                 {"description": "Nombre de Points - Joueur - Match (Hors TAB)", "markets": [
                     {"outcomes": [out("Sidney Crosby 1+", "1,60")]}]},
                 {"description": "1 N 2 - Temps Réglementaire", "markets": [{"outcomes": [out("A", "2,00")]}]}]}]}}
    p = unibet.parse_player_props(state)
    assert len(p) == 3 and set(p["stat"]) == {"Buts", "Points"}                 # suspendu et tiers-temps exclus
    g = p[(p["stat"] == "Buts") & (p["line"] == 0.5)].iloc[0]
    assert g["player"] == "Sidney Crosby" and g["odds"] == 2.9


def test_unibet_compare_value_and_settlement():
    import numpy as np
    from sportpred.live import nhl_scorers as L
    t = pd.Timestamp("2026-10-03T23:00:00Z")
    names = ["Sidney Crosby", "Evgeni Malkin", "Bryan Rust", "Erik Karlsson"]
    pred = pd.DataFrame({"event": "Pittsburgh Penguins - Montreal Canadiens", "start": t, "name": names,
                         "player_id": [1, 2, 3, 4], "model_prob": [0.40, 0.30, 0.20, 0.10], "team": "PIT",
                         "match": "PIT-MTL"})
    pin = pd.DataFrame([{"event": "Pittsburgh Penguins - Montreal Canadiens", "start": t, "league": "NHL",
                         "is_prop": True, "market": "Player Props: Sidney Crosby Total Goals", "selection": "Over",
                         "line": 0.5, "fair_prob": 0.42, "pin_margin": 0.07, "market_key": "k1"}])
    ub = pd.DataFrame({"ub_event_id": 9, "ub_event": "PIT Penguins vs MON Canadiens", "start": t + pd.Timedelta(minutes=5),
                       "stat": "Buts", "player": names, "line": 0.5, "odds": [2.50, 3.00, 6.00, 9.00]})
    cmp = L.compare_unibet(ub, pin, pred)
    c = cmp.set_index("player")
    assert c.loc["Sidney Crosby", "ref"] == "Pinnacle" and np.isclose(c.loc["Sidney Crosby", "ev"], 0.42 * 2.5 - 1)
    assert c.loc["Bryan Rust", "ref"] == "modèle" and np.isclose(c.loc["Bryan Rust", "ev"], 0.2 * 6 - 1)
    v = L.unibet_value_bets(cmp)
    # Crosby +5 % (seuil Pinnacle 3 %) et Rust +20 % (seuil modèle 10 %) ; Malkin -10 %, Karlsson -10 %
    assert set(v["player"]) == {"Sidney Crosby", "Bryan Rust"}
    assert v.set_index("player").loc["Sidney Crosby", "selection"] == "Sidney Crosby marque"
    hist = [{"stat": "Buts", "player": "Sidney Crosby", "player_id": 1, "line": 0.5, "odds": 2.5,
             "start": "2026-10-03T23:00:00+00:00"},
            {"stat": "Points", "player": "Bryan Rust", "player_id": 3, "line": 0.5, "odds": 1.8,
             "start": "2026-10-03T23:00:00+00:00"},
            {"stat": "Buts", "player": "Erik Karlsson", "player_id": 4, "line": 0.5, "odds": 9.0,
             "start": "2026-10-03T23:00:00+00:00"}]
    nhl = pd.DataFrame({"date": pd.Timestamp("2026-10-03"), "player_id": [1, 3], "name": ["Sidney Crosby", "Bryan Rust"],
                        "goals": [0, 0], "assists": [0, 2]})
    L.settle_player_props(hist, nhl, pd.Timestamp("2026-10-04T06:00Z"))
    assert hist[0]["result"] == "perdu" and hist[1]["result"] == "gagné" and hist[1]["profit_units"] == 0.8
    assert "result" not in hist[2]                                            # pas encore 3 jours
    L.settle_player_props(hist, nhl, pd.Timestamp("2026-10-08T06:00Z"))
    assert hist[2]["result"].startswith("remboursé") and hist[2]["profit_units"] == 0.0


def test_history_keeps_player_prop_fields_and_espn_skips_them():
    from sportpred.live import results as rs
    from sportpred.live.dashboard import update_history
    picks = pd.DataFrame([{"event": "A - B", "selection": "X marque", "book": "Unibet", "sport": "hockey",
                           "league": "NHL", "start": pd.Timestamp("2026-10-03T23:00Z"), "market": "Buteur — X",
                           "odds": 8.8, "fair_odds": 7.3, "ev": 0.2, "market_key": None, "source": "s",
                           "pin_selection": "Over", "player": "X", "stat": "Buts", "line": 0.5, "player_id": 7.0}])
    h = update_history([], picks, pd.DataFrame(), pd.Timestamp("2026-10-03T12:00Z"))
    assert h[0]["stat"] == "Buts" and h[0]["player_id"] == 7 and h[0]["line"] == 0.5
    h[0]["status"] = "commencé (CLV figée)"
    out = rs.settle(h, pd.Timestamp("2026-10-05T12:00Z"))
    assert "result" not in out[0]                                             # pas réglé via ESPN


def test_nhl_schedule_includes_previous_us_day(monkeypatch):
    """Après minuit UTC, les matchs du soir américain sont datés de la veille dans l'API NHL."""
    from sportpred.live import nhl_scorers as L
    asked = []
    monkeypatch.setattr(L, "schedule", lambda day: asked.append(day) or pd.DataFrame())
    monkeypatch.setattr(L, "load_model", lambda: (None, 0.98))
    pin = pd.DataFrame([{"league": "NHL", "event_id": 1, "start": pd.Timestamp("2026-10-03T01:00Z"), "home": "A",
                         "away": "B", "is_prop": False, "event": "A - B", "market": "moneyline"}])
    L.predict(pin, pd.Timestamp("2026-10-03T00:30Z"), hist=pd.DataFrame())
    assert asked and asked[0].date() == pd.Timestamp("2026-10-02").date()


def test_json_safe_and_history_market_key():
    import json
    import numpy as np
    from sportpred.live.dashboard import json_safe, update_history
    d = json_safe({"a": float("nan"), "b": [1.0, np.float64("inf"), {"c": np.int64(3)}], "e": "x"})
    assert json.dumps(d, allow_nan=False) == '{"a": null, "b": [1.0, null, {"c": 3}], "e": "x"}'
    picks = pd.DataFrame([{"event": "A - B", "selection": "X marque", "book": "Unibet", "sport": "hockey", "league": "NHL",
                           "start": pd.Timestamp("2026-10-03T23:00Z"), "market": "Buteur — X", "odds": 8.8,
                           "fair_odds": 7.3, "ev": 0.2, "market_key": np.nan, "source": "s"}])
    h = update_history([], picks, pd.DataFrame(), pd.Timestamp("2026-10-03T12:00Z"))
    assert h[0]["market_key"] is None
    json.dumps(h, allow_nan=False)


def test_nhl_api_retries_429_and_roster_fallback(monkeypatch):
    """L'API web NHL limite parfois les serveurs GitHub (429) : nouvel essai, puis repli sur
    l'historique pour la composition."""
    import requests
    from sportpred.live import nhl_scorers as L

    class Resp:
        def __init__(self, code, data=None):
            self.status_code, self._d, self.headers = code, data, {"Retry-After": "0"}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(str(self.status_code))

        def json(self):
            return self._d
    calls = []
    seq = [Resp(429), Resp(200, {"forwards": [{"id": 1, "firstName": {"default": "A"}, "lastName": {"default": "B"},
                                               "positionCode": "C"}], "defensemen": []})]
    monkeypatch.setattr(L.requests, "get", lambda url, timeout: calls.append(url) or seq.pop(0))
    monkeypatch.setattr(L.time, "sleep", lambda s: None)
    r = L.roster("BOS")
    assert len(calls) == 2 and r["name"].tolist() == ["A B"]
    monkeypatch.setattr(L.requests, "get", lambda url, timeout: Resp(429))
    assert L.roster("BOS").empty                                   # 4 échecs -> vide, sans exception
    hist = _nhl_games(10)
    fb = L.roster_from_hist("AAA", hist)
    assert set(fb["player_id"]) == {0, 1, 2}


def test_nhl_predict_survives_missing_rosters(monkeypatch):
    import numpy as np
    from sportpred.live import nhl_scorers as L
    hist = _nhl_games(30)
    now = pd.Timestamp("2025-12-15T12:00Z")
    t1 = now + pd.Timedelta(hours=10)
    sched = pd.DataFrame({"game_id": [1], "season": [20252026], "start": [t1], "home_abbr": ["AAA"],
                          "away_abbr": ["BBB"], "home_name": ["Alpha Aces"], "away_name": ["Beta Bears"]})
    monkeypatch.setattr(L, "schedule", lambda day: sched)
    monkeypatch.setattr(L, "roster", lambda abbr: pd.DataFrame(columns=["player_id", "name", "pos"]))
    monkeypatch.setattr(L.time, "sleep", lambda s: None)
    base = dict(event_id=101, start=t1, event="Alpha Aces - Beta Bears", home="Alpha Aces", away="Beta Bears",
                league="NHL", sport="hockey", is_prop=False, line=np.nan, pin_margin=0.03)
    pin = pd.DataFrame([dict(base, market="moneyline", selection="Alpha Aces", fair_prob=0.55),
                        dict(base, market="moneyline", selection="Beta Bears", fair_prob=0.45),
                        dict(base, market="total", selection="Plus", line=5.5, fair_prob=0.5),
                        dict(base, market="Player Props: P0 Total Goals", selection="Over", line=0.5,
                             fair_prob=0.4, is_prop=True)])
    pred = L.predict(pin, now, hist=hist)
    assert set(pred["player_id"]) == {0, 1, 2, 10, 11, 12}         # composition tirée de l'historique
    assert pred.loc[pred["player_id"] == 0, "prop_name"].eq("P0").all()


def test_nhl_block_compares_unibet_even_if_model_fails(monkeypatch, tmp_path):
    import numpy as np
    from sportpred.live import dashboard as D
    t = pd.Timestamp("2026-10-03T23:00Z")
    monkeypatch.setattr(D.nhl_mod, "load_hist", lambda now: (_ for _ in ()).throw(RuntimeError("429")))
    names = ["Sidney Crosby", "Evgeni Malkin", "Bryan Rust"]
    pin = pd.DataFrame([{"event": "Pittsburgh Penguins - Montreal Canadiens", "start": t, "league": "NHL",
                         "is_prop": True, "market": f"Player Props: {n} Total Goals", "selection": "Over",
                         "line": 0.5, "fair_prob": p, "pin_margin": 0.07, "market_key": f"k{i}"}
                        for i, (n, p) in enumerate(zip(names, (0.42, 0.33, 0.25)))])
    ub = pd.DataFrame({"ub_event_id": 9, "ub_event": "PIT vs MON", "start": t, "stat": "Buts", "player": names,
                       "line": 0.5, "odds": [2.60, 2.50, 3.00]})
    monkeypatch.setattr(D.unibet, "nhl_player_odds", lambda now, h: ub)
    block, vb, nhl_hist = D.nhl_block(pin, tmp_path, pd.Timestamp("2026-10-03T12:00Z"), D.DashConfig())
    assert list(vb["player"]) == ["Sidney Crosby"] and np.isclose(vb["ev"].iloc[0], 0.42 * 2.6 - 1)
    assert block["unibet"]["compared"] == 3 and nhl_hist.empty


def test_telephone_sonde_offline(monkeypatch, tmp_path):
    """Script du téléphone : lecture de l'état Winamax, matchs NHL, dépôt sur la branche dédiée."""
    import gzip
    import importlib.util
    import json
    spec = importlib.util.spec_from_file_location("collecte_fr", "telephone/collecte_fr.py")
    T = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(T)
    state = {"tournaments": {"7": {"tournamentName": "NHL"}, "8": {"tournamentName": "KHL"}},
             "matches": {"1": {"matchId": 101, "tournamentId": 7, "matchStart": 2},
                         "2": {"matchId": 102, "tournamentId": 8, "matchStart": 1},
                         "3": {"matchId": 103, "tournamentId": 7, "matchStart": 1}}}
    pages = {
        "https://www.winamax.fr/paris-sportifs/sports/4":
            "<script>var PRELOADED_STATE = " + json.dumps(state) + ";var X = 1;</script>",
        "https://www.betclic.fr/hockey-sur-glace-s13":
            '<a href="/hockey-sur-glace-sice_hockey/nhl-c83/a-b-m555">A-B</a>'
            '<a href="/hockey-sur-glace-sice_hockey/russie-khl-c1977/c-d-m777">C-D</a>'}
    asked = []

    def fake_get(url, timeout=30):
        asked.append(url)
        final = "https://m.betclic.fr/hockey-sur-glace-sice_hockey" if "betclic.fr/hockey-sur-glace-s13" in url else url
        return 200, final, pages.get(url, "<html>match</html>").encode()
    calls = []

    def fake_gh(method, path, body=None):
        calls.append((method, path, body))
        if method == "GET" and "/git/ref/heads/cotes-telephone" in path:
            return 404, {}
        if method == "GET" and "/git/ref/heads/main" in path:
            return 200, {"object": {"sha": "abc"}}
        if method == "GET":
            return 404, {}
        return 201, {}
    monkeypatch.setattr(T, "http_get", fake_get)
    monkeypatch.setattr(T, "gh", fake_gh)
    monkeypatch.setattr(T.time, "sleep", lambda s: None)
    T.sonde()
    assert T.extract_json_after(pages["https://www.winamax.fr/paris-sportifs/sports/4"], "PRELOADED_STATE") == state
    assert "https://www.winamax.fr/paris-sportifs/match/103" in asked             # NHL, le plus tôt d'abord
    assert "https://www.winamax.fr/paris-sportifs/match/102" not in asked         # KHL exclu
    assert "https://m.betclic.fr/hockey-sur-glace-sice_hockey/nhl-c83/a-b-m555" in asked       # site mobile
    assert not any("c-d-m777" in u for u in asked)                                         # KHL exclue
    assert ("POST", "/repos/Matttgic/Overstreamlit/git/refs") in [(m, p) for m, p, _ in calls]
    puts = {p.split("/contents/")[1]: b for m, p, b in calls if m == "PUT"}
    assert all(b["branch"] == "cotes-telephone" for b in puts.values())
    rep = json.loads(T.base64.b64decode(puts["sonde/rapport.json"]["content"]))
    assert rep["winamax_nhl_ids"] == ["103", "101"]
    assert gzip.decompress(T.base64.b64decode(puts["sonde/winamax_match_103.gz"]["content"])) == b"<html>match</html>"
