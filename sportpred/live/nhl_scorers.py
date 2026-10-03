"""Buteurs NHL du jour : probabilité du modèle à côté de la cote juste Pinnacle.

Pour chaque match NHL coté par Pinnacle :
1. buts attendus de chaque équipe λ = vainqueur + total Pinnacle sans marge
   (`models.nhl_scorers.team_lambdas`) ;
2. composition estimée : joueurs du dernier match de l'équipe (s'il date de moins de
   10 jours), sinon les 12 attaquants et 6 défenseurs les plus utilisés de l'effectif
   (API NHL) ; tout joueur proposé par Pinnacle en « buteur » est inclus d'office ;
3. part de chaque joueur : logit conditionnel ajusté par scripts/nhl_buteurs.py
   (data/processed/nhl_scorer_model.json) ;
4. P(marque) = 1 − exp(−λ · facteur tirs au but · part).

Le modèle est INDICATIF : il n'a pas encore été comparé à Pinnacle sur des matchs réels
(archive quotidienne en cours de constitution, voir docs/resultats/nhl_buteurs.md).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from ..data import nhl_players
from ..models import nhl_scorers as M
from .matching import match_events, norm, sim

WEB = "https://api-web.nhle.com/v1"
ROOT = Path(__file__).resolve().parents[2]
MODEL_FILE = ROOT / "data" / "processed" / "nhl_scorer_model.json"


def load_model(path: Path = MODEL_FILE) -> tuple[M.ShareParams, float]:
    d = json.loads(path.read_text(encoding="utf-8"))
    p = M.ShareParams(**d["params"])
    p.beta = np.array([d["beta"][k] for k in M.FEATURES])
    p.priors = d["priors"]
    return p, float(d["so_adj"])


def _json(url: str) -> dict:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def schedule(day: pd.Timestamp) -> pd.DataFrame:
    """Matchs de saison régulière de la semaine NHL contenant `day`."""
    rows = []
    for wk in _json(f"{WEB}/schedule/{day:%Y-%m-%d}").get("gameWeek", []):
        for g in wk.get("games", []):
            if g.get("gameType") != 2:
                continue
            row = {"game_id": int(g["id"]), "season": int(g["season"]), "start": pd.Timestamp(g["startTimeUTC"])}
            for side in ("home", "away"):
                t = g[f"{side}Team"]
                row[f"{side}_abbr"] = t["abbrev"]
                row[f"{side}_name"] = f'{t["placeName"]["default"]} {t["commonName"]["default"]}'
            rows.append(row)
    return pd.DataFrame(rows)


def roster(abbr: str) -> pd.DataFrame:
    d = _json(f"{WEB}/roster/{abbr}/current")
    rows = [{"player_id": int(x["id"]), "name": f'{x["firstName"]["default"]} {x["lastName"]["default"]}',
             "pos": x.get("positionCode", "C")}
            for grp in ("forwards", "defensemen") for x in d.get(grp, [])]
    return pd.DataFrame(rows)


def _find(name: str, cands: pd.DataFrame) -> int | None:
    """Identifiant du joueur `name` parmi `cands` (nom exact normalisé, sinon similarité ≥ 0,85
    et sans ambiguïté)."""
    if cands.empty:
        return None
    cands = cands.reset_index(drop=True)
    n = norm(name)
    exact = cands[cands["name"].map(norm) == n]
    if len(exact) == 1:
        return int(exact["player_id"].iloc[0])
    sc = cands["name"].map(lambda x: sim(name, x)).sort_values(ascending=False)
    if sc.iloc[0] >= 0.85 and (len(sc) == 1 or sc.iloc[0] - sc.iloc[1] >= 0.1):
        return int(cands.loc[sc.index[0], "player_id"])
    return None


def lineup(team: str, hist: pd.DataFrame, ros: pd.DataFrame, feat_now: pd.DataFrame,
           now: pd.Timestamp, must: set[int]) -> tuple[pd.DataFrame, str]:
    """18 joueurs de champ (player_id, pos) et la source de la composition."""
    th = hist[(hist["team"] == team) & (hist["date"] >= now.tz_localize(None).normalize() - pd.Timedelta(days=10))]
    if not th.empty:
        last = th[th["game_id"] == th.sort_values("date")["game_id"].iloc[-1]]
        lu, src = last[["player_id", "pos"]].drop_duplicates("player_id"), "dernier match"
    else:
        r = ros.merge(feat_now[["player_id", "toi_now"]], on="player_id", how="left")
        r["toi_now"] = r["toi_now"].fillna(0)
        f = r[r["pos"] != "D"].nlargest(12, "toi_now")
        d = r[r["pos"] == "D"].nlargest(6, "toi_now")
        lu, src = pd.concat([f, d])[["player_id", "pos"]], "effectif (aucun match récent)"
    missing = [i for i in must if i not in set(lu["player_id"])]
    for pid in missing:                                   # joueur coté absent : remplace le moins utilisé
        pos = ros.loc[ros["player_id"] == pid, "pos"]
        pos = pos.iloc[0] if len(pos) else "C"
        grp = lu["pos"].eq("D") if pos == "D" else ~lu["pos"].eq("D")
        cand = lu[grp & ~lu["player_id"].isin(must)].merge(feat_now[["player_id", "toi_now"]], on="player_id",
                                                           how="left").fillna({"toi_now": 0})
        if not cand.empty:
            lu = lu[lu["player_id"] != cand.nsmallest(1, "toi_now")["player_id"].iloc[0]]
        lu = pd.concat([lu, pd.DataFrame({"player_id": [pid], "pos": [pos]})])
    return lu, src


def _event_lambdas(ev: pd.DataFrame) -> tuple[float, float]:
    ml = ev[ev["market"] == "moneyline"]
    tot = ev[(ev["market"] == "total") & (ev["selection"] == "Plus")]
    if ml.empty or tot.empty:
        return np.nan, np.nan
    ph = ml.loc[ml["selection"] == ev["home"].iloc[0], "fair_prob"]
    if ph.empty:
        return np.nan, np.nan
    t = tot.iloc[(tot["fair_prob"] - 0.5).abs().argsort()].iloc[0]       # ligne principale
    return M.team_lambdas(float(ph.iloc[0]), float(t["fair_prob"]), float(t["line"]))


def seasons_for(now: pd.Timestamp, n_past: int = 2) -> list[int]:
    """Saison en cours (format 20262027) et les `n_past` précédentes."""
    y = now.year if now.month >= 9 else now.year - 1
    return [(y - k) * 10000 + y - k + 1 for k in range(n_past, -1, -1)]


def load_hist(now: pd.Timestamp, raw_dir: Path = ROOT / "data" / "raw") -> pd.DataFrame:
    """Historique joueur-match (2 saisons passées + saison en cours, rafraîchie)."""
    return nhl_players.load(raw_dir, seasons_for(now), refresh_current=True)


def predict(pin: pd.DataFrame, now: pd.Timestamp, hist: pd.DataFrame | None = None,
            raw_dir: Path = ROOT / "data" / "raw", horizon_hours: float = 36) -> pd.DataFrame:
    """Probabilité « marque au moins un but » pour les joueurs des matchs NHL cotés par Pinnacle."""
    nhl = pin[(pin["league"] == "NHL")] if not pin.empty and "league" in pin else pd.DataFrame()
    if nhl.empty:
        return pd.DataFrame()
    params, so_adj = load_model()
    sched = schedule(now)
    sched = sched[(sched["start"] > now) & (sched["start"] < now + pd.Timedelta(hours=horizon_hours))]
    if sched.empty:
        return pd.DataFrame()
    evs = nhl[~nhl["is_prop"]].drop_duplicates("event_id")[["event_id", "start", "home", "away"]]
    right = sched.rename(columns={"game_id": "event_id", "home_name": "home", "away_name": "away"})
    m = match_events(evs, right[["event_id", "start", "home", "away"]])
    if m.empty:
        return pd.DataFrame()

    cur = int(sched["season"].max())
    hist = load_hist(now, raw_dir) if hist is None else hist
    hist = hist[hist["date"] < now.tz_localize(None).normalize()]
    # temps de jeu « actuel » de chaque joueur (pour choisir la composition à défaut de match récent)
    base = M.add_history(hist, params)
    last = base.sort_values("date").groupby("player_id").tail(1)
    feat_now = pd.DataFrame({"player_id": last["player_id"],
                             "toi_now": 0.6 * last["toi"] + 0.4 * last["toi_exp"].fillna(last["toi"])})

    goal_props = nhl[nhl["is_prop"] & nhl["market"].str.endswith("Total Goals") & (nhl["line"] == 0.5)]
    synth, meta, ros_names = [], [], []
    for r in m.itertuples():
        g = sched[sched["game_id"] == r.right_id].iloc[0]
        ev = nhl[nhl["event_id"] == r.left_id]
        lam_h, lam_a = _event_lambdas(ev)
        if not np.isfinite(lam_h):
            continue
        event = ev["event"].iloc[0]
        names = goal_props.loc[goal_props["event"] == event, "market"] \
            .str.replace("Player Props: ", "", regex=False).str.replace(" Total Goals", "", regex=False).unique()
        rosters = {s: roster(g[f"{s}_abbr"]) for s in ("home", "away")}
        both = pd.concat([rosters["home"].assign(side="home"), rosters["away"].assign(side="away")],
                         ignore_index=True)
        ros_names.append(both[["player_id", "name"]])
        found = {nm: _find(nm, both) for nm in names}
        for side, lam in (("home", lam_h), ("away", lam_a)):
            team = g[f"{side}_abbr"]
            must = {pid for pid in found.values()
                    if pid is not None and pid in set(rosters[side]["player_id"])}
            lu, src = lineup(team, hist, rosters[side], feat_now, now, must)
            for pid, pos in zip(lu["player_id"], lu["pos"]):
                synth.append({"game_id": int(g["game_id"]), "date": g["start"].tz_localize(None).normalize(),
                              "season": cur, "team": team, "opp": g["away_abbr" if side == "home" else "home_abbr"],
                              "home": side == "home", "player_id": int(pid), "pos": pos, "goals": 0,
                              "pp_goals": 0, "ot_goals": 0, "shots": 0, "toi": 0.0, "pp_toi": 0.0, "sh_toi": 0.0})
            meta.append({"game_id": int(g["game_id"]), "team": team, "lam": lam, "lineup": src,
                         "event": event, "start": g["start"]})
        for nm, pid in found.items():
            meta.append({"game_id": int(g["game_id"]), "prop_name": nm, "player_id": pid})
    if not synth:
        return pd.DataFrame()
    sy = pd.DataFrame(synth)
    # caractéristiques « à aujourd'hui », une fois par joueur : un joueur qui a deux matchs
    # dans la fenêtre (back-to-back) ne doit pas voir son premier match fictif (0 minute)
    one = sy.drop_duplicates("player_id").assign(name="")
    allp = pd.concat([hist, one], ignore_index=True)
    allp["_synth"] = np.r_[np.zeros(len(hist), bool), np.ones(len(one), bool)]
    fe = M.features(M.add_history(allp, params), params)
    fe = fe.loc[fe["_synth"], ["player_id", "n_prev", *M.FEATURES]]
    f = sy.merge(fe, on="player_id", how="left")
    f["share"] = M.predict_shares(f, params.beta)
    mt = pd.DataFrame([x for x in meta if "lam" in x])
    f = f.merge(mt, on=["game_id", "team"], how="left")
    f["model_prob"] = M.p_score(f["lam"] * so_adj, f["share"])
    f["match"] = np.where(f["home"], f["team"] + "-" + f["opp"], f["opp"] + "-" + f["team"])
    names = pd.concat([hist[["player_id", "name"]], *ros_names]).drop_duplicates("player_id", keep="last")
    f = f.drop(columns="name", errors="ignore").merge(names, on="player_id", how="left")
    props = pd.DataFrame([x for x in meta if "prop_name" in x])
    if not props.empty:
        f = f.merge(props.dropna(subset=["player_id"]).astype({"player_id": int}),
                    on=["game_id", "player_id"], how="left")
    else:
        f["prop_name"] = np.nan
    return f[["event", "match", "start", "game_id", "team", "player_id", "name", "prop_name", "pos", "lineup",
              "lam", "share", "model_prob"]].sort_values(["start", "event", "model_prob"], ascending=[True, True, False])


def compare_with_pinnacle(pin: pd.DataFrame, pred: pd.DataFrame) -> pd.DataFrame:
    """Joueurs cotés « buteur » par Pinnacle : P Pinnacle (sans marge) vs P modèle."""
    if pred.empty or pin.empty:
        return pd.DataFrame()
    gp = pin[pin["is_prop"] & pin["market"].str.endswith("Total Goals") & (pin["line"] == 0.5)
             & (pin["selection"] == "Over")]
    gp = gp.assign(prop_name=gp["market"].str.replace("Player Props: ", "", regex=False)
                   .str.replace(" Total Goals", "", regex=False))
    out = gp[["event", "prop_name", "fair_prob", "fair_odds", "pin_margin"]].merge(
        pred.dropna(subset=["prop_name"])[["event", "prop_name", "team", "lam", "share", "model_prob", "lineup"]],
        on=["event", "prop_name"], how="inner")
    out["ecart"] = out["model_prob"] - out["fair_prob"]
    return out.rename(columns={"fair_prob": "pin_prob", "fair_odds": "pin_fair_odds"})


def evaluate_archive(arch_dir: Path, hist: pd.DataFrame) -> dict:
    """Bilan des prédictions archivées (dernier relevé avant le match), joueurs ayant joué.

    Compare la log-loss du modèle à celle de Pinnacle (sans marge) sur les joueurs cotés
    par les deux, et à un mélange 50/50 des logits : si le mélange ou le modèle fait mieux
    que Pinnacle sur un échantillon suffisant, le modèle apporte de l'information.
    """
    files = sorted(Path(arch_dir).glob("nhl_buteurs_*.csv.gz"))
    if not files or hist.empty:
        return {}
    a = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    a["captured_at"] = pd.to_datetime(a["captured_at"], utc=True)
    a["start"] = pd.to_datetime(a["start"], utc=True)
    a = a[a["captured_at"] < a["start"]].sort_values("captured_at")
    a = a.groupby(["game_id", "player_id"], as_index=False).tail(1)
    m = a.merge(hist[["game_id", "player_id", "goals"]], on=["game_id", "player_id"], how="inner")
    if m.empty:
        return {"n_model": 0}

    def ll(y, p):
        p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
        return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())

    y = (m["goals"] > 0).to_numpy(float)
    out = {"n_model": int(len(m)), "n_games": int(m["game_id"].nunique()),
           "ll_model": round(ll(y, m["model_prob"]), 4),
           "pred_mean": round(float(m["model_prob"].mean()), 4), "obs_mean": round(float(y.mean()), 4)}
    b = m.dropna(subset=["pin_prob"])
    if len(b):
        yb = (b["goals"] > 0).to_numpy(float)
        lg = lambda p: np.log(p / (1 - p))  # noqa: E731
        blend = 1 / (1 + np.exp(-(0.5 * lg(b["model_prob"].clip(1e-4, 1 - 1e-4))
                                  + 0.5 * lg(b["pin_prob"].clip(1e-4, 1 - 1e-4)))))
        out.update({"n_both": int(len(b)), "ll_model_both": round(ll(yb, b["model_prob"]), 4),
                    "ll_pinnacle": round(ll(yb, b["pin_prob"]), 4), "ll_blend": round(ll(yb, blend), 4),
                    "obs_mean_both": round(float(yb.mean()), 4)})
    return out
