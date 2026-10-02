# Catalogue des sources de données gratuites — résultats et cotes historiques (sports ANJ)

> Recherche faite le **2026-10-02** depuis un conteneur Linux (proxy HTTPS sortant, **IP de datacenter hors de France**).
> « Testé » = requête réelle depuis ce conteneur (code HTTP indiqué), avec un échantillon téléchargé et parsé avec pandas sauf mention contraire.
> Fichiers associés dans le même dossier :
> - `verified_urls.json` : URLs prêtes à l'emploi par sport (motif, exemple, colonnes, années, présence de cotes)
> - `helpers_sources.py` : `tennis_data()`, `sbr_season()`, `espn_odds()`, `understat_league()` (tous testés)
> - `betexplorer_results.py` : parseur des pages de résultats Betexplorer (score + cotes moyennes), testé sur handball, volley, tennis et NHL
> - `peek.py` / `probe.sh` : inspection rapide d'une URL (code HTTP, colonnes, plage de dates)

## 0. À retenir (changements importants en 2025-2026)

1. **Les dépôts tennis de Jeff Sackmann (`tennis_atp`, `tennis_wta`, `tennis_slam_pointbypoint`, `tennis_pointbypoint`) ont été supprimés** de GitHub (Software Heritage ne les trouve plus depuis le 2026-06-16). Seul `tennis_MatchChartingProject` reste en ligne. Miroirs fonctionnels : `Aneeshers/tennis-sackmann-archive` (GitHub et Hugging Face, instantané de juin 2026, CC BY-NC-SA) et `Tennismylife/TML-Database`.
2. **tennis-data.co.uk renvoie une erreur 403 (Cloudflare « Attention Required »)** depuis ce conteneur. Un miroir GitHub complet et à jour (ATP 2000-2026, WTA 2007-2026, jusqu'au 2026-09-13) existe : `nick-benelli/Tennis-Data-Pipeline`.
3. **Pinnacle a disparu des fichiers tennis-data.** La colonne PSW est vide depuis février 2026 (30 % en janvier, 0 % ensuite). La colonne **BFE (Betfair Exchange) a pris le relais à partir d'août 2025**. C'est pareil sur football-data.co.uk : PSH/PSCH ne sont remplis qu'à 50 % en 2025-26 et absents des fichiers 2026-27, qui gagnent en revanche BFD (Betfred), BV, PP, SKB et **HxG/AxG (xG)**. Les ligues « new » gardent PSCH à environ 93 %.
4. **L'API ClubElo (`api.clubelo.com`) est fermée.** Elle renvoie 502 sur toutes les routes en HTTP (serveur IIS de ClubElo) et le TLS ne répond pas. L'API passe derrière une authentification, sans inscription ouverte pour l'instant (cf. soccerdata issue #977). Le site `clubelo.com` (HTML) répond 200. Substitut : `xgabora/Club-Football-Match-Data-2000-2025/data/EloRatings.csv` (Elo jusqu'en 2025).
5. **Bookmakers français.** ParionsSport en ligne redirige vers **unibet.fr depuis le 24/03/2026** (FDJ United). ZEbet redirige aussi vers Unibet (absorbé par PSEL le 01/07/2025). La liste ANJ actuelle compte 16 opérateurs de paris sportifs : Betclic, Winamax, Unibet, PMU, Bwin, Betsson, Bet365, CircusBet, DAZN Bet, FeelingBet, Genybet, Netbet, Olybet, PokerStars Sports, Vbet et Yes or No.
6. **ESPN (API non documentée) est une source de cotes historiques gratuite et sous-exploitée** : NBA, NFL, NHL, MLB et football européen, avec plusieurs bookmakers US (Bet365, DraftKings, MGM, Caesars, Unibet, ESPN BET, etc.) et des cotes open/close structurées depuis 2023.
7. **OpenF1 (`api.openf1.org`) renvoie 401 pendant les sessions live.** Le message dit : « Global API access (including past sessions) is restricted to authenticated users until the session ends ». Il faut utiliser Jolpica-F1 ou FastF1.

---

## 1. Tennis (ATP / WTA)

| Source | URL | Contenu | Cotes ? | Période | Format | Accès testé (2026-10-02) | Licence / remarques |
|---|---|---|---|---|---|---|---|
| **Miroir tennis-data.co.uk — nick-benelli/Tennis-Data-Pipeline** | `https://raw.githubusercontent.com/nick-benelli/Tennis-Data-Pipeline/main/data/raw/uk/{atp\|wta}/uk_{atp\|wta}_singles_raw_{YYYY}.csv` | Résultats complets (tournoi, surface, tour, classements, score par set) | **Oui** : B365, PS (Pinnacle), Max, Avg (Oddsportal), BFE (Betfair Exchange). Anciennes années : EX, LB, SJ, CB, UB, IW… Ce sont des cotes pré-match proches de la clôture. | ATP 2000→2026-09-13, WTA 2007→2026-09-12 (2000 et 2001 WTA absents) | CSV | **200** (ATP 2000, 2007, 2015, 2023-2026 ; WTA 2007, 2015, 2023-2026) | Code sous MIT, données tennis-data (usage non commercial). **PSW à 0 % depuis février 2026, BFE à environ 100 % depuis septembre 2025.** |
| Miroir tennis-data — DanielSzakacs/atp_data et wta_data | `https://raw.githubusercontent.com/DanielSzakacs/atp_data/main/{YYYY}.csv` (pareil pour `wta_data`) | Idem tennis-data | Oui | ATP 2005-2024 | CSV | **200** | Pas de licence. Source de secours. |
| tennis-data.co.uk (source originale) | `http://www.tennis-data.co.uk/{YYYY}/{YYYY}.xlsx`, `/{YYYY}w/{YYYY}.xlsx` | Idem | Oui | 2000→ | XLSX/ZIP | **403 Cloudflare** | Bloqué depuis l'IP du datacenter. Fonctionne a priori depuis une IP résidentielle. |
| ATP 2000-2026 (miroir Hugging Face du Kaggle `dissfya/atp-tennis-2000-2023daily-pull`) | `https://huggingface.co/datasets/groundhog2107/atp_tennis/resolve/main/atp_tennis.csv` | 67 288 matchs ATP, 1 seul fichier de 9 Mo | Oui : `Odd_1`/`Odd_2` (une cote par joueur, -1 si absente) | 2000-01-03 → 2026-03-15 | CSV | **200** | Licence Kaggle non précisée. Le Kaggle d'origine est mis à jour quotidiennement mais demande un token. |
| Archive Sackmann — Aneeshers/tennis-sackmann-archive | `https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main/{atp\|wta}/{atp\|wta}_matches_{YYYY}.csv` (et `atp_rankings_*`, `atp_players.csv`, `slam_pointbypoint/*`). Miroir HF : `https://huggingface.co/datasets/Aneeshers/tennis-sackmann-archive` | Résultats et statistiques de service, classements, joueurs, point par point des Grands Chelems 2011-2024 | Non | 1968 → 2026-05-25 (instantané de juin 2026) | CSV | **200** | CC BY-NC-SA 4.0. Ne sera plus mis à jour. |
| TML-Database (Tennismylife) | `https://raw.githubusercontent.com/Tennismylife/TML-Database/master/{YYYY}.csv`, `ongoing_tourneys.csv`, `ATP_Database.csv` | Format Sackmann et colonne `indoor` | Non | 1968→2026 (2026.csv ne va que jusqu'à mi-janvier au 2026-10-02) | CSV | **200** | Licence non commerciale |
| Match Charting Project (Sackmann) | `https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/charting-{m\|w}-{matches\|points-*}.csv` | Point par point codé à la main | Non | Années 1970→2026 | CSV | **200** | CC BY-NC-SA 4.0. Seul dépôt Sackmann encore en ligne. |
| ATP stats officielles 2015-2025 (HF Yahya777777) | `https://huggingface.co/datasets/Yahya777777/ATP-Tennis-Matches-Dataset-2015-to-2025/resolve/main/data/{YYYY}/{tournoi}_{YYYY}.csv` | Stats de match et cumul de l'année, 78 colonnes | Non | 2015-2025 | CSV (611 fichiers) | **200** | GPL-3.0 |
| Betexplorer tennis | `https://www.betexplorer.com/tennis/atp-singles/{tournoi}/results/` | Résultats et **cote moyenne** 1/2 | Oui (moyenne du marché) | Plusieurs années | HTML statique (attribut `data-odd`) | **200**. Parseur `betexplorer_results.py` testé (Wimbledon : 129 matchs). | CGU restrictives. robots.txt interdit `?year=` et `/bookmaker/`. |
| tennisexplorer.com | `https://www.tennisexplorer.com/` | Résultats y compris ITF/Challenger, cotes par bookmaker sur les pages de match | Oui | Ancien | HTML | **200** | Scraping non autorisé par les CGU. robots.txt n'interdit que /redirect/ et /contact/. |
| Kaggle (`hakeem/atp-and-wta-tennis-data`, `edoardoba/atp-tennis-data`, `ehallmar/a-large-tennis-dataset-for-atp-and-itf-betting`) | `kaggle datasets download -d …` | tennis-data et autres | Oui | 2000-2019 environ | CSV | Kaggle.com répond 200, mais **le téléchargement sans token renvoie la page HTML de connexion** | Il faut un compte Kaggle gratuit et `~/.kaggle/kaggle.json`. |
| Ultimate Tennis Statistics | `https://www.ultimatetennisstatistics.com/` | Statistiques et Elo | Non | — | HTML/JSON | **200** | — |

**Ce qui est arrivé à Sackmann (`tennis_atp` en 404).** Les quatre dépôts ont été retirés par leur auteur (404 constaté sur GitHub et vérifié par des tickets tiers : MLT-OSS/FirstData#238, ClickHouse PR #121439). Il faut basculer vers `Aneeshers/tennis-sackmann-archive` (identique jusqu'en juin 2026) pour l'historique, et vers TML-Database ou le miroir tennis-data pour la suite.

## 2. Basket-ball (NBA, et au-delà)

| Source | URL | Contenu | Cotes ? | Période | Format | Accès testé | Licence / remarques |
|---|---|---|---|---|---|---|---|
| **SportsbookReviewsOnline (SBR)** | `https://www.sportsbookreviewsonline.com/scoresoddsarchives/nba-odds-{YYYY}-{YY}` | Score par quart-temps, rotation, ligne d'ouverture et de clôture (spread ou total), ML de clôture, 2e mi-temps | **Oui** (consensus Las Vegas) | 2007-08 → 2022-23 | Table HTML (`pd.read_html`), 2 lignes (V/H) par match | **200** (2007-08 : 2 633 lignes ; 2021-22 : 2 647 lignes) | robots.txt : `Allow: /` (sauf /go/). Les xlsx NBA ne sont plus en lien, il faut parser le HTML. Les archives s'arrêtent en 2022-23. |
| **flancast90/sportsbookreview-scraper** | `https://raw.githubusercontent.com/flancast90/sportsbookreview-scraper/main/data/nba_archive_10Y.json` | JSON propre : 1 ligne par match | Oui : ML de clôture, spread open/close, total open/close, 2H | 2011-12 → 2021-22 (13 903 matchs) | JSON, 7 Mo | **200** | MIT |
| **wippa-studios/wippa-nba-data** | `https://raw.githubusercontent.com/wippa-studios/wippa-nba-data/main/seasons/{YYYY}-{YYYY+1}/nba_{YYYY}-{YYYY+1}_results_odds.csv` (ex. `2025-2026`). Attention : le README indique à tort `2016-17`. | Résultats et cotes moneyline décimales (la doc dit « closing ») | Oui (ML uniquement) | 2016-17 → 2025-26 (jusqu'au 2026-06-14) | CSV/Parquet | **200** (les chemins avec année courte renvoient 404) | MIT. Bookmaker non précisé. Le fichier `datasets/nba_ml_dataset.csv` contient des features roulantes. |
| **ESPN core API (odds)** | Liste des matchs : `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=YYYYMMDD`. Cotes : `https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/{id}/competitions/{id}/odds` | Plusieurs bookmakers par match (spread, total, ML) | **Oui** : 2015 (5Dimes, Bovada, BetOnline, « Opening »…), 2019 (Caesars, Unibet, Westgate…), 2023 (DraftKings, MGM, ESPN BET avec open/close…), 2026 (DraftKings open/close) | Environ 2014-15 → aujourd'hui (rien en 2008 et 2012) | JSON | **200** | API non documentée. CGU ESPN : usage personnel. robots.txt de www.espn.com non applicable à l'API (domaines site.api / sports.core.api). À limiter à environ 1 requête par seconde. |
| Kaggle `cviaxmiwnptr/nba-betting-data-october-2007-to-june-2024` (mis à jour jusqu'en 2026 d'après la description) | `kaggle datasets download -d cviaxmiwnptr/nba-betting-data-october-2007-to-june-2024` | Spread, total, ML, 2H (SBR jusqu'en 2023, puis ESPN, puis SBR.com) | Oui | 2007 → 2026 | CSV | Il faut un token Kaggle | Licence Kaggle |
| HF `SupremeMonkey/NBA_betting_data`, `cdechoch/nba-data-archive` | `https://huggingface.co/datasets/…` | Game logs et stats en parquet (`cdechoch` pèse 3,7 Go) | Pas de cotes de match vérifiées | 2020→ | Parquet | API HF **200** | Volumineux |
| stats.nba.com / cdn.nba.com | — | Stats officielles | Non | — | JSON | **Timeout** (stats.nba.com) et **403** (cdn.nba.com) | Bloqué depuis le datacenter. Il faut passer par les miroirs HF ou l'API ESPN. |
| basketball-reference.com | — | — | Non | — | — | robots.txt restrictif (famille sports-reference, 403 constaté sur fbref et PFR) | À éviter |

## 3. Hockey sur glace (NHL, et au-delà)

| Source | URL | Contenu | Cotes ? | Période | Format | Accès testé | Licence / remarques |
|---|---|---|---|---|---|---|---|
| **SBR NHL** | `https://www.sportsbookreviewsonline.com/scoresoddsarchives/nhl-odds-{YYYY}-{YY}` (la saison 2020-21 s'appelle `nhl-odds-2021`) | Score par période, ML open/close, puck line et prix, O/U open/close et prix | **Oui** | 2007-08 → 2022-23 | HTML | **200** (2022-23 : 685 lignes) | Comme SBR NBA |
| **flancast90 NHL** | `https://raw.githubusercontent.com/flancast90/sportsbookreview-scraper/main/data/nhl_archive_10Y.json` | JSON propre | **Oui** : ML open/close, puck line et prix, O/U open/close et prix | 2011-12 → 2021-22 (13 678 matchs) | JSON, 7,3 Mo | **200** | MIT |
| **ESPN core API (odds)** | `https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/events/{id}/competitions/{id}/odds` | Plusieurs bookmakers | **Oui** : 2020 (Bet365, DraftKings, Caesars, Unibet, Westgate, CG Tech), 2024 avec **open et close** pour Bet365, BetfairSportsbook, Caesars, ESPN BET, MGM, SugarHouse, Unibet… | Environ 2019-20 → aujourd'hui (rien en 2010 et 2015) | JSON | **200** | API non documentée |
| Betexplorer NHL | `https://www.betexplorer.com/hockey/usa/nhl-{YYYY}-{YYYY+1}/results/` | Résultats et cote moyenne 1X2 | Oui (moyenne) | Plusieurs saisons | HTML | **200** (86 lignes : séries éliminatoires uniquement sur la page statique) | Voir la section éthique |
| NHL officiel | `https://api-web.nhle.com/v1/score/{YYYY-MM-DD}`, `https://api.nhle.com/stats/rest/en/team` | Scores, play-by-play, stats | Non | Historique complet | JSON | **200** | API publique non documentée |
| MoneyPuck | `https://moneypuck.com/moneypuck/playerData/seasonSummary/{YYYY}/regular/teams.csv`. Tirs : `https://peter-tanner.com/moneypuck/downloads/shots_{YYYY}.zip` | xG, Corsi, stats d'équipes et de joueurs, tirs | Non | 2008→ | CSV/ZIP | **200** (fichier de tirs d'environ 20 Mo) | Non commercial, attribution |
| HF `RentoSaijo/NHL_DB` | `https://huggingface.co/datasets/RentoSaijo/NHL_DB` | Play-by-play en parquet, 2010→2027, mis à jour par GitHub Actions | Non | 2010→ | Parquet (2,6 Go au total) | API HF **200** | Volumineux |
| Kaggle / nielsenz/odds-api-current-save | — | Instantanés The Odds API NHL 2023-2026 (BetMGM, Caesars, FanDuel, DraftKings, BetRivers) | Oui | 2023-10 → 2026-01 | CSV | Non testé (chemins introuvables, 404 via WebFetch) | — |

## 4. Football américain (NFL)

| Source | URL | Contenu | Cotes ? | Période | Format | Accès testé | Licence / remarques |
|---|---|---|---|---|---|---|---|
| **nflverse `games.csv`** | `https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv` ou `https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv` | 46 colonnes : résultats, repos, toit, surface, météo, QB, coach, arbitre, identifiants ESPN/PFR | **Oui** : `spread_line`, `total_line` (100 % depuis 1999) ; `home/away_moneyline`, `*_spread_odds`, `over/under_odds` (82 % en 2006, 100 % depuis 2007) | 1999 → 2026 (saison en cours partiellement remplie) | CSV, 2,2 Mo | **200** (raw et release GitHub) | CC-BY / MIT. **C'est la référence NFL.** |
| SBR NFL | `https://www.sportsbookreviewsonline.com/scoresoddsarchives/nfl-odds-{YYYY}-{YY}` et `nfl-preseason-odds-*` | Score par quart-temps, open/close, ML, 2H | Oui | 2007-08 → 2021-22 | HTML | **200** | — |
| flancast90 NFL | `…/data/nfl_archive_10Y.json` | Idem SBR | Oui | 2011-2021 | JSON | **200** | MIT |
| Spreadspoke (Kaggle, miroir HF) | `https://huggingface.co/datasets/tuxmx/nfl_bets_scores/resolve/main/spreadspoke_scores.csv` | Favori, spread, O/U, météo | Oui (lignes de clôture) | 1966 → février 2024 (lignes depuis 1979) | CSV | **200** (13 788 lignes) | Format de date M/J/AAAA |
| ESPN core API | `…/sports/football/leagues/nfl/events/{id}/competitions/{id}/odds` | Plusieurs bookmakers | Oui | Environ 2015 → | JSON | **200** | — |
| pro-football-reference | — | — | — | — | — | **403** | Bloqué |

## 5. Baseball (MLB)

| Source | URL | Contenu | Cotes ? | Période | Format | Accès testé | Licence / remarques |
|---|---|---|---|---|---|---|---|
| **SBR MLB xlsx** | `https://www.sportsbookreviewsonline.com/wp-content/uploads/sportsbookreviewsonline_com_737/mlb-odds-{YYYY}.xlsx` | Lanceur partant, score par manche, ML open/close, run line et prix, O/U open/close et prix | **Oui** | 2010 → 2021 | XLSX (lu avec openpyxl) | **200** (2021 : 4 924 lignes) | — |
| **HF Oronto/baseball-stats-cleaned_oddsportal_mlb** | `https://huggingface.co/datasets/Oronto/baseball-stats-cleaned_oddsportal_mlb/resolve/main/data/train-00000-of-00001.parquet` | Résultats et bilan des équipes | **Oui** : `home_odds`/`away_odds` (moneyline US, Oddsportal) | 2006-06 → 2024-09 (40 359 matchs) | Parquet, 1,3 Mo | **200** | Licence non précisée |
| flancast90 MLB | `…/data/mlb_archive_10Y.json` | SBR | Oui | 2011-2021 | JSON | **200** | MIT |
| ESPN core API | `…/sports/baseball/leagues/mlb/events/{id}/competitions/{id}/odds` | 2010 : surtout des totaux ; 2022 : 14 bookmakers (Bet365, DraftKings, MGM…) | Oui | 2010 → (partiel avant 2019) | JSON | **200** | — |
| MLB Stats API | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=YYYY-MM-DD` (et `/game/{pk}/feed/live`) | Officiel : calendrier, box-scores, play-by-play | Non | Complet | JSON | **200** | Usage non commercial (MLBAM) |
| Retrosheet | `https://www.retrosheet.org/gamelogs/gl{YYYY}.zip` | Game logs à 161 champs | Non | 1871 → 2025 | ZIP/CSV | **200** | Gratuit avec mention. robots.txt interdit `/gamelogs/` aux robots : téléchargement manuel ou ponctuel uniquement. |
| Betexplorer MLB/NPB/KBO | `https://www.betexplorer.com/baseball/usa/mlb/results/` | Résultats et cote moyenne | Oui | — | HTML | **200** (navigation) | — |

## 6. Rugby (à XV et à XIII)

| Source | URL | Contenu | Cotes ? | Période | Format | Accès testé | Licence / remarques |
|---|---|---|---|---|---|---|---|
| **transientlunatic/Rugby-Data** | `https://raw.githubusercontent.com/transientlunatic/Rugby-Data/master/json/{comp}-{YYYY}-{YYYY+1}.json`. Valeurs de `comp` vues : `top14`, `premiership`, `celtic` (URC/Pro14), `currie-cup`, `npc`, `super-rugby`, `rugby-world-cup-{YYYY}`… (127 fichiers) | Matchs avec **chaque événement de score** (minute, essai, transformation, pénalité, joueur) | Non | Top 14 2009-10→2026-27 (trou en 2015-16 selon le README) ; Premiership 2006→2027 ; URC 2002→2027 ; Coupe du monde 1987→ | JSON | **200** (top14-2018-2019 : 186 matchs ; top14-2025-2026 ; premiership-2026-2027) | Pas de licence. Mise à jour automatique d'après le README. Pas de fichier `six-nations-*` à ce nommage (404). |
| dirknbr/rugby-elo | `https://raw.githubusercontent.com/dirknbr/rugby-elo/main/match_data_{YYYYMMDD}.csv` (20230826, 20241102, 20251102) | Tests internationaux : date, équipes, score | Non | Environ 400 matchs récents | CSV | **200** (373 lignes) | — |
| rugbyarchive/rugbyarchive.github.io | Site statique, données JSON dans `data/` (chemin exact non indexé) | Tous les tests internationaux depuis 1871 (11 256 matchs) et classement World Rugby recalculé | Non | 1871 → 2026-09-06 | JSON | Non testé (chemin inconnu) | Pas de licence |
| ESPN rugby (API non documentée) | `https://site.api.espn.com/apis/site/v2/sports/rugby/{league_id}/scoreboard?dates=YYYYMMDD`. Identifiants : 180659 Six Nations, 270559 Top 14, 267979 Premiership, 270557 URC, 242041 Super Rugby, 164205 Coupe du monde. XIII : `sports/rugby-league/3` (NRL). | Résultats et compositions | Pas de cotes sur le scoreboard | Plusieurs saisons | JSON | **200** (Six Nations, Super Rugby, Coupe du monde 2023, NRL) | — |
| OddsPortal via **OddsHarvester** (jordantete, MIT) | `oddsharvester historic -s rugby-union -l <ligue> --season 2024-2025 -m 1x2 -f csv` | Résultats et **cotes par bookmaker** (1X2, handicap, O/U, double chance, DNB) | **Oui** | Environ 2008 → | Navigation Playwright | La page de résultats OddsPortal répond **200**. Les cotes passent par un AJAX chiffré, il faut un navigateur headless. Le CDN Playwright est joignable (`cdn.playwright.dev` répond 400 à la racine, donc l'hôte est accessible). | CGU OddsPortal : scraping interdit. robots.txt interdit `/ajax-widget/` et `*/feed/*`. Usage personnel modéré. |
| AusSportsBetting (NRL, Super Rugby…) | `https://www.aussportsbetting.com/data/historical-nrl-results-and-odds-data/` | xlsx résultats et cotes (open/close min/max) | Oui | 2009 → | XLSX | **403** (signalé en amont) | Bloqué depuis le datacenter. Fonctionne depuis une IP résidentielle. |
| Kaggle `oliviersportsdata/sample-world-rugby-master` | — | 25 392 matchs XV et XIII, cotes de **clôture**, 17 compétitions dont le Top 14, 2008-2026 | Oui | 2008-2026 | CSV | Non testé | **Échantillon gratuit (132 lignes) seulement**, le jeu complet est payant. Le même vendeur publie des échantillons sur HF (`oliviersportsdata/*`). |
| LNR (Top 14 / Pro D2) | `https://www.lnr.fr/rugby-top-14/calendrier-resultats-rugby-top-14` | Résultats officiels | Non | — | HTML | **200** | Scraping soumis aux CGU |

## 7. Handball

| Source | URL | Contenu | Cotes ? | Période | Format | Accès testé | Licence / remarques |
|---|---|---|---|---|---|---|---|
| **Betexplorer** (meilleure source gratuite de cotes et résultats testée) | `https://www.betexplorer.com/handball/{pays}/{ligue}-{YYYY}-{YYYY+1}/results/` (saison en cours : `…/{ligue}/results/`) | Score et **cote moyenne 1/X/2** (`data-odd`), tour, date | **Oui** (moyenne du marché) | Plusieurs saisons selon la ligue | HTML statique | **200**. Starligue 2024-2025 : 240 matchs avec cotes via `betexplorer_results.py`. | La page n'affiche qu'une partie de la saison (dernières phases). Les autres phases sont derrière des liens `stage`. robots.txt interdit `?year=`, `/bookmaker/`, `/redirect/`. Prévoir 3 à 5 s entre requêtes. |
| OddsPortal via OddsHarvester | `oddsharvester historic -s handball -l <ligue> --season …` | Cotes par bookmaker : 1X2, home/away, DC, DNB, O/U, handicap | Oui | Environ 2008 → | Playwright | Page **200** (HTML de 1 Mo avec la liste des matchs ; cotes en AJAX chiffré) | Voir rugby |
| Flashscore | `https://www.flashscore.fr/handball/france/starligue/resultats/` | Résultats | Cotes dans les flux internes (`d.flashscore.com`, en-tête `x-fsign`) | — | HTML/JS | **200** | robots.txt interdit /live/ et /standings/. Les CGU interdisent le scraping. |
| LNH, EHF | `https://www.lnh.fr/liquimoly-starligue/calendrier`, `https://www.eurohandball.com/` | Officiel | Non | — | HTML | **200** | Pas d'API publique documentée |
| GitHub | Aucun dépôt de résultats de handball maintenu trouvé (recherche GitHub : projets académiques uniquement) | — | — | — | — | — | Il faudra construire ce jeu nous-mêmes (Betexplorer, OddsPortal ou Flashscore) |

## 8. Volley-ball

| Source | URL | Contenu | Cotes ? | Période | Format | Accès testé | Licence / remarques |
|---|---|---|---|---|---|---|---|
| **Betexplorer** | `https://www.betexplorer.com/volleyball/{pays}/{ligue}-{YYYY}-{YYYY+1}/results/` (ex. `france/ligue-a-2024-2025`, `italy/superlega-2024-2025`, `poland/plusliga-2024-2025`) | Score en sets et cote moyenne 1/2 | Oui, mais partiel (les matchs de séries éliminatoires n'ont parfois pas de cote) | Plusieurs saisons | HTML | **200** (22 à 28 matchs par page statique) | Comme le handball |
| OddsPortal via OddsHarvester | `-s volleyball` | home/away, O/U sets et points, handicap, score exact | Oui | — | Playwright | Page **200** | Voir rugby |
| ESPN | `https://site.api.espn.com/apis/site/v2/sports/volleyball/mens-college-volleyball/scoreboard` | NCAA uniquement | Non | — | JSON | **200** | — |
| NCAA (mattwaite, dwillis) | `github.com/dwillis/NCAAWomensVolleyballData` | Stats NCAA féminines | Non | — | CSV | Non testé | — |
| LNV, Volleyball World | `https://www.lnv.fr/`, `https://en.volleyballworld.com/` | Officiel | Non | — | HTML | **200** | — |

## 9. Football (rappel, football-data.co.uk est déjà intégré)

| Source | URL | Contenu | Cotes ? | Période | Format | Accès testé | Licence / remarques |
|---|---|---|---|---|---|---|---|
| football-data.co.uk, ligues principales | `https://www.football-data.co.uk/mmz4281/{SSSS}/{DIV}.csv` (SSSS = 9394 … 2627). DIV : E0 E1 E2 E3 EC SC0 SC1 SC2 SC3 D1 D2 I1 I2 SP1 SP2 F1 F2 N1 B1 P1 T1 G1 | Résultats, stats, cotes pré-match et clôture | Oui : B365, BW, BF, BFD, BMGM, BV, CL, LB, PS (jusqu'en 2025-26), PP, SKB, WH, 1XB, Max, Avg, BFE ; O/U 2,5 ; handicap asiatique | 1993-94 → 2026-27 | CSV (aussi `mmz4281/{SSSS}/data.zip`) | **200** | Déjà intégré. Nouveautés 2026-27 : **HxG/AxG**, plus de Pinnacle. |
| football-data.co.uk, ligues « new » | `https://www.football-data.co.uk/new/{ARG\|AUT\|BRA\|CHN\|DNK\|FIN\|IRL\|JPN\|MEX\|NOR\|POL\|ROU\|RUS\|SWE\|SWZ\|USA}.csv` | Résultats et cotes de **clôture** PS/Max/Avg/BFE/B365 | Oui (PSCH à environ 93 %, BFE à environ 15 %) | 2012 → 2026-09 (RUS jusqu'à 2026-08) | CSV/XLSX | **200** (les 16) | Calendriers : `fixtures.csv`, `new_league_fixtures.csv` |
| **Understat** (xG) | `https://understat.com/getLeagueData/{EPL\|La_liga\|Bundesliga\|Serie_A\|Ligue_1\|RFPL}/{YYYY}` avec l'en-tête `X-Requested-With: XMLHttpRequest` | Par équipe : historique match par match (xG, xGA, npxG, PPDA, deep, xpts) ; joueurs ; matchs (xG, prévision w/d/l) | Non | 2014-15 → | JSON (gzip) | **200** (EPL 2024 : 20 équipes, 562 joueurs, 380 matchs) | **Le JSON n'est plus intégré dans le HTML** (un seul `JSON.parse`, pour la publicité). Il faut utiliser l'endpoint AJAX. **robots.txt = `Disallow: /`**, donc usage personnel et très peu fréquent. |
| ClubElo | `http://api.clubelo.com/{YYYY-MM-DD}` | Elo des clubs | Non | — | CSV | **502 (IIS) / TLS sans réponse** | **API fermée (auth)**. Substitut : `xgabora/.../EloRatings.csv` (2000-2025, 11 Mo) ou parsing HTML de `https://clubelo.com/{Club}` (**200**). |
| xgabora/Club-Football-Match-Data-2000-2025 | `https://raw.githubusercontent.com/xgabora/Club-Football-Match-Data-2000-2025/main/data/{Matches,EloRatings}.csv` | football-data et Elo pré-joints, forme 3/5 matchs | Oui (OddHome/Draw/Away, Max, O/U 2,5, handicap) | 2000 → 2025 | CSV (45 Mo et 11 Mo) | **200** | — |
| martj42/international_results | `https://raw.githubusercontent.com/martj42/international_results/master/{results,shootouts,goalscorers}.csv` | 49 000 matchs internationaux et plus | Non | 1872 → 2026 | CSV | **200** | CC0 |
| StatsBomb open data | `https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json`, `matches/{comp_id}/{season_id}.json`, `events/{match_id}.json`, `lineups/…`, `three-sixty/…` | Événements détaillés (CdM, Euro, Ligue 1 sélectionnée, Messi, etc.) | Non | Sélection | JSON | **200** | Licence StatsBomb (attribution) |
| openfootball | `https://raw.githubusercontent.com/openfootball/football.json/master/{SSSS-SS}/{en.1,fr.1,…}.json`, `worldcup.json` | Calendriers et résultats | Non | — | JSON | **200** | CC0 |
| Transfermarkt datasets (dcaribou) | `https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/{games,clubs,players,appearances,…}.csv.gz` | Matchs, compositions, valeurs marchandes | Non | 2012 → | CSV.gz (games : 5 Mo) | **200** | CC0 (le scraping de Transfermarkt est interdit, mais le dataset est publié) |
| ESPN soccer | `site.api.espn.com/apis/site/v2/sports/soccer/{fra.1,eng.1,…}/scoreboard` et `sports.core.api.espn.com/.../odds` | Résultats et cotes (Bet365, Unibet, DraftKings…) | Oui, à partir d'environ 2019 | 2010 → (résultats) | JSON | **200** | — |
| football-data.org v4 | `https://api.football-data.org/v4/competitions` | Résultats (offre gratuite : 12 compétitions, 10 requêtes/min, clé gratuite) | Non | — | JSON | **200** (la liste des compétitions répond sans clé) | Clé gratuite pour les matchs |
| TheSportsDB | `https://www.thesportsdb.com/api/v1/json/3/eventspastleague.php?id=4334` | Multi-sports (clé de test « 3 », derniers matchs seulement) | Non | — | JSON | **200** | Offre gratuite très limitée |
| API-Football (api-sports.io) | `https://v3.football.api-sports.io/` | Multi-sports, y compris des cotes | Oui | — | JSON | **403 « Missing application key »** | Offre gratuite : 100 requêtes par jour avec clé |
| Sportmonks | `https://api.sportmonks.com/v3/…` | — | Oui (payant) | — | — | **401** | Clé requise |
| FBref, Sofascore, FotMob | — | — | — | — | — | **403** (fbref, api.sofascore.com) ; FotMob : 404 (l'API a changé) | Bloqués ou modifiés |

## 10. Autres sports ANJ

| Sport | Source | URL | Contenu | Cotes ? | Période | Format | Accès testé | Licence / remarques |
|---|---|---|---|---|---|---|---|---|
| MMA (UFC) | **shortlikeafox/ultimate_ufc_dataset** | `https://raw.githubusercontent.com/shortlikeafox/ultimate_ufc_dataset/master/ufc-master.csv` | 7 177 combats et stats | **Oui** : `R_odds`/`B_odds` (US, 97 % remplis), cotes par méthode (décision, soumission, KO) | 2010-03 → 2026-03 | CSV, 3,2 Mo | **200** | Pas de licence |
| MMA (UFC) | jansen88/ufc-data | `https://raw.githubusercontent.com/jansen88/ufc-data/master/data/complete_ufc_data.csv` | Combats, profils, cotes favori/outsider | Oui | 1994 → 2023-09 | CSV | **200** | — |
| MMA (UFC) | Greco1899/scrape_ufc_stats | `https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/{ufc_event_details,ufc_fight_results,ufc_fight_stats,…}.csv` | ufcstats.com mis à jour régulièrement | Non | 1994 → **2026-09-26** | CSV | **200** | ufcstats.com ne répond pas en direct (000) |
| MMA | ESPN | `site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard` | Cartes et résultats | Pas de cotes trouvées (avril 2025) | — | JSON | **200** | — |
| Boxe | BoxRec | — | — | — | — | — | Non testé (accès avec compte, CGU strictes) | OddsPortal couvre la boxe |
| Formule 1 | **Jolpica-F1** (successeur d'Ergast) | `https://api.jolpi.ca/ergast/f1/{YYYY}/results.json` (et `qualifying`, `laps`, `pitstops`…) | Résultats complets | Non | 1950 → | JSON | **200** | Gratuit, environ 4 requêtes/s et 500/h |
| Formule 1 | F1 live timing statique (utilisé par FastF1) | `https://livetiming.formula1.com/static/{YYYY}/Index.json` | Télémétrie et timing | Non | 2018 → | JSON | **200** | Pour un usage via le package `fastf1` |
| Formule 1 | OpenF1 | `https://api.openf1.org/v1/sessions?year=2025` | — | — | 2023 → | JSON | **401 pendant une session live** (accès restreint aux comptes payants pendant les sessions) | Réessayer hors week-end de course |
| Golf | ESPN golf | `https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard?dates=YYYYMMDD` | Classements de tournois | Non | — | JSON | **200** | — |
| Golf | OWGR | `https://www.owgr.com/` | Classement mondial | Non | — | HTML/API interne | **200** | — |
| Golf, multi | HF `kennyhyder/sportsbookish-daily-odds` | `https://huggingface.co/datasets/kennyhyder/sportsbookish-daily-odds/resolve/main/data/latest.csv` | Instantané quotidien Kalshi contre médiane des books US (golf, NFL, NBA, MLB, NHL, EPL…) | Oui (probabilités implicites) | Instantané du jour uniquement | CSV | **200** | CC-BY-4.0. Il faut archiver soi-même chaque jour pour constituer un historique. |
| Fléchettes | dartsdatabase.co.uk, dartsorakel.com, mastercaller.com | Pages d'accueil | Résultats et stats (moyennes, 180) | Non | Ancien | HTML | **200** (les 3) | Scraping HTML. Cotes : OddsPortal (OddsHarvester ne gère pas les fléchettes, il faut un scraper Playwright maison). |
| Snooker | api.snooker.org | `https://api.snooker.org/?t=5` | API snooker.org | Non | Complet | JSON | **401**. Il faut un en-tête `X-Requested-By` obtenu en écrivant à snooker.org (gratuit sur demande). | — |
| Snooker | CueTracker | `https://www.cuetracker.net/` | Résultats et stats historiques | Non | Ancien | HTML | **200** | robots.txt interdit /Admin, /Update… |
| Tennis de table | ITTF results | `https://results.ittf.link/` | Résultats officiels | Non | — | HTML | **200** | Cotes : OddsPortal ou Betexplorer (non testé) |
| Badminton | BWF Tournament Software | `https://bwf.tournamentsoftware.com/` | Résultats | Non | — | HTML | **200** (page de cookies et consentement) | — |
| Cyclisme | ProCyclingStats, FirstCycling | `https://www.procyclingstats.com/race/tour-de-france/2025/gc` | Résultats | Non | — | HTML | **403** (les deux) | Package Python `procyclingstats` inutilisable depuis ici. robots.txt de PCS contient `Disallow: /` pour certains agents. |
| Cricket (bonus) | Cricsheet | `https://cricsheet.org/downloads/all_json.zip` (et des ZIP par format) | Balle par balle | Non | 2003 → | JSON/CSV | **200** (ZIP complet de 147 Mo, à éviter ; préférer les ZIP par compétition) | ODbL. robots.txt interdit `/data/`. |

## 11. Bookmakers agréés ANJ : accès en direct depuis ce conteneur

> L'objectif serait de capturer soi-même les cotes des bookmakers français pour construire un historique, faute de dataset public. **Aucun dataset public gratuit avec des cotes Winamax, Betclic, Unibet ou PMU n'a été trouvé.** Il faut donc les collecter soi-même, et cela demande une **IP française (résidentielle)**.

| Opérateur (licence ANJ) | Endpoint utilisé par les scrapers open source | Résultat depuis ici | Remarques |
|---|---|---|---|
| **Winamax** | HTML `https://www.winamax.fr/paris-sportifs/sports/{id}` contenant `var PRELOADED_STATE = {...};var BETTING_CONFIGURATION` (pretrehr/Sports-betting, kaiiine/axon, t0mm4rx…) ; WebSocket socket.io `sports-eu-west-3.winamax.*` (hugogpmr/surebets) | **403 CloudFront** (« Request blocked », y compris sur robots.txt et sur winamax.es) | Blocage géographique ou anti-datacenter. Fonctionne depuis une IP FR d'après les scrapers. |
| **Betclic** | `https://offer.cdn.betclic.fr/api/pub/v2/sports/{id}?application=2&countrycode=fr&language=fr&sitecode=frfr`, `…/v4/events/{id}?…` | **Proxy : `connect_rejected` (502 au CONNECT)** pour `offer.cdn.betclic.fr` ; www.betclic.fr répond **403** | Refus de la politique de sortie ou de l'amont. À tester depuis une IP FR. |
| **Unibet** (absorbe ParionsSport en ligne depuis le 24/03/2026 et ZEbet) | HTML `https://www.unibet.fr/paris-football` ; anciens `zones/*.json` (404) ; Kambi `ubfr` désactivé (« Unable to resolve customer ») | HTML **200**, mais DataDome (captcha) sur certaines routes et pas de cotes dans le HTML statique | `enligne.parionssport.fdj.fr` → 301 vers unibet.fr ; `zebet.fr` → unibet.fr. L'ancienne API ParionsSport `lvs-api` renvoie **401 « Missing X-LVS-HSToken »**. |
| PMU (paris-sportifs.pmu.fr) | Next.js côté client ; `pservices/more_events/…` (ancien) | **200**, mais la page est vide sans exécution JS | Il faut Playwright et une IP FR |
| Bwin.fr | `https://cds-api.bwin.fr/bettingoffer/fixtures?x-bwin-accessid={token}&lang=fr&country=FR` (le token se lit dans le trafic du site) | `sports.bwin.fr` redirige vers **help.bwin.fr/closed** (géobloqué) | — |
| PokerStars Sports FR | `https://sports.pokerstarssports.fr/sportsbook/v1/api/getSportTree…` | **Proxy `connect_rejected`** ; www redirige vers foxsports.com/betting | — |
| Bet365.fr, Betsson.fr, Olybet.fr | — | **403** | — |
| Netbet, Genybet, CircusBet, DAZN Bet, Vbet | HTML | **200** (Netbet 700 ko, CircusBet 460 ko, DAZN Bet 405 ko, Genybet 234 ko) | Parsing HTML possible a priori (non approfondi). Ce sont des bookmakers secondaires. |
| Feelingbet | — | Timeout (000) | — |
| **Pinnacle** (non agréé ANJ, référence « sharp ») | `https://guest.api.arcadia.pinnacle.com/0.1/sports/{sport_id}/leagues?all=false`, `/leagues/{id}/matchups`, `/leagues/{id}/markets/straight` | **200, sans clé** (Ligue 1 : 19 matchups, prix « s;0;m » avec limites) | Pas d'historique : il faut journaliser soi-même (par exemple ouverture + T-1h + clôture). C'est le meilleur substitut au « PS » disparu de football-data et tennis-data. Usage modéré. |
| The Odds API | `https://api.the-odds-api.com/v4/sports?apiKey=…` | **401** sans clé (hôte joignable) | Offre gratuite : 500 crédits par mois. Bookmakers de la région « eu » et, selon la documentation, des books FR (Winamax, Betclic, Unibet : **à vérifier**). L'historique est payant. |

**Projets open source de référence (France)** : `pretrehr/Sports-betting` (Winamax, Betclic, Unibet, ParionsSport, PMU, Zebet, Bwin, Netbet, PokerStars, Pinnacle…), `sferez/Arbitrage_Betting_Bot`, `t0mm4rx/french-betting-arbitrage`, `Cooya/Betbee`, `kaiiine/axon` (2026), `hugogpmr/surebets`. Beaucoup visent ParionsSport et ZEbet, **qui n'existent plus**.

**Historique des cotes FR : seule piste gratuite.** OddsPortal affiche les bookmakers selon le pays du visiteur. Depuis une IP française, les pages d'archives montrent les cotes de clôture Winamax, Betclic, Unibet.fr, etc. (à vérifier). Concrètement : OddsHarvester + Playwright + IP FR + cadence lente.

## 12. URLs vérifiées prêtes à l'emploi

Toutes ont répondu **200** le 2026-10-02 depuis ce conteneur, et un échantillon a été parsé. Elles sont aussi dans `verified_urls.json`.

```text
# --- TENNIS (résultats + cotes) ---
https://raw.githubusercontent.com/nick-benelli/Tennis-Data-Pipeline/main/data/raw/uk/atp/uk_atp_singles_raw_{2000..2026}.csv
https://raw.githubusercontent.com/nick-benelli/Tennis-Data-Pipeline/main/data/raw/uk/wta/uk_wta_singles_raw_{2007..2026}.csv
https://raw.githubusercontent.com/DanielSzakacs/atp_data/main/{2005..2024}.csv            # secours ATP
https://raw.githubusercontent.com/DanielSzakacs/wta_data/main/{YYYY}.csv                  # secours WTA (2024 vérifié)
https://huggingface.co/datasets/groundhog2107/atp_tennis/resolve/main/atp_tennis.csv      # ATP 2000-2026/03, Odd_1/Odd_2
# --- TENNIS (résultats + stats, sans cotes) ---
https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main/atp/atp_matches_{1968..2026}.csv
https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main/wta/wta_matches_{YYYY}.csv
https://raw.githubusercontent.com/Tennismylife/TML-Database/master/{1968..2026}.csv
https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/charting-{m,w}-matches.csv

# --- NBA ---
https://www.sportsbookreviewsonline.com/scoresoddsarchives/nba-odds-{2007-08..2022-23}        # HTML -> pd.read_html
https://raw.githubusercontent.com/flancast90/sportsbookreview-scraper/main/data/nba_archive_10Y.json
https://raw.githubusercontent.com/wippa-studios/wippa-nba-data/main/seasons/{2016-2017..2025-2026}/nba_{saison}_results_odds.csv
https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=YYYYMMDD     # -> event ids
https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/{id}/competitions/{id}/odds

# --- NHL ---
https://www.sportsbookreviewsonline.com/scoresoddsarchives/nhl-odds-{2007-08..2022-23}        # 2020-21 = nhl-odds-2021
https://raw.githubusercontent.com/flancast90/sportsbookreview-scraper/main/data/nhl_archive_10Y.json
https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/events/{id}/competitions/{id}/odds
https://api-web.nhle.com/v1/score/YYYY-MM-DD
https://moneypuck.com/moneypuck/playerData/seasonSummary/{YYYY}/regular/teams.csv

# --- NFL ---
https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv
https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv
https://www.sportsbookreviewsonline.com/scoresoddsarchives/nfl-odds-{2007-08..2021-22}
https://huggingface.co/datasets/tuxmx/nfl_bets_scores/resolve/main/spreadspoke_scores.csv

# --- MLB ---
https://www.sportsbookreviewsonline.com/wp-content/uploads/sportsbookreviewsonline_com_737/mlb-odds-{2010..2021}.xlsx
https://huggingface.co/datasets/Oronto/baseball-stats-cleaned_oddsportal_mlb/resolve/main/data/train-00000-of-00001.parquet
https://raw.githubusercontent.com/flancast90/sportsbookreview-scraper/main/data/mlb_archive_10Y.json
https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=YYYY-MM-DD
https://www.retrosheet.org/gamelogs/gl{YYYY}.zip

# --- RUGBY (résultats) ---
https://raw.githubusercontent.com/transientlunatic/Rugby-Data/master/json/{top14|premiership|celtic|super-rugby|currie-cup|npc}-{YYYY}-{YYYY+1}.json
https://raw.githubusercontent.com/dirknbr/rugby-elo/main/match_data_20251102.csv
https://site.api.espn.com/apis/site/v2/sports/rugby/{180659|270559|267979|270557|242041|164205}/scoreboard?dates=YYYYMMDD
https://site.api.espn.com/apis/site/v2/sports/rugby-league/3/scoreboard?dates=YYYYMMDD

# --- HANDBALL / VOLLEY / HOCKEY / BASEBALL (résultats + cote moyenne, HTML) ---
https://www.betexplorer.com/handball/france/starligue-2024-2025/results/
https://www.betexplorer.com/volleyball/france/ligue-a-2024-2025/results/
https://www.betexplorer.com/hockey/usa/nhl-2024-2025/results/
#   -> python3 betexplorer_results.py <url>

# --- FOOTBALL (hors football-data.co.uk déjà intégré) ---
https://understat.com/getLeagueData/{EPL|La_liga|Bundesliga|Serie_A|Ligue_1|RFPL}/{YYYY}   # header X-Requested-With
https://raw.githubusercontent.com/martj42/international_results/master/results.csv
https://raw.githubusercontent.com/xgabora/Club-Football-Match-Data-2000-2025/main/data/EloRatings.csv
https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json
https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/games.csv.gz                      # transfermarkt-datasets
https://sports.core.api.espn.com/v2/sports/soccer/leagues/{fra.1|eng.1|esp.1|ger.1|ita.1}/events/{id}/competitions/{id}/odds

# --- AUTRES ---
https://raw.githubusercontent.com/shortlikeafox/ultimate_ufc_dataset/master/ufc-master.csv  # UFC + cotes
https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/ufc_fight_results.csv
https://api.jolpi.ca/ergast/f1/{YYYY}/results.json
https://guest.api.arcadia.pinnacle.com/0.1/sports/{29=foot,33=tennis,4=basket,19=hockey,...}/leagues?all=false   # live uniquement
```

**Profondeur des cotes ESPN (testé)**

| Ligue | Premier match avec cotes trouvé | Bookmakers | open/close structurés |
|---|---|---|---|
| NBA | 2015-01 (rien en 2008 ni 2012) | 5Dimes, BetOnline, Bovada, « Opening », consensus → Caesars, Unibet, Westgate (2019) → DraftKings, MGM, ESPN BET, PointsBet (2023) | Depuis 2023 (ESPN BET), 2026 (DraftKings) |
| NFL | 2015-10 (rien en 2010) | idem | Récent |
| NHL | 2020-01 (rien en 2010 ni 2015) | Bet365, DraftKings, Caesars, Unibet, Westgate | Oui en 2024 (11 bookmakers) |
| MLB | 2010-07 (totaux surtout), complet en 2022 | 14 bookmakers en 2022 | Récent |
| Football (eng.1, fra.1) | 2020-03 (Bet365, Unibet, DraftKings) ; 2015 : seulement un O/U « bloomberg » | ESPN BET open/close en 2025 | 2025 |
| UFC, tennis | Pas de cotes trouvées | — | — |

## 13. Sources bloquées et contournements

| Source | Symptôme (depuis ce conteneur) | Cause probable | Contournement |
|---|---|---|---|
| tennis-data.co.uk | 403 « Attention Required! \| Cloudflare » (http et https) | Anti-bot Cloudflare sur les IP de datacenter | Miroir `nick-benelli/Tennis-Data-Pipeline` (à jour en septembre 2026). Sinon, téléchargement depuis une IP résidentielle puis commit dans le dépôt du projet. |
| JeffSackmann/tennis_atp, tennis_wta, tennis_slam_pointbypoint, tennis_pointbypoint | 404 | Dépôts supprimés par l'auteur (2026) | `Aneeshers/tennis-sackmann-archive` (GitHub et HF), `Tennismylife/TML-Database`, HF `davidtadediji/tennis-atp` |
| api.clubelo.com | 502 (IIS) en HTTP, TLS muet en HTTPS ; `/Fixtures` désactivé | API fermée, bientôt avec authentification | `clubelo.com` HTML (200), `xgabora/.../EloRatings.csv`, ou Elo maison calculé sur football-data |
| fbref.com, pro-football-reference, sports-reference | 403 | Anti-bot et politique d'usage stricte (sports-reference limite à environ 10-20 requêtes/min) | Understat (xG), football-data (HxG/AxG en 2026-27), nflverse, ESPN |
| api.sofascore.com, sofascore.com | 403 | Anti-bot | ESPN, Flashscore (HTML 200), Betexplorer |
| aussportsbetting.com | 403 | Anti-bot | Betexplorer, OddsPortal, ESPN rugby-league |
| stats.nba.com / cdn.nba.com | timeout / 403 | Blocage des IP cloud par la NBA | ESPN API, HF `cdechoch/nba-data-archive` |
| api.github.com, github.com (HTML), codeload.github.com (zip) | 403 | Politique du proxy | `raw.githubusercontent.com` (200), releases `github.com/<o>/<r>/releases/download/...` (200), Hugging Face (200), WebFetch côté outil pour lister les dépôts |
| winamax.fr | 403 CloudFront | Géoblocage hors FR / datacenter | IP FR résidentielle ; Pinnacle guest API comme référence |
| offer.cdn.betclic.fr, sports.pokerstarssports.fr | `connect_rejected` (proxy) | Politique de sortie du proxy ou refus en amont | Tester depuis le poste local ou une IP FR |
| www.betclic.fr, bet365.fr, betsson.fr, olybet.fr, zebet.fr | 403 / redirection | Géoblocage | IP FR |
| sports.bwin.fr | Redirection vers `help.bwin.fr/closed` | Géoblocage | IP FR |
| procyclingstats.com, firstcycling.com | 403 | Anti-bot | IP résidentielle ; package `procyclingstats` en local |
| api.openf1.org | 401 pendant les sessions live | Nouvelle restriction OpenF1 | Jolpica-F1, FastF1 (livetiming.formula1.com en 200) |
| Kaggle (téléchargement) | 200, mais renvoie la page HTML de connexion | Authentification requise | Compte gratuit, `pip install kaggle`, `~/.kaggle/kaggle.json`, puis `kaggle datasets download -d <slug>` (kaggle.com est joignable) |
| api.snooker.org | 401 | En-tête `X-Requested-By` obligatoire | Demander un identifiant à snooker.org (gratuit) |
| HF `michaelmallari/sportsbook-nhl` | 401 | Dataset restreint (gated) | Accepter les conditions sur HF et utiliser un token |

## 14. Faisabilité du scraping et éthique

- **Sources ouvertes, à privilégier.** raw GitHub (nflverse sous CC-BY, martj42 sous CC0, StatsBomb avec attribution, Sackmann et TML sous **CC BY-NC-SA**, donc non commercial et partage à l'identique), Hugging Face (licence propre à chaque dataset), Jolpica, MLB Stats API (non commercial) et Retrosheet (mention obligatoire). **Point d'attention licence** : les données tennis-data et football-data sont gratuites mais avec attribution et en principe non commerciales, et les jeux dérivés de Sackmann imposent la licence NC-SA. Une bibliothèque open source peut **fournir des loaders** pointant vers ces URLs, mais **ne doit pas redistribuer les données** si la licence ne le permet pas.
- **SBR (sportsbookreviewsonline)** : robots.txt `Allow: /` (sauf `/go/`) et archives publiques. Les archives s'arrêtent en 2022-23. Rester sous environ 1 requête par seconde.
- **ESPN (API non documentée)** : pas de CGU d'API publiques. Les CGU ESPN interdisent l'usage commercial et la redistribution. Mettre en cache, faire environ 1 requête par seconde, et prévoir que les endpoints changent sans préavis.
- **Understat** : `robots.txt: Disallow: /`. L'usage reste toléré par la communauté (soccerdata, understatapi), mais c'est contraire au souhait du site : usage personnel, cache agressif, aucune redistribution.
- **Betexplorer, OddsPortal, Flashscore** (même groupe, Livesport) : les CGU interdisent l'extraction automatisée. robots.txt interdit `?year=`, `/bookmaker/`, `/ajax-widget/`, `*/feed/*`, `/live/`. Si on les utilise : usage de recherche personnel, cadence lente (au moins 3 à 5 s), pas de contournement d'anti-bot, pas de redistribution brute.
- **Bookmakers ANJ** : les CGU de Winamax, Betclic, Unibet et des autres interdisent le scraping. Les protections sont actives (CloudFront, DataDome, géoblocage). La collecte pour un usage personnel non commercial est une zone grise ; ne jamais contourner un captcha ni une authentification. **Alternative propre** : The Odds API (offre gratuite à 500 crédits par mois ; couverture des books FR à vérifier), ou la Pinnacle guest API comme référence de marché.
- **Kaggle** : chaque dataset a sa licence (souvent CC BY-NC-SA ou « unknown »), à vérifier au cas par cas. Il faut un token pour télécharger.
- **Fiabilité des colonnes de cotes** : vérifier ce que « closing » veut dire selon la source (SBR = consensus Las Vegas à la clôture ; football-data = cotes relevées le vendredi ou samedi + colonnes C = clôture ; tennis-data = « pré-match juste avant le début »). Rappel : **PS (Pinnacle) a disparu en 2026**, passer à **BFE** (exchange, plus proche d'un prix « juste ») ou à **Avg/Max**.

## 15. Snippets utiles

Ils se trouvent dans `helpers_sources.py` et `betexplorer_results.py`. Les points clés :

```python
# SBR NHL/NBA/NFL : la table HTML a l'en-tête en 1re ligne et 2 lignes par match (V puis H)
t = pd.read_html(io.StringIO(requests.get(url, headers=UA).text))[0]
raw = t.iloc[1:]; raw.columns = t.iloc[0]
games = raw.iloc[0::2].reset_index(drop=True).add_suffix("_v").join(raw.iloc[1::2].reset_index(drop=True).add_suffix("_h"))

# ESPN : event ids puis odds
ev = requests.get("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard", params={"dates": "20240115"}).json()["events"]
odds = requests.get(f"https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/events/{eid}/competitions/{eid}/odds").json()["items"]
# item["homeTeamOdds"]["open"]["moneyLine"]["american"], item["homeTeamOdds"]["close"][...], item["provider"]["name"]

# Understat : endpoint AJAX (le HTML n'embarque plus les données)
d = requests.get("https://understat.com/getLeagueData/Ligue_1/2024", headers={"User-Agent": UA, "X-Requested-With": "XMLHttpRequest"}).json()
# d["dates"] (matchs + xG + forecast), d["teams"][id]["history"] (xG, PPDA par match), d["players"]

# Betexplorer : la cote du résultat gagnant est dans un <span data-odd> imbriqué, les autres sur le <td>
el = td if td.get("data-odd") else td.select_one("[data-odd]")
```

## 16. Recommandations par sport (synthèse)

| Sport | Résultats | Cotes historiques gratuites (vérifiées) | Trou / action |
|---|---|---|---|
| Football | football-data (intégré), Understat, StatsBomb, martj42 | football-data (B365, BFE, Avg/Max, clôture), ESPN (2019+) | Pinnacle a disparu : journaliser la Pinnacle guest API soi-même |
| Tennis | Archive Sackmann (jusqu'en 2026-05), TML | **Miroir tennis-data nick-benelli (ATP 2000-2026, WTA 2007-2026)**, HF atp_tennis | PS absent depuis février 2026 : utiliser BFE ou Avg |
| NBA | ESPN, nba_api (bloqué ici) | SBR 2007-2023, flancast90 2011-2022, wippa 2016-2026 (ML), ESPN 2015+ | Combler 2023-2026 (spread et total) avec ESPN |
| NHL | api-web.nhle.com, MoneyPuck | SBR 2007-2023, flancast90 2011-2022, ESPN 2019+ (open/close 2023+) | ESPN pour 2023→ |
| NFL | nflverse | **nflverse games.csv (1999-2026, ML depuis 2006)** | Rien |
| MLB | MLB Stats API, Retrosheet | SBR xlsx 2010-2021, HF Oronto 2006-2024 (ML), ESPN | ESPN pour 2025→ |
| Rugby | Rugby-Data JSON (Top 14, Premiership, URC…), ESPN | Aucune source gratuite en téléchargement direct | OddsHarvester (OddsPortal) ou AusSportsBetting depuis une IP résidentielle |
| Handball / Volley | Betexplorer, ESPN (NCAA volley) | Betexplorer (cote moyenne), OddsPortal (par bookmaker) | Construire un scraper lent et respectueux |
| MMA | Greco1899 (ufcstats, à jour) | ultimate_ufc_dataset (2010-2026/03) | — |
| F1 / Golf / Fléchettes / Snooker / TT / Badminton / Cyclisme | Jolpica, ESPN golf, CueTracker, dartsdatabase, ITTF, BWF | Pas de dataset gratuit vérifié | OddsPortal pour les vainqueurs et les duels |
