# Catalogue des dépôts open source : prédiction sportive, ratings, cotes, value betting, bankroll et scraping

> **Date de l'état des lieux : 2 octobre 2026.**
> **Méthode.** Métadonnées lues sur les pages GitHub (pages *topics* et dépôts) et sur l'API ecosyste.ms. Les READMEs et une partie du code ont été lus via `raw.githubusercontent.com`. Les statuts CRAN viennent de cran.r-project.org.
> - **Étoiles (★)** : valeurs approximatives. L'index ecosyste.ms peut avoir quelques mois de retard sur GitHub. Quand les deux sources divergeaient, la valeur GitHub a été retenue.
> - **« Dernier push »** : date de la dernière activité observée, au format AAAA-MM.
> - **Performances annoncées** : elles sont reprises **telles que publiées** puis commentées. Sauf mention contraire, aucune n'a été reproduite ici.
> - **Licence « aucune »** : le code est sous droit d'auteur par défaut. On peut s'en inspirer, mais on ne peut pas le copier.

---

## 0. TL;DR : ce qu'il faut retenir

1. **Deux briques sont réutilisables presque telles quelles.** `penaltyblog` (Python, MIT) regroupe les modèles de buts (Poisson, Dixon-Coles, Poisson bivarié, binomiale négative, Weibull-copule, Bayésien hiérarchique), les ratings (Elo, Pi, Massey, Colley), 7 méthodes de dé-margination, Kelly, l'arbitrage, le RPS et un backtest. `sports-betting` (georgedouzas, MIT) apporte des dataloaders stats+cotes, une API « bettor » compatible scikit-learn et un backtest walk-forward.
2. **La référence pour retirer la marge est le package R `implied`** (opisthokonta, GPL-3). Il propose 9 méthodes : basic/multiplicative, additive, wpo, power, shin, bb, odds ratio, jsd et goto/ooepc. On le porte en Python avec les mêmes vecteurs de test. Sur les cotes de clôture Pinnacle, la normalisation simple est **biaisée** par le biais favori-outsider. Power, Shin et odds-ratio font mieux (chiffres en §5).
3. **Bookmakers français (ANJ) : il n'existe pas de scraper open source maintenu et multi-opérateurs.**
   - Le seul projet de référence, `pretrehr/Sports-betting` (★≈534), couvre 12 opérateurs FR mais n'a **plus de commit depuis décembre 2023**.
   - Nos tests du 2 octobre 2026 depuis une IP non française : la page Winamax répond **403**, l'API CDN Betclic ne répond pas, et l'endpoint Unibet `zones/navigation.json` **redirige vers « page-introuvable »**.
   - Les projets récents (Winator, bethurtadom, paris-sportif) visent **Winamax seulement**, avec 0 étoile et un seul développeur.
   - **Conclusion : il faut écrire nos propres adaptateurs FR**, en s'inspirant de la cartographie des endpoints de pretrehr. En complément ou en repli légal : The Odds API, région `fr`, qui couvre betclic_fr, winamax_fr, unibet_fr, pmu_fr et netbet_fr.
4. **Plusieurs ruptures récentes de l'écosystème sont à intégrer dans le design** (détails en §3) :
   - FBref a perdu les stats avancées Opta (20/01/2026).
   - Les dépôts tennis de Jeff Sackmann ont été **supprimés** (~juin 2026).
   - L'API publique Pinnacle est **fermée** (23/07/2025).
   - `worldfootballR` a été archivé (09/2025) et `nfl_data_py` déprécié au profit de `nflreadpy`.
5. **Sur les performances, scepticisme par défaut.**
   - Les ROI à deux chiffres annoncés sur GitHub (tennis +20 % à +70 %, football +1069 %) tiennent presque toujours à de la fuite de données, à des hyperparamètres choisis sur la période de test, à l'usage des **meilleures cotes du marché** (inatteignables en pratique) ou à de petits échantillons.
   - Les résultats solides et reproductibles sont modestes. Buchdahl obtient **+2 à +5 % de yield** en pariant contre les cotes « justes » de Pinnacle. Kaunitz et al. obtiennent **+3,5 %** sur 479 440 matchs, puis ont vu leurs comptes **limités**.
   - Un exemple instructif : Walsh & Joshi (2024) avaient conclu que sélectionner les modèles par calibration plutôt que par exactitude rapportait **+34,7 % de ROI contre −35,2 %**. Le corrigendum de 2025 ramène ces chiffres à **−9,8 % contre −26,8 %**.

---

## 1. Tableau de synthèse

Légende de la colonne *Note* : ⭐⭐⭐ = brique de qualité production à réutiliser, ⭐⭐ = utile ou inspirant, ⭐ = référence historique ou à prendre avec précaution, ⚠️ = cassé, abandonné ou problématique.

| # | Catégorie | Projet | Lang. | ★ | Dernier push | Licence | Usage pour nous | Note |
|---|---|---|---|---|---|---|---|---|
| 1 | Modélisation+paris | [martineastwood/penaltyblog](https://github.com/martineastwood/penaltyblog) | Python/Cython | 228 | 2026-10 | MIT | Modèles de buts, ratings, dé-margination, Kelly, RPS, backtest | ⭐⭐⭐ |
| 2 | Modélisation+paris | [georgedouzas/sports-betting](https://github.com/georgedouzas/sports-betting) | Python | 804 | 2026-09 | MIT | Dataloaders, bettors sklearn, backtest, serveur MCP | ⭐⭐⭐ |
| 3 | Modélisation | [opisthokonta/goalmodel](https://github.com/opisthokonta/goalmodel) | R | 99 | 2024-03 | GPL-3 | Référence DC / NegBin / CMP / hurdle, expg depuis cotes | ⭐⭐⭐ |
| 4 | Dé-margination | [opisthokonta/implied](https://github.com/opisthokonta/implied) (CRAN `implied`) | R | 9 | 2026-02 | GPL-3 | 9 méthodes de probabilités implicites | ⭐⭐⭐ |
| 5 | Modélisation | [leoegidi/footbayes](https://github.com/leoegidi/footbayes) (CRAN `footBayes`) | R/Stan | 59 | 2026-09 | GPL-2 | Poisson bivarié, Skellam, diag-inflated, modèles dynamiques bayésiens | ⭐⭐ |
| 6 | Modélisation | [Torvaney/mezzala](https://github.com/Torvaney/mezzala) | Python | 40 | 2021-10 | Apache-2.0 | DC générique (« adapters ») | ⭐⭐ |
| 7 | Modélisation | [Torvaney/regista](https://github.com/Torvaney/regista) | R | 91 | 2025-11 | GPL-3 | DC « tidy » | ⭐⭐ |
| 8 | App ML football | [kochlisGit/ProphitBet](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor) | Python | 576 | 2026-04 | MIT | GUI, football-data + Footystats, ML | ⭐⭐ |
| 9 | Blog-code | [dashee87/blogScripts](https://github.com/dashee87/blogScripts) | Jupyter | 385 | 2022-12 | MIT | Tutoriels Poisson / DC / time-weighting | ⭐⭐ |
| 10 | Stratégie | [Lisandro79/BeatTheBookie](https://github.com/Lisandro79/BeatTheBookie) | MATLAB | 624 | 2021-10 | GPL-3 | Value bet par consensus du marché, dataset 479k matchs | ⭐⭐ |
| 11 | Dé-margination | [mberk/shin](https://github.com/mberk/shin) | Python | 105 | 2026-08 | MIT | Shin rapide (z analytique pour 2 issues) | ⭐⭐⭐ |
| 12 | Dé-margination | [gotoConversion/goto_conversion](https://github.com/gotoConversion/goto_conversion) | Python | 115 | 2026-09 | MIT | Méthode goto, Shin efficace | ⭐⭐ |
| 13 | Maths pari | [sedemmler/WagerBrain](https://github.com/sedemmler/WagerBrain) | Python | 315 | 2020-05 | MIT | Conversion cotes, EV, Kelly, arbitrage, vig | ⭐ |
| 14 | Maths pari | [ian-shepherd/pybettor](https://github.com/ian-shepherd/pybettor) | Python | 14 | 2024-09 | MIT | Conversion de cotes | ⭐ |
| 15 | Maths pari | [papagorgio23/bettoR](https://github.com/papagorgio23/bettoR) | R | 78 | 2023-05 | autre | Conversion, Kelly | ⭐ |
| 16 | Maths pari | [HintikkaKimmo/surebet](https://github.com/HintikkaKimmo/surebet) | Python | 87 | 2026-02 | MIT | Arbitrage, value bet sizing | ⭐ |
| 17 | Bankroll | [xandao-dev/monte-carlo-betting-simulations](https://github.com/xandao-dev/monte-carlo-betting-simulations) | Python | 26 | 2022-12 | MIT | Simulations Monte Carlo (Martingale…) | ⭐ |
| 18 | Évaluation | [conorwalsh99/ml-for-sports-betting](https://github.com/conorwalsh99/ml-for-sports-betting) | Python | 3 | archivé 2025-02 | MIT | Calibration vs exactitude (NBA) + corrigendum | ⭐⭐ |
| 19 | Stratégie | [BettingIsCool/woc-streamlit](https://github.com/BettingIsCool/woc-streamlit) | Python | 7 | 2021-06 | aucune | Démo « Wisdom of the Crowd » | ⭐ |
| 20 | Ratings | [sublee/elo](https://github.com/sublee/elo) | Python | 98 | 2023-04 | BSD | Elo minimal | ⭐ |
| 21 | Ratings | [mbhynes/skelo](https://github.com/mbhynes/skelo) | Python | 17 | 2022-12 | BSD | Elo / Glicko-2 avec API sklearn et ratings datés | ⭐⭐ |
| 22 | Ratings | [sublee/trueskill](https://github.com/sublee/trueskill) | Python | 803 | 2023-08 | BSD | TrueSkill | ⭐⭐ |
| 23 | Ratings | [sublee/glicko2](https://github.com/sublee/glicko2) | Python | 125 | 2022-12 | BSD-3 | Glicko-2 | ⭐ |
| 24 | Ratings | [vivekjoshy/openskill.py](https://github.com/vivekjoshy/openskill.py) | Python | 373 | 2026-05 | MIT | Weng-Lin (multi-joueurs), rapide | ⭐⭐ |
| 25 | Ratings | [eheinzen/elo](https://github.com/eheinzen/elo) (CRAN `elo`) | R | 38 | 2023-10 | GPL-2 | Elo avec formule, MOV, régression | ⭐⭐ |
| 26 | Ratings | CRAN [`PlayerRatings`](https://cran.r-project.org/package=PlayerRatings) | R/C | – | 2020-03 | GPL-3 | Elo, Glicko, Glicko-2, **Stephenson** | ⭐⭐ |
| 27 | Ratings | [larsvancutsem/piratings](https://github.com/larsvancutsem/piratings) (CRAN) | R | 13 | 2019-05 | GPL-2 | Pi-ratings (Constantinou & Fenton) | ⭐ |
| 28 | Ratings | CRAN `fbRanks` (E. Holmes) | R | – | archivé CRAN 2022-06 | – | Classement Poisson multi-ligues | ⚠️ |
| 29 | Ratings NFL | [fivethirtyeight/nfl-elo-game](https://github.com/fivethirtyeight/nfl-elo-game) | Python | 348 | 2023-05 | MIT | Elo 538 et protocole d'évaluation | ⭐⭐ |
| 30 | Ratings NFL | [greerreNFL/nfelo](https://github.com/greerreNFL/nfelo) | Python | 60 | 2026-09 | aucune | Elo NFL calé sur le marché | ⭐⭐ |
| 31 | Data foot | [probberechts/soccerdata](https://github.com/probberechts/soccerdata) | Python | 2071 | 2026-08 | Apache-2.0 | Scrapers ClubElo, ESPN, FBref, football-data, Sofascore, SoFIFA, Understat, WhoScored | ⭐⭐⭐ |
| 32 | Data foot | [oseymour/ScraperFC](https://github.com/oseymour/ScraperFC) | Python | 409 | 2026-05 | GPL-3 | Capology, ClubElo, FBref, Sofascore, Transfermarkt, Understat | ⭐⭐ |
| 33 | Data foot | [JaseZiv/worldfootballR](https://github.com/JaseZiv/worldfootballR) | R | 601 | **archivé 2025-09** | – | FBref / Transfermarkt / Understat | ⚠️ |
| 34 | Data foot | [amosbastian/understat](https://github.com/amosbastian/understat) | Python | 185 | 2025-12 | MIT | Client asynchrone Understat (xG) | ⭐⭐ |
| 35 | Data foot | [collinb9/understatAPI](https://github.com/collinb9/understatAPI) | Python | 36 | 2026-02 | MIT | Client Understat | ⭐ |
| 36 | Data foot | [statsbomb/statsbombpy](https://github.com/statsbomb/statsbombpy) + [open-data](https://github.com/statsbomb/open-data) | Python/JSON | 745 / 3,7k | actif | conditions d'utilisation StatsBomb | Événements gratuits (sélection de compétitions) | ⭐⭐ |
| 37 | Data foot | [PySport/kloppy](https://github.com/PySport/kloppy) | Python | 557 | 2026-10 | BSD-3 | Standardisation événements / tracking | ⭐⭐ |
| 38 | Data foot | [ML-KULeuven/socceraction](https://github.com/ML-KULeuven/socceraction) | Python | 817 | 2026-01 | MIT | SPADL, VAEP, xT | ⭐⭐ |
| 39 | Data foot | [ML-KULeuven/soccer_xg](https://github.com/ML-KULeuven/soccer_xg) | Python | 260 | 2024-06 | Apache-2.0 | Entraînement de modèles xG | ⭐ |
| 40 | Viz foot | [andrewRowlinson/mplsoccer](https://github.com/andrewRowlinson/mplsoccer) | Python | 547 | 2026-09 | MIT | Visualisations | ⭐ |
| 41 | Data foot | [American-Soccer-Analysis/itscalledsoccer](https://github.com/American-Soccer-Analysis/itscalledsoccer) | Python/R | 62 | 2026-09 | MIT | API MLS/NWSL (xG) | ⭐ |
| 42 | Dataset foot | [xgabora/Club-Football-Match-Data-2000-2025](https://github.com/xgabora/Club-Football-Match-Data-2000-2025) | CSV | 208 | 2026-09 | MIT | 238 858 matchs, 27 pays, cotes + Elo | ⭐⭐⭐ |
| 43 | Dataset foot | [jalapic/engsoccerdata](https://github.com/jalapic/engsoccerdata) | R | 781 | 2026-02 | GPL≥2 | Résultats 1871-2022 | ⭐⭐ |
| 44 | Dataset foot | [martj42/international_results](https://github.com/martj42/international_results) | CSV | 523 | 2026-08 | CC0 | Matchs internationaux depuis 1872 | ⭐⭐ |
| 45 | Dataset foot | [openfootball/football.json](https://github.com/openfootball/football.json) | JSON | 1025 | 2026-09 | CC0 | Calendriers et résultats, domaine public | ⭐⭐ |
| 46 | Ressources | [eddwebster/football_analytics](https://github.com/eddwebster/football_analytics) | – | 2776 | 2025-10 | – | Méga-liste de ressources | ⭐⭐ |
| 47 | Cotes | [jordantete/OddsHarvester](https://github.com/jordantete/OddsHarvester) | Python | 256 | 2026-10 | MIT | Scraper OddsPortal (historique + live) | ⭐⭐⭐ |
| 48 | Cotes | [S1M0N38/soccerapi](https://github.com/S1M0N38/soccerapi) | Python | 179 | 2022-12 | MIT | 888sport / bet365 / Unibet | ⚠️ |
| 49 | Cotes | [dos-2/oddshub](https://github.com/dos-2/oddshub) | Go | 126 | 2025-09 | Apache-2.0 | TUI sur The Odds API | ⭐ |
| 50 | Cotes | [cvidan/bet365-scraper](https://github.com/cvidan/bet365-scraper) | Python | 154 | 2019-02 | aucune | Selenium bet365 | ⚠️ |
| 51 | Cotes | [HaraldNordgren/betting-crawler](https://github.com/HaraldNordgren/betting-crawler) | Python | 48 | 2018-08 | MIT | Surebets Nordicbet / Unibet / Betway | ⚠️ |
| 52 | Cotes | [gto76/bets](https://github.com/gto76/bets) | – | 47 | 2016-01 | – | Scraper multi-bookmakers | ⚠️ |
| 53 | Arbitrage | [personal-coding/Live-Sports-Arbitrage-Bet-Finder](https://github.com/personal-coding/Live-Sports-Arbitrage-Bet-Finder) | Python | 294 | 2023-11 | – | Arbitrage live FanDuel / DK / WH | ⚠️ |
| 54 | Arbitrage | [l-portet/surebet-finder](https://github.com/l-portet/surebet-finder) | JS | 72 | 2024-10 | – | Bot surebet (auteur FR) | ⭐ |
| 55 | Cotes | [dashee87/betScrapeR](https://github.com/dashee87/betScrapeR) | R | 60 | 2016-12 | – | Cotes live (Betfair…) | ⚠️ |
| 56 | Cotes | [sportsdataverse/oddsapiR](https://github.com/sportsdataverse/oddsapiR) | R | 10 | 2026-09 | – | Wrapper The Odds API | ⭐ |
| 57 | **Cotes FR** | [pretrehr/Sports-betting](https://github.com/pretrehr/Sports-betting) | Python | 534 | **2023-12** | MIT | 12 bookmakers ANJ, freebets, surebets | ⭐⭐ (⚠️ scrapers) |
| 58 | **Cotes FR** | [Ghantard/winator](https://github.com/Ghantard/winator) | Python | 0 | 2026-09 | aucune | Winamax + consensus The Odds API + Kelly | ⭐⭐ |
| 59 | **Cotes FR** | [samuelhm/bethurtadom](https://github.com/samuelhm/bethurtadom) | Python | 0 | 2026-03 | MIT (badge) | Winamax + bet365 live, Playwright + Camoufox | ⭐⭐ |
| 60 | **Cotes FR** | [Harotensnor/paris-sportif](https://github.com/Harotensnor/paris-sportif) | JS/Python | 0 | 2026-09 | aucune | Dashboard Winamax, pipeline GitHub Actions | ⭐ |
| 61 | **Cotes FR** | [Cooya/Betbee](https://github.com/Cooya/Betbee) | JS | 0 | 2018-04 | – | Winamax / Unibet | ⚠️ |
| 62 | **Cotes FR** | [bettor-league/parions-sport-batch](https://github.com/bettor-league/parions-sport-batch) | – | 0 | 2020-06 | – | API point de vente FDJ | ⚠️ |
| 63 | **Cotes FR** | [BoboTiG/paris-en-ligne](https://github.com/BoboTiG/paris-en-ligne) | Python | 2 | archivé 2024-11 | MIT | Statistiques Betclic | ⚠️ |
| 64 | Cotes (hors ANJ) | [diouetq/Scrapping-Bet](https://github.com/diouetq/Scrapping-Bet) | Python | 0 | 2026-09 | – | Sportaza / Betify / Greenluck, **non agréés** | ⚠️ |
| 65 | Exchange | [betcode-org/flumine](https://github.com/betcode-org/flumine) | Python | 246 | 2026-10 | MIT | Framework événementiel, simulation, paper trading | ⭐⭐⭐ |
| 66 | Exchange | [betcode-org/betfair](https://github.com/betcode-org/betfair) (betfairlightweight) | Python | 515 | 2026-09 | MIT | Client API-NG + streaming | ⭐⭐⭐ |
| 67 | Exchange/modèles | [betfair-datascientists/predictive-models](https://github.com/betfair-datascientists/predictive-models) | Jupyter/R | 110 | 2022-02 | – | Tutoriels (EPL, AFL, rugby…) | ⭐⭐ |
| 68 | Tennis data | JeffSackmann/tennis_atp / tennis_wta | CSV | 856 / 230 | **supprimés ~2026-06** | CC BY-NC-SA | (miroirs uniquement) | ⚠️ |
| 69 | Tennis data | [JeffSackmann/tennis_MatchChartingProject](https://github.com/JeffSackmann/tennis_MatchChartingProject) | CSV | 434 | 2026-09 | CC BY-NC-SA | Point par point annoté | ⭐⭐ |
| 70 | Tennis data | [Tennismylife/TML-Database](https://github.com/Tennismylife/TML-Database) | CSV | 47 | 2026-01 | – | Base ATP mise à jour (alternative) | ⭐⭐ |
| 71 | Tennis | [mcekovic/tennis-crystal-ball](https://github.com/mcekovic/tennis-crystal-ball) | Java | 284 | 2022-02 | Apache-2.0 | Elo par surface, prédiction NN | ⭐⭐ |
| 72 | Tennis | [edouardthom/ATPBetting](https://github.com/edouardthom/ATPBetting) | Jupyter | 466 | 2021-09 | aucune | XGBoost + « confiance » vs Pinnacle | ⭐ (⚠️ ROI) |
| 73 | Tennis | [BrandoPolistirolo/Tennis-Betting-ML](https://github.com/BrandoPolistirolo/Tennis-Betting-ML) | Python | 13 | 2022-02 | MIT | Régression logistique SGD + Elo 538 | ⭐ |
| 74 | Tennis | [damienld/Tennis-predict](https://github.com/damienld/Tennis-predict) | Python | 0 | 2022-02 | Apache-2.0 | Elo + features OnCourt, cotes Pinnacle | ⭐ |
| 75 | Tennis | [jacksonpc2024/ATP-Value-Betting-Algorithm](https://github.com/jacksonpc2024/ATP-Value-Betting-Algorithm) | Python | 0 | 2026-03 | aucune | Elo vs bet365 | ⚠️ (ROI) |
| 76 | Tennis | [gmalbert/tennis-predictions](https://github.com/gmalbert/tennis-predictions) | Python | 9 | 2026-09 | GPL-3 | App Streamlit, cotes + ML | ⭐ |
| 77 | Tennis | [0xsimulacra/MLT](https://github.com/0xsimulacra/MLT) | Jupyter | 4 | 2020-02 | – | ML ATP/WTA + cotes tennis-data | ⭐ |
| 78 | NBA | [kyleskom/NBA-Machine-Learning-Sports-Betting](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting) | Python | ~1,7k | 2026-09 | **aucune** | XGBoost / NN, EV, Kelly | ⭐⭐ |
| 79 | NBA data | [swar/nba_api](https://github.com/swar/nba_api) | Python | 3778 | 2026-08 | MIT | Client NBA.com | ⭐⭐⭐ |
| 80 | NBA | [NBA-Betting/NBA_Betting](https://github.com/NBA-Betting/NBA_Betting) | Jupyter | 209 | 2026-01 | MIT | Pipeline complet + analyse des lignes Vegas | ⭐⭐ |
| 81 | NBA | [NBA-Betting/NBA_AI](https://github.com/NBA-Betting/NBA_AI) | Python | 123 | 2026-10 | MIT | Deep learning, pipeline quotidien | ⭐⭐ |
| 82 | NBA | [klane/databall](https://github.com/klane/databall) | Jupyter | 152 | 2025-01 | MIT | Betting NBA (spread) | ⭐ |
| 83 | NBA data | [sportsdataverse/hoopR](https://github.com/sportsdataverse/hoopR) | R | 146 | 2026-09 | – | Play-by-play NBA/NCAA | ⭐⭐ |
| 84 | NBA data | [jaebradley/basketball_reference_web_scraper](https://github.com/jaebradley/basketball_reference_web_scraper) | Python | 559 | 2026-09 | MIT | Basketball-Reference | ⭐ |
| 85 | NFL data | [nflverse/nflfastR](https://github.com/nflverse/nflfastR) + [nflverse-data](https://github.com/nflverse/nflverse-data) | R | 545 / 403 | 2026-09 | autre / CC-BY-4.0 | PBP NFL, EPA, lignes de paris | ⭐⭐⭐ |
| 86 | NFL data | [nflverse/nflreadpy](https://github.com/nflverse/nflreadpy) (remplace `nfl_data_py`, archivé) | Python | 189 | 2026-08 | MIT | Accès Python à nflverse | ⭐⭐⭐ |
| 87 | NHL data | [HarryShomer/Hockey-Scraper](https://github.com/HarryShomer/Hockey-Scraper) | Python | 157 | 2024-06 | GPL-3 | PBP et shifts NHL | ⭐⭐ |
| 88 | NHL | [pbulsink/HockeyModel](https://github.com/pbulsink/HockeyModel) | R | 6 | 2026-05 | GPL-3 | DC adapté NHL, simulation des playoffs | ⭐⭐ |
| 89 | NHL | [HarryShomer/NHL-Prediction-Model](https://github.com/HarryShomer/NHL-Prediction-Model) | Python | 13 | 2019-03 | – | Probabilités de victoire | ⭐ |
| 90 | Rugby | [seanyboi/rugbypy](https://github.com/seanyboi/rugbypy) | Python | 51 | 2026-05 | Apache-2.0 | Données rugby (dont **Top 14**) | ⭐⭐ |
| 91 | Rugby | [gmalbert/rugby](https://github.com/gmalbert/rugby) | Python | 0 | 2026-09 | GPL-3 | Elo + DC + RF (marqueurs d'essais) | ⭐ |
| 92 | Rugby/AFL | [robmakepeace/AustralianElo](https://github.com/robmakepeace/AustralianElo) | – | 0 | 2023-07 | GPL-3 | Elo AFL / NRL / Super Rugby | ⭐ |
| 93 | Handball | [florianfelice/HandballAnalysis](https://github.com/florianfelice/HandballAnalysis) | Jupyter | 0 | 2024-06 | MIT | CMP + forces estimées (articles) | ⭐⭐ |
| 94 | Handball | [nemanjarogic/handball-betting-prediction](https://github.com/nemanjarogic/handball-betting-prediction) | – | 0 | 2016-02 | – | NN Bundesliga handball | ⚠️ |
| 95 | MMA data | [Greco1899/scrape_ufc_stats](https://github.com/Greco1899/scrape_ufc_stats) | Python | 168 | 2026-09 | GPL-3 | Scraper ufcstats.com | ⭐⭐ |
| 96 | MMA | [WarrierRajeev/UFC-Predictions](https://github.com/WarrierRajeev/UFC-Predictions) | Jupyter | 81 | 2022-06 | – | RF / XGB (dataset Kaggle « ufcdata ») | ⭐ |
| 97 | MMA | [jdanielbcosta/ufc-predictor](https://github.com/jdanielbcosta/ufc-predictor) | Python | 7 | 2026-09 | – | Ensemble de 5 modèles, split temporel | ⭐ |
| 98 | F1 data | [theOehrly/Fast-F1](https://github.com/theOehrly/Fast-F1) | Python | 5395 | 2026-08 | MIT | Timing, télémétrie, résultats | ⭐⭐⭐ |
| 99 | F1 data | [jolpica/jolpica-f1](https://github.com/jolpica/jolpica-f1) | Python | 918 | 2026-09 | Apache-2.0 | Remplaçant de l'API Ergast | ⭐⭐ |
| 100 | F1 | [mar-antaya/2025_f1_predictions](https://github.com/mar-antaya/2025_f1_predictions) | Python | quelques centaines | 2025 | – | GBM sur qualifications (démo virale) | ⭐ |
| 101 | Multi-sport data | [roclark/sportsipy](https://github.com/roclark/sportsipy) | Python | 575 | 2025-01 | MIT | Sports-Reference (US) | ⭐ |
| 102 | ML foot | [jkrusina/SoccerPredictor](https://github.com/jkrusina/SoccerPredictor) | Python | 117 | 2022-11 | aucune | « Profit 1069 % » | ⚠️ (contre-exemple) |
| 103 | ML foot | [mhaythornthwaite/Football_Prediction_Project](https://github.com/mhaythornthwaite/Football_Prediction_Project) | Python | 311 | 2026-03 | MIT | ML EPL via api-football (~51 % accuracy) | ⭐ |
| 104 | Coupe du monde 2026 | [Hicruben/world-cup-2026-prediction-model](https://github.com/Hicruben/world-cup-2026-prediction-model), [AndyDu0921/wc26-predict](https://github.com/AndyDu0921/wc26-predict) | JS / Python | 92 / 32 | 2026-07 | MIT | Elo + DC + Monte Carlo | ⭐ |

> Le tableau compte **104 entrées**, dont plus de 60 projets distincts directement liés à la prédiction, aux paris ou au scraping. Les fiches détaillées suivent en §4.

---

## 2. Top 10 à réutiliser

| Rang | Projet | Pourquoi | Comment l'intégrer |
|---|---|---|---|
| 1 | **penaltyblog** (MIT) | Le plus complet en Python pour le football. Modèles DC / bivarié / NegBin / ZIP / Weibull-copule / Bayésien hiérarchique optimisés en Cython. `dixon_coles_weights` pour la pondération temporelle. Ratings Elo, Pi, Massey, Colley. `implied` (7 méthodes). `betting` : Kelly simple et multiple, arbitrage, value. `metrics` : RPS, Brier, ignorance. `backtest`. Scrapers ClubElo, FBref, football-data, Understat. | Dépendance directe ou vendoring sélectif (MIT). On reprend l'interface `fit / predict → FootballProbabilityGrid`, qui donne une grille de scores d'où l'on dérive 1X2, O/U, AH et BTTS. |
| 2 | **implied** (R, GPL-3) + **shin** (Python, MIT) | La référence méthodologique pour retirer la marge (9 méthodes, diagnostics `z`, `problematic`, solveur robuste). `shin` est rapide et testé. | Ré-implémenter en Python (la GPL interdit de copier le code, mais pas de reprendre les formules publiées). Valider contre `implied` avec des vecteurs de test croisés. Exposer `margin`, `z` et `problematic`. |
| 3 | **sports-betting** (georgedouzas, MIT) | Bonne architecture : `DataLoader(stats source × odds source)`, `ClassifierBettor` qui emballe n'importe quel estimateur sklearn, `backtest` avec `TimeSeriesSplit`, `BettorGridSearchCV`, `OddsComparisonBettor`, résolveur de noms d'équipes (`normalize_team_name`, `pair_rosters`), source `OddsApi`, serveur MCP. | Copier le **design d'API** (sources interchangeables, X/Y/O séparés, backtest walk-forward) et le résolveur de noms. |
| 4 | **soccerdata** (Apache-2.0) | Scrapers football avec identifiants harmonisés et cache local. Huit sources. | Couche « données football ». **Attention** : FBref n'a plus de stats avancées depuis le 20/01/2026. |
| 5 | **OddsHarvester** (MIT) | Seule source open source maintenue de **cotes historiques multi-bookmakers**, avec historique des mouvements (`--odds-history`), 11 sports, proxys et géolocalisation, export S3. | Construire notre historique de cotes, dont l'ouverture et la clôture par bookmaker. Avec un proxy FR et `--locale fr`, OddsPortal peut afficher des bookmakers FR (à vérifier). Respecter les CGU. |
| 6 | **xgabora/Club-Football-Match-Data-2000-2025** (MIT) | 238 858 matchs (2000 → 09/2026), 38 divisions, 27 pays, cotes bet365 et **max** d'environ 17 bookmakers (1X2, O/U, AH), Elo ClubElo, stats de match. | Jeu de données de backtest prêt à l'emploi. Il dérive de football-data.co.uk : citer la source. |
| 7 | **goalmodel** (R, GPL-3) | Modèles de buts les plus riches : Poisson, NegBin, **Conway-Maxwell-Poisson**, Gaussien, DC, Rue-Salvesen, **hurdle** 0-0, paramètres fixés (estimation en deux étapes), `expg_from_ou` et `expg_from_probabilities` (on remonte des cotes aux λ). | Référence pour valider nos implémentations. Fonctionnalité clé : **inférer les λ depuis les cotes du marché**, utile comme prior et comme feature. |
| 8 | **flumine + betfairlightweight** (MIT) | Framework de trading événementiel mature : simulation sur historique, paper trading, contrôle du risque, multi-venues. | Modèle d'architecture pour notre moteur d'exécution et de simulation (stratégie → ordres → contrôles de risque). Betfair Exchange est accessible depuis la France, mais il faut vérifier l'agrément ANJ au moment de l'usage. |
| 9 | **skelo / openskill.py / PlayerRatings** | Ratings avec historique daté (skelo) pour éviter la fuite temporelle, Weng-Lin rapide (openskill), Glicko / **Stephenson** de référence (PlayerRatings). | Module « ratings » générique (tennis, MMA, rugby, handball) avec interface sklearn `fit / predict_proba` et ratings résolus à une date donnée. |
| 10 | **nflverse / nba_api / Fast-F1 / jolpica / rugbypy / scrape_ufc_stats** | Les meilleures sources ouvertes et maintenues pour les sports hors football. | Adaptateurs « données » par sport. Pour le tennis, remplacer Sackmann (supprimé) par TML-Database, tennis-data.co.uk ou un miroir CC BY-NC-SA, **en vérifiant la licence non commerciale**. |

**Mention spéciale FR** : `pretrehr/Sports-betting`. Ses scrapers sont à refaire, mais il fournit une cartographie des **endpoints JSON** de 12 opérateurs ANJ (détails en §4.7) et toute la **mathématique des freebets** : conversion à environ 80 % et répartition optimale des mises sur plusieurs issues.

---

## 3. Alertes écosystème 2025-2026 (impact direct sur le design)

| Date | Événement | Impact | Parade |
|---|---|---|---|
| 23/07/2025 | **Fermeture de l'API publique Pinnacle** (accès sur demande seulement : commercial ou académique) | Plus de cotes « sharp » en temps réel gratuites. La mesure de la CLV devient plus difficile. | Pinnacle reste présent dans les CSV football-data (`PSH/PSD/PSA`, clôture `PSCH…`). Sinon : OddsHarvester, The Odds API, ou demande académique à api@pinnacle.com. |
| 09/2025 | **worldfootballR archivé** (« will no longer be maintained ») | Fin du principal wrapper R FBref / Transfermarkt | soccerdata / ScraperFC côté Python |
| 20/01/2026 | **FBref perd les stats avancées Opta** (xG, actions de création de tirs…). L'historique reste, plus de mise à jour. | Les features xG doivent venir d'ailleurs | Understat (top 5 ligues), StatsBomb open data, Sofascore et WhoScored (scraping), ou fournisseurs payants |
| ~06/2026 | **Suppression de `JeffSackmann/tennis_atp`, `tennis_wta`, `tennis_pointbypoint`, `tennis_slam_pointbypoint`** (404 ; constaté aussi par Software Heritage depuis le 16/06/2026). `git ls-remote` demande désormais une authentification. | Des dizaines de projets tennis sont cassés | TML-Database (Tennismylife), tennis-data.co.uk (résultats + cotes), miroirs d'archive (ex. `Aneeshers/tennis-sackmann-archive`, CC BY-NC-SA, donc **non commercial**) |
| 2025 | `nfl_data_py` déprécié → `nflreadpy` | – | Utiliser nflreadpy |
| 2025 | FiveThirtyEight fermé (03/2025) ; dépôt `data` figé | Les ratings SPI / Elo 538 ne sont plus mis à jour | ClubElo, eloratings.net, ratings maison |
| fin 2024 | Ergast (F1) arrêté → **jolpica-f1** reprend l'API | – | jolpica-f1, Fast-F1 |
| permanent | Les bookmakers FR durcissent l'anti-bot. Nos tests du 02/10/2026 depuis une IP non FR : **Winamax 403**, **API CDN Betclic sans réponse**, **Unibet `zones/navigation.json` → « page-introuvable »** | Les scrapers 2020-2023 ne fonctionnent plus | Navigateur headless avec empreinte réaliste (Playwright, Camoufox), IP FR, extraction du JSON embarqué, monitoring synthétique, ou flux licencié |

---

## 4. Fiches détaillées par catégorie

### 4.1 Bibliothèques de modélisation et de paris (football)

#### penaltyblog — Martin Eastwood
- **URL** : https://github.com/martineastwood/penaltyblog · doc : https://penaltyblog.readthedocs.io · PyPI `penaltyblog`
- **Langage** : Python + Cython · **★** ≈228 · **Dernier push** 2026-10 · **Licence** MIT
- **Ce que ça fait** : boîte à outils football « production-ready ».
  - `models` : `PoissonGoalsModel`, `DixonColesGoalModel`, `BivariatePoissonGoalModel`, `NegativeBinomialGoalModel`, `ZeroInflatedPoissonGoalsModel`, `WeibullCopulaGoalsModel`, `BayesianGoalModel`, `HierarchicalBayesianGoalModel`, `dixon_coles_weights`, `goal_expectancy` (λ depuis les cotes), `FootballProbabilityGrid`.
  - `ratings` : `Elo`, `PiRatingSystem`, `Massey`, `Colley`.
  - `implied` : `multiplicative`, `additive`, `power`, `shin`, `differential_margin_weighting`, `odds_ratio`, `logarithmic`.
  - `betting` : `kelly_criterion`, `multiple_kelly_criterion`, `arbitrage_hedge`, `identify_value_bet`, `find_arbitrage_opportunities`, `convert_odds`.
  - `metrics` : `rps_average`, `multiclass_brier_score`, `ignorance_score`.
  - Autres modules : `backtest` (`Backtest`, `Account`, `Context`), `scrapers` (ClubElo, FBRef, FootballCharts, FootballData, Understat), `matchflow` (pipeline JSON paresseux, connecteurs StatsBomb et Opta), `fpl`, `xt`, `viz`.
- **Données** : football-data.co.uk, Understat, ClubElo, FBref, StatsBomb.
- **Performance annoncée** : le README ne revendique aucun ROI. Le blog pena.lt/y contient des comparaisons de modèles par RPS.
- **Qualité** : très bonne. Typage par dataclasses (`ImpliedProbabilities`), CI, docs, notebooks Colab, et même un fichier SKILL pour les agents de code.
- **Ce qu'on en retient / réutilise** :
  - L'API `ImpliedProbabilities(probabilities, method, margin, method_params)`.
  - Le concept de **grille de probabilités de scores**, d'où l'on dérive tous les marchés.
  - Les métriques RPS et ignorance.
  - Les ratings Pi, très adaptés au football (avantage du terrain séparé, effet décroissant des gros écarts).

#### sports-betting — Georgios Douzas
- **URL** : https://github.com/georgedouzas/sports-betting · PyPI `sports-betting`
- **Langage** : Python · **★** ≈804 · **Dernier push** 2026-09 · **Licence** MIT
- **Ce que ça fait** :
  - Dataloaders qui combinent une **source de stats** (`FootballDataStats`, `NBAStats`, `EuroLeagueStats`) et une **source de cotes** (`FootballDataOdds`, `OddsApi`), puis renvoient `X, Y, O`.
  - Bettors : `ClassifierBettor`, qui emballe n'importe quel classifieur sklearn, et `OddsComparisonBettor`.
  - `backtest` avec `TimeSeriesSplit` et `BettorGridSearchCV`.
  - CLI `sportsbet`, **serveur MCP**, module d'**exécution** de paris (API ou pilotage du site via Playwright ; l'auteur prévient lui-même que cela viole la plupart des CGU).
- **Performance annoncée** : l'exemple du README (pari « nul » par régression logistique, Allemagne / Italie / France D1-D2, 2021-2024) affiche des yields par pli de −2,3 % à +8 %.
- **⚠️ Scepticisme** : l'exemple utilise `odds_type='market_maximum'`, c'est-à-dire la **meilleure cote du marché**, inatteignable en pratique (limites, latence, comptes restreints). Il suffit de passer à une cote réaliste d'un seul bookmaker pour retirer plusieurs points de yield.
- **Qualité** : très bonne : ruff, mypy, pytest, couverture, nox, docs mkdocs.
- **Ce qu'on en retient** :
  - La **séparation stats / cotes / cibles**.
  - Le **résolveur de noms d'équipes** entre sources : c'est le problème n°1 en pratique.
  - Le backtest walk-forward intégré.
  - L'option `odds_type`, qu'il faut obliger à être réaliste.

#### goalmodel — Jonas C. Lindstrøm (opisthokonta)
- **URL** : https://github.com/opisthokonta/goalmodel · **R** · ★≈99 · 2024-03 · GPL-3 · v0.6.4 (dev)
- **Ce que ça fait** :
  - `goalmodel()` ajuste les modèles `poisson`, `negbin`, `cmp` (Conway-Maxwell-Poisson), `gaussian`, Dixon-Coles (`dc=TRUE`), l'ajustement Rue-Salvesen, le **modèle hurdle** (0-0, Owen 2017), des covariables, des poids (`weights_dc`) et des paramètres fixés.
  - Prédictions : `predict_expg`, `predict_goals`, `predict_result`, `predict_ou`, `predict_btts`.
  - Conversions : `expg_from_ou` et `expg_from_probabilities` (**cotes → λ**).
- **Qualité** : excellente, issue d'un statisticien publié. README très pédagogique.
- **Ce qu'on en retient** : la fonction « cotes → buts attendus » permet d'utiliser le marché comme feature ou comme prior. La CMP gère la sous-dispersion (utile en handball et hockey). Le hurdle sert aux 0-0. Réutiliser les jeux de données d'exemple pour nos tests de non-régression.

#### footBayes — Leonardo Egidi
- **URL** : https://github.com/leoegidi/footbayes · CRAN `footBayes` 2.0.0 (2025-05) · R/Stan · ★≈59 · GPL-2
- **Ce que ça fait** : double Poisson, Poisson bivarié, Skellam, Student-t, Poisson bivarié diagonal-inflated, Skellam zero-inflated. Estimation MLE (statique) ou bayésienne (HMC, Pathfinder, ADVI). **Modèles dynamiques**, où les forces évoluent dans le temps.
- **Ce qu'on en retient** : la référence bayésienne. Les forces dynamiques sont une alternative propre à la pondération exponentielle DC.

#### mezzala / regista — Ben Torvaney
- https://github.com/Torvaney/mezzala (Python, Apache-2.0, ★40, 2021-10) · https://github.com/Torvaney/regista (R, GPL-3, ★91, 2025-11)
- **Ce que ça fait** : Dixon-Coles avec un système d'**adapters** qui rend le modèle indépendant du format des données. Les exemples s'appuient sur openfootball.
- **Ce qu'on en retient** : un pattern d'API propre. L'auteur a aussi écrit de bons articles de blog sur la modélisation de la forme des équipes.

#### ProphitBet — Vasileios Kochliaridis
- https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor · Python · ★≈576 · 2026-04 · MIT
- **Ce que ça fait** : application GUI. Télécharge football-data.co.uk (toutes les ligues) et les fixtures Footystats, calcule des stats d'équipe, entraîne des modèles ML avec CV et holdout, propose de l'explicabilité et des filtres par plage de cotes. Nouvelle métrique « Profit Balance ».
- **Scepticisme** : la logique « filtrer par plage de cotes puis évaluer » sur le même historique invite au **sur-ajustement par sélection**.
- **Ce qu'on en retient** : l'UX pour les utilisateurs non développeurs (ligues sauvegardées, tableaux exportables). Pas de méthodologie de référence.

#### BeatTheBookie — Kaunitz, Zhong, Kreiner (2017)
- https://github.com/Lisandro79/BeatTheBookie · MATLAB / Octave · ★≈624 · 2021-10 · GPL-3 · article [arXiv:1710.02824](https://arxiv.org/abs/1710.02824)
- **Stratégie** : aucun modèle sportif. On calcule la **probabilité de consensus** à partir de la moyenne des cotes de 32 bookmakers. On parie quand la **cote maximale** dépasse la cote juste de consensus, avec une marge de sécurité α.
- **Résultats annoncés** :
  - Simulation sur 10 ans de cotes de clôture : **479 440 matchs** (2005-2015), environ 44 % de paris gagnants, **+3,5 %** de rendement.
  - Profit également sur 6 mois de cotes minute par minute, puis 5 mois en argent réel.
  - Ensuite, **limitation des mises** et vérification manuelle des paris par les bookmakers.
- **Qualité** : code de recherche, mais la **base de données (≈1,8 Go) est publique** (Kaggle « Beat The Bookie: Odds Series Football Dataset »).
- **Ce qu'on en retient** :
  - Le marché agrégé est un excellent estimateur.
  - Le « value » vient surtout des **bookmakers lents ou récréatifs**.
  - La viabilité est limitée par la **gestion des comptes gagnants**, pas par les maths. Notre outil doit suivre la santé des comptes : limites, rejets.

#### dashee87/blogScripts — David Sheehan
- https://github.com/dashee87/blogScripts · Jupyter · ★≈385 · 2022-12 · MIT
- **Contenu** : code des articles « Predicting Football Results With Statistical Modelling » (Poisson, 2017) et « …Dixon-Coles and Time-Weighting » (2018).
- **Ce qu'on en retient** : implémentation pédagogique de la log-vraisemblance DC avec ρ et ξ. Les chiffres clés sont en §6.

### 4.2 Retirer la marge : probabilités implicites

#### implied (R) — opisthokonta
- https://github.com/opisthokonta/implied · CRAN `implied` 0.5 (2023-06), dev 0.6.1 (2026-02) · GPL-3
- **Méthodes** : `basic`, `additive`, `wpo`, `power`, `or`, `shin` (algorithmes `js` Jullien-Salanié ou `uniroot`), `bb` (balanced books), `jsd`, `goto` / `ooepc`. Options `grossmargin` (Fingleton-Waldron) et `target_probability`, pour les marchés dont la somme ≠ 1, comme « qualifié » ou « top 4 ». Fonction inverse `implied_odds()` (probabilités → cotes avec une marge donnée).
- **Sorties** : `probabilities`, `margin`, `zvalues` (part d'initiés selon Shin), `odds_ratios`, `exponents`, `distance`, `problematic` (drapeau en cas d'échec).
- **Ce qu'on en retient** : c'est **la spécification** à reproduire. Le détail des formules et des recommandations est en §5.

#### shin — Maurice Berk
- https://github.com/mberk/shin · Python · ★≈105 · 2026-08 · MIT · `pip install shin`
- **Ce que ça fait** : méthode de Shin itérative (Jullien-Salanié), avec un `z` **analytique** quand il n'y a que 2 issues. `full_output` renvoie `iterations`, `delta` et `z`.
- **Vecteur de test** : `[2.6, 2.4, 4.3]` → `[0.37299, 0.40478, 0.22223]`, z ≈ 0.01694.
- **Ce qu'on en retient** : on peut l'utiliser tel quel. Le vecteur de test sert à notre CI.

#### goto_conversion — Kaito Goto
- https://github.com/gotoConversion/goto_conversion · Python · ★≈115 · 2026-09 · MIT
- **Ce que ça fait** : on retire à chaque probabilité inverse **le même nombre d'erreurs-types**, l'erreur-type étant plus large sur les outsiders, ce qui corrige le biais favori-outsider. Contient aussi `efficient_shin_conversion` (Shin analytique) et une variante `zero_sum` pour les marchés boursiers.
- **Performance annoncée** : « 47 000 $ de prix, plus de 10 médailles d'or Kaggle » (March Machine Learning Mania, basket NCAA).
- **Scepticisme** : ces médailles reflètent surtout l'intérêt d'utiliser **les cotes comme feature dominante** dans des compétitions de log-loss. Elles ne prouvent pas qu'on bat le marché.
- **Ce qu'on en retient** : une méthode de plus à benchmarker. L'idée clé est que **les cotes du marché sont souvent la meilleure feature**.

### 4.3 Maths du pari, Kelly, bankroll, backtest

| Projet | Contenu | Verdict |
|---|---|---|
| **WagerBrain** (sedemmler, ★315, 2020-05, MIT) | Conversion US / décimal / fractionnel, EV, Kelly, combinés, arbitrage, vig, probabilité depuis un Elo 538 | Abandonné. Les fonctions sont triviales mais servent de liste de contrôle des utilitaires à fournir. |
| **pybettor** (★14, 2024-09, MIT) et **bettoR** (R, ★78, 2023-05) | `implied_prob`, `implied_odds`, `convert_odds`, Kelly | Même auteur (theFirmAI). Simple et tabulaire. |
| **surebet** (HintikkaKimmo, ★87, 2026-02, MIT) | Conversion, arbitrage, value bet sizing | Petit, mais testé (CI, codecov). |
| **monte-carlo-betting-simulations** (★26, MIT) | Monte Carlo sur Martingale, D'Alembert, etc. | Utile pour **démontrer pédagogiquement** la ruine des systèmes de progression. |
| **ml-for-sports-betting** (Walsh & Joshi, archivé) | Pipeline NBA : sélection de modèle par **calibration (ECE classwise) ou exactitude**, puis mise fixe ou Kelly fractionnel | Code reproductible, avec un **corrigendum** (détails en §6). La leçon tient : **optimiser la calibration**. |
| **penaltyblog.backtest** / **sports-betting.backtest** / **flumine** (simulation) | Backtests | Combiner : walk-forward (sports-betting) et simulation d'exécution réaliste (flumine). |

**Ce qu'on en retient** :
- **Kelly** : f* = (o·p − 1)/(o − 1).
- On l'implémente en **fractionnel** (¼ à ½), avec **plafond par pari** (par exemple 2 à 5 % de la bankroll) et **Kelly simultané** pour plusieurs paris en même temps (`multiple_kelly_criterion` de penaltyblog).
- Uhrín et al. (2021, [arXiv:2107.08827](https://arxiv.org/abs/2107.08827)) concluent qu'une variante **adaptative de Kelly fractionnel** convient à un large éventail de contextes (courses, basket, football) et que les **contrôles de risque additionnels sont nécessaires**.

### 4.4 Systèmes de rating

| Projet | Méthodes | Points saillants pour nous |
|---|---|---|
| **penaltyblog.ratings** | Elo, **Pi-ratings**, Massey, Colley | Pi-ratings (Constantinou & Fenton 2013) : notes domicile et extérieur séparées, effet décroissant des gros écarts de buts. Bien adapté au football. |
| **piratings** (R, CRAN 0.1.9, 2019) | Pi-ratings, avec optimisation des taux d'apprentissage λ et γ | Implémentation de référence de l'article. |
| **skelo** (Python) | Elo, Glicko-2, avec **interface sklearn** et **intervalles de validité** des ratings | Résout le problème de **fuite temporelle** : on obtient le rating d'un joueur à une date t. À imiter. |
| **elo** (R, CRAN 3.0.2) | Elo par formule, marge de victoire (MOV), K variable, régression vers la moyenne, `elo.glm`, `elo.markovchain` | Formulation la plus complète des variantes d'Elo. |
| **PlayerRatings** (R, CRAN) | Elo, Glicko, Glicko-2, **Stephenson** (gagnant de la compétition Kaggle « chess ratings ») | Référence pour les sports individuels (tennis, MMA). |
| **trueskill**, **glicko2**, **openskill.py** | TrueSkill (Microsoft), Glicko-2, Weng-Lin (Plackett-Luce, Thurstone-Mosteller) | Utiles pour la F1 (classements multi-pilotes) et les sports individuels. openskill est très rapide. |
| **fivethirtyeight/nfl-elo-game** | Elo 538 NFL (K=20, avantage terrain, MOV, régression inter-saison) avec protocole d'évaluation (Brier-like) | Protocole d'évaluation transposable. |
| **nfelo** | Elo 538 adapté et **ancré sur les lignes du marché** | L'idée clé : mélanger le rating et la ligne du marché. |
| **mcekovic/tennis-crystal-ball** | Elo tennis personnalisé par surface, indoor/outdoor, sets/jeux, et prédiction par réseau de neurones | Elo par surface : indispensable en tennis. |
| **fbRanks** (R) | Classement Poisson multi-ligues | **Retiré du CRAN (2022)**. À citer uniquement. |

**Ce qu'on en retient** : un module unique `ratings` avec Elo, Glicko-2, Pi et Stephenson. Chaque rating doit être **résolu à la date du match** (pas de fuite) et exposer une interface `predict_proba`. Hyperparamètres (K, λ, γ…) à **optimiser sur une période de validation**, puis à figer.

### 4.5 Données football (scrapers et datasets)

| Projet | Sources | Statut 10/2026 | Ce qu'on en retient |
|---|---|---|---|
| **soccerdata** | ClubElo, ESPN, FBref, football-data.co.uk, Sofascore, SoFIFA, Understat, WhoScored | Actif. FBref sans stats avancées depuis 01/2026. | Identifiants harmonisés et cache local : la base de notre couche data. |
| **ScraperFC** | Capology, ClubElo, FBref, Sofascore, Transfermarkt, Understat | Actif (2026-05), GPL-3 | Transfermarkt (valeurs de marché = bon prior de force). Attention à la GPL. |
| **worldfootballR** | FBref, Transfermarkt, Understat, FotMob (retiré) | **Archivé 09/2025** | Ne pas dépendre. |
| **understat** / **understatAPI** | Understat (xG par tir, top 5 ligues + RPL) | Actifs | Source xG gratuite principale depuis la perte d'Opta par FBref. |
| **statsbombpy** / **open-data** | StatsBomb (événements et 360 de certaines compétitions) | Actifs, conditions d'utilisation (attribution) | Pour entraîner un xG maison, pas pour la couverture des ligues. |
| **kloppy**, **socceraction**, **soccer_xg**, **mplsoccer** | Standardisation, VAEP, xT, xG, visualisation | Actifs | Features avancées et visualisation. |
| **Club-Football-Match-Data-2000-2025** | Dérivé de football-data.co.uk + ClubElo | Actif (09/2026), MIT | **Dataset de backtest prêt.** |
| **engsoccerdata**, **international_results**, **openfootball/football.json**, **footballcsv** | Résultats historiques | Actifs, CC0 / GPL | Résultats longs pour ratings et internationaux (Coupe du monde). |
| football-data.co.uk (site, pas un dépôt) | CSV résultats, stats et **cotes** (dont Pinnacle, max et moyenne, **clôture** depuis 2019/20) | Référence | **La** source de cotes historiques gratuites pour le football. |
| ClubElo (api.clubelo.com) / eloratings.net | Elo clubs / nations | Actifs | Features et baselines. Gratuits. |

### 4.6 Cotes : scrapers et agrégateurs génériques

- **OddsHarvester** (★≈256, 2026-10, MIT) :
  - Playwright sur OddsPortal, pour les matchs à venir, l'historique et le live, plus les données communautaires.
  - 11 sports et beaucoup de marchés (1X2, BTTS, DC, DNB, O/U, handicap européen, AH).
  - `--odds-history` pour les mouvements de cotes, `--target-bookmaker`, détection des cotes retirées.
  - Proxys en rotation, `--base-url` vers des miroirs régionaux, sortie JSON / CSV / S3.
  - **Le meilleur point de départ open source pour un historique de cotes.**
  - **Risques** : CGU d'OddsPortal, fragilité du DOM.
- **soccerapi** (★179, dernier commit 2022-12) : wrapper simple (888sport, bet365, Unibet). Le README avertit : « *not actively developed… may be broken* ». Leçon de l'auteur : *« heavy framework with selenium… was an unmaintainable nightmare »*, d'où l'importance de **privilégier les endpoints JSON**.
- **bet365-scraper**, **betting-crawler**, **gto76/bets**, **betScrapeR** : historiques, cassés.
- **Live-Sports-Arbitrage-Bet-Finder** (★≈294) : scraping Selenium (undetected-chromedriver) de FanDuel / DraftKings / William Hill « toutes les 10 ms » et placement automatique. Risques **CGU et fermeture de comptes**. Contre-exemple éthique et opérationnel.
- **oddshub** (Go) et **oddsapiR** (R) : clients de **The Odds API**, un agrégateur commercial avec offre gratuite limitée. Il couvre la **région `fr`** : `betclic_fr`, `netbet_fr`, `pmu_fr`, `unibet_fr`, `winamax_fr`.
- **l-portet/surebet-finder** (★≈72, JS, 2024-10) : bot surebet par un développeur français.

### 4.7 Bookmakers français (ANJ) : état des lieux détaillé

> **Contexte réglementaire.** L'ANJ publie la liste à jour des opérateurs agréés sur [anj.fr](https://anj.fr/offre-de-jeu-et-marche/operateurs-agrees). Les listes publiques de 2026 citent notamment Betclic, Winamax, Unibet, PMU, Bwin, NetBet, PokerStars Sports, Vbet, Genybet, Feelingbet, Olybet, Betsson, Bet365, CircusBet et DAZN Bet. ParionsSport en ligne est l'offre de la FDJ. **ZEbet n'apparaît plus dans les listes 2026.** Le scraping est généralement **contraire aux CGU** des opérateurs, et automatiser des mises sur un compte expose à sa **fermeture**.

| Projet | Opérateurs | Technique | Dernier commit | État (vérifié le 02/10/2026) | Ce qu'on en retient |
|---|---|---|---|---|---|
| **[pretrehr/Sports-betting](https://github.com/pretrehr/Sports-betting)** (★≈534, MIT) | Betclic, Betfair, Betway, Bwin, France Pari, JOA, NetBet, ParionsSport, Pasinobet, Pinnacle, PMU, PokerStars, Unibet, Winamax, Zebet | **Winamax** : JSON `PRELOADED_STATE` embarqué dans le HTML. **Betclic** : `offer.cdn.betclic.fr/api/pub/v2/…`. **Unibet** : `unibet.fr/zones/navigation.json`. **ParionsSport** : `enligne.parionssport.fdj.fr/lvs-api/ff/…` avec en-tête `X-LVS-HSToken` capturé par selenium-wire. **Bwin** : `cds-api.bwin.fr/bettingoffer/fixtures` avec `x-bwin-accessid` capturé par selenium-wire. **PokerStars** : `sports.pokerstarssports.fr/sportsbook/v1/api/…`. **PMU** : `pservices`. NetBet / Zebet : HTML. | **2023-12** | **Considéré comme cassé.** Tests depuis IP non FR : Winamax **403**, CDN Betclic **sans réponse**, Unibet navigation.json → **« page-introuvable »**. Plusieurs marques supportées ont disparu ou changé (France Pari, JOA, Pasinobet, Zebet). Issues ouvertes en 2026 sans réponse. | **Cartographie des endpoints** pour repartir, interface PySimpleGUI, et surtout la **mathématique des promotions** : conversion des freebets (≈80 % de leur valeur), « bonus si n matchs gagnés », « remboursé si perdant », optimisation des mises sur plusieurs bookmakers. |
| **[Ghantard/winator](https://github.com/Ghantard/winator)** (0★, 2026-09) | Winamax (+ consensus de 20 à 38 bookmakers via The Odds API) | JSON embarqué des pages Winamax. Marge retirée par bookmaker, **médiane** comme probabilité de référence (Winamax exclu du consensus). Niveaux de risque DC / DNB / simple. **Kelly fractionné**. Streamlit. | 2026-09 | Actif (un seul développeur) | Approche **honnête** : « la marge Winamax est de 8 à 12 % ; la plupart des scans ne trouvent aucun pari à EV+ ». Le pattern « consensus marché comme référence, puis comparaison avec le bookmaker FR » est exactement celui que nous voulons. |
| **[samuelhm/bethurtadom](https://github.com/samuelhm/bethurtadom)** (0★, 2026-03, MIT) | Winamax + Bet365 (live) | asyncio + **Playwright + Camoufox** (anti-détection), Pydantic, `BaseScraper` (pattern Strategy), **normalisation des noms d'équipes** (automatique et manuelle), dashboard | 2026-03 | Actif (récent) | Architecture d'adaptateurs à reprendre. Camoufox est la parade actuelle à l'anti-bot. Matching manuel des équipes en repli. |
| **[Harotensnor/paris-sportif](https://github.com/Harotensnor/paris-sportif)** (0★, 2026-09) | Winamax | Fetchers Python, cron GitHub Actions, GitHub Pages, **QA gates**, **moniteur synthétique**, `health.json` | 2026-09 | Actif | Bonnes pratiques **d'exploitation** : contrôles de dérive du pipeline, intégrité des données, santé des sources. |
| **[Cooya/Betbee](https://github.com/Cooya/Betbee)** | Winamax, Unibet | JS | 2018-04 | Mort | – |
| **[bettor-league/parions-sport-batch](https://github.com/bettor-league/parions-sport-batch)** | ParionsSport point de vente (`pointdevente.parionssport.fdj.fr/api/`) | Batch | 2020-06 | Probablement mort | Indique l'existence d'une API « point de vente » (réseau physique FDJ). À réexaminer. |
| **[BoboTiG/paris-en-ligne](https://github.com/BoboTiG/paris-en-ligne)** | Betclic | Statistiques de ses propres paris | archivé 2024-11 | Archivé | Idée : **import de l'historique personnel** de l'utilisateur pour suivre son ROI et sa CLV. |
| egnonisse/betclic-agent | **Betclic Côte d'Ivoire** (pas FR) | Backend public Betclic sans authentification | 2026 | – | Montre que la plateforme Betclic expose un backend JSON, probablement commun aux marchés. À vérifier pour `.fr`. |
| **[diouetq/Scrapping-Bet](https://github.com/diouetq/Scrapping-Bet)** | Sportaza, Betify, Greenluck | Requêtes vers des sites **non agréés ANJ** | 2026-09 | – | **À exclure.** Opérateurs illégaux en France. |
| **The Odds API** (commercial, offre gratuite) | betclic_fr, winamax_fr, unibet_fr, pmu_fr, netbet_fr | REST | – | Stable | **Repli légal et stable.** ParionsSport, Bwin, PokerStars et Vbet n'y figurent pas. |

**Recommandations pour notre module « FR »** :
1. **Un adaptateur par opérateur** sur le modèle de `BaseScraper` (bethurtadom), avec un **schéma Pydantic commun** : event, market, selection, price, timestamp, source.
2. **Priorité aux endpoints JSON** : JSON embarqué (Winamax), APIs publiques d'offre (Betclic, Unibet, PokerStars, Bwin). Navigateur seulement pour **capturer des jetons** (ParionsSport, Bwin), comme pretrehr avec selenium-wire.
3. **IP française**, débit faible, cache, **monitoring synthétique** (paris-sportif), et alerte quand le taux d'événements parsés chute.
4. **Normalisation des noms d'équipes et compétitions** : dictionnaire et fuzzy matching (`sports-betting.sources._resolver`), plus une correction manuelle.
5. **Repli The Odds API** (région `fr`). On stocke **les séries temporelles** de cotes, pas seulement le dernier prix, pour mesurer la CLV.
6. **Ne pas automatiser le placement des mises.** L'outil reste un outil d'**aide à la décision** (risque CGU et fermeture de compte).

### 4.8 Exchanges et trading

- **flumine** (★≈246, 2026-10, MIT) : framework événementiel (stratégies `check_market_book` / `process_market_book`), contrôles de risque, **simulation sur données historiques Betfair**, paper trading. Venues : Betfair, Betdaq, Betconnect ; Smarkets, Matchbook, Polymarket et Kalshi sont sur la feuille de route. Communauté Slack de plus de 2 500 membres. **Qualité production.**
- **betfairlightweight** (`betcode-org/betfair`, ★≈515, MIT) : client API-NG avec streaming, utilisé par flumine.
- **betfair-datascientists/predictive-models** (★110) : tutoriels officiels Betfair Australie (EPL, AFL, NRL, Super Rugby…), en R et Python. Bons exemples pédagogiques de bout en bout.
- **Ce qu'on en retient** : séparer **stratégie**, **gestion des ordres** et **contrôles de risque**. La simulation doit rejouer la **liquidité** et la **latence**.

### 4.9 Tennis

| Projet | Données | Modèle / stratégie | Performance annoncée | Avis |
|---|---|---|---|---|
| **tennis_atp / tennis_wta** (Sackmann) | Résultats et stats ATP/WTA depuis 1968 | – | – | **Supprimés ~06/2026.** Utiliser des miroirs (CC BY-NC-SA, non commercial). |
| **tennis_MatchChartingProject** | Point par point annoté (bénévoles) | – | – | Toujours en ligne (2026-09). Features de style de jeu. |
| **TML-Database** | Base ATP « live updated » | – | – | Remplaçant crédible pour les résultats. |
| tennis-data.co.uk (site) | Résultats + **cotes** (bet365, Pinnacle, max, moyenne) ATP depuis 2000, WTA depuis 2007 | – | – | Source de cotes historique. |
| **tennis-crystal-ball** (★284, Java) | Sackmann | Elo par surface, réseau de neurones, prévisions de tournois | – | Site ultimatetennisstatistics.com. Elo par surface, set et jeu à reprendre. |
| **ATPBetting** (★≈466) | tennis-data 2000-03/2018 | XGBoost (features : cote Pinnacle, forme, blessures, Elo). « Confiance » = p_modèle / p_bookmaker. | **ROI +70 % sur les 5 % de matchs les plus « sûrs », +20 % sur 35 % des matchs (Pinnacle)**. Précision 68,7 %. | **⚠️ Très suspect.** Hyperparamètres « choisis pour maximiser le ROI » sur la période évaluée, features de blessures potentiellement postérieures, Elo calculé sur tout l'historique. Fait instructif : parier tous les favoris sur Pinnacle rapporte ≈ −2 %, ce qui montre que **Pinnacle est très efficient**. |
| **Tennis-Betting-ML** | Kaggle ehallmar (ATP + ITF + cotes) | Régression logistique SGD + Elo 538 (K décroissant) | 66 % d'exactitude sur ~125 000 matchs | Exactitude typique d'un Elo. Pas de preuve de profit. |
| **Tennis-predict** (damienld) | OnCourt + cotes Pinnacle | Elo et features | – | Bonne doc de l'Elo (K, dates multi-matchs par jour). |
| **ATP-Value-Betting-Algorithm** | Sackmann + tennis-data | Elo contre bet365, seuil d'edge de 20 % | **+34,72 % ROI sur 106 paris** (2020-2024) | **⚠️ Échantillon minuscule, seuil choisi a posteriori**, bet365 à forte marge. Intervalle de confiance d'environ ±23 points. |
| **gmalbert/tennis-predictions**, **MLT** | Cotes et ML | – | – | Exemples d'apps. |

**Ce qu'on en retient** :
- Elo **par surface**, et mélange Elo global / surface (approche FiveThirtyEight et Tennis Abstract).
- K décroissant avec l'expérience du joueur.
- **Toujours comparer à Pinnacle sans marge** plutôt qu'à bet365.
- Les données sont fragiles (suppression de Sackmann) : nous devons **archiver nos propres snapshots** en respectant les licences.

### 4.10 Basketball (NBA)

- **kyleskom/NBA-Machine-Learning-Sports-Betting** (★≈1,7k ; **aucune licence**) :
  - Pipeline : stats d'équipe NBA.com (2007-08 → aujourd'hui) en SQLite, cotes SBR, features de matchup et de repos, puis **XGBoost et réseau de neurones** pour moneyline et totals, EV et **Kelly** optionnel, app Flask.
  - Cotes récupérées pour FanDuel, DraftKings, BetMGM, Caesars, etc.
  - Les anciennes versions du README annonçaient environ 69 % d'exactitude moneyline et 55 % sur les totals. **Aucune mesure de ROI ni de CLV.**
  - **Avis** : bon squelette pédagogique. Pas de licence, donc **pas de copie de code**.
- **swar/nba_api** (★≈3,8k, MIT) : client de référence des endpoints NBA.com.
- **NBA-Betting/NBA_Betting** (★≈209, MIT) : pipeline très documenté. Analyse utile : l'erreur moyenne des spreads Vegas sur ~23 000 matchs passe de **9,12 points (2006-2016) à 10,49 points (2020-2026)**, ce que l'auteur relie à la révolution du tir à 3 points. Il conclut que battre les lignes Vegas reste difficile.
- **NBA-Betting/NBA_AI** (★≈123, MIT) : pipeline quotidien automatisé (NBA API + ESPN), plusieurs moteurs de prédiction (deep learning, ML, ensemble), dashboard qui compare aux **lignes d'ouverture**.
- **klane/databall**, **hoopR**, **basketball_reference_web_scraper**, **sportsipy** : données et exemples.
- **goto_conversion / March Machine Learning Mania** (Kaggle) : en NCAA, les cotes dé-marginées sont la meilleure feature.

### 4.11 NFL

- **nflverse** : `nflfastR` (R), `nflverse-data` (releases automatiques en CC-BY-4.0, qui incluent les **lignes de paris** et les résultats), `nflreadpy` (Python, remplace `nfl_data_py`, archivé). Écosystème de référence, très maintenu.
- **nfelo** (greerreNFL) : Elo 538 adapté et **ancré sur le marché** (power ranking, prédictions, modèle QB). Site nfeloapp.com. Pas de licence.
- **fivethirtyeight/nfl-elo-game** : scores depuis 1920 avec probabilités Elo et code d'évaluation des prévisions. Données figées.
- **Ce qu'on en retient** : la meilleure pratique en NFL consiste à partir de la **ligne du marché** et à n'ajuster que marginalement (approche nfelo).

### 4.12 NHL

- **Hockey-Scraper** (★157, GPL-3, 2024-06) : PBP et shifts NHL.
- **HockeyModel** (pbulsink, R, GPL-3, 2026-05) : modèle de type DC adapté à la NHL, avec simulation de saison et de playoffs. Évolutions documentées : **boost des nuls et prolongations** (« diagonal-inflated »), puis passage aux **xG MoneyPuck** à la place des buts réels. Résultats publiés automatiquement sur Bluesky.
- **NHL-Prediction-Model** (Shomer, 2019) : probabilités de victoire.
- **Ce qu'on en retient** : la gestion de la **prolongation et des tirs au but** (marché 3 issues ou 2 issues) et l'usage des xG plutôt que des buts.

### 4.13 Rugby, handball, MMA, F1

- **Rugby**
  - **rugbypy** (★51, Apache-2.0) : plus de 8 000 joueurs, 250 équipes, 6 000 matchs (2022-2025), **dont le Top 14**.
  - **gmalbert/rugby** : Elo, DC (forces attaque/défense) et RF pour les marqueurs d'essais.
  - **AustralianElo** : AFL, NRL, Super Rugby.
  - **hans-brgs/rugby-data-scraper** : API cachée ESPN, Top 14 inclus.
  - **transientlunatic/rugby-pymc** et l'exemple PyMC « rugby analytics » (Baio & Blangiardo).
  - **Leçon** : le score en rugby n'est pas poissonien (essais 5/7, pénalités 3). Il vaut mieux modéliser la **marge** (gaussienne ou Student-t sur la différence de points) ou les **essais et pénalités séparément**.
- **Handball**
  - **florianfelice/HandballAnalysis** : notebooks des articles Felice (2023) et Felice & Ley (2023/2025). La distribution de **Conway-Maxwell-Poisson** est nécessaire (sous-dispersion des scores). Plus de 80 % d'exactitude rapportés avec « statistically enhanced learning ». Certaines bibliothèques ne sont pas publiques.
  - **handball-betting-prediction** : 2016, réseau de neurones, obsolète.
  - **Leçon** : CMP (disponible dans goalmodel) plutôt que Poisson.
- **MMA**
  - **scrape_ufc_stats** (★168, GPL-3, actif) : scraper de référence ufcstats.com (événements, combats, stats, combattants).
  - **UFC-Predictions** : RF / XGB, 72 % d'exactitude en validation (rééchantillonnage).
  - **ufc-predictor** : ensemble de 5 modèles, pipeline sans fuite revendiqué, 68,45 % sur 2023-2026, ROI backtesté de +3,3 à +4,2 % sur les combats à forte conviction.
  - Base de comparaison : le « coin rouge » (souvent le favori) gagne 55,7 %. Les ROI annoncés restent faibles et non significatifs.
- **F1**
  - **Fast-F1** (★≈5,4k, MIT) et **jolpica-f1** (★918, remplaçant d'Ergast) sont les deux sources.
  - **2025_f1_predictions** : démo virale GBM sur qualifications.
  - **Leçon** : pour la F1, les modèles de classement (Plackett-Luce, openskill/TrueSkill) et la simulation Monte Carlo de course sont plus adaptés que la classification.

### 4.14 Kaggle : jeux de données et notebooks connus

| Ressource | Contenu | Usage |
|---|---|---|
| [Beat The Bookie: Odds Series Football Dataset](https://www.kaggle.com/datasets/austro/beat-the-bookie-worldwide-football-dataset) (Kaunitz et al.) | Cotes de clôture de **479 440 matchs** (818 ligues, 2005-2015, jusqu'à 32 bookmakers : max, moyenne, nombre), séries de cotes minute par minute, plus 880 494 matchs 2000-2015 | Tester les stratégies de consensus et le « steam ». |
| [European Soccer Database](https://www.kaggle.com/datasets/hugomathien/soccer) (H. Mathien) | Plus de 25 000 matchs, 11 pays, 2008-2016, cotes de 10 bookmakers, attributs FIFA des joueurs | Très utilisé dans les notebooks. Ancien. |
| [ATP Tennis 2000-2026 daily update](https://www.kaggle.com/datasets/dissfya/atp-tennis-2000-2023daily-pull) | Plus de 60 000 matchs ATP avec cotes | Alternative à Sackmann pour le tennis avec cotes. |
| [ATP and WTA Tennis Results and Betting odds](https://www.kaggle.com/datasets/hakeem/atp-and-wta-tennis-data) | tennis-data.co.uk compilé | Base de MLT. |
| Kaggle « A Large Tennis Dataset for ATP and ITF Betting » (ehallmar) | ATP + ITF + cotes | Base de Tennis-Betting-ML. |
| Kaggle « ufcdata » (rajeevw) | UFC 1993 → | Base de UFC-Predictions. |
| Notebook « Beating the bookmakers on tennis matches » (E. Thomas) | Voir ATPBetting | **Contre-exemple à étudier** (fuite, sur-ajustement). |
| Compétitions **March Machine Learning Mania** | Prévision NCAA évaluée en Brier / log-loss | Les solutions gagnantes s'appuient sur des cotes dé-marginées (goto_conversion). |

---

## 5. Retirer la marge du bookmaker : méthodes (référence `implied`)

Notations : cotes décimales oᵢ, probabilités brutes πᵢ = 1/oᵢ, booksum Π = Σπᵢ (> 1), marge M = Π − 1, n issues, probabilités « justes » pᵢ.

| Méthode (`implied` / penaltyblog) | Idée / formule | Paramètre résolu | Remarques |
|---|---|---|---|
| **basic / multiplicative** | pᵢ = πᵢ / Π | – | La plus simple. **Ignore le biais favori-outsider** (surestime les outsiders). Selon `implied`, c'est « la moins précise ». |
| **additive** | pᵢ = πᵢ − M/n | – | Peut produire des **probabilités négatives** sur les gros outsiders ou quand n est grand. À éviter. |
| **wpo** (*weights proportional to the odds*, Buchdahl ; `differential_margin_weighting` chez penaltyblog) | Marge appliquée à chaque issue proportionnellement à sa cote : cote juste = n·oᵢ / (n − M·oᵢ) | – | Analytique. Bon résultat empirique (voir ci-dessous). |
| **power** (« logarithmic » chez Buchdahl) | pᵢ = πᵢᵏ, avec k > 1 tel que Σpᵢ = 1 | k (solveur) | Robuste. Excellent en pratique. |
| **or** (*odds ratio*, Cheung 2015) | πᵢ/(1−πᵢ) = c · pᵢ/(1−pᵢ) ⇒ pᵢ = πᵢ / (c − c·πᵢ + πᵢ), c tel que Σpᵢ = 1 | c (solveur) | Sous-estime légèrement le biais favori-outsider (Buchdahl). |
| **shin** (Shin 1992-93 ; Jullien-Salanié 1994) | Fraction z de parieurs initiés : pᵢ = [√(z² + 4(1−z)·πᵢ²/Π) − z] / [2(1−z)] | z (itératif ; analytique si n = 2) | Donne aussi z, une mesure de l'« information privée ». Excellent en pratique. |
| **bb** (*balanced books*, Fingleton & Waldron 1999) | Variante de Shin : le bookmaker **minimise son risque** au lieu de maximiser son profit. Option `grossmargin` (coûts d'exploitation, 0 à 5 %). | z | Moins utilisé. |
| **jsd** (Christopher D. Long) | Les πᵢ sont vus comme une version bruitée des pᵢ. On impose une **distance de Jensen-Shannon** constante entre les lois binaires (pᵢ, 1−pᵢ) et (πᵢ, 1−πᵢ). | distance (solveur) | Récent. Moins documenté. |
| **goto / ooepc** (Kaito Goto) | On retire à chaque πᵢ le **même nombre d'erreurs-types** (SEᵢ plus large pour les outsiders), puis on normalise | c | Bons résultats en compétitions Kaggle de log-loss. |

**Résultats empiriques à retenir** :
- **Buchdahl, *Wisdom of the Crowd* (version mise à jour).**
  - Échantillon : **136 876 matchs** (Pinnacle 1X2, clôture, 08/2007 → 06/2016 ; 410 628 cotes).
  - Yield théorique en pariant toutes les issues aux cotes « justes » (0 % si la méthode est parfaite) : cotes brutes Pinnacle **−3,36 %** ; marge égale (multiplicative) **−0,56 %** ; *margin proportional to odds* **+0,10 %** ; *odds ratio* **−0,20 %** ; *logarithmic / power* **+0,07 %**.
  - **La normalisation simple est la plus biaisée.** WPO et power sont quasi parfaits. OR sous-corrige légèrement le biais favori-outsider.
- **Comparaisons par log-loss** (article Medium, football) : **Shin et power** sont les meilleurs, au coude à coude selon le bookmaker (Shin pour Pinnacle, bet365, Betfair, 10Bet ; power pour 1xbet, William Hill, TitanBet). Quand la cote maximale d'un match est < 3,45 (pas de gros outsider), **toutes les méthodes se valent**. Au-delà d'environ 5,3, power et Shin apportent un vrai gain.
- **Notre choix** : implémenter **toutes** les méthodes, garder **Shin** par défaut pour les marchés 1X2 et **power** comme alternative robuste. Exposer `margin`, `z` et `problematic`. Permettre `target_probability ≠ 1` pour les marchés « top N » et « qualifié ».

---

## 6. Lectures de praticiens : les enseignements chiffrés

| # | Source | Enseignement clé (chiffré) |
|---|---|---|
| 1 | **Joseph Buchdahl — *The Wisdom of the Crowd*** ([PDF](https://www.football-data.co.uk/The_Wisdom_of_the_Crowd_updated.pdf), [blog](https://football-data.co.uk/blog/wisdom_of_the_crowd.php)) | Pinnacle est le « crowd » de référence. Sur **37 303 matchs** (2012-2017), parier toute cote > cote juste Pinnacle rapporte **+1,6 à +2,5 %** (≈36 500 paris). Avec une value > 2 % : **+3,3 à +5,7 %**. Avec une value > 5 % : **+6,8 à +13,5 %** (3 400 à 5 100 paris). Le rendement réel suit à peu près le rendement attendu. Marges moyennes : Pinnacle 2,7 %, Betvictor 4,1 %, bet365 5,5 %, William Hill 7,4 %, Ladbrokes 7,8 %. |
| 2 | **Buchdahl — *What is the true expected profit for the WoC system?*** ([blog](https://football-data.co.uk/blog/wisdom_of_crowd_betting_system_closing_odds.php)) | Bilan publié en temps réel : **26 960 paris**, yield réel **+4,90 %** (cote moyenne 3,83). Yield attendu selon les cotes pré-clôture **+4,13 %** (p = 0,47), selon la clôture **+2,88 %** (p = 0,05). **48,8 %** des matchs avec plus de 2 % de value offraient aussi un **arbitrage**, contre 19 % en moyenne et 73 % pour plus de 5 % de value. Autrement dit, la value vient de bookmakers **en retard** sur le marché. |
| 3 | **Buchdahl — *Testing betting models*** ([blog](https://football-data.co.uk/blog/model_testing.php)) | 6 562 paris : yield réel 3,79 % contre 4,19 % attendu, **p = 0,838** (aucune différence significative). Sur des fenêtres glissantes de 1 000 paris, des écarts « 1 chance sur 60 » ou « 1 sur 40 » apparaissent puis régressent. **Méthodes : t-test (attendu contre réel), p-value à partir de yield, cote moyenne et n, Monte Carlo.** Biais psychologique : on remet en cause le modèle après des pertes, jamais après des gains. |
| 4 | **Buchdahl — *Squares & Sharps, Suckers & Sharks* (livre, 2016)** et articles Pinnacle | Il faut **beaucoup** de paris pour distinguer le talent de la chance. Approximation : l'écart-type d'un pari à cote o vaut ≈ √(o−1), donc **n ≈ (1,96)²·(o−1)/yield²**. Yield de 5 % à cote 2,0 : **≈1 540 paris**. Yield de 3 % à cote 2,0 : **≈4 270**. Yield de 5 % à cote 3,5 : **≈3 840**. Yield de 2 % à cote 2,0 : **≈9 600**. La **CLV** (battre la cote de clôture sans marge) converge bien plus vite que le P&L. |
| 5 | **Kaunitz, Zhong, Kreiner (2017)** — *Beating the bookies with their own numbers* ([arXiv](https://arxiv.org/abs/1710.02824)) | Consensus de 32 bookmakers. Simulation sur **479 440 matchs** (2005-2015) : environ 44 % de réussite, **+3,5 %**. Profit en paper trading et en argent réel sur 5 mois, puis **limitation des mises et contrôle manuel** des paris par les bookmakers. **La contrainte réelle est la gestion des comptes gagnants.** |
| 6 | **opisthokonta.net** (J. C. Lindstrøm) — ex. [*Better prediction… using data from other competitions*](https://opisthokonta.net/?p=1108), [Dixon-Coles time weighting](https://opisthokonta.net/?p=1013) | Métrique : **RPS** (modèle nul : 0,2249). Premier League seule : 0,19558. Avec les données de Championship : **0,19292** (−1,4 %). Ajouter la FA Cup n'apporte rien. ξ optimal ≈ **0,0018 par jour** (demi-vie ≈ 385 jours). Le ξ optimal est **le même pour les trois modèles testés**. Le blog documente aussi Shin, l'odds ratio, la CMP et les λ dérivés des cotes. |
| 7 | **David Sheehan (dashee87)** — *Predicting Football Results With Statistical Modelling: Dixon-Coles and Time-Weighting* ([blog](https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling-dixon-coles-and-time-weighting/)) | ρ ≈ **−0,13** (corrige les scores 0-0, 1-0, 0-1 et 1-1). ξ optimal ≈ **0,00325 par jour** (demi-vie ≈ 213 jours ; Dixon-Coles avait 0,0065 par demi-semaine, soit ≈ 0,0019 par jour). Log-vraisemblance sur la seconde moitié 2017/18 : −125,15 avec 5 saisons pondérées contre −125,38 avec une saison non pondérée, un gain **marginal**. Conclusion de l'auteur sur le profit : *« They won't »* (ces modèles ne vous feront pas gagner d'argent). |
| 8 | **Beat the Bookie blog** — [*The predictive power of xG*](https://beatthebookie.blog/2021/06/07/the-predictive-power-of-xg/) | Plus de 12 000 matchs (top 5 ligues, 5 saisons, Understat et football-data). Brier : meilleur modèle xG **58,6**, meilleur modèle buts **59,7**, cotes bet365 **57,2**. **Le marché reste meilleur.** 8 des 10 meilleurs modèles utilisent les xG. Fenêtres de 5 à 15 matchs optimales. **Tous les modèles perdent** (−300 à −800 unités). Un meilleur Brier ne garantit pas un meilleur profit. |
| 9 | **Walsh & Joshi (2024) + corrigendum (2025)** — *Should model selection be based on accuracy or calibration?* ([article](https://www.sciencedirect.com/science/article/pii/S266682702400015X), [corrigendum](https://www.sciencedirect.com/science/article/pii/S2666827025000106)) | NBA. Version initiale : sélection par **calibration** **+34,7 %** de ROI moyen, contre **−35,2 %** par exactitude. **Après correction d'un bug dans le feature engineering** : **−9,8 % contre −26,8 %** en moyenne, **+23,1 % contre +10,9 %** dans le meilleur cas. Le corrigendum note aussi que « Kelly peut échouer même avec un modèle bien calibré ». **Deux leçons : optimiser la calibration (log-loss, ECE), et même les résultats publiés évalués par des pairs peuvent être faux.** |
| 10 | **Uhrín, Šourek, Hubáček, Železný (2021)** — *Optimal sports betting strategies in practice* ([arXiv](https://arxiv.org/abs/2107.08827)) ; **Hubáček et al. (2019, IJF)** — *Exploiting sports-betting market using ML* | Un **Kelly fractionnel adaptatif** est un bon choix dans de nombreux contextes, et des **contrôles de risque additionnels** sont indispensables. Hubáček et al. : **décorréler** le modèle des cotes du bookmaker (pénalité dans la loss) améliore le profit. Un modèle qui imite le marché ne trouve pas de value. |
| 11 | **Pinnacle Betting Resources** (Buchdahl, Mark Taylor…) — ex. [Kelly risk assessment](https://www.pinnacle.com/betting-resources/en/betting-strategy/revisiting-the-kelly-criterion-part-1-a-risk-assessment/nj2jwgv9yhxjp6gj), [How to use Kelly](https://www.pinnacle.com/betting-resources/en/betting-strategy/how-to-use-kelly-criterion-for-betting/2bt2lk6k2qwq7qj8) | **Kelly** (résultats mathématiques classiques, Thorp). Avec une fraction c de Kelly, la probabilité de **tomber un jour à x % de la bankroll** vaut ≈ x^(2/c − 1). En full Kelly, il y a **50 %** de chances de perdre la moitié à un moment donné. En **½ Kelly : 12,5 %**. En **¼ Kelly : ≈ 0,8 %**. La croissance en ½ Kelly reste à **75 %** de l'optimum. Si l'edge est surestimé d'un facteur 2, le « full Kelly » apparent devient du 2× Kelly réel, et la **croissance espérée tombe à zéro**. **CLV** : comparer à la clôture **sans marge**. Battre la clôture brute de 2 % peut n'être qu'à l'équilibre. Mark Taylor ([The Power of Goals](http://thepowerofgoals.blogspot.com/)) : xG, espérances de buts et pricing live. |
| 12 | **Tony ElHabr** ([blog](https://tonyelhabr.rbind.io/posts.html)) — *Calibrating Binary Probabilities*, *xG Model Calibration*, *What exactly is an "expected point"?* | Recalibrer les probabilités FiveThirtyEight (football féminin) fait passer le Brier skill score de **0,196 à 0,205**. Méthodes de calibration (Platt, isotonique), diagnostics par courbes de fiabilité, comparaison de la calibration des probabilités de match Understat et FotMob. |
| 13 | **Friends of Tracking / David Sumpter** (*Soccermatics*) | Expérience de paris réels avec un modèle de **biais de cotes** (favori-outsider), avec d'autres modèles testés sur 2015-16. Sumpter a publié sur Medium un article affirmant que « suivre les conseils du livre aurait rendu très riche » (à lire avec précaution). Les vidéos Friends of Tracking (2020-2021) sont une excellente formation à l'analytics football (xG, modèles de passes, tracking). |
| 14 | **Wilkens (2026)** — *Can simple models predict football — and beat the odds?* (J. Sports Analytics) | Modèle xG simple sur la Bundesliga : environ **+10 % de ROI aux cotes moyennes, environ +15 % aux meilleures cotes**. **À prendre avec précaution** : une seule ligue, cotes moyennes et maximales (pas la clôture d'un bookmaker précis), pas de prise en compte des limites. |

---

## 7. Leçons transverses pour notre bibliothèque

### 7.1 Signaux d'alerte observés (à automatiser dans nos tests)
1. **Meilleures cotes du marché** (`market_maximum`, *best odds*) utilisées en backtest. C'est irréaliste. **Il faut imposer une cote d'un bookmaker identifié, horodatée avant le match.**
2. **Fuite temporelle** : ratings ou Elo calculés sur tout l'historique, features postérieures au match (blessures, « forme » incluant le match), normalisation globale. Exemples : ATPBetting et SoccerPredictor (« profit 1069 %, 90 % d'exactitude, ROI 33,4 % sur 113 jours et 32 paris »).
3. **Hyperparamètres ou seuils choisis sur la période d'évaluation** (« hyperparameters chosen to maximize ROI », seuil d'edge de 20 %). Il faut un **walk-forward strict** et des périodes de test intouchées.
4. **Petits échantillons** : 106 ou 32 paris. Calculer systématiquement la **p-value** (t-test) et l'**intervalle de confiance** du yield.
5. **Exactitude présentée comme métrique principale.** Il faut à la place **log-loss, RPS, Brier, ECE et CLV**. L'exactitude d'un Elo tennis (~66 à 69 %) ne dit rien du profit.
6. **Absence de licence** (kyleskom, nfelo, ATPBetting, SoccerPredictor) : on peut s'inspirer des idées, pas copier le code.

### 7.2 Ce que le consensus des praticiens recommande
- **Le marché est la meilleure baseline.** Pinnacle à la clôture, sans marge, est quasi parfaitement calibré.
- Le profit vient de deux sources : **(a)** les bookmakers **en retard** sur le marché (wisdom of the crowd, Kaunitz) ; **(b)** une information **décorrélée** du marché (Hubáček). Un modèle « maison » qui ne fait que reproduire le marché ne rapporte rien (dashee87, beatthebookie).
- **Mesurer la CLV** sur chaque pari, en comparant à la clôture sans marge. Elle converge en quelques centaines de paris, contre plusieurs milliers pour le P&L.
- **Kelly fractionnel (¼ à ½), plafonné, simultané**, et une bankroll **par stratégie**.
- **Les marges FR sont élevées** (Winamax 8 à 12 % selon winator, contre 2 à 3 % chez Pinnacle). La value y est rare. Il faut **cibler les promotions et freebets** (pretrehr), les **cotes boostées** et les **retards de mise à jour**.
- **Les comptes gagnants sont limités** (Kaunitz). Notre outil doit le documenter et suivre les limites.

### 7.3 Architecture cible inspirée des meilleurs dépôts
```
data/        sources (adapters): football-data, Understat, ClubElo, StatsBomb, nflverse, nba_api, FastF1/jolpica, rugbypy, ufcstats
             + résolveur d'entités (équipes/joueurs/compétitions) [sports-betting._resolver, bethurtadom]
odds/        ingestion (OddsHarvester, The Odds API fr, adaptateurs ANJ maison), séries temporelles, ouverture/clôture
             devig/ (multiplicative, additive, wpo, power, odds_ratio, shin, bb, jsd, goto) [implied, shin, penaltyblog]
models/      goals (Poisson, DC+ξ, bivarié, NegBin, CMP, hurdle, ZIP) [penaltyblog, goalmodel, footBayes]
             ratings (Elo, Glicko-2, Pi, Stephenson, Weng-Lin), datés [skelo, PlayerRatings, openskill]
             ml (wrappers sklearn + calibration isotonique/Platt) [sports-betting, Walsh & Joshi]
             market (λ depuis cotes, mélange modèle/marché) [goalmodel expg_from_*, nfelo]
eval/        RPS, Brier, log-loss, ECE, CLV, t-test yield, bootstrap, Monte Carlo [penaltyblog.metrics, Buchdahl]
betting/     value detection (vs fair consensus/Pinnacle), Kelly fractionnel/simultané/plafonné, arbitrage, freebets [penaltyblog.betting, pretrehr]
backtest/    walk-forward strict, cotes réalistes horodatées, limites, frais, latence [sports-betting, flumine]
ops/         monitoring synthétique des scrapers, santé des sources, alertes [paris-sportif]
```

---

## 8. Sources principales consultées

- Pages topics GitHub (`sports-betting`, `betting`, `football-prediction`, `football-analytics`, `dixon-coles`, `kelly-criterion`, `winamax`, `betclic`), API ecosyste.ms, READMEs bruts (raw.githubusercontent.com) et code de `pretrehr/Sports-betting/sportsbetting/bookmakers/*.py`, `penaltyblog/*/__init__.py`, `sports-betting/src/sportsbet/*`, `opisthokonta/implied/R/implied_probabilities.R`.
- CRAN : `implied`, `elo`, `PlayerRatings`, `piratings`, `footBayes`, `worldfootballR`, `fbRanks` (archivé le 15/06/2022).
- Buchdahl : [Wisdom of the Crowd (PDF)](https://www.football-data.co.uk/The_Wisdom_of_the_Crowd_updated.pdf), [WoC closing odds](https://football-data.co.uk/blog/wisdom_of_crowd_betting_system_closing_odds.php), [Model testing](https://football-data.co.uk/blog/model_testing.php).
- [Kaunitz et al., arXiv:1710.02824](https://arxiv.org/abs/1710.02824) · [Kaggle Beat The Bookie](https://www.kaggle.com/datasets/austro/beat-the-bookie-worldwide-football-dataset).
- [dashee87 — DC & time-weighting](https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling-dixon-coles-and-time-weighting/) · [opisthokonta p=1108](https://opisthokonta.net/?p=1108) · [opisthokonta p=1013](https://opisthokonta.net/?p=1013).
- [beatthebookie.blog — predictive power of xG](https://beatthebookie.blog/2021/06/07/the-predictive-power-of-xg/).
- [Walsh & Joshi 2024](https://www.sciencedirect.com/science/article/pii/S266682702400015X) · [Corrigendum 2025](https://www.sciencedirect.com/science/article/pii/S2666827025000106) · [Uhrín et al. 2021](https://arxiv.org/abs/2107.08827) · [Hubáček et al. 2019](https://econpapers.repec.org/article/eeeintfor/v_3a35_3ay_3a2019_3ai_3a2_3ap_3a783-796.htm).
- [Pinnacle — Kelly risk assessment](https://www.pinnacle.com/betting-resources/en/betting-strategy/revisiting-the-kelly-criterion-part-1-a-risk-assessment/nj2jwgv9yhxjp6gj) · [Pinnacle — How to use Kelly](https://www.pinnacle.com/betting-resources/en/betting-strategy/how-to-use-kelly-criterion-for-betting/2bt2lk6k2qwq7qj8).
- [Tony ElHabr — posts](https://tonyelhabr.rbind.io/posts.html) · [The Power of Goals (M. Taylor)](http://thepowerofgoals.blogspot.com/) · [Soccermatics docs](https://soccermatics.readthedocs.io/).
- Écosystème : [FBref & Stathead data update (01/2026)](https://www.sports-reference.com/blog/2026/01/fbref-stathead-data-update/) · [Pinnacle API fermée (07/2025)](https://dev.to/ryankr/pinnacle-killed-its-public-api-heres-how-to-get-pinnacle-odds-in-2026-with-code-39pe) · [Issue Sackmann 404 (MLT-OSS/FirstData #238)](https://github.com/MLT-OSS/FirstData/issues/238) · [The Odds API — bookmakers](https://the-odds-api.com/sports-odds-data/bookmaker-apis.html) · [ANJ — opérateurs agréés](https://anj.fr/offre-de-jeu-et-marche/operateurs-agrees).
- Comparaison des méthodes de dé-margination (log-loss) : [Medium — How to Compute Football Implied Probabilities](https://medium.com/geekculture/how-to-compute-football-implied-probabilities-from-bookmakers-odds-bbb33ccf7c1d) · [CRAN implied — vignette](https://cran.r-project.org/web/packages/implied/vignettes/introduction.html).
