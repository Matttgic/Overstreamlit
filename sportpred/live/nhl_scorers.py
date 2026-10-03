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
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.stats import poisson

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


def _json(url: str, attempts: int = 4) -> dict:
    """GET JSON avec nouvelles tentatives sur 429 / 5xx (les serveurs GitHub sont partagés et
    l'API web de la NHL les limite parfois) ; respecte l'en-tête Retry-After (plafonné à 15 s)."""
    for i in range(attempts):
        r = requests.get(url, timeout=30)
        if r.status_code == 429 or r.status_code >= 500:
            if i == attempts - 1:
                r.raise_for_status()
            try:
                wait = float(r.headers.get("Retry-After", 2 ** (i + 1)))
            except ValueError:
                wait = 2 ** (i + 1)
            time.sleep(min(wait, 15))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(url)


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
    """Effectif actuel (attaquants, défenseurs) ; tableau vide si l'API reste inaccessible."""
    try:
        d = _json(f"{WEB}/roster/{abbr}/current")
    except (requests.RequestException, RuntimeError, ValueError) as e:
        print(f"effectif {abbr} indisponible ({e}) : composition tirée de l'historique")
        return pd.DataFrame(columns=["player_id", "name", "pos"])
    rows = [{"player_id": int(x["id"]), "name": f'{x["firstName"]["default"]} {x["lastName"]["default"]}',
             "pos": x.get("positionCode", "C")}
            for grp in ("forwards", "defensemen") for x in d.get(grp, [])]
    return pd.DataFrame(rows)


def roster_from_hist(team: str, hist: pd.DataFrame, days: int = 400) -> pd.DataFrame:
    """Effectif de repli : joueurs dont le dernier match (moins de `days` jours) était avec `team`."""
    if hist.empty:
        return pd.DataFrame(columns=["player_id", "name", "pos"])
    recent = hist[hist["date"] >= hist["date"].max() - pd.Timedelta(days=days)]
    last = recent.sort_values("date").groupby("player_id").tail(1)
    return last.loc[last["team"] == team, ["player_id", "name", "pos"]].reset_index(drop=True)


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
    sched = schedule(now - pd.Timedelta(days=1))      # la veille : matchs du soir américain (après minuit UTC)
    if sched.empty:                                    # pause, présaison : aucun match de saison régulière
        return pd.DataFrame()
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
        rosters = {}
        for side in ("home", "away"):
            ros = roster(g[f"{side}_abbr"])
            rosters[side] = ros if not ros.empty else roster_from_hist(g[f"{side}_abbr"], hist)
            time.sleep(0.3)
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
    right = pred.dropna(subset=["prop_name"]) if "prop_name" in pred else pred.iloc[0:0]
    if gp.empty or right.empty:            # aucun buteur Pinnacle apparié (props pas encore publiées)
        return pd.DataFrame()
    right = right.assign(prop_name=right["prop_name"].astype(str))
    out = gp[["event", "prop_name", "fair_prob", "fair_odds", "pin_margin"]].merge(
        right[["event", "prop_name", "team", "lam", "share", "model_prob", "lineup"]],
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


# ------------------------------------------------------------- comparaison avec Unibet.fr
PIN_STATS = {"Total Goals": "Buts", "Total Points": "Points", "Total Assists": "Passes décisives"}
MODEL_MIN_EV = 0.10        # marge exigée quand la cote juste vient du modèle (pas de Pinnacle)
# Prolongations NHL (saisons 2018-19 -> 2025-26, 9 781 matchs) : 67,2 % des prolongations se
# terminent par un but (le reste aux tirs au but) ; 2,46 % des buts de joueurs sont marqués en
# prolongation. Sert à convertir une cote juste « prolongation comprise » (Pinnacle, modèle)
# en cote « temps réglementaire » (paris joueurs Winamax).
P_OT_GOAL = 0.672
OT_GOAL_SHARE = 0.0246


def reg_ratio(lam_home: float, lam_away: float) -> float:
    """Part des buts attendus d'une équipe marqués dans le temps réglementaire.

    Buts de prolongation attendus d'une équipe = P(égalité après 60 min) × P(but en prolongation)
    × λ_équipe / (λ_dom + λ_ext) ; le rapport est le même pour les deux équipes."""
    if not (np.isfinite(lam_home) and np.isfinite(lam_away)) or lam_home + lam_away <= 0:
        return 1 - OT_GOAL_SHARE
    ks = np.arange(0, 25)
    p_tie = float((poisson.pmf(ks, lam_home) * poisson.pmf(ks, lam_away)).sum())
    return 1 - P_OT_GOAL * p_tie / (lam_home + lam_away)


def to_regulation(p_full, ratio):
    """P(au moins un) prolongation comprise -> temps réglementaire (Poisson : μ_rég = μ × ratio)."""
    return 1 - (1 - np.asarray(p_full, float)) ** np.asarray(ratio, float)


def pinnacle_player_props(pin: pd.DataFrame) -> pd.DataFrame:
    """Props joueurs NHL Pinnacle (côté « Over ») : event, player, stat, line, fair_prob."""
    if pin.empty or "league" not in pin:
        return pd.DataFrame()
    p = pin[(pin["league"] == "NHL") & pin["is_prop"] & (pin["selection"] == "Over")
            & pin["market"].str.startswith("Player Props:")].copy()
    rows = []
    for r in p.itertuples():
        d = r.market.replace("Player Props: ", "")
        for en, fr in PIN_STATS.items():
            if d.endswith(" " + en):
                rows.append({"event": r.event, "player": d[: -len(en) - 1], "stat": fr, "line": float(r.line),
                             "pin_prob": float(r.fair_prob), "pin_margin": float(r.pin_margin),
                             "market_key": r.market_key})
    return pd.DataFrame(rows)


def drop_mixed_markets(ub: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Écarte les cotes d'un opérateur pour un match quand un même joueur a deux cotes
    différentes sur la même ligne : la lecture a mélangé plusieurs marchés (03/10/2026,
    Betclic avant-match : « Buteur » lu avec 8,00 et 50,00 pour Tage Thompson, Winamax 2,25).
    Doublons à cote identique : simplement dédoublonnés.

    Renvoie (cotes conservées, {opérateur: nombre de matchs écartés})."""
    if ub is None or ub.empty:
        return ub, {}
    ub = ub.assign(book=ub["book"].fillna("Unibet") if "book" in ub else "Unibet",
                   ub_event_id=ub["ub_event_id"].astype(str))
    k = ub["player"].map(norm)
    ub = ub.assign(_k=k).drop_duplicates(["book", "ub_event_id", "_k", "stat", "line", "odds"])
    n = ub.groupby(["book", "ub_event_id", "_k", "stat", "line"])["odds"].transform("size")
    bad = ub.loc[n > 1, ["book", "ub_event_id"]].drop_duplicates()
    if bad.empty:
        return ub.drop(columns="_k").reset_index(drop=True), {}
    drop = ub.set_index(["book", "ub_event_id"]).index.isin(bad.set_index(["book", "ub_event_id"]).index)
    return ub[~drop].drop(columns="_k").reset_index(drop=True), bad["book"].value_counts().to_dict()


def compare_book_props(ub: pd.DataFrame, pin: pd.DataFrame, pred: pd.DataFrame, cfg_min_ev: float = 0.03,
                       max_hours: float = 1.5) -> pd.DataFrame:
    """Chaque cote joueur d'un opérateur (Unibet, Winamax, Betclic : colonne `book`) face à sa
    cote juste : Pinnacle s'il cote ce joueur et cette ligne (seuil `cfg_min_ev`), sinon le
    modèle pour « buteur » (seuil MODEL_MIN_EV). Pari « hors prolongation » (`reg_only`,
    Winamax) : cote juste convertie en temps réglementaire (`reg_ratio`).

    Appariement des matchs : même heure (± `max_hours`) et le plus de joueurs en commun
    (noms de l'opérateur ↔ composition du modèle et props Pinnacle). Les noms d'équipe des
    opérateurs (« VEG GKnights », « CLB BJackets »…) ne sont pas utilisés.
    """
    if ub is None or ub.empty:
        return pd.DataFrame()
    ub = ub.assign(book=ub["book"].fillna("Unibet") if "book" in ub else "Unibet",
                   reg_only=ub["reg_only"].astype("boolean").fillna(False).astype(bool) if "reg_only" in ub else False,
                   ub_event_id=ub["ub_event_id"].astype(str))    # Unibet : entiers ; téléphone : texte
    ratios = {}
    if pred is not None and not pred.empty and "lam" in pred:
        for ev, g in pred.groupby("event"):
            lams = g.drop_duplicates("team")["lam"].tolist()
            if len(lams) == 2:
                ratios[ev] = reg_ratio(lams[0], lams[1])
    pp = pinnacle_player_props(pin)
    roster = []
    if pred is not None and not pred.empty:
        roster.append(pred[["event", "start", "name", "player_id", "model_prob", "team", "match"]]
                      .rename(columns={"name": "player"}))
    if not pp.empty:
        st = pin.drop_duplicates("event").set_index("event")["start"]
        roster.append(pp.assign(start=pp["event"].map(st))[["event", "start", "player"]])
    if not roster:
        return pd.DataFrame()
    ro = pd.concat(roster, ignore_index=True)
    ro["k"] = ro["player"].map(norm)
    ro["start"] = pd.to_datetime(ro["start"], utc=True)
    ub["k"] = ub["player"].map(norm)
    out = []
    for ub_id, g in ub.groupby("ub_event_id"):
        t = pd.Timestamp(g["start"].iloc[0])
        t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
        cand = ro[(ro["start"] - t).abs() <= pd.Timedelta(hours=max_hours)]
        if cand.empty:
            continue
        common = cand[cand["k"].isin(set(g["k"]))].groupby("event")["k"].nunique()
        if common.empty or common.max() < 3:
            continue
        event = common.idxmax()
        pr = ro[(ro["event"] == event) & ro["model_prob"].notna()].drop_duplicates("k") if "model_prob" in ro else ro.iloc[0:0]
        x = g.merge(pr[["k", "player_id", "model_prob", "team", "match"]], on="k", how="left") if not pr.empty \
            else g.assign(player_id=np.nan, model_prob=np.nan, team=None, match=None)
        pe = pp[pp["event"] == event].assign(k=lambda d: d["player"].map(norm)) if not pp.empty else pp
        if not pe.empty:
            x = x.merge(pe[["k", "stat", "line", "pin_prob", "pin_margin", "market_key"]], on=["k", "stat", "line"],
                        how="left")
        else:
            x = x.assign(pin_prob=np.nan, pin_margin=np.nan, market_key=None)
        x["event"] = event
        x["start"] = t
        use_model = x["pin_prob"].isna() & (x["stat"] == "Buts") & (x["line"] == 0.5)
        x["ref"] = np.where(x["pin_prob"].notna(), "Pinnacle", np.where(use_model & x["model_prob"].notna(), "modèle", None))
        x["fair_prob"] = x["pin_prob"].where(x["pin_prob"].notna(), x["model_prob"].where(use_model))
        x = x[x["fair_prob"].notna()].copy()
        ratio = ratios.get(event, 1 - OT_GOAL_SHARE)
        x["fair_prob"] = np.where(x["reg_only"], to_regulation(x["fair_prob"], ratio), x["fair_prob"])
        x["ev"] = x["fair_prob"] * x["odds"] - 1
        x["threshold"] = np.where(x["ref"] == "Pinnacle", cfg_min_ev, MODEL_MIN_EV)
        out.append(x)
    if not out:
        return pd.DataFrame()
    res = pd.concat(out, ignore_index=True)
    return res.drop(columns="k").sort_values(["start", "event", "ev"], ascending=[True, True, False])


compare_unibet = compare_book_props


def drop_implausible(cmp: pd.DataFrame, max_median_ev: float = 0.05, min_rows: int = 5) -> tuple[pd.DataFrame, dict]:
    """Écarte les cotes d'un opérateur pour un match quand elles sont, en médiane, au-dessus de
    la cote juste : impossible pour un vrai marché (marge des opérateurs : écart médian −10 à
    −20 %), donc mauvais marché lu. Seulement à partir de `min_rows` cotes comparées.

    Renvoie (comparaison conservée, {opérateur: nombre de matchs écartés})."""
    if cmp is None or cmp.empty:
        return cmp, {}
    g = cmp.groupby(["book", "ub_event_id"])["ev"]
    bad = (g.transform("size") >= min_rows) & (g.transform("median") > max_median_ev)
    if not bad.any():
        return cmp, {}
    rej = cmp.loc[bad].drop_duplicates(["book", "ub_event_id"])["book"].value_counts().to_dict()
    return cmp[~bad], rej


def book_value_bets(cmp: pd.DataFrame, max_odds: float = 10.0, min_odds: float = 1.15,
                      max_ev: float = 0.30, max_pin_margin: float = 0.10) -> pd.DataFrame:
    """Paris joueurs des opérateurs au-dessus du seuil, au format des « paris à jouer ».
    Marge Pinnacle tolérée un peu plus haute que pour les matchs (props ≈ 7-9 %)."""
    if cmp is None or cmp.empty:
        return pd.DataFrame()
    v = cmp[(cmp["ev"] >= cmp["threshold"]) & (cmp["ev"] <= max_ev) & (cmp["odds"] <= max_odds)
            & (cmp["odds"] >= min_odds) & ~(cmp["pin_margin"] > max_pin_margin)].copy()
    if v.empty:
        return v
    v["pin_margin"] = np.nan                  # déjà contrôlée ici (seuil propre aux props)
    label = {"Buts": "Buteur", "Points": "Points", "Passes décisives": "Passes décisives"}
    v["market"] = [f"{label[s]} — {p}" for s, p in zip(v["stat"], v["player"])]
    if "book" not in v:
        v["book"] = "Unibet"
    if "reg_only" not in v:
        v["reg_only"] = False
    v["selection"] = [(f"{p} marque" if (s == "Buts" and l == 0.5) else f"{p} : {int(l + 0.5)}+ {label[s].lower()}")
                      + (" (60 min, hors prolongation)" if r else "")
                      for p, s, l, r in zip(v["player"], v["stat"], v["line"], v["reg_only"])]
    v["fair_odds"] = (1 / v["fair_prob"]).round(3)
    v["pin_selection"] = "Over"
    v["source"] = [f"Pinnacle vs {b} (joueurs)" if r == "Pinnacle" else f"Modèle vs {b} (buteurs)"
                   for b, r in zip(v["book"], v["ref"])]
    v = v.assign(sport="hockey", league="NHL")
    return v[["sport", "league", "start", "event", "market", "selection", "book", "odds", "fair_odds", "fair_prob",
              "ev", "pin_margin", "market_key", "pin_selection", "source", "player", "stat", "line", "player_id",
              "reg_only"]]


unibet_value_bets = book_value_bets


def settle_player_props(hist: list[dict], nhl: pd.DataFrame, now: pd.Timestamp) -> list[dict]:
    """Règle les paris joueurs (champ « stat ») avec les feuilles de match NHL.

    Joueur trouvé : gagné si sa stat dépasse la ligne. Joueur connu (player_id) absent d'un
    match que son équipe a joué : « remboursé (n'a pas joué) », comme chez les opérateurs.
    """
    if nhl is None or nhl.empty:
        return hist
    nhl = nhl.assign(k=nhl["name"].map(norm))
    for h in hist:
        if not h.get("stat") or h.get("result"):
            continue
        start = pd.Timestamp(h["start"])
        start = start.tz_localize("UTC") if start.tzinfo is None else start
        if now < start + pd.Timedelta(hours=4):
            continue
        local = start.tz_convert("America/New_York").tz_localize(None).normalize()   # date NHL du match
        day = nhl[(nhl["date"] >= local - pd.Timedelta(days=1)) & (nhl["date"] <= local + pd.Timedelta(days=1))]
        pid = h.get("player_id")
        rows = day[day["player_id"] == int(pid)] if pid not in (None, "") and pid == pid else day.iloc[0:0]
        if rows.empty:
            rows = day[day["k"] == norm(h.get("player", ""))]
        if len(rows) == 1:
            r = rows.iloc[0]
            goals = r["goals"] - (r.get("ot_goals", 0) if h.get("reg_only") else 0)   # Winamax : 60 min
            val = {"Buts": goals, "Points": goals + r.get("assists", 0),
                   "Passes décisives": r.get("assists", 0)}.get(h["stat"])
            won = float(val) > float(h["line"])
            h["result"] = "gagné" if won else "perdu"
            h["score"] = f"{int(val)} ({h['stat'].lower()})"
            h["profit_units"] = round(h["odds"] - 1, 3) if won else -1.0
            h["status"] = "réglé"
        elif now > start + pd.Timedelta(days=3):
            h["result"] = "remboursé (n'a pas joué)" if pid == pid and pid not in (None, "") else \
                "non réglé (joueur introuvable)"
            if h["result"].startswith("remboursé"):
                h["profit_units"], h["status"] = 0.0, "réglé"
    return hist
