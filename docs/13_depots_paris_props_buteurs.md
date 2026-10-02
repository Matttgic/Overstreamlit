# Dépôts open source : modèles de props, buteurs, NHL/NBA, détecteurs de value bets et scrapers ANJ

> Recherche effectuée le 2 octobre 2026 pour le projet **Overstreamlit**.
> Méthode : recherches web + lecture directe des README / fichiers clés via `raw.githubusercontent.com` et métadonnées (étoiles, dates de création / dernier push) via le proxy public `ungh.cc` (miroir de l’API GitHub) et les badges `img.shields.io` (étoiles, dernier commit, licence). Les dates « dernière activité » sont celles du dernier commit de la branche par défaut.
> Règle : seuls les dépôts effectivement consultés sont listés. Les « performances » annoncées sont rapportées telles quelles, avec un commentaire critique. « ≈ » = valeur au moment de la consultation.

**Statut : version complète du 2 octobre 2026.**

## Sommaire
* Synthèse en 6 points · Tableau récapitulatif · Top 15 à réutiliser
* 1. NHL (modèles de match, ATG/props, données et xG)
* 2. NBA (props, minutes/blessures, modèle de match)
* 3. Football (buteurs, tirs) et tennis (aces, jeux)
* 4. Détecteurs de value bets / +EV / odds screens
* 5. Scrapers des bookmakers français (ANJ)
* 6. Projets avec résultats documentés (lecture critique)
* 7. Idées d'architecture pour un tableau de bord automatisé

## Synthèse en 6 points

1. **~90 dépôts vérifiés** (README et/ou code lus, métadonnées via l'API GitHub). La grande majorité des projets NHL/NBA de props ont été créés en **2026** (souvent avec un assistant de code) et n'ont **aucun historique réel** ; leur valeur est architecturale.
2. **Tous les projets qui mesurent honnêtement contre la clôture Pinnacle confirment le constat d'Overstreamlit** : les modèles statistiques ne battent pas le marché (NHL props −0,3 % sur 25 911 paris ; Dixon-Coles perdant dans 36/36 championnats ; NFL −2 % ; ML foot −6,7 %), alors que l'**ancre sharp + line shopping** est le seul edge reproductible (+4,86 %, CLV +3,05 % sur 20 676 paris en Europe).
3. **Alerte France** : le même auteur (ryan00x/Bet-Model) a testé les **5 books ANJ** en août 2026 : meilleure cote FR en médiane = **0,936 × Pinnacle**, **aucune** cote à +2 % d'EV sur 4 342 prix / 99 matchs. Sur les marchés principaux français, la méthode est quasi stérile ; il faut viser **boosts, promotions, props/marchés secondaires** et la **vitesse sur l'info** (gardien, compositions).
4. **Buteurs** : pas de modèle « anytime goalscorer » foot open source sérieux ; en NHL, plusieurs modèles récents (Mbennett00, kylewish19, jaredkimble-coder). La meilleure idée trouvée vient d'un projet français sur les marqueurs d'essai (Jejeh040/marqueurs-xiii) : **ancrer le total d'équipe sur le marché et ne modéliser que la répartition entre joueurs** ; et pour dé-viger un marché à un seul côté, ajuster la forme de l'échelle 1+/2+/3+ (JChan23).
5. **Scrapers ANJ** : peu de projets récents. Winamax (JSON `PRELOADED_STATE` ou Socket.IO), Unibet (cotes buteur/points NHL : mazalazop), Betclic (extracteur polonais récent + endpoints 2021 de pretrehr). The Odds API couvre désormais une **région `fr`** (Betclic, NetBet, PMU, Unibet, Winamax) pour les marchés principaux.
6. **Architecture gagnante** : GitHub Actions (crons calés sur l'info) + JSON/SQLite + GitHub Pages ; prix juste = dé-vig Shin/power par book, agrégation log-odds pondérée sharp, book évalué exclu ; ledger verrouillé avant le match ; CLV, groupe témoin et test placebo.

## Tableau récapitulatif (projets principaux)

Intérêt : ★★★ = à étudier en priorité, ★★ = idées ou code utiles, ★ = pédagogique / à éviter.

| Cat. | Projet | ★ GitHub | Dernière activité | Licence | Intérêt | En un mot |
|---|---|---|---|---|---|---|
| NHL | Mbennett00/NHLModel | 0 | 10/2026 | — | ★★★ | ATG/SOG/points + match, Actions + Pages, onglet « Check » |
| NHL | cooperross399/nhl-betting-lab | 0 | 10/2026 | — | ★★★ | Props NHL, protocole de validation, **aucune edge** |
| NHL | jaredkimble-coder/nhl-atg-lamp-lab | 0 | 10/2026 | — | ★★★ | ATG, cotes toutes les 30 min, modèle/cotes découplés |
| NHL | CarsonBillig/nhl-model | 0 | 10/2026 | — | ★★ | Méthode Pizzola, gardien GSAx, cage vide |
| NHL | MJACode/betting-model | 0 | 10/2026 | — | ★★ | Market lab NHL (archive SBR), doc CLV |
| NHL | flagk/nhl-tracker | 0 | 10/2026 | — | ★★ | README-dashboard, fake bets, « no bet » |
| NHL | kylewish19/wshl-x-nhl-model | 0 | 09/2026 | — | ★★ | GBM-Poisson + NB, carte verrouillée avant cotes |
| NHL | renenunezg/momentumnhl | 0 | 10/2026 | MIT | ★★ | MoneyPuck, fraîcheur des cotes |
| NHL | shawnmcgee/degenpredicts | 1 | 10/2026 | — | ★★ | Multi-sports Actions/Pages, alerte quota |
| NHL | sheridanmi/nhl-sog-predictor | 0 | 09/2026 | — | ★ | SOG Monte Carlo, poids ad hoc |
| NHL | gmalbert/hockey-predictions | 4 | 10/2026 | — | ★ | Streamlit complet (onglets) |
| NHL data | Zmalski/NHL-API-Reference | 608 | 11/2025 | MIT | ★★★ | Doc des endpoints NHL |
| NHL data | coreyjs/nhl-api-py | 152 | 09/2026 | Apache-2.0 | ★★ | Client API NHL |
| NHL data | HarryShomer/Hockey-Scraper | 157 | 06/2024 | GPL-3.0 | ★★ | Play-by-play + shifts |
| NHL data | JNoel71/NHL-Expected-Goals-xG-Model | 7 | 01/2025 | GPL-3.0 | ★★ | xG LightGBM + biais d'aréna |
| NBA | Risky-Scout/nba-player-props-model & nba-prop-quant | 1 / 0 | 08-09/2026 | — | ★★★ | PMF ZINB, minutes, snapshots CLV |
| NBA | pradazay1-code/Sports-betting-model | 0 | 10/2026 | — | ★★★ | Props multi-sports 100 % Actions/Pages, Pinnacle guest |
| NBA | ethanllawrence/nba-props-projection | 0 | 10/2026 | — | ★★ | PRA sur Pages, heartbeat données périmées |
| NBA | pranavcheedalla/propsim | 0 | 09/2026 | — | ★★ | Monte Carlo C++, signal de minutes |
| NBA | KamranSHussain/NBA-Propositions-Forecasting-App | 0 | 05/2026 | MIT | ★ | Transformer quantile points |
| NBA | bendominguez0111/nba-models | 20 | 03/2023 | — | ★ | Modèle 3PM |
| NBA | kyleskom/NBA-Machine-Learning-Sports-Betting | 1 729 | 01/2026 | — | ★ | Match NBA, populaire, sans CLV |
| NBA data | swar/nba_api | 3 792 | 08/2026 | MIT | ★★★ | Client stats.nba.com |
| NBA data | mxufc29/nbainjuries | 45 | 02/2026 | MIT | ★★★ | Rapports de blessures officiels |
| Foot | tanamsethi31/footymodel | 3 | 10/2026 | — | ★★★ | Props tirs/SOT, déclenchement sur composition |
| Foot | jbern1022/futbol-modelo | 0 | 10/2026 | MIT | ★★ | LightGBM-Poisson props, ledger append-only |
| Rugby XIII | Jejeh040/marqueurs-xiii | 0 | 09/2026 | MIT | ★★★ | Modèle de marqueurs ancré sur le marché (FR, Unibet) |
| Foot data | probberechts/soccerdata | 2 100 | 08/2026 | Apache-2.0 | ★★★ | FBref/Understat/WhoScored/Sofascore |
| Tennis | JChan23/Tennis-Most-Aces | 0 | 09/2026 | — | ★★★ | Dé-vig d'échelles « N+ » à marge libre |
| Tennis | dbabsy/tennis-props | 0 | 10/2026 | — | ★★ | Point→match, aces, live, mesuré vs Pinnacle |
| Tennis | DanielTomaro13/Tennis-Modelling | 2 | 10/2026 | MIT | ★ | Site Pages toutes les 3 h |
| +EV | ryan00x/Bet-Model | 0 | 10/2026 | MIT | ★★★ | Ancre sharp +4,86 %, **test ANJ négatif** |
| +EV | emmanueladutwum123/sports-betting-dashboard | 0 | 08/2026 | — | ★★★ | Prix juste Shin + log-odds, marché 36/36 |
| +EV | Lisandro79/BeatTheBookie | 658 | 10/2021 | GPL-3.0 | ★★ | Stratégie consensus (papier 2017) |
| +EV | aqsmith02/paper-betting-tracker | 6 | 09/2026 | — | ★★ | Paper trading, témoin aléatoire, Actions 7×/h |
| +EV | kieranaston/bet-bot | 0 | 09/2026 | — | ★★ | Alertes Telegram bidirectionnelles |
| +EV | wilfhawk/sharpline | 0 | 10/2026 | — | ★★ | Clone OddsJam, repli de books sharp |
| +EV | bramos0/edge-finder | 0 | 09/2026 | — | ★ | Outil navigateur, notation des tipsters au CLV |
| +EV | djscott03/Scott-Sports-Predictions | 0 | 10/2026 | — | ★★ | Résultats négatifs honnêtes (NFL) |
| Infra | jordantete/OddsHarvester | 256 | 10/2026 | MIT | ★★★ | Cotes historiques OddsPortal |
| Infra | martineastwood/penaltyblog | 228 | 10/2026 | MIT | ★★★ | Dé-vig (7 méthodes), Dixon-Coles |
| Infra | betcode-org/betfair & flumine | 515 / 246 | 09-10/2026 | MIT | ★★ | API Betfair Exchange |
| Infra | declanwalpole/sportsbook-odds-scraper | 21 | 04/2025 | — | ★ | Abstraction de scrapers d'API non documentées |
| FR | pretrehr/Sports-betting | 534 | 10/2021 | MIT | ★★ | 15 books FR, carte des endpoints, bonus |
| FR | Matttgic/Cotescope | 0 | 09/2026 | — | ★★★ | Scanner ANJ + Pinnacle, garde-fou grosses cotes |
| FR | mazalazop/nhl-unibet-odds-scraper | 0 | 10/2026 | — | ★★★ | Cotes buteur/points NHL Unibet.fr |
| FR | Ghantard/winator | 0 | 09/2026 | — | ★★ | Winamax via `PRELOADED_STATE` vs médiane marché |
| FR | HKB06/ScriptWinamax | 0 | 09/2025 | — | ★★ | Winamax Socket.IO (tous marchés) |
| FR | anach-ai/winamax | 2 | 11/2025 | MIT | ★ | API locale Winamax foot |
| FR | Tomek765/betclic-odds-extractor | 0 | 10/2026 | — | ★ | Extracteur Betclic (PL) |
| FR | almoundji/ALL | 0 | 09/2026 | — | ★ | Value bets foot FR, Netlify |

## Top 15 à réutiliser

1. **ryan00x/Bet-Model** — `value_bet_sharp.py` (power devig Pinnacle, seuil 2 %, ¼ Kelly, `--evaluate` CLV) + test placebo ; **lire la section sur l'échec ANJ** avant d'investir dans les marchés principaux FR.
2. **emmanueladutwum123/sports-betting-dashboard** — pipeline de prix juste (Shin par book → log-odds pondéré sharp → exclusion du book évalué), filtre de marge plausible, Kelly rétréci.
3. **Jejeh040/marqueurs-xiii** — architecture d'un modèle de buteur « ancré marché + répartition par minute de jeu », rapport Pages en français, mesure de la marge buteur.
4. **JChan23/Tennis-Most-Aces** — dé-vig d'échelles à un seul côté (1+/2+/3+) par binomiale négative à marge libre → applicable aux cotes buteur/points des books FR.
5. **Mbennett00/NHLModel** — modèle NHL ATG/SOG/points complet + automatisation (crons gardiens, release `data-latest`, onglet Check).
6. **cooperross399/nhl-betting-lab** — protocole de validation (régression du désaccord, ROI par tranche d'edge, réplication) et document « why the model has no edge ».
7. **jaredkimble-coder/nhl-atg-lamp-lab** — découplage modèle lent / cotes toutes les 30 min, exclusion des matchs commencés, `name_match()`.
8. **mazalazop/nhl-unibet-odds-scraper** — collecte des cotes buteur NHL chez Unibet.fr avec contrôle d'acceptation et runner self-hosted.
9. **Matttgic/Cotescope** — cahier des charges d'un scanner ANJ (EV vs Pinnacle, garde-fou grosses cotes, CLV, snapshots).
10. **pradazay1-code/Sports-betting-model** — squelette Actions + SQLite committé + Pages, client Pinnacle guest, workflows daily/refresh/nightly.
11. **Risky-Scout/nba-player-props-model** — minutes → PMF ZINB pour les props NBA, snapshots T-25/close-lock, manifestes de snapshots manqués.
12. **tanamsethi31/footymodel** — props tirs/SOT foot calibrés, déclenchement sur compositions confirmées, discipline CLV vs yield.
13. **Ghantard/winator** + **HKB06/ScriptWinamax** — deux voies de collecte Winamax (JSON embarqué léger / Socket.IO complet).
14. **martineastwood/penaltyblog** + **probberechts/soccerdata** — dé-vig prêt à l'emploi et données joueurs foot (xG, minutes, tirs).
15. **aqsmith02/paper-betting-tracker** — suivi papier automatisé avec **groupe témoin aléatoire** et simulation sous H0 ; à combiner avec le ledger verrouillé de jbern1022/futbol-modelo.

---


## Avertissement général (à lire avant tout)

* **Effet « saison 2026-27 + assistants de code »** : une grande partie des dépôts NHL/NBA trouvés ont été **créés entre août et septembre 2026** (0 étoile, quelques jours d'existence, souvent un fichier `CLAUDE.md` ou une branche `claude/...`). Ils sont parfois très bien architecturés, mais **aucun n'a d'historique réel**. Leur valeur est dans l'architecture et le code réutilisable, pas dans les chiffres de performance.
* Les étoiles et dates proviennent de l'API GitHub (via `ungh.cc`) au 2 octobre 2026. « pas de licence » = aucun fichier LICENSE trouvé à la racine (donc, juridiquement, tous droits réservés : on peut s'en inspirer, pas copier).
* Les rares projets qui mesurent honnêtement leurs résultats contre le prix de clôture (CLV) **confirment le constat d'Overstreamlit** : un modèle statistique seul ne bat pas le marché ; ce qui reste, c'est la comparaison de prix (line shopping) contre une référence sharp, et l'information que le marché n'a pas encore intégrée (gardien confirmé, composition, blessures).

---

## 1. NHL : modèles de match, gardiens, xG, buteurs, props

### 1.1 Modèles de paris NHL complets (match + props)

#### Mbennett00/NHLModel
* **URL** : https://github.com/Mbennett00/NHLModel — site : https://mbennett00.github.io/NHLModel/
* **Langage** : Python (+ page HTML statique) · **★ 0** · créé le 30/09/2026, dernier push 02/10/2026 · **pas de licence**
* **Ce que ça fait** : price **buteur à tout moment (ATG)**, tirs cadrés (SOG), passes, points, moneyline, puck line, totaux, totaux d'équipe, 1re période. Pour chaque pari : projection, probabilité, cote juste américaine, prix sans marge du book, edge.
* **Données** : API NHL `api-web.nhle.com` (play-by-play + shift charts), fichiers MoneyPuck (téléchargés à la main), compositions Daily Faceoff (lignes F1-F4, unités PP1/PP2, gardien confirmé), The Odds API (mode « lean » : un seul book, Caesars, 3 crédits par appel, ~180 crédits/mois ; props non récupérées car trop chères en crédits).
* **Méthode** : Poisson bivarié pour le match ; modèles joueurs avec **shrinkage**, temps de glace (TOI), facteur PP/PK, SOG en **binomiale négative** ; **contrôle de cohérence** (somme des λ joueurs vs λ équipe) ; ajustement **but en cage vide** ajusté sur l'historique ; validation walk-forward, log loss / Brier vs baseline, CLV ; grid search des hyperparamètres sur une fenêtre puis holdout intact.
* **Automatisation** : GitHub Actions (`daily.yml`) : ~6 h ET récupération des matchs de la veille + correction des paris + backtest ; repricing à 11 h, 13 h, 15 h 30, 17 h 30, 18 h 40 ET avec les lignes Daily Faceoff, gardiens et blessures ; l'état (historique, `bets_log.csv`) est stocké dans une **release GitHub `data-latest`** ; page GitHub Pages (onglets Tonight / Players / Check / Lineups / Model), l'onglet **Check** price n'importe quelle cote dans le navigateur. Rien n'est signalé tant que gardien et composition ne sont pas confirmés.
* **Performance annoncée** : aucune réelle (dépôt de 2 jours). Le README avertit lui-même que les résultats synthétiques « ne disent rien des vrais edges ».
* **Qualité** : très bonne architecture (tests, config centralisée, documentation des hypothèses). Jeune, non éprouvé.
* **Ce qu'on peut réutiliser** : (1) le **schéma d'automatisation** (cron multiples calés sur l'annonce des gardiens, état dans une release plutôt que dans le dépôt, page statique + `data.json`) ; (2) l'**onglet « Check »** (saisir la cote Winamax/Betclic et obtenir l'edge) ; (3) la cohérence joueurs/équipe pour l'ATG ; (4) la règle « pas de signal sans gardien + ligne confirmés ».

#### cooperross399/nhl-betting-lab — ⭐ le plus instructif
* **URL** : https://github.com/cooperross399/nhl-betting-lab
* **Langage** : Python · **★ 0** · créé le 25/08/2026, push 01/10/2026 · pas de licence · ~420 fichiers, 5+ workflows (`closing-lines.yml`, `gameday-refresh.yml`, `line-movement.yml`, `historical-props-purchase.yml`…)
* **Ce que ça fait** : laboratoire « à barrières » pour props NHL (SOG, points, buts dont **ATG**, passes, arrêts gardien, tirs bloqués, mises en échec, échelles alternatives) et marchés d'équipe. Ne place jamais de pari, « n'invente jamais un prix ».
* **Données** : boxscores NHL (gratuit), cotes historiques et live de props achetées via une API de cotes (secret `NHL_ODDS_API_KEY`), 8 bookmakers.
* **Méthode** : calibration walk-forward, backtest au prix, test de **réplication** saison 2024-25 vs 2025-26, CLV contre le dernier prix avant le match, gel du premier avis du jour (jamais re-pricé).
* **Résultats rapportés (honnêtes)** : **25 911 paris distincts, ROI −0,3 % (IC 95 % −1,5 % à +1,0 %)** ; 284 493 avis pricés. Régression `résultat ~ prix_marché + (modèle − marché)` : **coefficient sur le désaccord = +0,03 [−0,04 ; +0,10]** → « quand le modèle et le marché sont en désaccord, le marché a raison ». Plus l'edge annoncé est grand, plus le ROI réel est mauvais (−18 % pour des edges de 20-30 %). Le **line shopping entre 8 books** n'a rien donné non plus sur ces props US. Seules pistes restantes selon l'auteur : **information que le marché n'a pas encore** (gardien partant confirmé, etc.).
* **Ce qu'on peut réutiliser** : le document `docs/why_the_model_has_no_edge.md` comme **protocole de validation** (régression sur le désaccord, ROI par tranche d'edge, réplication inter-saisons, « un pari = un pari au meilleur prix », pas un pari par book) ; `what_we_can_and_cannot_claim.md` régénéré à chaque run ; publication de la carte du jour en commentaire d'issue GitHub (notification e-mail gratuite).

#### MJACode/betting-model (« NHL market lab »)
* **URL** : https://github.com/MJACode/betting-model (doc : `docs/nhl_market_lab.md`, `docs/clv.md`, `docs/best_line.md`)
* **Langage** : Python (Supabase/Postgres, Procfile, dashboard) · **★ 0** · créé le 04/04/2026, push 02/10/2026 · pas de licence · >8 000 fichiers, multi-sports (MLB, NFL, NHL, UFC…)
* **Ce que ça fait** : système de picks multi-sports avec suivi papier, CLV, meilleure ligne ; le « NHL market lab » backteste moneyline, totaux et puck line **aux vrais prix d'ouverture**.
* **Données** : cotes historiques NHL gratuites de l'archive **Sportsbook Reviews Online (SBR)** (25 659 lignes, 5 135 matchs 2018-19 → nov. 2022, ouverture + clôture), The Odds API (7 books) pour le live.
* **Résultats rapportés** : le modèle moneyline (22 features, dont groupe gardien) a une log loss **0,702 vs 0,656 pour le marché à l'ouverture** ; ROI **−3,4 % à −6 %** selon le seuil d'edge ; même en ajoutant la proba du marché en feature, toujours négatif. Les stratégies naïves « toujours le favori » ≈ −0,03 %. Les PR #804/#805/#860 annoncent ensuite des modèles props (arrêts, SOG, passes) à +5,7 % à +10,9 % « au meilleur prix sur trois saisons » → **à prendre avec beaucoup de prudence** (meilleur prix ex post = biais optimiste, cf. cooperross399).
* **Ce qu'on peut réutiliser** : la **formule CLV** documentée (dé-vig multiplicatif des deux côtés, 3 voies pour la NHL régulation ; marchés à un seul côté type buteur exclus du CLV publié) ; l'idée de l'archive SBR pour backtester gratuitement ; le diagnostic « bug : un marché récupéré sur un seul book » (`best_line.md`).

#### CarsonBillig/nhl-model
* **URL** : https://github.com/CarsonBillig/nhl-model · Python (scripts `.bat` Windows) · ★ 0 · dernier commit 02/10/2026 · pas de licence
* **Ce que ça fait** : picks NHL quotidiens selon la méthode de **Rob Pizzola** : ratings d'équipe (xG 5v5 pour/contre par 60, part de tentatives, PP/PK, finition fortement rétrécie) → **modèle gardien** (GSAx par xG faced, rétréci vers la moyenne) → ajustements du jour (gardien partant, glace, back-to-back) → prix (régression de Poisson + **étape « cage vide »** mesurée sur 7 440 matchs : équipe +1 → 32 % de but en cage vide, +2 → 66 %).
* **Données** : API NHL (play-by-play depuis 2020-21, ~8 000 matchs), modèle xG maison entraîné uniquement sur les saisons antérieures (pas de fuite), cotes ESPN/DraftKings.
* **Résultats rapportés** : backtest 2024-26, value bets (edge ≥ 6 points) **+2,6 % à +5 % à la cote d'ouverture, battent la clôture ~70 % du temps, mais perdent à la cote de clôture** → conclusion de l'auteur : parier tôt le matin. Cohérent avec l'idée que l'edge est dans la **vitesse** (info gardien) plus que dans le modèle.
* **Ce qu'on peut réutiliser** : fichier `goalie_overrides.csv` (surcharger le gardien confirmé), ledger « logué avant le match, corrigé après », colonne `valueBeatClose`.

#### flagk/nhl-tracker
* **URL** : https://github.com/flagk/nhl-tracker — site : https://flagk.github.io/nhl-tracker/
* **Langage** : Python · **★ 0** · créé le 03/02/2026, push 02/10/2026 · pas de licence · workflows `daily.yml`, `odds-close.yml`, `goals.yml`, `backfill.yml`, `ci.yml`
* **Ce que ça fait** : proba de victoire par match vs prix sans marge ; « la plupart des jours, la réponse honnête est : pas de pari ». Le README est **réécrit automatiquement** entre balises `<!-- PICKS:START -->`/`END` (ex. 01/10/2026 : 8 matchs, 0 pari recommandé). PR #26 : props SOG (binomiale négative, taux récent rétréci, tirs concédés par l'adversaire, TOI, repos) en **paper trading uniquement**.
* **Ce qu'on peut réutiliser** : **README comme tableau de bord** ; pages « My bets » (stockées dans le navigateur) et « Fake bets » (paris fictifs sur chaque match pour mesurer le modèle) ; export CSV/Power BI ; publication « public-safe » (pas de noms de books ni de prix par book) ; champ « prix dans votre appli » donnant la **pire cote encore jouable**.

#### renenunezg/momentumnhl
* **URL** : https://github.com/renenunezg/momentumnhl · Python · **★ 0** · créé le 14/09/2026, push 01/10/2026 · **MIT** · workflows `daily.yml`, `ci.yml`
* **Méthode** : portage Python d'un modèle Google Sheets : fenêtres des 25 derniers matchs domicile/extérieur par situation (5v5, 5v4, 4v5) à partir des fichiers MoneyPuck, carte linéaire « qualité de tir → buts/60 », forces attaque/défense en ratio de la moyenne, Poisson. Seuils : moneyline ≥ 13 points d'edge, totaux ≥ 1 but d'écart. Décisions **figées à la première publication**, mises plates.
* **Données/cotes** : MoneyPuck (CSV ~126 Mo), flux « partenaire » de la NHL (DraftKings US / FanDuel Canada) avec règles de fraîcheur des cotes (horodatage < 24 h, ou listing DraftKings corroboré < 15 min).
* **Ce qu'on peut réutiliser** : règles de **fraîcheur des cotes** et de corroboration ; protocole de sélection de modèle séparant saisons de calibration / sélection / test ; avertissement que MoneyPuck révise rétroactivement son xG historique (fuite possible dans les backtests).

#### kylewish19/wshl-x-nhl-model
* **URL** : https://github.com/kylewish19/wshl-x-nhl-model · Python · **★ 0** · créé le 29/09/2026 · pas de licence
* **Marchés** : ML, puck line, total, **ATG**, passe décisive, arrêts O/U, 1+ point, 2+ points.
* **Méthode** : régresseurs **gradient boosting Poisson** (buts équipe, buts/passes/points joueur) + couche **binomiale négative** pour la surdispersion (P(1+), P(2+)) ; calibration isotonique ; Monte Carlo pour ML/PL/total ; validation strictement chronologique. Données NHL API + MoneyPuck.
* **Idée intéressante** : **verrouiller une « Top 10 Probability Card » AVANT de regarder les cotes**, puis appliquer une « Playable Price Gate » séparée (implied prob, edge, EV) → évite que le modèle soit contaminé par le prix ; journal `logs/LESSONS.md`.

#### shawnmcgee/degenpredicts
* **URL** : https://github.com/shawnmcgee/degenpredicts · Python · **★ 1** · créé le 04/09/2026, push 02/10/2026 · pas de licence
* **Ce que ça fait** : prédictions spread/total pour NCAAF, NFL, EPL, **NHL** (2× par jour, gardiens partants), NBA (rapport de blessures), NCAAB. « Actions = ordonnanceur, le dépôt = la base de données, Pages = le site. »
* **Architecture réutilisable** : un dossier par sport (`docs/nhl/`, `docs/nba/`…) + page d'accueil « chooser » générée qui ne fait que lire ce que chaque pipeline a publié ; workflows `*-predict` / `*-grade` / `*-train` (réentraînement le mardi) ; **`odds-quota.yml`** : vérifie chaque jour les crédits restants de The Odds API et ouvre une issue qui vous mentionne avant épuisement. GLM de Poisson « market-offset » pour puck line/total (PR #19).

#### Autres modèles NHL de match (plus anciens ou plus simples)
* **gmalbert/hockey-predictions** (« Oracle on Ice ») — https://github.com/gmalbert/hockey-predictions · Python/Streamlit · ★ 4 · créé 02/2026, push 01/10/2026 · app Streamlit : matchs du jour + cotes ESPN (`site.api.espn.com`), « Value Finder » sur un xG mélangé, props (taux par 60, régression du % de tir), comparaison de gardiens (GSAA, HD SV%), blessures, mouvements de ligne, backtest. Bonne liste d'onglets à copier pour un tableau de bord Streamlit.
* **kirbypuckett031460-web/nhl** — https://github.com/kirbypuckett031460-web/nhl · ★ 0 · créé 11/2025, push 01/10/2026 · modèle Over/Under NHL, deux apps Streamlit (publique/privée), workflow `run-nhl-model.yml`, publication Twitter/Discord optionnelle.
* **justin-m-5/my-puckzone-model** — https://github.com/justin-m-5/my-puckzone-model · ★ 1 · 2026 · scikit-learn + Supabase, Poisson bivarié, données 2017-18 → 2025-26, benchmark vs marché.
* **gschwaeb/NHL_Game_Prediction** — https://github.com/gschwaeb/NHL_Game_Prediction · ★ 25 · inactif depuis 07/2021 · classique « modèle de victoire + stratégie de paris » (pédagogique).
* **HarryShomer/NHL-Prediction-Model** — https://github.com/HarryShomer/NHL-Prediction-Model · ★ 16 · inactif depuis 2019 · proba de victoire par match (référence historique de la communauté hockey analytics).
* **pbulsink/HockeyModel** — https://github.com/pbulsink/HockeyModel · R · ★ 6 · **GPL** · push 01/10/2026 · package R qui prédit vainqueurs de matchs, points de fin de saison et probabilités de playoffs ; graphiques régénérés et postés automatiquement (Bluesky), site reconstruit via workflow Netlify.

### 1.2 Buteur à tout moment (ATG) et props NHL (SOG, arrêts, points)

#### jaredkimble-coder/nhl-atg-lamp-lab — tableau ATG automatisé
* **URL** : https://github.com/jaredkimble-coder/nhl-atg-lamp-lab · Python + HTML · **★ 0** · créé le 29/09/2026, push 02/10/2026 (~320 commits, en majorité automatiques) · pas de licence
* **Ce que ça fait** : modèle ATG NHL ; **cotes live rafraîchies toutes les 30 min par GitHub Actions** (`cron: */30 * * * *`), page servie par GitHub Pages.
* **Architecture** : séparation nette (1) `players_base.json` = sortie du modèle saisonnier (**taux de Poisson + multiplicateurs de matchup**), reconstruite « par n8n » quelques fois par jour ; `lineups.json` (unités PP1 issues de DailyFaceOff) ; (2) `refresh.py` qui ne recalcule PAS le modèle : il récupère le calendrier du jour, les cotes ATG DraftKings et les totaux via **Optic Odds** (API payante), recalcule edge/EV, écarte les joueurs sans cote, **exclut les matchs commencés** (« les prix in-play contre un modèle pré-match produisent de faux edges ») et injecte les données dans `template.html` (`__SEED_DATA_JSON__`). Filtre « adversaire en back-to-back ». Fichiers `graded.json` / `track_record.json` pour l'historique.
* **Ce qu'on peut réutiliser** : le **découplage modèle lent / cotes rapides** (exactement ce qu'il faut pour Overstreamlit : modèle ATG recalculé 2×/jour, cotes FR rafraîchies toutes les 15-30 min) ; la fonction `name_match()` (normalisation accents, surnoms Matt/Matthew, Nick/Nicholas, comparaison restreinte à une équipe) — indispensable pour rapprocher les noms Winamax/Betclic des noms NHL.

#### Acethemvp82/nhl-anytime-goal-model
* **URL** : https://github.com/Acethemvp82/nhl-anytime-goal-model · Python/Streamlit · ★ 0 · créé le 29/09/2026 · pas de licence
* **Méthode** : **score heuristique**, pas une probabilité calibrée : « Goal Threat » (buts/match + tirs/match plafonnés), « Goal Match » (buts encaissés/match de l'adversaire), « Goalie Match » (SV%/GAA du gardien adverse), pondérés 70/30. Données uniquement `api-web.nhle.com` (avec gestion des 429).
* **Verdict** : utile seulement comme exemple d'appels à l'API NHL ; le score n'est pas une probabilité → inutilisable tel quel pour calculer un EV.

#### ChungChainz/nhl-anytime-goal-comparison
* **URL** : https://github.com/ChungChainz/nhl-anytime-goal-comparison · Python/Streamlit · ★ 0 · créé le 30/09/2026 · pas de licence
* **Ce que ça fait** : comparateur ATG **DraftKings vs FanDuel** du jour via The Odds API (`/v4`), conversion américaine → proba implicite, table d'alias de noms (Joseph/Joe Veleno, Zachary/Zack Bolduc, Egor/Yegor Chinakhov…). Pas de modèle.
* **Réutilisable** : la table d'alias ; le principe « comparer deux books entre eux » sur un marché à un seul côté (l'ATG n'a pas de « non » coté chez la plupart des books → le dé-vig doit se faire **sur l'ensemble du marché** ou contre une référence sharp).

#### sheridanmi/nhl-sog-predictor (« SOG Edge Finder »)
* **URL** : https://github.com/sheridanmi/nhl-sog-predictor · JavaScript (Node + React/Vite) · ★ 0 · créé 02/2026, push 29/09/2026 · pas de licence · workflow `daily-deploy.yml`
* **Méthode** : moyenne pondérée **ad hoc** (5 derniers matchs 25 %, saison 20 %, 10 derniers 15 %, tirs concédés adversaire 10 %, tendance TOI 8 %, temps de PP 7 %, dom/ext 5 %, SV% gardien 4 %, B2B 3 %, total Vegas 3 %) puis **10 000 simulations Monte Carlo** par joueur ; comparaison aux lignes SOG de The Odds API (offre gratuite 500 req/mois, ~10-15 req/jour).
* **Verdict** : poids choisis à la main, aucune validation → pédagogique. Mais la **liste des facteurs** est un bon point de départ pour un modèle SOG.

#### rysohn/nhl-sog-model
* **URL** : https://github.com/rysohn/nhl-sog-model — site : https://rysohn.github.io/nhl-sog-model/ · R (Rmd, `.rds`) + JS · ★ 0 · créé 01/2026, push 02/10/2026 · workflow `daily_update.yml`
* **Ce que ça fait** : modèle quotidien des **tirs d'équipe** par match, edges = modèle − lignes des books ; site mis à jour toutes les deux heures. Pas encore de suivi cumulatif (prévu).

> Voir aussi plus haut : **Mbennett00/NHLModel** (ATG/SOG/points/passes), **cooperross399/nhl-betting-lab** (toutes les props avec résultats honnêtes : aucune edge), **kylewish19/wshl-x-nhl-model** (ATG, arrêts, points), **MJACode/betting-model** (arrêts/SOG/passes, résultats à vérifier), **flagk/nhl-tracker** (SOG en paper trading).

### 1.3 Briques de données et modèles xG NHL

| Projet | URL | Lang. | ★ | Dernière activité | Licence | Intérêt pour nous |
|---|---|---|---|---|---|---|
| **Zmalski/NHL-API-Reference** | https://github.com/Zmalski/NHL-API-Reference | doc | 608 | 11/2025 | MIT | **Référence non officielle des endpoints** `api-web.nhle.com` et `api.nhle.com/stats/rest` (calendrier, boxscore, play-by-play, game logs, shift charts). À lire avant d'écrire le moindre scraper NHL. |
| **coreyjs/nhl-api-py** (`nhl-api-py`) | https://github.com/coreyjs/nhl-api-py | Python | 152 | 09/2026 | Apache-2.0 | Client Python maintenu (« 2026/2027 updated »), y compris les stats NHL EDGE. Bon remplaçant d'appels `requests` maison. |
| **HarryShomer/Hockey-Scraper** | https://github.com/HarryShomer/Hockey-Scraper | Python | 157 | 06/2024 | GPL-3.0 | Scraper historique play-by-play + shifts (HTML/JSON NHL). Référence, mais peu actif depuis 2024 → vérifier la compatibilité avec la nouvelle API. |
| **TopDownHockey/TopDownHockey_Scraper** | https://github.com/TopDownHockey/TopDownHockey_Scraper | Python | 34 | 04/2026 | (licence PyPA par défaut) | `full_scrape(game_ids, shift=True)` → play-by-play avec joueurs sur la glace ; aussi Elite Prospects. Utile pour TOI par situation (PP). |
| **JNoel71/NHL-Expected-Goals-xG-Model** | https://github.com/JNoel71/NHL-Expected-Goals-xG-Model | Python | 7 | 01/2025 | GPL-3.0 | xG LightGBM avec **ajustement de biais d'aréna** (méthodes Krzywicki et Schuckers-Curro) ; features documentées (côté fort, angle, distance, type de tir, force). |
| **HarryShomer/xG-Model** | https://github.com/HarryShomer/xG-Model | Python | 21 | 2018 | — | Modèle xG historique de référence (pédagogique). |
| **nat544/nhl-xg-model** | https://github.com/nat544/nhl-xg-model | Python | 0 | 09/2026 | — | xG XGBoost vs logistique depuis l'API NHL publique + **simulation Monte Carlo** (chaque tir = Bernoulli(xG)) ; une variante `nhl-xg-model-player-analysis` ajoute rebonds/rush et **finition par joueur (buts − xG)**, utile pour l'ATG. |
| **saiemgilani/Goalie_Model_NHL** | https://github.com/saiemgilani/Goalie_Model_NHL | Python/SQL | 1 | 2020 | — | Modèle empirique d'évaluation des gardiens (inspiration pour un facteur gardien). |

**À retenir pour un modèle ATG NHL** (synthèse des dépôts ci-dessus) : λ_buts_joueur = (tirs/60 ou ixG/60 rétréci vers la moyenne de poste) × TOI projeté (5v5 + PP séparés, unité PP1 prioritaire) × facteur défense adverse × facteur gardien adverse (GSAx rétréci) × ajustement cage vide ; P(ATG) = 1 − e^(−λ) (ou binomiale négative) ; **contrôle de cohérence** Σλ_joueurs ≈ λ_équipe issu du marché des totaux d'équipe ; et surtout **ne publier qu'après confirmation du gardien et des lignes**.

---

## 2. NBA : props joueurs, minutes, blessures, modèles de match

### 2.1 Modèles de props NBA comparés aux lignes des books

#### Risky-Scout/nba-player-props-model et Risky-Scout/nba-prop-quant — ⭐ les plus sérieux côté NBA
* **URL** : https://github.com/Risky-Scout/nba-player-props-model · https://github.com/Risky-Scout/nba-prop-quant · Python · `nba-player-props-model` ★ 1, dernier commit 08/2026 ; `nba-prop-quant` ★ 0, dernier commit 30/09/2026 · pas de licence
* **Ce que ça fait** : produit des **PMF discrètes complètes** (distribution de probabilité de chaque valeur : 0, 1, 2… rebonds) par prop, les convertit en probabilités over/under justes, compare aux prix du marché ; publie chaque jour des snapshots **« current live », « T-25 min » et « close lock »** par match (pour mesurer le CLV), des rapports d'impact composition/blessures, et un export pour Wizard of Odds.
* **Méthode (`nba-prop-quant`, gelé le 18/08/2026)** : modèles de **minutes** walk-forward, puis moyennes par stat (XGBoost / ensembles), marges **ZINB** (binomiale négative à inflation de zéros, préservant la moyenne) pour PTS/REB/AST/STL/BLK/3PM, dépendance pour les combos (R+A avec λ = 0,85), calibration par prop ; **aucun seuil de pari automatique**.
* **Résultats rapportés (honnêtes)** : « approximativement compétitif avec le marché dé-vigé » sur le scoring propre (Brier, log loss) ; le rapport de variance indique **`model_trails_market=True`** → « ne pas revendiquer de supériorité sur le marché ». Règle dure : **ne jamais fabriquer de snapshot pré-match après le coup d'envoi** (les snapshots manqués sont documentés, pas reconstitués).
* **Ce qu'on peut réutiliser** : l'approche **minutes → taux par minute → PMF** ; les trois snapshots T-25 / close-lock pour CLV ; les manifestes « snapshot manqué / échoué » (évite les faux succès silencieux d'un cron) ; une grille de statut de production générée dans le README.

#### pradazay1-code/Sports-betting-model (« Pradapicks »)
* **URL** : https://github.com/pradazay1-code/Sports-betting-model · Python · **★ 0** · créé le 28/04/2026, push 02/10/2026 · pas de licence
* **Ce que ça fait** : modèle + tableau de bord **100 % gratuit** pour props NBA/MLB/NHL/NFL/foot ; tout tourne sur **GitHub Actions**, affichage **GitHub Pages**, base **SQLite committée** dans le dépôt (`data/pradapicks.db`), modèles `models/*.joblib` committés.
* **Données** : stats.nba.com, MLB Stats API, `api-web.nhle.com`, API publique ESPN ; lignes de props **PrizePicks, DraftKings, FanDuel, Bovada** et **Pinnacle via l'API « guest » Arcadia** (clé publique du site web, endpoints `/0.1/sports/{id}/matchups` et `/0.1/matchups/{id}/markets/related/straight` ; le code passe 487 (NBA), 246 (MLB), 1456 (NHL) à `/sports/{id}/matchups` alors que ce sont des IDs de **ligue** Pinnacle — l'endpoint par ligue `/0.1/leagues/{id}/matchups` est probablement le bon, à vérifier) ; blessures ESPN, météo Open-Meteo.
* **Méthode** : un LightGBM par (sport, marché) sur fenêtres glissantes (5/10/25 matchs, concédé par l'adversaire, repos, dom/ext) → P(over) via Poisson (comptages) ou Normale → **calibrateur isotonique** → dé-vig multiplicatif, Kelly, note 0-100 ; parlays avec **copule gaussienne** pour la corrélation intra-match ; « grader » de pari saisi par l'utilisateur (note A+ → F).
* **Workflows** : `daily-picks.yml` (09 h ET), `refresh-odds.yml` (toutes les 2 h pendant le slate), `nightly.yml` (04 h ET : correction + **réentraînement quotidien**), `bootstrap.yml` (backfill 45 jours), `pages.yml`.
* **Limites** : le code Pinnacle ne récupère que les lignes de match (les props Pinnacle sont des « specials » au schéma différent, laissé en TODO) ; 45 jours d'historique = très court ; aucune mesure CLV.
* **Ce qu'on peut réutiliser** : **le squelette complet Actions + SQLite committé + Pages** (zéro serveur) ; le client Pinnacle guest ; l'idée de pondérer Pinnacle plus fortement dans le prix « juste » consensus.

#### ethanllawrence/nba-props-projection (« PRAjections »)
* **URL** : https://github.com/ethanllawrence/nba-props-projection · Python · ★ 0 · dernier commit 02/10/2026 · pas de licence
* **Ce que ça fait** : projections points/rebonds/passes/PRA, site **GitHub Pages** (table triable colorée selon l'écart projection/ligne), pipeline SQLite, ingestion ESPN ; `daily.yml` 2×/jour qui committe le JSON ; page **résultats** (MAE par stat, bilan des edges ≥ 6 % vs 52,4 % de seuil à −110) depuis le 22/09/2026 ; **heartbeat `status.json` + `stale.js`** qui affiche un avertissement si les données sont périmées ; correspondance de noms ESPN ↔ books (exact → alias → initiale + nom, avec warnings).
* **Ce qu'on peut réutiliser** : le **heartbeat anti-données périmées** sur la page publique, et l'auto-évaluation quotidienne (MAE).

#### pranavcheedalla/propsim
* **URL** : https://github.com/pranavcheedalla/propsim · C++ (pybind11) + Python + React · ★ 0 · créé le 19/09/2026 · pas de licence
* **Ce que ça fait** : moteur **Monte Carlo en C++**, features Python (moyennes glissantes, ajustement matchup, **signal de disponibilité** = tendance des minutes en baisse), backend FastAPI + SQLite, cotes et blessures via l'**API publique ESPN**, dashboard React, bet tracker, backtest 2023-24 → 2025-26 avec breakdown par saison. Note honnête : « les cotes de props joueurs ne sont disponibles dans aucune source gratuite » → saisie manuelle.

#### akhil-aswin/Player_Data_Projection
* **URL** : https://github.com/akhil-aswin/Player_Data_Projection · Python (FastAPI + SPA) · ★ 0 · créé 07/2026, push 16/09/2026
* **Ce que ça fait** : récupère historique joueur + lignes props books et **PrizePicks** (The Odds API), **dé-vig**, projette avec contexte adversaire, affiche l'edge ; tracker SQLite qui alimente une **correction de biais auto-calibrée** dans la projection. Démarré en CLI NBA, la partie MLB est la plus développée.

#### KamranSHussain/NBA-Propositions-Forecasting-App
* **URL** : https://github.com/KamranSHussain/NBA-Propositions-Forecasting-App · Python (PyTorch + Streamlit) · ★ 0 · 03→05/2026 · **MIT**
* **Méthode** : **transformer de régression quantile** (pinball loss, q10/q50/q90) pour les points ; ingestion live des lignes FanDuel ; backtest sur cotes historiques ; onglets « Predict Matchup / Betting Lines / Test Stats ». Intéressant pour des **intervalles** plutôt qu'une moyenne ; à comparer à une simple binomiale négative avant d'adopter la complexité.

#### Rithvik09/NBA-Player-Props-Analyzer
* **URL** : https://github.com/Rithvik09/NBA-Player-Props-Analyzer · Python/Flask · ★ 0 · créé 12/2024, push 02/10/2026 · pas de licence
* **Méthode** : 408 features, XGBoost par prop mélangé à une baseline (forme récente + moyenne saison), sources NBA API, FantasyPros, ESPN, Basketball-Reference, The Odds API ; **suivi des mouvements de lignes** en thread de fond, bankroll/Kelly. Risque de sur-ajustement élevé (408 features).

#### bendominguez0111/nba-models
* **URL** : https://github.com/bendominguez0111/nba-models · Python · **★ 20** · inactif depuis 03/2023 · pas de licence
* **Ce que ça fait** : modèle de **paniers à 3 points (3PM)** par simulation, cotes via The Odds API, utilitaires `betting_math.py`. Ancien mais propre ; bonne base pour un modèle 3PM (Binomiale tentatives × réussite).

#### Petits projets pédagogiques (moyennes glissantes, sans validation)
* **parlayparlor/nba-prop-prediction-model** — https://github.com/parlayparlor/nba-prop-prediction-model · MIT · moyennes sur N derniers matchs via `nba_api` (PTS/REB/AST/combos). Utile uniquement comme exemple `nba_api`.
* **mmyoung77/betModel** — https://github.com/mmyoung77/betModel · ★ 2 · 2024 · notebooks props NBA.
* **stanleychenusa/nba_pts_pred_model** — https://github.com/stanleychenusa/nba_pts_pred_model · MIT · 09/2026 · régression linéaire poolée (minutes, usage, DRtg adverse, dom/ext, **nombre de coéquipiers blessés**).

### 2.2 Minutes, blessures, données

| Projet | URL | ★ / activité | Licence | Utilité |
|---|---|---|---|---|
| **swar/nba_api** | https://github.com/swar/nba_api | **3 792** · push 08/2026 | MIT | Client de référence de stats.nba.com (game logs, boxscores avancés, matchups). Attention : stats.nba.com bloque souvent les IP de datacenters (GitHub Actions) → prévoir ESPN en secours, comme plusieurs projets ci-dessus. |
| **mxufc29/nbainjuries** (`pip install nbainjuries`) | https://github.com/mxufc29/nbainjuries | ★ 45 · v1.1.1 (02/2026) | MIT | Extrait les **rapports de blessures officiels NBA (PDF)** historiques et temps réel en JSON/DataFrame. Rappel utile : statut publié avant 17 h locales la veille (13 h le jour même pour un back-to-back) → fixe les heures de cron. |
| **UBC-MDS/NBA-Minutes-Predictor** | https://github.com/UBC-MDS/NBA-Minutes-Predictor | ancien (projet universitaire) | — | LightGBM de **minutes** : MSE 38,2 / R² 0,65 vs 50,2 / 0,55 pour la moyenne des 5 derniers matchs. Bon ordre de grandeur de ce qu'on peut gagner sur la baseline. |
| **shermanash/DFSharp** | https://github.com/shermanash/DFSharp | ancien | — | Pipeline DFS : modèle réentraîné à 6 h, **projections recalculées toutes les 10 min de midi à 23 h** à partir des depth charts, rapports de blessures et tweets ; ajustement manuel des minutes dans l'interface. Le principe « re-projection événementielle » reste valable. |

### 2.3 Modèle de match NBA de référence

#### kyleskom/NBA-Machine-Learning-Sports-Betting
* **URL** : https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting · Python · **★ 1 729, 573 forks** · dernier commit 01/2026 (push 09/2026) · pas de fichier licence trouvé
* **Ce que ça fait** : vainqueur et total (O/U) NBA avec XGBoost et réseau de neurones, stats d'équipe depuis 2007-08, cotes historiques **SBR**, EV et Kelly, app Flask.
* **Regard critique** : projet le plus populaire du domaine, mais le README ne montre aucun suivi CLV ni résultat vérifiable ; une bonne « précision » de vainqueur ne dit rien d'un edge (le favori du marché gagne déjà souvent). À utiliser comme **pipeline de données** (SBR + stats d'équipe), pas comme preuve d'edge.

---

## 3. Football (buteurs, tirs) et tennis (aces, jeux)

> **Constat** : malgré des recherches ciblées (« anytime goalscorer model github », Understat/FBref + cotes), **aucun dépôt open source sérieux de modèle « buteur à tout moment » en football n'a été trouvé**. Les briques existent (xG joueur, minutes, compositions), et deux projets voisins (tirs/tirs cadrés en foot, marqueurs d'essai au rugby à XIII) donnent la méthode à transposer.

### 3.1 Football : props joueurs

#### tanamsethi31/footymodel ⭐
* **URL** : https://github.com/tanamsethi31/footymodel — dashboard : https://footymodel.vercel.app/ · Python · ★ 3 · dernier commit 02/10/2026 · « all rights reserved » (pas de licence libre)
* **Ce que ça fait** : recherche « existe-t-il un ROI positif contre la cote de clôture, et où exactement ? » ; Dixon-Coles + **modèle sensible aux compositions** ; props **tirs / tirs cadrés (SOT)** par joueur ; paper trading live.
* **Données** : football-data.co.uk (résultats + cotes), Understat (xG + effectifs), FBref (SOT joueur), **WhoScored (tirs/SOT, minutes réelles)**, API-Football (source live principale), replis RapidAPI / SofaScore (navigateur) / Apify.
* **Résultats rapportés (honnêtes)** : O/U et 1X2 : **pas d'edge** (CLV ≈ −0,2 %, yield ≈ −7 %) ; handicap asiatique : meilleure config +2,05 % de yield mais **CLV −1,52 %** → « piège du yield positif / CLV négatif » ; modèle sensible aux compositions : meilleure précision des totaux (t = 3,04 sur le big 5) ; SOT joueurs **bien calibrés (écarts ≤ ±0,03)** mais **pas de backtest de rentabilité possible faute d'archive de cotes de props** → paper trading seulement.
* **Point clé d'architecture** : le pipeline live déclenche les recommandations **quand les compositions sont confirmées (~20-40 min avant le coup d'envoi) et avant que les books ne re-pricent** → la fenêtre d'edge est temporelle, pas statistique. Un seul poll partagé entre moteur buts et moteur props (`run_all.py`) pour économiser les quotas.
* **Réutilisable** : la méthode de calibration SOT, le déclenchement sur composition confirmée, la discipline « yield sans CLV = bruit ».

#### jbern1022/futbol-modelo
* **URL** : https://github.com/jbern1022/futbol-modelo — site : futbol.josephbernal.com · Python (FastAPI + Next.js) · ★ 0 · dernier commit 01/10/2026 · **MIT**
* **Ce que ça fait** : système de prédiction calibré (MLS en priorité avec **props joueurs complets**, PL, Serie A, Liga, + NFL/NBA partiels) ; props en **LightGBM objectif Poisson** (tirs cadrés, **buts joueur**…) ; chaque prédiction est **verrouillée dans un registre append-only avant le match** et corrigée automatiquement ; produit final = courbe de calibration de fin de saison.
* **Infra** : k3s auto-hébergé, Postgres, CronJobs (ingestion nocturne FBref/Understat/API-Football, génération des slates, correction/annulation) ; assistant Q&A local (Ollama) qui n'écrit jamais son propre SQL.
* **Réutilisable** : le **ledger append-only verrouillé avant le coup d'envoi** (preuve d'absence de triche a posteriori) ; LightGBM-Poisson pour les comptages joueurs.

#### Jejeh040/marqueurs-xiii — modèle de buteur (essais) transposable ⭐
* **URL** : https://github.com/Jejeh040/marqueurs-xiii — rapport : https://jejeh040.github.io/marqueurs-xiii/ · Python · ★ 0 · push 30/09/2026 · **MIT** · projet **français**
* **Ce que ça fait** : pour chaque joueur des matchs NRL / Super League (Catalans Dragons compris), proba de **marquer un essai**, comparée à la **cote Unibet** (API publique Kambi, sans clé), rapport HTML publié sur GitHub Pages (branche `gh-pages` réécrite en un seul commit pour ne pas gonfler le dépôt), tâche Windows à 8 h et 20 h.
* **Méthode (3 étages, chacun mesuré)** : (1) essais de l'équipe par Poisson attaque/défense pondéré dans le temps (demi-vie 400 j) — **mais quand le book cote le total d'essais de l'équipe, c'est la valeur du marché qui est retenue** ; le modèle ne fait que **répartir** ces essais entre joueurs ; (2) part du joueur = taux d'essais **par minute du poste** × **temps de jeu attendu** × coefficient individuel régularisé vers 1 ; (3) faiblesse défensive adverse par poste/côté → **mesurée sans effet, désactivée**. Probabilités conditionnées à l'entrée en jeu (règle de règlement : remboursé si le joueur ne joue pas).
* **Mesures (honnêtes)** : 33 304 prédictions hors échantillon : log loss 0,446 vs 0,496 (moyenne simple), Brier 0,141 vs 0,158, bonne calibration jusqu'à 45 % ; optimisme au-dessus de 50 % → **garde-fou : aucun conseil au-dessus de 50 %**. « C'est le volume de données qui a fait le travail, pas le réglage fin. » **Marge du bookmaker sur ce marché : 16 à 55 % selon le match** (3 à 5 fois un 1X2) → « partir du principe que c'est perdant jusqu'à preuve du contraire » ; aucun backtest contre les cotes possible (pas d'archive gratuite) ; verdict « désaccord » quand modèle et marché divergent sur le total du match (« c'est presque toujours l'outil qui a tort »).
* **Réutilisable (directement pour l'ATG NHL et le buteur foot)** : **ancrer le λ d'équipe sur le marché (total d'équipe / handicap) et ne modéliser que la répartition entre joueurs** — c'est la meilleure idée de tout ce panorama pour les buteurs ; dé-vig pondéré par le temps de jeu attendu (gain mesuré) ; rapport du marché « toutes les cotes buteur du moment » (`cotes.html`) ; mesure explicite de la marge du marché buteur.

#### Briques de données football
| Projet | URL | ★ | Activité | Licence | Utilité |
|---|---|---|---|---|---|
| **probberechts/soccerdata** | https://github.com/probberechts/soccerdata | **2,1k** | 08/2026 | Apache-2.0 (`LICENSE.rst`) | Scrapers unifiés **FBref, Understat, WhoScored, Sofascore, ESPN, ClubElo, Football-Data.co.uk, SoFIFA** → xG/xA joueur, minutes, tirs : la base d'un modèle buteur. |
| **ML-KULeuven/soccer_xg** | https://github.com/ML-KULeuven/soccer_xg | 260 | 04/2021 | Apache-2.0 | Package d'entraînement/analyse de modèles xG (référence académique). |
| **martineastwood/penaltyblog** | voir §4.3 | 228 | 10/2026 | MIT | Dixon-Coles, dé-vig, scrapers Understat. |
| **IceCool30/match-prediction-engine** | https://github.com/IceCool30/match-prediction-engine | 0 | 09/2026 | — | « Skill » d'agent IA multi-sports (Poisson/Dixon-Coles, « buteur » mentionné) : **marketing, aucune validation** — à éviter. |

### 3.2 Tennis : aces, jeux

#### dbabsy/tennis-props ⭐
* **URL** : https://github.com/dbabsy/tennis-props · Python (bibliothèque standard uniquement) · ★ 0 · dernier commit 02/10/2026 · pas de licence
* **Méthode** : taux service/retour ajustés adversaire et **surface**, propagés point → jeu → tie-break → set → match ; un seul moteur pour vainqueur, **total de jeux**, scores exacts, handicaps, et volume de service pour les props **aces / doubles fautes** ; page **live** (même propagation depuis le score courant, états précalculés en ~1 Ko).
* **Mesures walk-forward** : ATP 2025 log loss 0,623, MAE jeux 5,54, MAE aces 2,83 ; corriger la surface a beaucoup plus amélioré les props aces (3,06 → 2,83) que le vainqueur. **Contre la clôture : 0,028-0,033 de log loss derrière Pinnacle/Bet365** (n ≈ 1 700-1 930 par cellule) — « un modèle public qui battrait la clôture serait suspect ».

#### JChan23/Tennis-Most-Aces — dé-vig d'un marché à un seul côté ⭐ (idée clé pour l'ATG)
* **URL** : https://github.com/JChan23/Tennis-Most-Aces · Python · ★ 0 · 09/2026 · pas de licence
* **Ce que ça fait** : P(A fait plus d'aces que B) à partir des **échelles « N+ aces »** des books (Pinnacle, Bet365) et du marché total de jeux ; meilleur des 8 marchés modélisés par l'auteur dans une compétition de marchés prédictifs pendant l'US Open 2026 (13e mondial).
* **Méthode** : les échelles « N+ » n'ont pas de côté « moins » → on ne peut pas dé-viger en normalisant à 1. On ajuste `1/cote_i = c · P(X ≥ N_i)` avec X ~ **binomiale négative**, en laissant la marge `c` libre (intercept en log) : **seuls les rapports entre échelons comptent, et ils sont sans marge**. Moindres carrés pondérés en log ; cotes plafonds (26,00) écartées ; analyse de l'« étendue » (span) nécessaire pour estimer `c` ; `c` ajusté varie de 0,99 à 1,20 selon l'échelle (imposer une marge commune biaise le résultat).
* **Réutilisable** : **exactement la technique pour dé-viger les marchés buteur « 1+ / 2+ / 3+ buts » ou « 1+ / 2+ points » des books FR**, et pour extraire un λ « marché » par joueur à comparer au modèle.

#### Autres tennis
* **qitaoshi/tennis-model-v2** — https://github.com/qitaoshi/tennis-model-v2 · Python · ★ 0 · 09/2026 · pricer pré-match en **forme fermée Barnett & Clarke** (Monte Carlo seulement pour vérifier), toutes les échelles (total de jeux, handicap, tie-break, jeux par joueur), données TML-Database ; jugé sur Brier/log loss/ECE/CRPS ; l'auteur a **abandonné l'objectif « trouver des lignes mal pricées » le 08/08/2026** au profit de la seule précision.
* **DanielTomaro13/Tennis-Modelling** (« Grand Slam Tennis ») — https://github.com/DanielTomaro13/Tennis-Modelling · Python · ★ 2 · 02/10/2026 · **MIT** · site GitHub Pages reconstruit toutes les 3 h (Actions **en pause** en 09/2026), Elo par surface + Markov point→match + Monte Carlo, marchés complets dont **aces, doubles fautes, « most aces »** ; même auteur que **DanielTomaro13/sportsdata-mcp** (serveur MCP multi-sources de cotes, fournisseur Pinnacle anonyme).

---

## 4. Détecteurs de value bets / +EV / « odds screens » automatisés

### 4.1 Les références méthodologiques (à lire en premier)

#### emmanueladutwum123/sports-betting-dashboard (« Quantitative Betting Research ») — ⭐ meilleure doc sur le prix juste
* **URL** : https://github.com/emmanueladutwum123/sports-betting-dashboard · Python/Streamlit · ★ 0 · dernier commit 08/2026 · pas de licence
* **Ce que ça fait** : dashboard Streamlit (onglets Daily Card, **+EV Board** « souvent vide », Fixtures avec désaccord sharp vs récréatifs), foot + basket.
* **Méthode du prix juste (4 étapes)** : (1) **dé-vig de chaque book séparément** sur son vecteur complet, **méthode de Shin** par défaut (puissance, additive, odds-ratio, multiplicative disponibles) ; (2) **agrégation en log-odds** (pas de moyenne de cotes décimales : par Jensen, ça fabrique de l'edge) ; (3) **pondération des books sharp ×4 à ×8** (Pinnacle, exchanges) ; (4) **exclure le book évalué de sa propre référence**. Mise : Kelly sur une probabilité **rétrécie selon le désaccord entre books**, quart de Kelly, plafond d'exposition par journée. Verdicts du ledger seulement si n ≥ 30 et |t| > 2.
* **Résultat clé (honnête)** : Dixon-Coles walk-forward, **18 championnats européens, ~32 000 matchs, 6 saisons**, contre la clôture Pinnacle dé-vigée : **le marché gagne dans les 36 tests** (1X2 et O/U, Ligue 1 et Ligue 2 compris) ; poids optimal sur le modèle = 0 dans 32 cas sur 36. Les petits championnats ne sont pas plus « mous » à la clôture. Par contre, **parier le consensus sharp au meilleur prix disponible = +2,10 % sur 1 408 paris** (t ≈ 0,79, donc non significatif seul).
* **Bug instructif** : Betfair renvoyait `1.04/1.04/1.04` sans liquidité → 71 faux value bets (« nuls à +17 % EV ») ; un **filtre de plausibilité de la marge par book** (MIN/MAX) les a réduits à 1.
* **Ce qu'on peut réutiliser** : **tout le pipeline de prix juste** (c'est exactement l'approche Overstreamlit), le filtre de marge plausible, l'exclusion du book évalué, Kelly rétréci. **Le README confirme indépendamment la conclusion du projet.**

#### Lisandro79/BeatTheBookie (Kaunitz, Zhong, Kreiner 2017)
* **URL** : https://github.com/Lisandro79/BeatTheBookie · MATLAB/Python · **★ 658** · dernier commit 10/2021 · **GPL-3.0**
* **Ce que ça fait** : code + jeu de données du papier « Beating the bookies with their own numbers – and how the online sports betting market is rigged » (arXiv 1710.02824) : pas de modèle, on utilise la **cote moyenne du marché (moins une marge)** comme probabilité, et on parie quand le meilleur book dépasse ce consensus.
* **Résultats rapportés** : rentable sur 10 ans de cotes de clôture, 6 mois de cotes minute par minute et 5 mois d'argent réel (ROI de ~3,5 % à ~9,9 % selon les simulations) ; **les comptes des auteurs ont été limités par les bookmakers** — c'est la vraie limite.
* **Réutilisable** : la stratégie « consensus » comme **baseline** quand aucune cote Pinnacle n'est disponible sur un marché ; le dataset historique pour backtester.

#### aqsmith02/paper-betting-tracker
* **URL** : https://github.com/aqsmith02/paper-betting-tracker · Python · ★ 6 · dernier commit 27/09/2026 · pas de licence
* **Ce que ça fait** : réplication en **paper trading** de Kaunitz et al. via The Odds API, moneyline seulement, books de Caroline du Nord, toutes les ligues ; trois stratégies : **« Fair Average Odds »** (moyenne des probas dé-vigées de tous les books), **« Modified Z-Score »** (en plus, le meilleur prix doit être une valeur aberrante, z-score modifié robuste), et **« Random » (groupe témoin)**. Demi-Kelly, EV > 5 %, mise max 2,5 unités. Collecte du 15/10/2025 au 22/01/2026 (arrêtée).
* **Automatisation** : GitHub Actions **7 fois par heure** pour la recherche, toutes les 6 h pour les résultats ; CSV committés (`*_bets.csv` minimal + `*_full.csv` avec toutes les cotes).
* **Évaluation** : test d'hypothèse par **simulation Monte Carlo sous H0 (EV = −5 %)** pour savoir si le profit observé est explicable par la chance. Les chiffres ne sont donnés qu'en graphiques → non vérifiables ici ; ~3 mois de données = trop court.
* **Réutilisable** : le **groupe témoin aléatoire** et la simulation sous H0 — très bonne pratique à copier dans le suivi Overstreamlit ; stocker *toutes* les cotes au moment du pari (`_full.csv`).

### 4.2 Bots et tableaux de bord +EV

#### kieranaston/bet-bot
* **URL** : https://github.com/kieranaston/bet-bot · Python (Docker + SQLite) · ★ 0 · créé 09/2026 · pas de licence
* **Ce que ça fait** : trouve les paris +EV chez les books **licenciés en Ontario** en comparant à **Pinnacle dé-vigé** (ou, pour les props, à un **consensus multi-books** ; repli sur la médiane FanDuel/DraftKings/BetMGM si Pinnacle est absent ou périmé), **alerte Telegram** ; l'utilisateur répond `/placed`, `/skip`, `/settle` ; bankroll, digest quotidien, ROI.
* **Détails utiles** : scans à heures fixes (fuseau Est, gestion heure d'été) pour économiser les crédits The Odds API ; props et lignes alternatives récupérées **par événement et seulement à l'approche du match** (les books les publient tard) ; plancher de probabilité vraie (filtre les grosses cotes) ; quart de Kelly ; **cooldown de ré-alerte** sauf mouvement de prix significatif ; règlement automatique via `/scores` (pas pour les props). Tourne sur un VPS ; GitHub Actions seulement en secours manuel (Actions n'est pas fiable pour un polling serré).
* **Réutilisable** : le **flux Telegram bidirectionnel** (alerte → `/placed` → suivi), le cooldown d'alertes, le scan des props « proximity-gated ».

#### wilfhawk/sharpline (« SharpLine »)
* **URL** : https://github.com/wilfhawk/sharpline · TypeScript (Next.js 16, Supabase, Stripe, Vercel cron) · ★ 0 · dernier commit 02/10/2026 · pas de licence
* **Ce que ça fait** : clone type OddsJam : +EV vs Pinnacle dé-vigé avec **liste de repli priorisée de books sharp** (`pinnacle,circasports,betonlineag`), arbitrages, middles, EV de SGP, Kelly, CLV, edges live ; props via `ODDS_API_EXTRA_MARKETS` ; alertes e-mail (Resend) via routes `/api/cron/*` protégées par `CRON_SECRET` ; **fonctionne en données simulées par défaut** sans clé.
* **Réutilisable** : la variable `ODDS_API_SHARP_BOOKS` (référence sharp avec repli marché par marché), le mode « mock » pour développer sans brûler de crédits.

#### bramos0/edge-finder
* **URL** : https://github.com/bramos0/edge-finder · HTML/JS (une seule page) · ★ 0 · dernier commit 28/09/2026
* **Ce que ça fait** : outil **100 % navigateur** : prix des books vs ligne juste (Pinnacle ou médiane du marché) pour ML/spreads/totaux/**props**, suivi de « tailers » (tipsters) notés sur **ROI et CLV**, suivi de ses propres paris, **compte papier avec autopilote**. La clé API et les données restent dans le `localStorage`.
* **Réutilisable** : idée de **noter les tipsters/sources au CLV** ; architecture sans backend (clé côté client — acceptable pour un usage personnel uniquement).

#### djscott03/Scott-Sports-Predictions
* **URL** : https://github.com/djscott03/Scott-Sports-Predictions · Python · ★ 0 · dernier commit 01/10/2026 · pas de licence
* **Ce que ça fait** : NFL/NCAAF, carte hebdomadaire **gelée et corrigée automatiquement** (publiée mardi/jeudi), scanner +EV multi-books, dé-vig, Kelly fractionné, CLV, dashboard Streamlit.
* **Résultats rapportés (honnêtes)** : NFL 2019-2025, 1 960 matchs : MAE ligne de clôture 9,82 vs modèle 10,29 vs mélange 70/30 9,86 ; paris signalés **51,1 % ATS, ROI −2,0 %** ; NCAAF 1 600 paris **50,4 %, −3,7 %**. « Un modèle de ratings ne bat pas les lignes de clôture NFL. » Encore une confirmation.

#### ahirsch17/sports-ev-system
* **URL** : https://github.com/ahirsch17/sports-ev-system · Python · ★ 0 · dernier commit 09/2026 · pas de licence
* **Ce que ça fait** : boîte à outils +EV multi-sports (NFL, MLB), ingestion Pinnacle/DraftKings/FanDuel, Postgres, **circuit breakers** sur les sources, rafraîchissement planifié toutes les 4 h (tâche Windows), « control room » Streamlit, paper betting et CLV uniquement.

#### Petits calculateurs +EV historiques (The Odds API)
* **roman-smith/oddsapi_ev** — https://github.com/roman-smith/oddsapi_ev · Python · ★ 20 · 09/2022 · **MIT** · package PyPI `oddsapi_ev` : EV de chaque cote vs deux standards de « vraies cotes » (Pinnacle dé-vigé et/ou moyenne du marché).
* **jbram22/ev_sports_betting** — https://github.com/jbram22/ev_sports_betting · ★ 16 · 01/2024 · script EV : moyenne des probas implicites entre books, signale les écarts.
* **jrey999/mlb-positive-ev** — https://github.com/jrey999/mlb-positive-ev · ★ 12 · 10/2023 · +EV MLB via The Odds API.

### 4.3 Briques d'infrastructure (cotes, exchanges, maths)

| Projet | URL | ★ | Activité | Licence | Pour quoi faire |
|---|---|---|---|---|---|
| **jordantete/OddsHarvester** | https://github.com/jordantete/OddsHarvester | 256 | commit 02/10/2026 | MIT | Scraper **OddsPortal** (Playwright) : cotes à venir, **historiques** et live, 11 sports, 100+ ligues, dizaines de marchés, sortie JSON/CSV/S3, package PyPI `oddsharvester`. Source gratuite de cotes historiques multi-books (dont books FR présents sur OddsPortal) pour backtester. |
| **betcode-org/betfair** (`betfairlightweight`) | https://github.com/betcode-org/betfair | 515 | 09/2026 | MIT | Client Python officieux de l'**API Betfair Exchange** (REST + streaming). Indispensable si on prend Betfair comme référence « juste ». |
| **betcode-org/flumine** | https://github.com/betcode-org/flumine | 246 | 01/10/2026 | MIT | Framework de trading/backtest événementiel sur Betfair (stratégies, simulation à partir des flux historiques). |
| **martineastwood/penaltyblog** | https://github.com/martineastwood/penaltyblog | 228 | 01/10/2026 | MIT | Modèles foot (Poisson, Poisson bivarié, Dixon-Coles, variantes bayésiennes, optimisés en Cython), **dé-vig `calculate_implied`** avec 7 méthodes vérifiées dans le code (multiplicative, additive, power, **shin**, differential margin weighting, odds ratio, logarithmic), scrapers (Understat, Club Elo, FPL…), notations Elo/Massey/Colley/Pi. Remplace du code maison. |
| **declanwalpole/sportsbook-odds-scraper** | https://github.com/declanwalpole/sportsbook-odds-scraper | 21 | 04/2025 | — | Récupère **tous les marchés** d'un match via les **API non documentées** (DraftKings, BetMGM, Caesars, BetRivers, Bovada, Ladbrokes AU, Sportsbet, PointsBet…) → modèle d'abstraction `EventScraper` réutilisable pour des books FR. |
| **failin3/Oddsmatcher** | https://github.com/failin3/Oddsmatcher | 1 | 09/2025 | — | Appariement books ↔ **exchanges Betfair et Matchbook** (orienté matched betting néerlandais), backend Python + MySQL. |
| **gto76/bets** | https://github.com/gto76/bets | 47 | 12/2015 | — | Ancien scraper multi-bookmakers (historique). |
| **TonyTor99/pinnacle-parser** | https://github.com/TonyTor99/pinnacle-parser | 0 | 09/2026 | — | Bot de signaux (russe) sur les corners : lignes via l'**API guest Arcadia de Pinnacle sans compte** (`matchups` + `markets/related/straight` ; les corners sont des matchups « special » rattachés au match parent), stats SofaScore/FlashScore, alertes Telegram. Exemple concret de lecture des marchés « special » Pinnacle (même mécanique que les props joueurs). |
| **rozzac90/pinnacle** | https://github.com/rozzac90/pinnacle | 55 | 09/2018 | MIT | Wrapper de l'**API officielle** Pinnacle (réservée aux titulaires de compte). Historique, non maintenu. |

## 5. Scrapers des bookmakers français (ANJ)

> **Constat global** : aucun bookmaker ANJ ne documente d'API publique. Tous les projets ci-dessous utilisent des **endpoints internes non documentés** (JSON servis au site web/appli) ou un navigateur headless ; ils cassent à chaque refonte de site. Très peu de projets récents (2025-2026) couvrent les **marchés joueurs (buteur, points)**. Bonne nouvelle vérifiée sur la doc de The Odds API (02/10/2026) : une **région `fr`** existe avec `betclic_fr`, `netbet_fr`, `pmu_fr`, `unibet_fr`, `winamax_fr` (Pinnacle et `betfair_ex_eu` sont dans la région `eu`) — pour les marchés principaux (1N2, handicap, totaux), c'est la voie la plus robuste. La doc ne précise pas de props joueurs pour les books FR → pour le buteur, il faut scraper.

### 5.1 Projets multi-bookmakers FR

#### pretrehr/Sports-betting — la référence historique FR
* **URL** : https://github.com/pretrehr/Sports-betting · Python (interface PySimpleGUI) · **★ 534** · dernier commit **10/2021** (branche par défaut) · **MIT**
* **Ce que ça fait** : assistant pour **optimiser bonus, freebets et paris remboursés** (conversion de freebets en cash, couverture multi-books). Modules par bookmaker dans `sportsbetting/bookmakers/` : **Betclic, Betfair, Betway, Bwin, France Pari, JOA, NetBet, ParionsSport, Pasinobet, Pinnacle, PMU, PokerStars, Unibet, Winamax, ZEbet**.
* **Endpoints présents dans le code** (non documentés, à re-tester car datant de 2021) :
  * Betclic : `https://offer.cdn.betclic.fr/api/pub/v2/sports/{id}?application=2&countrycode=fr&language=fr&sitecode=frfr`, `.../v2/competitions/{id}`, `.../v4/events/{id}`
  * ParionsSport : `https://www.enligne.parionssport.fdj.fr/lvs-api/leagues?sport={id}`, `.../lvs-api/next/50/{id}?originId=3&lineId=1&breakdownEventsIntoDays=true`, `.../lvs-api/ff/{id}?originId=3&lineId=1&showMarketTypeGroups=true&ext=1`
  * Unibet : `https://www.unibet.fr/zones/navigation.json?publicUrl=…`, `/zones/event.json?eventId=…`, `/zones/sportnode/markets.json?nodeId=…`
  * Bwin : `https://cds-api.bwin.fr/bettingoffer/fixtures?x-bwin-accessid={}&lang=fr&country=FR&userCountry=FR`
  * PokerStars Sports : `https://sports.pokerstarssports.fr/sportsbook/v1/api/getSportTree?…`
  * PMU : `https://paris-sportifs.pmu.fr/pservices/more_events/…` ; Winamax, ZEbet, NetBet : parsing des pages HTML.
  * Pinnacle : API guest (voir §4).
* **Ce qu'on peut réutiliser** : la **carte des endpoints** comme point de départ (beaucoup existent encore sous une forme proche) et la logique d'optimisation des bonus (utile pour la bankroll réelle d'un parieur français).

#### Matttgic/Cotescope (« CoteScope FR »)
* **URL** : https://github.com/Matttgic/Cotescope · TypeScript (Next.js) · ★ 0 · dernier commit 27/09/2026 · pas de licence
* **Ce que ça fait** : scanner privé **limité aux books ANJ** : value bets (cote juste / EV / score de qualité), arbitrages, boosts, mouvements de lignes, **CLV**, tracker. Provider The Odds API implémenté côté serveur pour **Betclic, NetBet, PMU, Unibet, Winamax** avec **Pinnacle comme référence sans marge** sur le H2H ; mode démo sans clé.
* **Règles intéressantes** : **« garde-fou grosses cotes »** (masquer les cotes > 4,00 ; au-delà, exiger score ≥ 85, EV ≥ 5 % et cote ≤ 8,00 ; une divergence isolée n'est jamais une opportunité suffisante) ; filtres de fraîcheur/stabilité ; snapshots pour CLV ; **aucun secret API dans le navigateur**.
* **Réutilisable** : quasiment le cahier des charges d'Overstreamlit en version web ; le garde-fou grosses cotes est à copier tel quel.

#### Ghantard/winator
* **URL** : https://github.com/Ghantard/winator · Python/Streamlit · ★ 0 · dernier commit 09/2026 · pas de licence
* **Ce que ça fait** : scan Winamax foot (1N2 + double chance) en lisant le **JSON `PRELOADED_STATE` embarqué dans les pages** (`httpx`, pas de navigateur) ; référence marché = **médiane de 20 à 38 books (The Odds API) après retrait de la marge de chacun, Winamax exclu du consensus** ; 3 niveaux de risque (DC, DNB manuel, simple) ; ticket du jour avec Kelly fractionné en mode « valeur uniquement ». Note : marge Winamax 8-12 % selon les matchs.
* **Réutilisable** : `winamax_scraper.py` (`_extract_preloaded_state`) = **méthode la plus légère pour Winamax** ; exclusion du book évalué de la référence (même principe que §4.1).

#### mazalazop/nhl-unibet-odds-scraper — buteurs NHL chez Unibet ⭐
* **URL** : https://github.com/mazalazop/nhl-unibet-odds-scraper · Python · ★ 0 · dernier commit 01/10/2026 · pas de licence
* **Ce que ça fait** : extrait et normalise les **cotes joueurs NHL d'Unibet.fr** : marché **« Buteur »** (en excluant « 2 buts ou plus », points, double chance…) et **points « 1 ou plus »** ; pipeline par marché **batch → rapport d'acceptation → normalisation → upload d'artefacts** ; un seul workflow officiel par marché (`unibet-event-goals-batch.yml`, `unibet-event-points-batch.yml`), entrée = liste d'URL d'événements.
* **Détail notable** : les workflows tournent sur un **runner GitHub self-hosted installé sur le Mac de l'utilisateur** — ce qui suggère (déduction, non écrit explicitement) que le site n'est pas scrapé de façon fiable depuis les runners hébergés par GitHub (IP de datacenter US).
* **Réutilisable** : exactement notre besoin (cote buteur FR à comparer à un modèle ATG) ; l'étape **« acceptance report »** (contrôle qualité avant d'utiliser une cote) ; la solution **runner self-hosted** (PC/Raspberry Pi en France) pour contourner le géoblocage.

#### Winamax : collecte temps réel (Socket.IO)
* **HKB06/ScriptWinamax** — https://github.com/HKB06/ScriptWinamax · Python · ★ 0 · dernier commit 09/2025 · collecteur des données temps réel Winamax via leur **Socket.IO** (hôte `sports-eu-west-3.winamax.fr`) ; V3 en **Playwright** uniquement ; produit `winamax_matches.json` (foot, basket, **hockey**, tennis) et `odds_<matchId>.json` (tous les marchés d'un match → potentiellement les marchés buteurs).
* **anach-ai/winamax** — https://github.com/anach-ai/winamax · Python/Flask · ★ 2 · dernier commit 11/2025 · **MIT** · capture Socket.IO + auto-scroll headless, **API REST locale** `/api/matches` (630+ matchs de foot avec cotes), rafraîchissement chaque minute, docs EN/FR.
* **bixentecapelli-cell/try** (« Winamax Bet Analyzer ») — https://github.com/bixentecapelli-cell/try · TypeScript · ★ 0 · dernier commit 01/10/2026 · scraper live du board foot Winamax via `PRELOADED_STATE` + cotes agrégées (Winamax, Unibet, Betclic, Pinnacle, Bwin) via The Odds API (PR #3).
* **samuelhm/bethurtadom** — https://github.com/samuelhm/bethurtadom · Python 3.14 + Playwright + **Camoufox** (anti-détection) · ★ 1 · dernier commit 03/2026 · projet espagnol : détection de discrépances **live** Winamax (probablement winamax.es) vs Bet365, **normalisation des noms d'équipes** automatique + manuelle, patron « Abstract Scraper ».

#### Autres (anciens ou hors ANJ)
* **sferez/Arbitrage_Betting_Bot** — https://github.com/sferez/Arbitrage_Betting_Bot · Python · ★ 18 · dernier commit 03/2023 · arbitrage entre books FR (Unibet, Betclic, ParionsSport…) : Selenium pour les sites dynamiques (ParionsSport, Unibet), BeautifulSoup pour les statiques (Betclic), requêtes JSON directes quand c'est possible.
* **Cooya/Betbee** — https://github.com/Cooya/Betbee · JavaScript · ★ 1 · 2016 · scraper Winamax.fr / Unibet.fr (historique).
* **bettor-league/parions-sport-batch** — https://github.com/bettor-league/parions-sport-batch · ★ 0 · 2020 · récupère l'offre du **réseau physique** ParionsSport (`pointdevente.parionssport.fdj.fr/api/`).
* **danielcardeenas/surebet** — https://github.com/danielcardeenas/surebet · TypeScript · ★ 58 · dernier commit 01/2026 · **MIT** · logiciel d'arbitrage temps réel extensible (non spécifique FR) — utile pour l'architecture de connecteurs.
* **diouetq/Scrapping-Bet** — https://github.com/diouetq/Scrapping-Bet · Python · ★ 0 · commit 02/10/2026 · en français mais pour des books **non ANJ** (Sportaza, Betify, Greenluck) ; export Excel avec probas implicites, TRJ, Kelly — à éviter (books offshore illégaux en France).

* **Tomek765/betclic-odds-extractor** (« APEX Context Engine ») — https://github.com/Tomek765/betclic-odds-extractor · Python (GUI + .exe Windows) · ★ 0 · créé 09/2026, push 02/10/2026 · projet **polonais** (README en polonais, donc a priori betclic.pl, même plateforme que betclic.fr) : extrait **l'ensemble des cotes d'une page d'événement Betclic** en conservant la provenance de chaque enregistrement, puis module de **dé-vig**, Poisson, « market graph » et détection d'anomalies entre marchés liés. Seul extracteur Betclic récent trouvé ; à adapter au domaine `.fr`.
* **almoundji/ALL** (« Value Bets Football ») — https://github.com/almoundji/ALL · Python + TypeScript (Netlify Functions) · ★ 0 · dernier commit 28/09/2026 · dashboard FR : cotes 1N2 et plus/moins via The Odds API (Betclic, Unibet, Winamax, Bet365, Pinnacle…), Poisson/Dixon-Coles sur football-data.co.uk **combiné au consensus de marché dé-margé**, value bets = meilleure cote > cote juste, Kelly fractionné plafonné ; Ligue 1/Ligue 2 incluses ; page de connexion par variables d'environnement Netlify.

**Bilan §5** : Vbet, Olybet, DAZN Bet, Betsson.fr, bet365.fr : **aucun scraper open source récent (2024-2026) trouvé**. Betclic : seulement l'extracteur polonais ci-dessus et les endpoints 2021 de pretrehr. Marchés joueurs FR : seul **mazalazop** (Unibet, buteurs/points NHL) les traite explicitement. Pour Winamax (Socket.IO / `PRELOADED_STATE`), Unibet (buteurs NHL) et les marchés principaux de 5 books via The Odds API, il existe des bases récentes.

---

## 6. Projets qui documentent des résultats (backtest, paper trading, CLV) — lecture critique

### 6.1 ryan00x/Bet-Model — ⭐ le résultat le plus important pour Overstreamlit
* **URL** : https://github.com/ryan00x/Bet-Model (voir `STRATEGY.md`, `RESULTS_ML.md`, `AUDIT.md`) · Python · ★ 0 · dernier commit 02/10/2026 · **MIT**
* **Données** : football-data.co.uk (25 saisons × 10 ligues, cotes de 6+ books dont Pinnacle), Understat (xG).
* **Deux réponses opposées** :
  1. **ML sur données publiques** (5 itérations, 53 features, walk-forward 25 saisons) : **ROI −6,7 %**, AUC plafonnée à ~0,56.
  2. **Ancre sharp + line shopping** (Pinnacle dé-vigé par méthode **« power »**, parier quand un book du panel dépasse la valeur juste de +2 %) : **+4,86 % sur 20 676 paris (IC 95 % +2,6 à +7,1), CLV +3,05 %**, 68 % des paris battent la clôture Pinnacle, positif sur les 13 saisons ; 1X2 +4,8 % (17 890 paris), O/U 2,5 +5,9 % (1 311), handicap asiatique +5,0 % mais CLV +0,4 % (déclaré « non prouvé »).
* **Tests de robustesse** : leave-one-league-out (+4,4 à +5,4 %) ; **placebo** : gradient monotone du ROI par tranche d'EV (−7,3 % → +10,9 %) ; parier au meilleur prix au hasard = −1,0 % (la prime de meilleur prix n'explique rien) ; exécution pessimiste chez Bet365 seul = +1,6 % (CLV +1,4 %) ; slippage −3 % tue les seuils < 1 % ; le multiplicatif surestime les outsiders en 1X2 → **power devig** indispensable.
* **Mise** : ¼ Kelly, max 2 % de bankroll par pari, exposition journalière ≤ 25 % → drawdown max 22,6 % vs > 60 % en Kelly plein.
* **Limites déclarées** : les opportunités ont **diminué de moitié** (≈1 810/saison en 2012-14 → ≈845 en 2022-24), ROI 2022-24 +1,75 % [−4,4 ; +8,1] mais CLV toujours +2,96 % ; **ne marche pas sur Betfair Exchange** (51 % de paris battant la clôture, commission → négatif : l'exchange bouge *avec* Pinnacle) ; les books « soft » limitent les gagnants en quelques semaines ; chiffres déjà **corrigés deux fois à la baisse** (honnêteté appréciable).
* **⚠️ Test sur les bookmakers français (ANJ), août 2026 — abandonné** : sur **4 342 cotes, 99 matchs, les 5 books ANJ**, la meilleure cote française est en médiane **0,936 × Pinnacle** et **aucune n'a atteint le seuil de 2 % d'EV** (meilleure : +0,25 %). « Un panel pricé sous le book sharp ne peut pas produire de valeur aberrante au-dessus de la valeur juste. » → **Implication directe pour Overstreamlit** : sur les marchés principaux (1N2/O/U) en France, le TRJ légalement plafonné en France (85 % en moyenne) rend la méthode « ancre Pinnacle » quasi stérile ; les seuls terrains plausibles sont **les cotes boostées, les promotions, les marchés secondaires/props où les books FR pricent lentement**, et la vitesse sur les infos (compositions, gardiens). Échantillon de 99 matchs : à re-mesurer soi-même, mais c'est cohérent avec la mécanique du TRJ.
* **Réutilisable** : tout (`src/value_bet_sharp.py --predict / --evaluate`), surtout le **test placebo par tranche d'EV** et la règle « 3 mois de CLV positif en paper trading valent plus que 13 saisons de backtest ».

### 6.2 Autres résultats documentés (classés du plus crédible au moins crédible)

| Projet | Résultat annoncé | Crédibilité / commentaire |
|---|---|---|
| **cooperross399/nhl-betting-lab** (§1.1) | Props NHL : 25 911 paris, **−0,3 %** [−1,5 ; +1,0] ; désaccord modèle-marché non informatif (coef. 0,03) | **Très crédible** : mesure honnête, corrections publiées, « un pari = un pari au meilleur prix ». |
| **emmanueladutwum123/sports-betting-dashboard** (§4.1) | Dixon-Coles perd contre la clôture Pinnacle dans 36/36 tests ; line shopping du consensus sharp +2,10 % (t ≈ 0,79) | **Crédible**, prudent sur la significativité. |
| **djscott03/Scott-Sports-Predictions** (§4.2) | NFL −2,0 % ATS, NCAAF −3,7 % | **Crédible** (résultat négatif publié). |
| **tanamsethi31/footymodel** (§3.1) | O/U & 1X2 : CLV −0,2 %, yield −7 % ; AH : yield +2 % mais CLV −1,5 % | **Crédible**, bonne pédagogie « yield sans CLV = bruit ». |
| **MJACode/betting-model** (§1.1) | NHL ML −3,4 à −6 % à l'ouverture ; props NHL +5,7 à +10,9 % « au meilleur prix » (PR #860) | Partie négative crédible ; **partie props positive douteuse** (meilleur prix ex post, multiples tests). |
| **CarsonBillig/nhl-model** (§1.1) | +2,6 à +5 % à l'ouverture, **perd à la clôture** | Plausible : edge = vitesse ; à confirmer en forward test. |
| **dbabsy/tennis-props** (§3.2) | 0,03 de log loss derrière Pinnacle/Bet365 | **Crédible** (« le modèle est derrière la clôture, comme il se doit »). |
| **Risky-Scout/nba-player-props-model** (§2.1) | `model_trails_market=True` | **Crédible**, mesuré prospectivement. |
| **Lisandro79/BeatTheBookie** (§4.1) | 3,5 à 9,9 % de ROI, dont 5 mois d'argent réel | Crédible à l'époque (2015-17) ; comptes limités ; marché plus efficient aujourd'hui. |
| **aqsmith02/paper-betting-tracker** (§4.1) | Courbes de profit en paper trading (oct. 2025 → janv. 2026) | Méthode saine (témoin aléatoire, Monte Carlo sous H0) ; durée trop courte, chiffres seulement en images. |
| **hughesed/Sports-Line** (« Line Scout ») — https://github.com/hughesed/Sports-Line · ★ 1 · commit 02/10/2026 | Bot GitHub Actions toutes les ~45 min (ESPN), modèle « ratings + lignes », se note lui-même (Brier), argent fictif, bankroll dans le `localStorage` | Outil de pratique honnête ; pas de prétention de gain. Architecture « page fixe + `data/*.json` réécrits par le bot » à copier. |
| **throwawayhub25/Sports-Betting-Model** — https://github.com/throwawayhub25/Sports-Betting-Model · ★ 12 · 06/2025 · MIT | NBA moneyline « ~10 % de ROI de façon constante » | **Non crédible** : `train_test_split` **aléatoire** (pas chronologique → fuite temporelle), features et hyperparamètres non publiés, aucun CLV. Exemple type de ce qu'il faut rejeter. |

**Leçon transversale** : tous les projets qui mesurent le CLV contre Pinnacle concluent que (1) les modèles statistiques seuls ne battent pas la clôture, (2) l'edge restant vient de la **dispersion des prix entre books** et de la **lenteur de certains books**, (3) cet edge **s'amenuise** et (4) les comptes gagnants sont limités. Pour un parieur français, (2) est fortement réduit par le TRJ plafonné (cf. test ANJ de ryan00x) → regarder les **boosts, promotions et props**.

---

## 7. Idées d'architecture pour un tableau de bord automatisé (« quoi parier aujourd'hui »)

Synthèse des bonnes pratiques observées dans les dépôts ci-dessus, adaptée au contexte d'Overstreamlit (parieur français, comparaison des books ANJ à un prix juste Pinnacle/Betfair).

### 7.1 Squelette « zéro serveur » (le plus répandu et le plus robuste)
* **GitHub Actions = ordonnanceur, dépôt (ou release) = base de données, GitHub Pages = site** (shawnmcgee/degenpredicts, pradazay1-code, Mbennett00, jaredkimble-coder, ethanllawrence, hughesed). La page HTML est **fixe** et lit des `data/*.json` réécrits par le bot (hughesed, jaredkimble-coder).
* **Séparer les rythmes** : modèle lent (1-2×/jour, réentraînement hebdo le mardi chez degenpredicts) / cotes rapides (toutes les 15-30 min : `cron: */30` chez jaredkimble-coder, 7×/heure chez aqsmith02) / correction des paris (une fois la nuit). Un job de cotes **ne recalcule jamais le modèle**, il ne fait que réappliquer l'EV.
* **Crons calés sur l'information** plutôt que sur l'heure ronde : NHL → après l'annonce des gardiens (11 h, 13 h, 15 h 30, 17 h 30, 18 h 40 ET chez Mbennett00) ; NBA → après les rapports de blessures officiels (17 h locale la veille, 13 h le jour même en back-to-back) ; foot → **20-40 min avant le coup d'envoi** quand les compositions tombent (footymodel) ; rugby/NRL → la veille au soir (marqueurs-xiii).
* **Stockage d'état** : SQLite committé (Pradapicks) pour démarrer ; **release GitHub `data-latest`** (Mbennett00) pour ne pas gonfler l'historique git ; branche `gh-pages` réécrite en un seul commit (marqueurs-xiii) ; Postgres/Supabase quand ça grossit (MJACode, momentumnhl, Cotescope).
* **Limites connues** : GitHub suspend les workflows planifiés d'un dépôt inactif depuis 60 jours (rappelé par Mbennett00) ; les crons Actions peuvent être retardés de plusieurs minutes ; stats.nba.com et certains books bloquent les IP de datacenters → **runner self-hosted en France** (Mac/PC/Raspberry Pi, comme mazalazop) pour scraper Winamax/Unibet/Betclic avec une IP française.

### 7.2 Le prix juste (cœur du système)
1. **Dé-viger chaque book séparément** sur son vecteur complet, avec une méthode qui respecte le biais favori/outsider : **Shin** ou **power** (emmanueladutwum123, ryan00x) ; jamais de moyenne de cotes décimales.
2. **Référence sharp avec repli** marché par marché : Pinnacle → Betfair Exchange (si liquidité réelle) → consensus pondéré (sharps ×4-8) en **log-odds** (wilfhawk `ODDS_API_SHARP_BOOKS`, emmanueladutwum123, kieranaston).
3. **Exclure le book évalué de sa propre référence** (emmanueladutwum123, winator).
4. **Filtres anti-artefacts** : marge plausible par book (le bug Betfair 1.04/1.04/1.04), fraîcheur des cotes (horodatage, renunezg), exclusion des matchs commencés (jaredkimble-coder), **garde-fou grosses cotes** (> 4,00 masquées sauf conditions strictes, Cotescope), plancher de probabilité vraie (kieranaston).
5. **Marchés à un seul côté (buteur, « 1+ point », « N+ aces »)** : dé-vig par ajustement de forme sur l'échelle 1+/2+/3+ avec marge libre (JChan23) ; sinon dé-vig global du marché buteur du match, **pondéré par le temps de jeu attendu** (marqueurs-xiii) ; mesurer et afficher la marge du marché (16-55 % sur les marqueurs !).

### 7.3 Les modèles de props : où ils ont une place
* Ils servent surtout à **produire une référence là où Pinnacle ne cote pas** (props des books FR) et à **réagir plus vite** à une info (gardien, composition), pas à « battre le marché » en général (cooperross399 : coefficient 0,03 sur le désaccord).
* Recette convergente : **λ d'équipe ancré sur le marché** (total d'équipe/handicap) → **répartition entre joueurs** = taux par minute (ou ixG/60) rétréci × **minutes/TOI projetés** (PP séparé) × ajustements adverses → loi de Poisson / **binomiale négative** (ou ZINB pour la NBA) → calibration isotonique → **contrôle de cohérence** Σ joueurs ≈ équipe (Mbennett00, marqueurs-xiii, Risky-Scout, kylewish19).
* Verrouiller la « carte de probabilités » **avant** de regarder les cotes, puis appliquer une barrière de prix séparée (kylewish19) ; geler le premier avis du jour (cooperross399, momentumnhl).
* Ne jamais publier un signal sans **gardien / composition confirmés** (Mbennett00) ; afficher « désaccord » plutôt que « value » quand le modèle et le marché divergent sur le total du match (marqueurs-xiii).

### 7.4 Ce que la page doit afficher (UX observée)
* Par pari : proba modèle, proba marché sans marge, **cote minimale encore jouable** (« bet at or better than », flagk / Mbennett00), EV, mise ¼ Kelly plafonnée, horodatage de la cote, book.
* Un onglet **« Check »** où l'on tape la cote vue dans l'appli Winamax/Betclic et qui rend l'EV (Mbennett00, flagk) — indispensable quand on ne peut pas scraper un book.
* Un message explicite **« aucun pari aujourd'hui »** (flagk, emmanueladutwum123) plutôt qu'un remplissage.
* **Heartbeat / données périmées** (`status.json` + bandeau d'alerte, ethanllawrence) ; manifestes de snapshot manqué/échoué (Risky-Scout).
* README réécrit automatiquement entre balises (`<!-- PICKS:START -->`, flagk) ; carte du jour postée en **commentaire d'issue** (notification e-mail gratuite, cooperross399) ou **Telegram** bidirectionnel (`/placed`, `/skip`, `/settle`, kieranaston) ; alerte de quota The Odds API via issue (degenpredicts).
* Données personnelles (paris réels, bankroll) dans le `localStorage` du navigateur ou un dépôt privé (flagk, bramos0, hughesed) ; publier « public-safe » (pas de noms de books ni prix par book, flagk).

### 7.5 Suivi et évaluation (ce qui distingue les projets sérieux)
* **Ledger append-only verrouillé avant l'événement** (futbol-modelo, CarsonBillig) + snapshots **T-25 min et clôture** pour le **CLV** (Risky-Scout) ; formule CLV documentée (dé-vig des deux côtés à la clôture ; exclure les marchés à un seul côté du CLV publié, MJACode).
* **Groupe témoin aléatoire** et simulation Monte Carlo sous H0 (aqsmith02) ; **test placebo par tranche d'EV** (le ROI doit croître avec l'EV estimé, ryan00x) ; ROI par tranche d'edge (s'il décroît, le modèle est faux, cooperross399) ; réplication sur une autre saison ; leave-one-league-out.
* Verdicts seulement si n ≥ 30 et |t| > 2 (emmanueladutwum123) ; « 3 mois de CLV positif en paper trading > 13 saisons de backtest » (ryan00x).
* Un pari = un pari, au prix réellement obtenable (pas un pari par book, pas le maximum ex post du panel ; tester l'exécution pessimiste « un seul book »).

### 7.6 Budget de données (gratuit d'abord)
* **NHL** : `api-web.nhle.com` (doc Zmalski), MoneyPuck (CSV), Daily Faceoff (lignes/gardiens), archive SBR pour cotes historiques de match.
* **NBA** : `nba_api` (+ ESPN en secours), `nbainjuries`.
* **Foot** : `soccerdata` (FBref, Understat, WhoScored, Sofascore), football-data.co.uk (cotes historiques avec Pinnacle), `penaltyblog` (dé-vig).
* **Cotes** : The Odds API (région `fr` : Betclic, NetBet, PMU, Unibet, Winamax ; `eu` : Pinnacle, Betfair EX — marchés principaux ; props surtout US), API guest Pinnacle (matchups + specials), `betfairlightweight` ; scrapers Winamax (`PRELOADED_STATE` ou Socket.IO) et Unibet (marchés joueurs) pour les props FR ; OddsHarvester pour l'historique OddsPortal.

---

