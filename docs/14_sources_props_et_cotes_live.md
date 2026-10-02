# Sources gratuites — cotes live/pré-match & marchés joueurs (props)

Recherche effectuée le 2026-10-02 (UTC) depuis un conteneur Linux (IP datacenter, via proxy HTTPS).
Codes HTTP = résultat réel de `curl -sL -o /dev/null -w '%{http_code}'` depuis ce conteneur.
Fichiers associés : `live_helpers.py` (fonctions testées), `verified_urls2.json` (URLs testées + codes), `samples/` (échantillons).


## ★ Synthèse (TL;DR)

| Besoin | Source gratuite recommandée (testée 02/10/2026) | Auth |
|---|---|---|
| Cotes sharp pré-match/live NBA, NHL, NFL, MLB, foot, tennis ATP/WTA | **Pinnacle guest API** (`guest.api.arcadia.pinnacle.com/0.1`) | aucune |
| Props joueurs NBA (points, rebonds, passes, 3PM, PRA) | **Pinnacle** (O/U 2 voies → proba sans marge ; format vérifié sur WNBA) + **ESPN propBets** (DraftKings) | aucune |
| Props NHL (buteur = `Goals` O/U 0.5, tirs, points, passes, arrêts) | **Pinnacle** (publiées l'après-midi du jour de match) + **ESPN propBets** (Anytime Goalscorer DraftKings) + **Kambi `ub`** ("Marque", tirs cadrés) | aucune |
| Buteur foot (Ligue 1, EPL...) | **Kambi `ub`** ("To Score", tirs cadrés, passes — règlement Opta) ; Pinnacle : non (seulement Top Goalscorer saison) | aucune |
| Prix des bookmakers FR (Winamax, Betclic, Unibet FR, PMU, NetBet) | **The Odds API** région `fr` (ML/totaux seulement, pas de props FR) | clé gratuite 500 crédits/mois |
| Stats NHL (modèle buteur) | **api-web.nhle.com** (game logs, boxscores) + **MoneyPuck** CSV (xG, match par match) + **DailyFaceoff** (gardiens partants) | aucune |
| Stats NBA | **bucket S3 NBA** (`nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/...` : boxscores, calendrier) + **ESPN gamelog** ; cdn.nba.com/stats.nba.com bloqués | aucune |
| Blessures NBA | **ESPN injuries** JSON + PDF officiel NBA (Referer requis) | aucune |
| Stats foot joueurs | **Understat** AJAX JSON (xG, tirs, minutes par match) + ESPN compos | aucune |
| Historique de cotes de props (backtest) | **Kalshi** (NHL buteur 38k marchés depuis 22/11/2025, NBA points 23,5k depuis 19/11/2025, EPL buteur 7,5k depuis 02/12/2025, prix horaires) ; sinon **archiver soi-même** Pinnacle/ESPN/Kambi dès maintenant | aucune |
| Closing lines marchés principaux (backtest) | **ESPN core `odds`** (DraftKings open/close conservés après match) | aucune |

Points d'attention : aucune source gratuite d'historique de cotes **bookmaker** pour props NBA/NHL/foot (The Odds API historique = payant ;
ESPN propBets → 404 après match ; Kaggle/HF : seulement NFL/MLB). Over/Under ESPN non étiquetés (1er = Over).

## 0. Tableau de reachabilité initial (2026-10-02 ~12:40 UTC)

| Code | URL |
|---|---|
| 200 | https://guest.api.arcadia.pinnacle.com/0.1/sports |
| 200 | https://guest.api.arcadia.pinnacle.com/0.1/sports/4/leagues?all=false |
| 401 | https://api.the-odds-api.com/v4/sports (sans clé → joignable) |
| 000 (timeout, à re-tester) | https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard |
| 200 | https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events |
| 400 | https://eu-offering-api.kambicdn.com/offering/v2018/ubfr/listView/football.json (paramètres à ajuster) |
| 403 | https://www.betclic.fr/ , https://www.winamax.fr/ |
| 200 | https://api-web.nhle.com/v1/schedule/2026-10-07 |
| 200 | https://moneypuck.com/moneypuck/playerData/seasonSummary/2024/regular/skaters.csv |
| 403 | https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json (sans headers) |
| 000 | https://stats.nba.com/stats/... (timeout, sans headers) |
| 401 | https://api.balldontlie.io/v1/players (clé requise) |
| 200 | https://www.basketball-reference.com/ |
| 200 | https://understat.com/league/EPL/2025 |
| 403 | https://v3.football.api-sports.io/status (sans clé) |
| 200 | https://api.football-data.org/v4/competitions |
| 403 | Betfair exchange readonly (www.betfair.com / ero.betfair.com) |


---
## A1. Pinnacle — API "guest" (arcadia) ✅ FONCTIONNE (meilleure source gratuite de cotes "sharp" + props US)

- **Base** : `https://guest.api.arcadia.pinnacle.com/0.1` — testé 200 le 2026-10-02.
- **Auth** : aucune nécessaire aujourd'hui (200 sans header). La clé publique du front est publiée dans
  `https://www.pinnacle.com/config/app.json` → champ `api.haywire.apiKey` = `CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R`
  (header `X-API-Key`, testé 200 aussi). Le helper l'envoie par prudence + `Referer: https://www.pinnacle.com/`.
- **Endpoints testés (tous 200)** :
  | Endpoint | Contenu |
  |---|---|
  | `/sports` | 63 sports (id, name, matchupCount, primaryMarketType) |
  | `/sports/{sportId}/leagues?all=false` | ligues actives (id, name, group, matchupCount) |
  | `/leagues/{leagueId}/matchups` | matchs + "specials" (props, futures) |
  | `/leagues/{leagueId}/markets/straight` | toutes les cotes de la ligue (y.c. alternatives & specials) |
  | `/sports/{sportId}/matchups?withSpecials=true` | tous les matchs d'un sport (⚠️ foot = 24 Mo) |
  | `/sports/{sportId}/markets/straight?primaryOnly=false&withSpecials=true` | cotes d'un sport (basket = 3,7 Mo) |
  | `/matchups/{matchupId}` , `/matchups/{id}/markets/straight` | un match |
  | `/matchups/{id}/related` , `/matchups/{id}/markets/related/straight` | le match + tous ses specials/props |
- **IDs utiles (vérifiés)** : sports baseball=3, basketball=4, football US=15, hockey=19, soccer=29, tennis=33.
  Ligues : NBA=487, WNBA=578, Euroleague=382, Pro A=414, Pro B=415, NHL=1456, AHL=1264, KHL=1484, NFL=889, NCAAF=880,
  MLB=246, Premier League=1980, Ligue 1=2036, LaLiga=2196, Serie A=2436, Bundesliga=1842, UCL=2627, UEL=2630, UECL=214101.
  Tennis : une ligue par tournoi+tour (ex. `3844 WTA Beijing - R2`, `3372 ATP Beijing - R16`, `3547 ATP Tokyo - R16`) → filtrer par nom.
- **Structure** :
  - `matchups[]` : `type` = `matchup` (match) ou `special` ; `participants[]` (`alignment` home/away/neutral, `id`, `name`) ;
    `special.category` (`Player Props`, `Game Props`, `Team Props`, `Futures`, `Goalscorer`, `Exact Scores`, `Regular Season Wins`...),
    `special.description` (ex. *"Bhayshul Tuten Total Receiving Yards"*, *"Arike Ogunbowale Total Points"*), `units` (stat : `Points`,
    `Rebounds`, `Assists`, `Threes Made`, `Pts & Rebs & Asts`, `Receiving Yards`, `Home Runs`, `Strikeouts`...), `parentId` → id du match parent
    (+ objet `parent` avec les équipes). Tennis : enfant `type=matchup` avec `parentId` et `units="Games"` (handicap/total jeux).
  - `markets/straight[]` : `matchupId`, `type` (`moneyline`/`spread`/`total`/`team_total`), `period` (0 = match ; 1 = 1re MT/1re période ;
    hockey 1/2/3 = périodes, **6 = temps réglementaire** avec ML 3 voies ; NFL 3 = 1er quart-temps), `isAlternate`, `key` (ex. `s;0;ou`),
    `limits` (`maxRiskStake`), `prices[]` = `{designation: home/away/draw/over/under | participantId, points, price}` — **prix en cote américaine**.
  - Props joueur = special `Over`/`Under` avec marché `total` (`points` = la ligne).
- **Couverture observée le 2026-10-02** (NBA : pré-saison, saison régulière le 20/10 ; NHL : saison régulière depuis le 29/09) :
  | Ligue | Matchs | Props joueurs observées |
  |---|---|---|
  | NFL (889) | 15 matchs | ✅ 575 props (Receiving Yards, Receptions, Rushing Yards, Rush Attempts, Passing Yards, TD Passes, Interceptions, Field Goals...) |
  | MLB (246) | 3 matchs (playoffs) | ✅ 92 props (Home Runs, Bases, Strikeouts, Pitching Outs) |
  | WNBA (578) | finales | ✅ 38 props (Points, Rebounds, Assists, Threes Made, Pts & Rebs & Asts) → **même format attendu pour la NBA** |
  | NBA (487) | 12 matchs (20-22/10) + futures (Regular Season Wins, Playoffs) | pas encore (ouvertes ~J-1/J0 en saison) |
  | NHL (1456) | 5 matchs (saison régulière) | ✅ **apparues le jour du match** (absentes à 12h40 UTC, présentes à 17h20 UTC pour des matchs à 22h30) : 215 lignes O/U — `Goals` (O/U 0.5 = **buteur avec cote Over ET Under → proba sans marge**), `Points`, `Assists`, `Shots On Goal`, `Saves` (gardiens). Description `"Alex DeBrincat Total Goals"` ; marge ~7 %. Échantillon `samples/pinnacle_NHL_player_props_20261002.csv` |
  | Premier League / Ligue 1 | 20 / 18 matchs (10-19/10) | ❌ pas de props buteur par match ; seulement "Tournament Top Goalscorer" (category `Goalscorer`, futures) ; `Team Props` sur ~8 000 specials foot |
  | Tennis ATP/WTA | Beijing, Tokyo | ML, handicap sets, total/handicap jeux (enfant `Games`), pas de props joueur |
- **Limites/ToS** : API non documentée destinée au site web ; pas de clé personnelle, pas de SLA. Les CGU Pinnacle interdisent
  l'usage automatisé abusif → rester raisonnable (1 appel/ligue toutes les quelques minutes), cache local. Pas d'historique
  (snapshot instantané uniquement) → **pour backtester il faut archiver soi-même** (cron quotidien → CSV/Parquet).
- **Utilité** : (a) dashboard quotidien ★★★★★ (cotes sharp, référence "fair odds" pour comparer Winamax/Betclic ; props NBA/NFL/MLB) ;
  (b) backtest props ★★ (seulement si on archive soi-même dès maintenant).
- **Helpers testés** : `pinnacle_sports()`, `pinnacle_leagues(sport_id)`, `pinnacle_markets(league, include_alternates, include_specials, periods)`,
  `pinnacle_player_props(league)` (format large Over/Under + proba sans marge), `pinnacle_tennis()`, `devig_two_way(df)`.
  Échantillons : `samples/pinnacle_{NBA,NHL,NFL,WNBA,EPL,LIGUE1}_20261002.csv`, `samples/pinnacle_tennis_20261002.csv`.
  Colonnes : `league_id, league, matchup_id, parent_id, start_time, home, away, kind, category, description, player, units, market, period,
  is_alt, side, selection, line, price_american, price_decimal, max_stake, status, is_live, fetched_at`.

---
## A2. The Odds API (the-odds-api.com) — clé GRATUITE (500 crédits/mois) ✅ joignable

- **Test sans clé** (2026-10-02) : `https://api.the-odds-api.com/v4/sports` → **401** `{"error_code":"MISSING_KEY"}` ; clé invalide → 401 `INVALID_KEY`.
  → le serveur est joignable depuis le conteneur ; non testé avec une vraie clé (pas de clé fournie).
- **Plans** (page officielle https://the-odds-api.com/#get-access, lue le 2026-10-02) : **Starter gratuit = 500 crédits/mois** ;
  20K = 30 $/mois ; 100K = 59 $ ; 5M = 119 $ ; 15M = 249 $.
  ⚠️ **Historique = plans payants uniquement** ("Historical data is only available on paid usage plans" — https://the-odds-api.com/historical-odds-data/) :
  marchés principaux depuis le 06/06/2020 (snapshots 10 min, puis 5 min depuis 09/2022) ; **props joueurs depuis le 03/05/2023** (5 min).
- **Coût en crédits** (guide v4 https://the-odds-api.com/liveapi/guides/v4/) :
  - `/v4/sports` et `/v4/sports/{sport}/events` : **gratuits** (ne décomptent pas).
  - `/v4/sports/{sport}/odds` et `/v4/sports/{sport}/events/{eventId}/odds` : **coût = nb de marchés × nb de régions** (par appel ;
    pour l'endpoint event, compté sur les marchés effectivement renvoyés).
  - `/scores` : 1 (2 avec `daysFrom`) ; `/participants` : 1 ; `/events/{id}/markets` : 1.
  - historique `/v4/historical/sports/{sport}/odds?date=...` : 10 × marchés × régions (payant).
  - Headers de quota : `x-requests-remaining`, `x-requests-used`, `x-requests-last`.
- **Régions & bookmakers** (https://the-odds-api.com/sports-odds-data/bookmaker-apis.html) :
  - **`fr`** existe : `betclic_fr, netbet_fr, pmu_fr, unibet_fr, winamax_fr` (⚠️ pas de `parionssport_fr` ni `zebet`).
  - `eu` : inclut `pinnacle`, `betclic_fr`, `pmu_fr`, `unibet_fr`, `winamax_fr`, `winamax_de`, `betfair_ex_eu`, `matchbook`, `marathonbet`, `tipico_de`...
  - `uk`, `us`, `us2`, `us_dfs` (prizepicks, underdog, pick6, dabble), `us_ex` (kalshi, polymarket, novig, prophetx), `au`, `ca`, `se`, `fi`.
  - Astuce crédits : `bookmakers=winamax_fr,betclic_fr,pinnacle` à la place de `regions` (tarif : chaque groupe de 10 bookmakers = 1 région).
- **Sport keys** : `basketball_nba`, `icehockey_nhl`, `americanfootball_nfl`, `baseball_mlb`, `basketball_euroleague`, `soccer_epl`,
  `soccer_france_ligue_one`, `soccer_france_ligue_two`, `soccer_spain_la_liga`, `soccer_italy_serie_a`, `soccer_germany_bundesliga`,
  `soccer_uefa_champs_league`, tennis = un key par tournoi `tennis_atp_*`, `tennis_wta_*` (listés dynamiquement par `/v4/sports`, gratuit).
- **Props joueurs** (https://the-odds-api.com/sports-odds-data/betting-markets.html) — uniquement via `/events/{eventId}/odds` :
  - NBA : `player_points, player_rebounds, player_assists, player_threes, player_blocks, player_steals, player_points_rebounds_assists,
    player_double_double, ...` (+ `_alternate`).
  - NHL : `player_points, player_assists, player_goals, player_shots_on_goal, player_blocked_shots, player_power_play_points,
    player_total_saves, player_goal_scorer_anytime / _first / _last` (+ alternates).
  - Foot : `player_goal_scorer_anytime, player_first_goal_scorer, player_shots_on_target, player_assists, player_to_receive_card`
    — EPL, Ligue 1, Bundesliga, Serie A, LaLiga, MLS **mais "limited to US bookmakers"**.
  - Doc : *"Coverage of player props is mainly limited to US sports and US bookmakers at this time."* → **les bookmakers FR
    (Winamax/Betclic) ne sont PAS couverts pour les props** ; on obtient les props via `regions=us` (DraftKings, FanDuel, BetMGM...)
    ou `us_dfs` — utile comme référence de marché, pas pour le prix jouable en France.
- **Budget gratuit** : 500 crédits ≈ 1 appel h2h+totals (2 crédits) × 1 région par ligue/jour pour ~8 ligues sur 30 j ;
  les props coûtent 1 crédit/marché/région/**match** → une soirée NBA de 10 matchs × 3 marchés = 30 crédits → props quotidiennes NBA impossibles en gratuit
  au-delà de quelques matchs. → **Usage conseillé : h2h/totals en région `fr` (prix réels Winamax/Betclic/Unibet/PMU/NetBet), props via Pinnacle.**
- **Helpers** (non testables sans clé, chemin d'erreur 401 testé) : `oddsapi_odds(sport, regions, markets, api_key)`,
  `oddsapi_event_props(sport, event_id, markets, regions, api_key)`, `oddsapi_events(sport, api_key)` (gratuit).
- **ToS** : usage personnel OK avec clé ; ne pas redistribuer les données brutes.

---
## A3. ESPN — APIs site & core (gratuit, sans clé) ✅ FONCTIONNE — cotes DraftKings + **props joueurs** (NHL, NBA/WNBA, NFL)

- **Site API** `https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/...` (200 ; 1 timeout transitoire → prévoir retry)
  - `scoreboard?dates=YYYYMMDD` : matchs du jour + `competitions[0].odds[0]` = **DraftKings** (provider id 100) avec
    `moneyline/pointSpread/total` × `open`/`close` (cotes US) ; en foot aussi `drawOdds`. Ligues : `basketball/nba`, `basketball/wnba`,
    `hockey/nhl`, `football/nfl`, `baseball/mlb`, `soccer/eng.1`, `soccer/fra.1`, `soccer/esp.1`, `soccer/ita.1`, `soccer/ger.1`,
    `soccer/uefa.champions`, `tennis/atp`, `tennis/wta`.
  - `injuries` : blessures par équipe (NBA : 24 équipes / 59 joueurs listés le 02/10 ; NHL 1,2 Mo) — statut Out/Day-To-Day/Questionable + commentaire.
  - `summary?event={id}` : boxscore joueurs, `rosters` (compos foot), `pickcenter`, `odds`.
  - Tennis ATP/WTA : calendrier/résultats (groupings → competitions) **sans cotes** (0/61 matchs avec odds).
- **Core API** `https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{id}/competitions/{id}/...`
  - `odds` : tous providers (DraftKings 100 ; **Bet365 2000 en foot** avec 1X2 décimal) ; **reste disponible après le match**
    (open/close/current ML+spread+total testé sur NFL du 01/10, NBA du 01/03/2026, NHL, EPL) → **closing lines gratuites pour backtest des marchés principaux**.
  - `odds/100/propBets?limit=1000` : **props DraftKings** (200) —
    - NHL (match du 02/10, 424 items) : `Anytime Goalscorer`, `First/Last Goalscorer`, `First Team Goalscorer`, `To Score 2+/3+ Goals`,
      `Total Shots on Goal`, `Shots on Goal Milestones`, `Total Points`, `Points Milestones`, `Total Assists`, `Assists Milestones`, périodes...
    - WNBA (finale 03/10, 677 items) : `Total Points/Rebounds/Assists/3-Point FG`, combos (`Total Points, Rebounds, and Assists`...),
      `* Milestones` (10+, 15+...), `To Record a Double Double/Triple Double` → **NBA identique attendu** (pré-saison NBA : pas encore de cotes).
    - NFL (1228 items) : yards, receptions, TD scorers (anytime/first/last)...
    - Foot EPL (J-8) : 160 items mais **uniquement marchés d'équipe** (Correct Score, Total Goals Bands, BTTS...) — pas de buteur observé à J-8.
    - Format : `athlete.$ref` (→ nom via GET du $ref), `type.name`, `odds.decimal.value/open`, `odds.total.value` (ligne).
      ⚠️ Over/Under **non étiquetés** : 2 items consécutifs, le 1er = Over, le 2e = Under (vérifié vs Pinnacle sur 10 joueurs WNBA).
    - ⚠️ **Pas d'historique** : après le match les cotes sont retirées (lignes seules, testé NFL 01/10) puis 404 (testé NBA/NHL/EPL 03/2026).
- **Licence/ToS** : API non officielle d'ESPN (usage personnel toléré, pas de garantie) ; cotes = DraftKings (US), indicatives pour un parieur FR.
- **Utilité** : (a) dashboard ★★★★ (props NHL/NBA DraftKings + 2e avis vs Pinnacle, blessures) ; (b) backtest ★★★ pour closing lines
  ML/spread/total (historique via `odds` des matchs passés) ; ★ pour props (à archiver soi-même).
- **Helpers testés** : `espn_scoreboard(league, 'YYYYMMDD')`, `espn_odds(league, event_id)`, `espn_prop_bets(league, event_id)`,
  `espn_injuries(league)`, `espn_summary(league, event_id)`. Échantillons : `samples/espn_nhl_propbets_401891803.csv`, `samples/espn_nba_injuries_20261002.csv`.

---
## B5. NHL — API officielle `api-web.nhle.com` + `api.nhle.com/stats/rest` ✅ + MoneyPuck ✅ + DailyFaceoff ✅

Saison 2026-27 : `regularSeasonStartDate` = 2026-09-29 (selon `/v1/schedule`), fin 2027-04-10.

| URL (pattern) | Code 02/10 | Contenu |
|---|---|---|
| `https://api-web.nhle.com/v1/schedule/{YYYY-MM-DD}` | 200 | semaine de matchs (`gameWeek[].games[]` : id, gameType 1/2/3, startTimeUTC, équipes, état) |
| `https://api-web.nhle.com/v1/score/{YYYY-MM-DD}` | 200 | scores du jour + buts |
| `https://api-web.nhle.com/v1/gamecenter/{gameId}/boxscore` | 200 | `playerByGameStats` : goals, assists, points, **sog**, toi, powerPlayGoals, hits, blockedShots, shifts ; gardiens : saves, shotsAgainst, `starter` |
| `https://api-web.nhle.com/v1/gamecenter/{gameId}/landing` | 200 | avant-match : `matchup.goalieComparison`, `skaterComparison`, stats saison (pas de gardien partant officiel) |
| `https://api-web.nhle.com/v1/gamecenter/{gameId}/play-by-play` | 200 | événements avec coordonnées (tirs, buts) |
| `https://api-web.nhle.com/v1/player/{playerId}/game-log/{20252026}/{2}` | 200 | game log joueur (82 matchs McDavid 2025-26 : goals, assists, shots, toi, PP...) |
| `https://api-web.nhle.com/v1/player/{playerId}/landing` | 200 | bio + stats carrière |
| `https://api-web.nhle.com/v1/roster/{TEAM}/{20262027}` | 200 (`/current` → 307, suivre la redirection) | effectif |
| `https://api-web.nhle.com/v1/club-schedule-season/{TEAM}/{20262027}` | 200 | calendrier équipe |
| `https://api-web.nhle.com/v1/edge/skater-detail/{playerId}/{20252026}/2` | 200 | NHL EDGE (vitesse, tirs, zones) |
| `https://api.nhle.com/stats/rest/en/skater/{summary|realtime|powerplay|timeonice}?limit=-1&cayenneExp=seasonId=20252026 and gameTypeId=2` | 200 | stats saison de tous les skaters (940 lignes) ; `goalie/summary` idem |
| `https://moneypuck.com/moneypuck/playerData/seasonSummary/{2025}/regular/{skaters|goalies|lines|teams}.csv` | 200 | 154 colonnes (xGoals, shotsOnGoal, icetime par situation) ; saison 2026 déjà à jour (2 matchs) |
| `https://moneypuck.com/moneypuck/playerData/careers/gameByGame/regular/skaters/{playerId}.csv` | 200 | **match par match, toute la carrière** (McDavid : 3 975 lignes, 2015-10-08 → 2026-10-01, 157 col.) |
| `https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv` | 200 | équipes match par match |
| `https://peter-tanner.com/moneypuck/downloads/shots_{2025}.zip` | 200 (20 Mo) | tous les tirs avec xG (modèle buteur) |
| `https://www.dailyfaceoff.com/starting-goalies/{YYYY-MM-DD}` | 200 | **gardiens partants** (JSON `__NEXT_DATA__` : homeGoalieName, `homeNewsStrengthName` = Confirmed/Likely...) |

- **Licences** : NHL API = non documentée, usage raisonnable ; **MoneyPuck : "free to use for non-commercial purposes… clearly credit MoneyPuck.com"**,
  scraping non approuvé interdit → utiliser uniquement les CSV publiés ; DailyFaceoff : page publique, scraping léger (1 req/jour).
- **Utilité** : (a) dashboard ★★★★★ (calendrier, gardiens, forme récente) ; (b) backtest props ★★★★★ (game logs complets : buts, tirs, points, TOI).
- **Helpers testés** : `nhl_schedule(date)`, `nhl_boxscore_players(game_id)`, `nhl_player_gamelog(player_id, season, game_type)`, `nhl_roster(team, season)`,
  `nhl_skater_stats(season, report=...)`, `moneypuck_skaters(season, kind, who)`, `moneypuck_player_games(player_id)`, `dailyfaceoff_starting_goalies(date)`.
  Échantillons : `samples/nhl_*.csv`, `samples/moneypuck_*.csv`, `samples/dailyfaceoff_goalies_20261002.csv`.

---
## B6. NBA — game logs joueurs & blessures

| Source / URL | Code 02/10 | Contenu / remarque |
|---|---|---|
| `https://cdn.nba.com/static/json/...` (liveData, staticData) | **403** (même avec Referer/Origin) | Akamai bloque les IP datacenter |
| ✅ **`https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/boxscore/boxscore_{gameId}.json`** | **200** | bucket S3 d'origine du CDN : boxscore complet (points, rebonds, passes, 3PM, minutes, starter, `notPlayingReason`) — saisons passées OK (testé `0022500900`, `0042500401`) |
| ✅ `.../NBA/staticData/scheduleLeagueV2_1.json` | 200 (5 Mo) | calendrier 2026-27 : 1 274 matchs (67 pré-saison `001`, 1 206 saison `002`) du 03/10/2026 au 12/04/2027 |
| ✅ `.../NBA/liveData/scoreboard/todaysScoreboard_00.json` | 200 | scoreboard du jour |
| ✅ `.../NBA/liveData/playbyplay/playbyplay_{gameId}.json` | 200 | play-by-play |
| ✅ `.../NBA/liveData/odds/odds_todaysGames.json` | 200 | cotes Sportradar (FanDuel, Novibet, TabAustralia, Mozzartbet : 2way/spread, ouverture) — **pas de props** |
| `https://stats.nba.com/stats/leaguegamelog?...` | **timeout (000)** même avec headers x-nba-stats-* | bloqué depuis datacenter (nba_api inutilisable ici ; OK depuis IP résidentielle) |
| ✅ `https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{espnId}/gamelog?season=2026` | 200 | game log ESPN (MIN, FG, 3PT, REB, AST, BLK, STL, TO, PTS) ; marche aussi NHL (`hockey/nhl` : goals, assists, shotsTotal, TOI) et foot |
| ✅ `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={id}` | 200 | boxscore ESPN + odds |
| ⚠️ `https://www.basketball-reference.com/players/j/jokicni01/gamelog/2026` | 200 (curl 12h50) puis **403** (17h30) | instable (anti-bot) ; ToS Sports-Reference : ≤ 20 req/min → **ne pas en dépendre** |
| `https://api.balldontlie.io/v1/...` | 401 sans clé | **free = teams/players/games seulement, 5 req/min** ; stats joueurs + blessures = ALL-STAR 9,99 $/mois ; cotes & props = GOAT 39,99 $/mois (docs.balldontlie.io) → **pas utile en gratuit** |
| ✅ **Blessures ESPN** `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries` | 200 | JSON propre (statut Out/Day-To-Day/Questionable + commentaire) → **recommandé pour le dashboard** |
| ✅ **Injury Report officiel NBA (PDF)** `https://ak-static.cms.nba.com/referee/injury/Injury-Report_{YYYY-MM-DD}_{hh}_{mm}{AM|PM}.pdf` | **200 avec header `Referer: https://official.nba.com/`** (403 sans) | format 2025-26+ : `_05_00PM` (MAJ toutes les 15 min) ; avant : `_05PM` (testé `2025-03-01_05PM` = 200). Liste : `https://official.nba.com/nba-injury-report-2025-26-season/` (200). Parsing via `pdfplumber` (texte, colonnes collées → regex). Historique utile pour backtest (statuts à H-x). |
| `https://www.rotowire.com/basketball/nba-lineups.php` | 200 | compos probables (HTML) |
| `https://www.cbssports.com/nba/injuries/` | 200 | blessures HTML |

- **Recommandation** : game logs = boucle sur boxscores S3 (1 230 matchs/saison, 40 matchs en ~1 s en parallèle) ; blessures = ESPN JSON (+ PDF officiel pour l'historique).
- **Helpers testés** : `nba_schedule()`, `nba_boxscore_players(game_id)`, `nba_season_player_logs('00225', n_games)`, `nba_odds_today()`,
  `nba_injury_report_pdf('2026-10-01_12_45PM')`, `espn_athlete_gamelog(league, athlete_id, season)`, `espn_injuries('NBA')`.
  Échantillons : `samples/nba_boxscore_0022500900.json`, `samples/nba_player_logs_2025-26_first40games.csv`, `samples/nba_odds_today_20261002.csv`,
  `samples/nba_injury_report_2026-03-01_05_00PM.pdf`.
- **ToS** : données NBA.com = usage personnel/non commercial ; bucket S3 non documenté (peut fermer).

---
## A4. Kambi (Unibet & co.) ✅, Betfair ❌, bookmakers FR

- **Kambi** `https://eu-offering-api.kambicdn.com/offering/v2018/{operator}/...` (sans clé) :
  - opérateurs `ubfr` et `pafr` → **400** `"Unable to resolve customer for extApiEndpoint ubfr"` (Unibet FR / ParionsSport non servis).
  - opérateurs **`ub`** (Unibet international) et `kambi` → **200**. Prix Unibet .com (≠ prix Unibet FR, mais même trading Kambi → très proche ; le TRJ FR est plafonné).
  - `group.json?lang=fr_FR&market=FR` : arbre des compétitions (NHL 259 offres, NBA 143, Ligue 1 34, EPL 64, ATP Beijing/Tokyo...).
  - `listView/{sport}/{region}/{league}/all/matches.json?lang=fr_FR&market=FR&useCombined=true` ex. `listView/ice_hockey/nhl/all/all/matches.json`,
    `listView/football/france/ligue_1/all/matches.json`, `listView/basketball/nba/all/all/matches.json` → matchs + 1X2/total/handicap.
  - `betoffer/event/{eventId}.json?lang=fr_FR&market=FR&includeParticipants=true` → **toutes les offres dont props joueurs** :
    - NHL (match du 02/10, 645 lignes) : **"Marque - Prolongations incluses" (buteur, 36 joueurs)**, "Marque au moins 2 buts", "Premier buteur",
      "Tirs cadrés du joueur" (O/U 1.5...), "Le joueur marque au moins 1/2/3 point(s)", "au moins 1 passe", "point en supériorité".
    - Foot Ligue 1 : "To Score" (buteur, 33), "First Goal Scorer", "Player's shots on target", "To give an assist", "To score at least 2 goals" (règlement Opta).
  - Cotes en millièmes (`odds: 2250` → 2.25). Helpers testés : `kambi_events(path, operator='ub')`, `kambi_event_offers(event_id)`.
    Échantillon : `samples/kambi_ub_nhl_event_1028398378.csv`.
  - Utilité : (a) ★★★★★ — **seule source testée offrant des cotes européennes de buteur NHL & foot** (référence proche des books FR) ; (b) à archiver soi-même.
- **Betfair Exchange** : `www.betfair.com/www/sports/exchange/readonly/v1/bymarket`, `ero.betfair.com`, `apieds.betfair.com` → **403**.
  L'API officielle exige un compte + app key (gratuite pour usage perso mais login requis, compte FR impossible) → non retenue.
- **Sites FR** : betclic.fr 403, winamax.fr 403, unibet.fr 403, enligne.parionssport.fdj.fr 403, zebet.fr timeout ; netbet.fr 200 et sports.pmu.fr 200 (HTML, pas d'API publique identifiée).
  → **prix FR = The Odds API région `fr`** (clé gratuite, ML/totaux seulement, pas de props FR).
- **PropLine** (`https://api.prop-line.com/v1/...`, clé gratuite **1 000 req/jour**, sans CB) : cotes temps réel props NBA/NHL/foot
  (`player_points`, `player_goals`, `player_shots_on_goal`, `anytime_goal_scorer`...) sur 25+ books US/offshore + **Pinnacle, Kalshi, Polymarket**, Ligue 1 incluse.
  Historique/résolution **masqués en gratuit** (Hobby 9 $/mois). Testé : endpoint 200/429 (la clé démo publique est épuisée) — non testé avec clé perso.

---
## B7. Foot — stats joueurs pour modèle buteur

| Source | URL | Code 02/10 | Contenu |
|---|---|---|---|
| ✅ **Understat** (AJAX JSON, header `X-Requested-With: XMLHttpRequest` obligatoire) | `https://understat.com/getLeagueData/{EPL|La_liga|Bundesliga|Serie_A|Ligue_1|RFPL}/{saison début}` | 200 | `players` (goals, xG, npxG, shots, time, xA, key_passes, position, team — 424 joueurs L1 2026-27), `dates` (calendrier + xG + forecast), `teams` (historique par match) |
| ✅ Understat joueur | `https://understat.com/getPlayerData/{playerId}` | 200 | log match par match toutes saisons (goals, shots, xG, time, position) + tirs |
| ✅ Understat match | `https://understat.com/getMatchData/{matchId}` | 200 | compos (minutes, xG, tirs par joueur) + tous les tirs |
| ✅ ESPN compos | `site.api.espn.com/.../soccer/{league}/summary?event={id}` → `rosters` | 200 | titulaires/remplaçants, postes (dispo ~1 h avant le match) |
| ✅ ESPN game log joueur | `site.web.api.espn.com/apis/common/v3/sports/soccer/eng.1/athletes/{id}/gamelog` | 200 | stats par match |
| FBref | — | 403 (bloqué) | — |
| football-data.org | `api.football-data.org/v4/competitions` 200 sans clé ; `/competitions/FL1/matches` **403** sans clé | clé gratuite (10 req/min) : calendrier/résultats/compos, **pas de stats joueurs détaillées** |
| API-Football (api-sports.io) | `v3.football.api-sports.io/status` 403 sans clé | clé gratuite 100 req/jour (compos, events, stats joueurs) — non testé sans clé |

- Helpers testés : `understat_league(league, season)`, `understat_player_matches(player_id)`, `understat_match(match_id)`, `espn_soccer_lineups(league, event_id)`.
  Échantillon : `samples/understat_ligue1_2026_players.csv`.
- ToS Understat : pas d'API officielle ; usage personnel, requêtes espacées.

---
## B8. HISTORIQUE de cotes de PROPS joueurs (backtest) — résultat : rare en gratuit

| Source | Accès | Testé | Couverture | Verdict |
|---|---|---|---|---|
| ✅ **Kalshi API publique** `https://api.elections.kalshi.com/trade-api/v2` (sans clé, rate-limit → 429, backoff) | `/historical/markets?series_ticker=KXNHLGOAL&limit=1000&cursor=...` ; prix horaires `/historical/markets/{ticker}/candlesticks?start_ts&end_ts&period_interval=60` ; marchés récents `/markets?series_ticker=...` | 200 | **NHL buteur (KXNHLGOAL "X: 1+ goals", 2+, 3+) : 37 973 marchés archivés depuis 2025-11-22** ; **NBA points (KXNBAPTS) : 23 562 depuis 2025-11-19** ; **EPL buteur (KXEPLGOAL) : 7 563 depuis 2025-12-02** ; aussi KXNBAREB/AST/3PT/PRA, KXNHLPTS/AST/SAVE, KXLIGUE1GOAL (pas encore d'archive), KXUCLGOAL... `result` yes/no = résultat réel | ★★★★ **meilleure source GRATUITE d'historique de props** (prix de marché de prédiction, pas de bookmaker ; utiliser le prix ~1 h avant le match via candlesticks, pas `last_price` qui est post-match) |
| PropLine (HF) `propline/graded-player-props-sample` | `https://huggingface.co/datasets/propline/graded-player-props-sample/resolve/main/nfl_graded_props_14d.csv.gz` | 200 | 14 jours NFL (213 190 lignes, 23 books dont Pinnacle, ouverture/clôture + résultat) et MLB ; **pas NBA/NHL/foot** ; CC BY 4.0 | ★ (démo) ; archive complète payante |
| HF `Karmane/polymarket-sports-lines-and-player-props(-sample)` | `.../resolve/main/data/data.parquet` | 200 | snapshot Polymarket (575 lignes sample, 107 col.), props surtout NFL | ★ |
| HF `Karmane/nhl-shots-on-goal-prop-trends-sample` | parquet 1,4 Mo | 200 | **features** tirs NHL (rolling SOG, gardien adverse) — **pas de cotes** | ★★ features |
| HF `SupremeMonkey/NBA_betting_data` | parquet | listé | game logs NBA (pas de lignes de props) | ★ |
| HF `michaelmallari/sportsbook-nhl` | — | **401 (gated)** | cotes match NHL 2021-23 | ✗ |
| HF `kennyhyder/sportsbookish-daily-odds` | `data/latest.csv` | 200 | probabilités Kalshi du jour (golf...), 430 lignes | ✗ |
| Kaggle (téléchargement anonyme OK : `https://www.kaggle.com/api/v1/datasets/download/{owner}/{slug}` en GET, ou `kagglehub.dataset_download`) | ex. `ehallmar/nba-historical-stats-and-betting-data` (36 Mo, ML/spread/total NBA) | 200 | recherche API Kaggle "player props / prizepicks / goalscorer" : **aucun dataset NBA/NHL/foot de props** ; seulement `andyt338/graded-player-props-mlb-nfl-23-sportsbooks` (MLB+NFL) | ✗ pour NBA/NHL/foot |
| The Odds API historique | payant (props depuis 03/05/2023, snapshots 5 min) | — | NBA/NHL/foot US books | payant |
| BigDataBall, SportsDataIO, OddsWarehouse, PropLine Backfill | payant | — | — | payant |
| ESPN core `propBets` | gratuit | 404 après match | — | ✗ (pas d'historique) |

→ **Stratégie backtest recommandée** : (1) Kalshi pour l'historique gratuit NHL buteur / NBA points / EPL buteur depuis nov.-déc. 2025 ;
(2) **démarrer dès maintenant un archivage quotidien** (cron) de Pinnacle (props NBA), ESPN/DraftKings (props NHL/NBA), Kambi `ub` (buteurs NHL/foot), Kalshi (marchés actifs).
Helpers testés : `kalshi_markets(series, historical=True)`, `kalshi_candles(ticker, start, end)`.
Échantillons : `samples/kalshi_nhl_goal_historical.csv` (12 000 marchés 04-06/2026), `samples/kalshi_candles_hertl_20260614.csv`, `samples/hf/*`.


---
## Annexe — exécution
- `python3 live_helpers.py` lance un self-test de 16 fonctions (toutes OK le 2026-10-02 17h UTC) + test 401 The Odds API.
- `verified_urls2.json` : 72 URLs re-testées (code HTTP + horodatage UTC + headers requis).
- Dépendances : `pip install requests pandas pyarrow` (+ `pdfplumber` pour le PDF blessures NBA, `kagglehub` optionnel).
