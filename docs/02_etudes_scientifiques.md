# Revue de littérature : prédiction sportive et efficience des marchés de paris

> **État des connaissances : 2 octobre 2026.** Revue rédigée pour une bibliothèque open source de stratégies de prédiction et de paris sportifs. Langue : français. Les références ont été vérifiées en ligne (résumés via Semantic Scholar, arXiv, pages éditeurs, RePEc, et texte intégral quand il était accessible).

## Comment lire ce document

Chaque fiche suit le même format :

- **Référence** : auteurs, année, titre, revue.
- **Lien** : DOI ou URL.
- **Résumé** : 2 à 5 lignes.
- **Résultat clé** : chiffres (RPS, log-loss, Brier, précision, ROI, taille d'échantillon, période) quand ils existent.
- **Implication pratique pour nous** : ce qu'il faut adopter ou éviter.
- **Vérif.** : niveau de vérification.
  - `[TI]` : texte intégral lu (PDF).
  - `[R]` : résumé officiel lu.
  - `[S]` : chiffres de seconde main (citation dans un autre article ou une page de synthèse), à revérifier avant de les citer.
  - `[?]` : détail incertain, signalé comme tel.

Abréviations :

- **RPS** : *Ranked Probability Score*. Plus bas = meilleur. En football 1X2, les bons modèles sont autour de 0,19 à 0,21, et les cotes des bookmakers font généralement mieux que les modèles publics.
- **ROI** : bénéfice net / total misé.
- **CLV** : *closing line value*, l'écart entre la cote prise et la cote de clôture.
- **FLB** : *favourite-longshot bias*, ou biais favori-outsider.
- **1X2** : victoire domicile / nul / victoire extérieur.

## Sommaire

1. Football : modèles de prédiction
2. Football : efficience des marchés, conversion des cotes, stratégies publiées
3. Tennis
4. Autres sports : basket (NBA), hockey (NHL), football américain (NFL), baseball (MLB), rugby, handball, volley
5. Théorie du pari et gestion de bankroll (Kelly et variantes)
6. Pièges méthodologiques : surapprentissage, tests multiples, biais de backtest, limitation des comptes, CLV
7. Biais comportementaux exploitables
8. Synthèse : ce que dit la science, consensus et stratégies les plus prometteuses
9. Index des fiches (133 fiches, environ 150 références)
10. Limites de cette revue

---

## 1. Football : modèles de prédiction

### 1.1 Modèles de comptage de buts (Poisson et extensions)

#### [F1] Maher (1982) : le Poisson indépendant attaque/défense
- **Référence** : Maher, M. J. (1982). *Modelling association football scores*. Statistica Neerlandica, 36(3), 109–118.
- **Lien** : https://doi.org/10.1111/j.1467-9574.1982.tb00782.x
- **Résumé** : Chaque équipe reçoit un paramètre d'attaque et un paramètre de défense. Les buts de chaque équipe suivent une loi de Poisson indépendante, dont l'intensité est le produit attaque × défense adverse × avantage du terrain. Les tests d'ajustement montrent qu'un Poisson indépendant décrit raisonnablement les scores, contrairement aux travaux antérieurs qui préféraient la binomiale négative.
- **Résultat clé** : bon ajustement global. Une légère sous-estimation des matchs nuls et des faibles scores est connue, et c'est ce que Dixon-Coles corrigera.
- **Implication pratique pour nous** : c'est le **modèle de base** de toute la bibliothèque (baseline obligatoire). Il est simple, interprétable et donne toute la distribution des scores, donc les marchés 1X2, over/under, BTTS et score exact.
- **Vérif.** : [R]

#### [F2] Dixon & Coles (1997) : correction des faibles scores et pondération temporelle
- **Référence** : Dixon, M. J., & Coles, S. G. (1997). *Modelling association football scores and inefficiencies in the football betting market*. Journal of the Royal Statistical Society, Series C (Applied Statistics), 46(2), 265–280.
- **Lien** : https://doi.org/10.1111/1467-9876.00065
- **Résumé** : Poisson de Maher plus deux ajouts :
  - un facteur de dépendance (τ, paramètre ρ) qui corrige les probabilités des scores 0-0, 1-0, 0-1 et 1-1 ;
  - une pondération exponentielle décroissante des matchs passés (paramètre ξ), pour suivre la forme des équipes.
  Le modèle est ajusté sur les championnats et coupes anglais de 1992 à 1995, puis testé contre les cotes des bookmakers de 1995-96.
- **Résultat clé** : rendement **positif** d'une stratégie qui ne parie que lorsque le ratio probabilité modèle / probabilité implicite dépasse un seuil élevé. Ce résultat repose sur une seule saison de test, avec les marges britanniques de l'époque, nettement plus élevées qu'aujourd'hui.
- **Implication pratique pour nous** : c'est la **baseline de référence** des modèles de buts. Il faut implémenter ρ et ξ, et optimiser ξ en validation hors échantillon. Le profit de 1997 n'est **pas transposable** aux marchés actuels.
- **Vérif.** : [R]. Le détail des seuils n'a pas été relu `[?]`.

#### [F3] Rue & Salvesen (2000) : modèle bayésien dynamique
- **Référence** : Rue, H., & Salvesen, Ø. (2000). *Prediction and retrospective analysis of soccer matches in a league*. Journal of the Royal Statistical Society, Series D (The Statistician), 49(3), 399–418.
- **Lien** : https://doi.org/10.1111/1467-9884.00243
- **Résumé** : Modèle bayésien où les forces d'attaque et de défense évoluent dans le temps, estimé par MCMC. Il est appliqué à la Premier League et à la Division 1 anglaise 1997-98, pour la prédiction, le pari, l'analyse rétrospective du classement et la détection de matchs « surprenants ».
- **Résultat clé** : les auteurs présentent une application au pari. Ce sont des résultats d'une saison, à interpréter avec prudence.
- **Implication pratique pour nous** : c'est l'ancêtre des modèles à états. Il justifie de laisser les forces varier dans le temps plutôt que de les figer sur une saison.
- **Vérif.** : [R]

#### [F4] Karlis & Ntzoufras (2003) : Poisson bivarié et inflation des nuls
- **Référence** : Karlis, D., & Ntzoufras, I. (2003). *Analysis of sports data by using bivariate Poisson models*. Journal of the Royal Statistical Society, Series D (The Statistician), 52(3), 381–393.
- **Lien** : https://doi.org/10.1111/1467-9884.00366
- **Résumé** : Un Poisson bivarié introduit une covariance entre les buts des deux équipes. Une version « diagonale gonflée » ajoute de la masse sur les scores nuls (0-0, 1-1…), observés plus souvent que ne le prévoit le Poisson indépendant.
- **Résultat clé** : meilleure estimation des matchs nuls. Le modèle permet aussi une surdispersion marginale.
- **Implication pratique pour nous** : c'est l'alternative à Dixon-Coles pour les marchés « nul » et « score exact ». Les deux doivent être testés : Ley et al. (2019, [F7]) trouvent que Poisson bivarié et indépendant sont les meilleurs.
- **Vérif.** : [R]

#### [F5] Karlis & Ntzoufras (2009) : loi de Skellam sur la différence de buts
- **Référence** : Karlis, D., & Ntzoufras, I. (2009). *Bayesian modelling of football outcomes: using the Skellam's distribution for the goal difference*. IMA Journal of Management Mathematics, 20(2), 133–145.
- **Lien** : https://academic.oup.com/imaman/article-abstract/20/2/133/716512 (DOI probable : 10.1093/imaman/dpn026 `[?]`)
- **Résumé** : On modélise directement la différence de buts (loi de Skellam, avec variante gonflée en zéro) au lieu des deux scores. Le modèle est bayésien, avec covariables, et appliqué à la Premier League 2006-07.
- **Résultat clé** : la Skellam est insensible à une corrélation positive commune entre les buts des deux équipes, ce qui la rend robuste.
- **Implication pratique pour nous** : c'est l'outil adapté aux marchés **handicap asiatique** et 1X2. Il ne convient pas aux marchés de total de buts, qui nécessitent les deux marges.
- **Vérif.** : [R]. Le DOI exact n'a pas été revérifié `[?]`, d'où le lien éditeur fourni.

#### [F6] Koopman & Lit (2015) : Poisson bivarié dynamique (espace d'états)
- **Référence** : Koopman, S. J., & Lit, R. (2015). *A dynamic bivariate Poisson model for analysing and forecasting match results in the English Premier League*. Journal of the Royal Statistical Society, Series A, 178(1), 167–186.
- **Lien** : https://doi.org/10.1111/rssa.12042
- **Résumé** : Poisson bivarié dont les intensités d'attaque et de défense suivent des processus stochastiques. Estimation par méthodes d'espace d'états et échantillonnage préférentiel. Prévisions hors échantillon sur les saisons 2010-11 et 2011-12 de Premier League.
- **Résultat clé** : les auteurs rapportent « un rendement positif significatif » face aux cotes des bookmakers, sur deux saisons.
- **Implication pratique pour nous** : c'est la version « propre » de la pondération temporelle de Dixon-Coles. Elle est plus lourde à estimer. On peut l'implémenter en option avancée, mais le gain par rapport à Dixon-Coles pondéré reste faible selon la revue de Hubáček et al. (2021, [F8]).
- **Vérif.** : [R]

#### [F7] Ley, Van de Wiele & Van Eetvelde (2019) : comparaison de 10 modèles de force
- **Référence** : Ley, C., Van de Wiele, T., & Van Eetvelde, H. (2019). *Ranking soccer teams on the basis of their current strength: A comparison of maximum likelihood approaches*. Statistical Modelling, 19(1), 55–73 `[?]` (volume et pages non revérifiés).
- **Lien** : https://doi.org/10.1177/1471082X18817650 (préprint arXiv:1705.09575)
- **Résumé** : Dix modèles sont comparés au RPS : Thurstone-Mosteller, Bradley-Terry, Poisson indépendant et Poisson bivarié. Ils sont estimés par maximum de vraisemblance pondéré, avec un poids d'importance du match et une **dépréciation temporelle** (demi-vie). La comparaison porte sur des championnats nationaux et des sélections.
- **Résultat clé** : les **Poisson bivarié et indépendant** sont les meilleurs au RPS.
- **Implication pratique pour nous** : c'est la confirmation empirique que les modèles de buts avec pondération temporelle sont un excellent socle. La demi-vie doit être optimisée, typiquement autour d'une saison selon les auteurs `[?]`.
- **Vérif.** : [R]

#### [F8] Hubáček, Šourek & Železný (2021) : quarante ans de modèles fondés sur les scores
- **Référence** : Hubáček, O., Šourek, G., & Železný, F. (2021). *Forty years of score-based soccer match outcome prediction: an experimental review*. IMA Journal of Management Mathematics, 33(1), 1–18.
- **Lien** : https://doi.org/10.1093/imaman/dpab029
- **Résumé** : Les auteurs réimplémentent et comparent sur la plus grande base de résultats disponible :
  - des modèles statistiques (Poisson, Weibull) ;
  - des classements génériques (Elo, Steph, Gaussian-OD) ;
  - des ratings spécifiques au football (Berrar, pi-ratings).
- **Résultat clé** : les meilleurs modèles ont des performances et des prédictions individuelles **très proches**. Les approches qui n'utilisent que les scores semblent avoir atteint un **plafond**.
- **Implication pratique pour nous** : inutile de multiplier les variantes de modèles de buts. Le gain est ailleurs : nouvelles **informations** (compositions, xG, blessures, marché) et **calibration**. Ce résultat est central pour prioriser le travail.
- **Vérif.** : [R]

#### [F9] Goddard (2005) : modèles « buts » contre modèles « résultats »
- **Référence** : Goddard, J. (2005). *Regression models for forecasting goals and match results in association football*. International Journal of Forecasting, 21(2), 331–340.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2004.08.002
- **Résumé** : Comparaison entre des modèles de Poisson bivarié sur les buts et des probit ordonnés sur le résultat (1X2), avec des covariables construites sur l'historique des buts ou des résultats, sur environ 25 saisons de football anglais `[S]`.
- **Résultat clé** : les écarts de performance prédictive entre les familles sont **faibles**. Le meilleur compromis est un modèle de résultat (probit ordonné) nourri de covariables construites sur les buts `[S]`.
- **Implication pratique pour nous** : le choix « modéliser les buts ou le résultat » est secondaire. Il faut surtout de bonnes variables. On peut garder les deux et les combiner.
- **Vérif.** : [S]. Le résumé n'a pas pu être consulté ; la conclusion est conforme à la manière dont l'article est cité dans la littérature.

#### [F10] Egidi, Pauli & Torelli (2018) : combiner historique et cotes dans un Poisson bayésien
- **Référence** : Egidi, L., Pauli, F., & Torelli, N. (2018). *Combining historical data and bookmakers' odds in modelling football scores*. Statistical Modelling, 18(5-6), 436–459.
- **Lien** : https://doi.org/10.1177/1471082X18798414 (arXiv:1802.08848)
- **Résumé** : Poisson hiérarchique bayésien dont les intensités sont une **combinaison convexe** de paramètres estimés sur l'historique et de l'information contenue dans les cotes. Le modèle est entraîné sur 9 saisons des grands championnats européens et prédit la 10e.
- **Résultat clé** : le mélange améliore l'ajustement et la prédiction par rapport à l'historique seul.
- **Implication pratique pour nous** : c'est une **brique clé**. Les cotes du marché, surtout celles d'un bookmaker « sharp », doivent être une **entrée** du modèle (prior ou variable), et non seulement une cible à battre.
- **Vérif.** : [R]

### 1.2 Systèmes de rating

#### [F11] Hvattum & Arntzen (2010) : Elo et logit ordonné
- **Référence** : Hvattum, L. M., & Arntzen, H. (2010). *Using ELO ratings for match result prediction in association football*. International Journal of Forecasting, 26(3), 460–470.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2009.10.002 (RePEc : https://ideas.repec.org/a/eee/intfor/v26yi3p460-470.html)
- **Résumé** : La différence d'Elo sert de covariable dans un logit ordonné (1X2). Le modèle est comparé à six méthodes de référence, avec des mesures statistiques (perte) et économiques (pari), sur environ 15 saisons de football anglais `[S]`.
- **Résultat clé** : l'Elo bat toutes les références **sauf les deux qui utilisent les cotes du marché**, qui restent significativement meilleures. Les stratégies de pari fondées sur l'Elo ne sont pas rentables.
- **Implication pratique pour nous** : l'Elo est une excellente variable, peu coûteuse, mais **insuffisante seule** pour battre le marché. On l'utilise comme variable d'entrée et comme baseline.
- **Vérif.** : [R]. Le DOI est déduit de la référence RePEc `[?]`.

#### [F12] Constantinou & Fenton (2013) : pi-ratings
- **Référence** : Constantinou, A. C., & Fenton, N. E. (2013). *Determining the level of ability of football teams by dynamic ratings based on the relative discrepancies in scores between adversaries*. Journal of Quantitative Analysis in Sports, 9(1), 37–50.
- **Lien** : https://doi.org/10.1515/jqas-2012-0036 (PDF auteur : http://www.constantinou.info/downloads/papers/pi-ratings.pdf ; package R `piratings`)
- **Résumé** : Rating dynamique avec une note domicile et une note extérieur par équipe. Mise à jour par l'écart entre la différence de buts attendue et observée, avec un rendement décroissant des gros écarts (une victoire compte plus qu'un but de plus). Deux taux d'apprentissage : λ et γ.
- **Résultat clé** : il surpasse les ratings Elo. Il génère « un certain profit » contre les cotes publiées sur **cinq saisons de Premier League**.
- **Implication pratique pour nous** : c'est la **meilleure variable de rating** documentée pour le ML football. Elle a été reprise comme variable principale par Yeung et al. (CatBoost, challenge 2023, [F21]). À implémenter tôt. Le profit annoncé, sur un échantillon modeste, n'est pas une preuve de rentabilité actuelle.
- **Vérif.** : [R], via la notice et le package R. Le PDF auteur n'était pas accessible (erreur 503).

#### [F13] Constantinou, Fenton & Neil (2012, 2013) : réseaux bayésiens (pi-football)
- **Références** :
  - Constantinou, A. C., Fenton, N. E., & Neil, M. (2012). *pi-football: A Bayesian network model for forecasting Association Football match outcomes*. Knowledge-Based Systems, 36, 322–339. https://doi.org/10.1016/j.knosys.2012.07.008
  - Constantinou, A. C., Fenton, N. E., & Neil, M. (2013). *Profiting from an inefficient association football gambling market: Prediction, risk and uncertainty using Bayesian networks*. Knowledge-Based Systems, 50, 60–86. https://doi.org/10.1016/j.knosys.2013.05.008
- **Résumé** : Réseau bayésien combinant données objectives et **informations subjectives d'experts** (blessures, motivation, fatigue). Les prévisions de la saison de Premier League 2011-12 ont été **publiées en ligne avant chaque match**, ce qui en fait une vraie prévision hors échantillon.
- **Résultat clé** : profits contre les cotes publiées, avec différentes stratégies à mise unitaire. Le modèle 2013, plus simple, est « encore plus rentable » que celui de 2012. L'échantillon reste d'une saison (380 matchs).
- **Implication pratique pour nous** : publier les prévisions **avant** les matchs (horodatage) est une excellente pratique de crédibilité, à reproduire dans la bibliothèque. L'intégration de facteurs subjectifs est intéressante mais difficile à industrialiser.
- **Vérif.** : [R]

#### [F14] Wunderlich & Memmert (2018) : Elo nourri par les cotes
- **Référence** : Wunderlich, F., & Memmert, D. (2018). *The betting odds rating system: Using soccer forecasts to forecast soccer*. PLoS ONE, 13(6), e0198668.
- **Lien** : https://doi.org/10.1371/journal.pone.0198668
- **Résumé** : Elo dont la mise à jour utilise l'écart entre cotes et résultats plutôt que le seul résultat. L'étude porte sur environ 15 000 matchs de 2007-08 à 2016-17 : Premier League, Bundesliga, Liga, Serie A, Ligue des champions et Ligue Europa.
- **Résultat clé** : l'Elo fondé sur les cotes **surpasse les Elo classiques**. Les cotes d'avant-match contiennent plus d'information pertinente que le résultat du match lui-même.
- **Implication pratique pour nous** : il faut construire des ratings « market-implied » (forces d'équipes déduites des cotes de clôture). C'est une variable très puissante et peu coûteuse.
- **Vérif.** : [R]

#### [F15] Robberechts & Davis (2019) : ratings résultats contre buts (Coupe du monde)
- **Référence** : Robberechts, P., & Davis, J. (2019). *Forecasting the FIFA World Cup – Combining result- and goal-based team ability parameters*. In *Machine Learning and Data Mining for Sports Analytics (MLSA 2018)*, LNCS 11330, Springer, 16–30 `[?]` (pages selon la source).
- **Lien** : https://doi.org/10.1007/978-3-030-17274-9_2 (PDF : https://people.cs.kuleuven.be/~pieter.robberechts/repo/robberechts-mlsa18-forecasting_worldcup.pdf)
- **Résumé** : Comparaison entre un Elo (fondé sur les résultats) et un ODM *Offense-Defense Model* (fondé sur les buts), utilisés comme covariables dans un logit ordonné ou un Poisson bivarié. Évaluation sur les Coupes du monde 2002 à 2014.
- **Résultat clé** : un **logit ordonné avec l'Elo comme seule covariable** est le meilleur.
- **Implication pratique pour nous** : pour les sélections nationales (peu de matchs, adversaires hétérogènes), il faut un modèle **parcimonieux** de type Elo plus logit ordonné. Les modèles riches surapprennent.
- **Vérif.** : [R], via la notice. Le détail n'a pas été lu `[?]`.

#### [F16] Holmes & McHale (2024) : modèle fondé sur les notes des joueurs
- **Référence** : Holmes, B., & McHale, I. G. (2024). *Forecasting football match results using a player rating based model*. International Journal of Forecasting, 40(1), 302–312.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2023.03.002
- **Résumé** : La force d'une équipe est agrégée à partir des notes des **joueurs alignés**. Les changements d'effectif et de composition entrent donc directement dans le modèle. Le modèle est comparé aux prédictions des bookmakers et testé avec une stratégie de type Kelly sur le marché 1X2.
- **Résultat clé** : « rendements de pari positifs significatifs » selon les auteurs. Les chiffres précis n'ont pas été consultés `[?]`.
- **Implication pratique pour nous** : l'information **compositions** (XI probable, absents) est l'une des pistes les plus crédibles pour trouver un avantage informationnel. Elle confirme que le plafond des modèles fondés sur les scores ([F8]) se dépasse en ajoutant de l'information au niveau des joueurs.
- **Vérif.** : [R], via la notice IDEAS/Liverpool. Les chiffres sont à vérifier.

### 1.3 Apprentissage automatique et compétitions de prédiction

#### [F17] Dubitzky, Lopes, Davis & Berrar (2019) : base ouverte et Soccer Prediction Challenge 2017
- **Référence** : Dubitzky, W., Lopes, P., Davis, J., & Berrar, D. (2019). *The Open International Soccer Database for machine learning*. Machine Learning, 108(1), 9–28.
- **Lien** : https://doi.org/10.1007/s10994-018-5726-0
- **Résumé** : Base ouverte de plus de 200 000 résultats, 52 championnats et environ 35 pays `[S]`. Elle sert de support au **2017 Soccer Prediction Challenge** : prédire en probabilités 1X2, avec le RPS comme métrique, des matchs futurs à partir des seuls scores et dates.
- **Résultat clé** : elle fournit un protocole de référence. Les RPS gagnants se situent autour de 0,206 ([F18]).
- **Implication pratique pour nous** : c'est un **jeu de données de référence** pour tester nos modèles de buts et de ratings et se comparer à la littérature, avec le même RPS et le même protocole.
- **Vérif.** : [R] pour les métadonnées. Les comptes exacts sont de seconde main `[S]`.

#### [F18] Hubáček, Šourek & Železný (2019a) : gradient boosting relationnel (vainqueur 2017)
- **Référence** : Hubáček, O., Šourek, G., & Železný, F. (2019). *Learning to predict soccer results from relational data with gradient boosted trees*. Machine Learning, 108(1), 29–47.
- **Lien** : https://doi.org/10.1007/s10994-018-5704-6
- **Résumé** : Variables construites à la main (ratings, forme, statistiques historiques), ainsi que des approches relationnelles et PageRank, combinées dans des gradient boosted trees (XGBoost).
- **Résultat clé** : **RPS = 0,2063** sur le jeu de test du challenge, soit la première place. Dans environ 30 % des matchs, le nul était l'issue la moins probable, ce qui viole l'hypothèse de monotonie implicite du RPS.
- **Implication pratique pour nous** : un pipeline « bonnes variables + GBM » est l'état de l'art pratique quand on n'a que les scores. Il faut prévoir des variables de rating (Elo, pi, Berrar) et de forme.
- **Vérif.** : [R]

#### [F19] Berrar, Lopes & Dubitzky (2019) : connaissances métier en ML
- **Référence** : Berrar, D., Lopes, P., & Dubitzky, W. (2019). *Incorporating domain knowledge in machine learning for soccer outcome prediction*. Machine Learning, 108(1), 97–126.
- **Lien** : https://doi.org/10.1007/s10994-018-5747-8
- **Résumé** : Deux méthodes d'ingénierie de variables : *recency feature extraction* et *rating feature learning* (les « Berrar ratings »). Elles sont utilisées avec k-NN et XGBoost.
- **Résultat clé** : leur k-NN sur les ratings appris figure parmi les meilleurs modèles du challenge 2017, hors compétition officielle car les auteurs étaient les organisateurs `[?]`. Le RPS est d'environ 0,2054 selon certaines sources, chiffre non vérifié `[?]`.
- **Implication pratique pour nous** : l'**ingénierie des variables guidée par le domaine** compte plus que l'algorithme. Un k-NN bien nourri rivalise avec un GBM.
- **Vérif.** : [R]. Le chiffre de RPS n'est pas confirmé.

#### [F20] Berrar, Lopes & Dubitzky (2024) : Soccer Prediction Challenge 2023
- **Référence** : Berrar, D., Lopes, P., & Dubitzky, W. (2024). *A data- and knowledge-driven framework for developing machine learning models to predict soccer match outcomes*. Machine Learning, 113(10), 8165–8204.
- **Lien** : https://doi.org/10.1007/s10994-024-06625-9
- **Résumé** : Le **2023 Soccer Prediction Challenge** porte sur 736 matchs futurs et comporte deux tâches : score exact, et probabilités 1X2. Les auteurs utilisent k-NN, réseaux de neurones, Bayes naïf et forêts ordinales, sur des séries temporelles interdépendantes d'équipes adverses.
- **Résultat clé** : leurs modèles k-NN et réseaux de neurones obtiennent les meilleures performances. Message principal : des algorithmes **relativement simples** font remarquablement bien, et la clé est l'intégration des connaissances du domaine.
- **Implication pratique pour nous** : c'est la même leçon qu'en 2017 ([F18], [F19]). Les variables comptent plus que la complexité. Il ne faut pas investir d'emblée dans le deep learning.
- **Vérif.** : [R]

#### [F21] Yeung, Bunker, Umemoto & Fujii (2024) : CatBoost et pi-ratings face au deep learning
- **Référence** : Yeung, C., Bunker, R., Umemoto, R., & Fujii, K. (2024). *Evaluating soccer match prediction models: a deep learning approach and feature optimization for gradient-boosted trees*. Machine Learning, 113, 4709–4728 `[?]` (pages).
- **Lien** : https://doi.org/10.1007/s10994-024-06608-w (arXiv:2309.14807)
- **Résumé** : CatBoost avec les **pi-ratings** comme variables, comparé à des modèles de deep learning. Entraînement sur les 5 dernières saisons, recherche d'hyperparamètres sur trois jeux de validation.
- **Résultat clé** : bonne stabilité en validation par rapport aux modèles publiés du challenge 2017. Au challenge 2023, le modèle obtient un **RPS de 0,2195, au 16e rang**. L'écart entre bons modèles est minime, et le RPS du jeu de test dépend fortement de la période.
- **Implication pratique pour nous** : CatBoost + pi-ratings est une **baseline ML solide et simple**. Les RPS ne sont comparables qu'à **jeu de test identique**.
- **Vérif.** : [R]. Les pages sont à confirmer.

#### [F22] Baboota & Kaur (2019) : ML sur la Premier League
- **Référence** : Baboota, R., & Kaur, H. (2019). *Predictive analysis and modelling football results using machine learning approach for English Premier League*. International Journal of Forecasting, 35(2), 741–755.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2018.01.003
- **Résumé** : Ingénierie de variables (ratings issus de FIFA, forme, buts, tirs, etc.) et modèles SVM, random forest et gradient boosting. Test sur les journées 6 à 38 des saisons 2014-15 et 2015-16.
- **Résultat clé** : le meilleur modèle, en gradient boosting, obtient un **RPS de 0,2156**, contre **0,2012** pour Bet365 et Pinnacle sur la même période. **Le modèle ne bat pas les bookmakers.**
- **Implication pratique pour nous** : c'est un ordre de grandeur réaliste. Un modèle ML « public » reste nettement derrière le marché. Ce qui compte n'est pas de « battre le RPS des cotes », mais de trouver des **sous-ensembles** où le modèle apporte une information orthogonale ([F45]).
- **Vérif.** : [R]

#### [F23] Bunker & Thabtah (2019) : cadre méthodologique ML (SRP-CRISP-DM)
- **Référence** : Bunker, R. P., & Thabtah, F. (2019). *A machine learning framework for sport result prediction*. Applied Computing and Informatics, 15(1), 27–33.
- **Lien** : https://doi.org/10.1016/j.aci.2017.09.005
- **Résumé** : Revue critique des réseaux de neurones appliqués à la prédiction sportive, puis proposition d'un cadre en étapes : compréhension du domaine, préparation des données, extraction de variables, entraînement, évaluation, déploiement. Insistance sur la **validation respectant l'ordre temporel**.
- **Résultat clé** : c'est un cadre conceptuel, sans résultat chiffré central.
- **Implication pratique pour nous** : il sert de **gabarit de pipeline** pour la bibliothèque : découpage temporel strict, pas de validation croisée aléatoire sur des matchs.
- **Vérif.** : [R]

#### [F24] Bunker & Susnjak (2022) : revue du ML en sports collectifs
- **Référence** : Bunker, R., & Susnjak, T. (2022). *The application of machine learning techniques for predicting match results in team sport: A review*. Journal of Artificial Intelligence Research, 73, 1285–1322.
- **Lien** : https://doi.org/10.1613/jair.1.13509 `[?]` (préprint : https://arxiv.org/abs/1912.11762)
- **Résumé** : Revue systématique des études de ML pour prédire les résultats en sports collectifs : football, basket, football américain, hockey, rugby, etc.
- **Résultat clé** : beaucoup d'études ont de **petits échantillons**, utilisent des métriques inadaptées (précision plutôt que métriques probabilistes), et peu se comparent aux cotes.
- **Implication pratique pour nous** : la plupart des « 80 % de précision » publiés sont **non comparables ou surappris**. La bibliothèque doit imposer : métriques probabilistes, comparaison aux cotes, validation temporelle.
- **Vérif.** : [R] pour les métadonnées. Le DOI est à confirmer.

#### [F25] Wunderlich & Memmert (2021) : revue narrative de la prévision sportive
- **Référence** : Wunderlich, F., & Memmert, D. (2021). *Forecasting the outcomes of sports events: A review*. European Journal of Sport Science, 21(7), 944–957.
- **Lien** : https://doi.org/10.1080/17461391.2020.1793002
- **Résumé** : Revue des méthodes (ratings, modèles statistiques, ML, marchés, experts). Elle distingue les effets **systématiques** (force) et **non systématiques** (hasard) et discute l'impact des données plus riches.
- **Résultat clé** : les cotes de paris sont la référence la plus précise dans la plupart des sports étudiés.
- **Implication pratique pour nous** : c'est une bonne porte d'entrée bibliographique. Elle conforte l'usage des cotes comme benchmark et comme variable.
- **Vérif.** : [R]

### 1.4 Expected goals (xG) et statistiques de match

#### [F26] Wheatcroft (2021) : prédire les statistiques de match pour prédire le résultat
- **Référence** : Wheatcroft, E. (2021). *Forecasting football matches by predicting match statistics*. Journal of Sports Analytics, 7(2), 77–97.
- **Lien** : https://doi.org/10.3233/JSA-200462 (arXiv:2001.09097)
- **Résumé** : Si l'on connaissait à l'avance les statistiques du match (tirs, tirs cadrés, corners), on prédirait très bien le résultat. On prédit donc ces statistiques avant le match, avec les ratings GAP et BA (*Bivariate Attacking*).
- **Résultat clé** : les prévisions apportent de l'information **au-delà des cotes**. Un « profit de long terme et robuste » est démontré avec deux stratégies de pari, sur plusieurs ligues et saisons.
- **Implication pratique pour nous** : il faut utiliser les **tirs, tirs cadrés et corners** (données gratuites de type football-data.co.uk) plutôt que les seuls buts. C'est l'une des pistes les mieux documentées.
- **Vérif.** : [R] et [TI] partiel.

#### [F27] Mead, O'Hare & McMenemy (2023) : améliorer les modèles xG
- **Référence** : Mead, J., O'Hare, A., & McMenemy, P. (2023). *Expected goals in football: Improving model performance and demonstrating value*. PLoS ONE, 18(4), e0282295.
- **Lien** : https://doi.org/10.1371/journal.pone.0282295
- **Résumé** : Modèle xG par ML avec des variables nouvelles (qualité des joueurs et des équipes, effets psychologiques), comparé aux statistiques traditionnelles pour prédire les performances futures.
- **Résultat clé** : l'xG est un **meilleur prédicteur du succès futur** que les statistiques traditionnelles (buts, points). Leurs résultats dépassent ceux d'un leader industriel.
- **Implication pratique pour nous** : les modèles de force doivent intégrer **xG pour et contre**, par exemple via un Poisson ou un Dixon-Coles « sur xG », ou un mélange buts/xG. Point de vigilance : l'xG est désormais public, donc probablement déjà intégré aux cotes des bookmakers sharp.
- **Vérif.** : [R]

#### [F28] Brechot & Flepp (2020) : l'aléa des résultats et l'xG
- **Référence** : Brechot, M., & Flepp, R. (2020). *Dealing with randomness in match outcomes: How to rethink performance evaluation in European club football using expected goals*. Journal of Sports Economics, 21(4), 335–362.
- **Lien** : https://doi.org/10.1177/1527002519897962
- **Résumé** : Les décideurs jugent les équipes sur les résultats récents, très bruités. Les auteurs proposent un graphique fondé sur l'xG qui identifie les équipes dont la performance « réelle » s'écarte des résultats.
- **Résultat clé** : il existe des erreurs de jugement systématiques quand les résultats sont trompeurs. C'est une base conceptuelle pour exploiter la **surréaction aux résultats** ([F38]).
- **Implication pratique pour nous** : on peut créer une variable « écart points/xG » (chance ou malchance récente) pour détecter les équipes sur ou sous-cotées après des séries.
- **Vérif.** : [R]

### 1.5 Évaluer une prévision : métriques et lien avec la rentabilité

#### [F29] Constantinou & Fenton (2012) : le RPS comme règle de score
- **Référence** : Constantinou, A. C., & Fenton, N. E. (2012). *Solving the problem of inadequate scoring rules for assessing probabilistic football forecast models*. Journal of Quantitative Analysis in Sports, 8(1).
- **Lien** : https://doi.org/10.1515/1559-0410.1418
- **Résumé** : Les règles de score usuelles ignorent l'**ordre** des issues (domicile > nul > extérieur). Les auteurs proposent le **Ranked Probability Score** pour le 1X2.
- **Résultat clé** : le RPS est devenu le standard des compétitions de prédiction (challenges 2017 et 2023).
- **Implication pratique pour nous** : on reporte toujours le RPS, pour être comparable à la littérature, **mais pas seul** (voir [F30]).
- **Vérif.** : [R]

#### [F30] Wheatcroft (2021) : contre le RPS
- **Référence** : Wheatcroft, E. (2021). *Evaluating probabilistic forecasts of football matches: the case against the ranked probability score*. Journal of Quantitative Analysis in Sports, 17(4), 273–287.
- **Lien** : https://doi.org/10.1515/jqas-2019-0089 (arXiv:1908.08980)
- **Résumé** : Deux expériences de simulation comparent le RPS (non local, sensible à la distance), le Brier (non local) et l'**Ignorance score**, c'est-à-dire la log-loss (local).
- **Résultat clé** : l'**Ignorance score (log-loss) surpasse le RPS et le Brier** pour identifier le meilleur modèle. La « sensibilité à la distance » n'apporte rien.
- **Implication pratique pour nous** : la **métrique principale de sélection** de modèles doit être la **log-loss**. Le RPS et le Brier sont reportés en complément. Il faut aussi des courbes de **calibration** ([F32]).
- **Vérif.** : [R]

#### [F31] Wunderlich & Memmert (2020) : le ROI n'est pas une mesure de précision
- **Référence** : Wunderlich, F., & Memmert, D. (2020). *Are betting returns a useful measure of accuracy in (sports) forecasting?* International Journal of Forecasting, 36(2), 713–722.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2019.08.009
- **Résumé** : Par la théorie, la simulation et des données réelles de trois sports, les auteurs montrent qu'on peut obtenir des **rendements positifs sans meilleure précision**, systématiquement ou par hasard.
- **Résultat clé** : le ROI mesure la rentabilité, **pas** la qualité du modèle. Les deux doivent être évalués séparément.
- **Implication pratique pour nous** : un backtest rentable ne valide pas un modèle. Il faut exiger : (1) une meilleure log-loss que le marché sur le sous-ensemble parié, ou (2) un CLV positif, et (3) un test statistique du ROI ([section 6](#6-pièges-méthodologiques)).
- **Vérif.** : [R]

#### [F32] Walsh & Joshi (2024) : calibration plutôt que précision pour sélectionner le modèle
- **Référence** : Walsh, C., & Joshi, A. (2024). *Machine learning for sports betting: Should model selection be based on accuracy or calibration?* Machine Learning with Applications, 16, 100539.
- **Lien** : https://doi.org/10.1016/j.mlwa.2024.100539 (arXiv:2303.06021)
- **Résumé** : Modèles entraînés sur plusieurs saisons NBA, expériences de pari sur **une seule saison**, avec des cotes publiées (de clôture). Sélection des modèles par précision ou par calibration (ECE).
- **Résultat clé** : sélectionner par calibration donne un **ROI moyen de +34,69 %, contre −35,17 %** pour la sélection par précision. Dans le meilleur cas : +36,93 % contre +5,56 %. **Attention** : une seule saison, mises de type Kelly, et ROI irréalistes sur un marché NBA efficient. Le **sens** du résultat est robuste, l'**ampleur** ne l'est pas.
- **Implication pratique pour nous** : sélectionner les modèles par **log-loss et calibration** (ECE, diagrammes de fiabilité), jamais par précision. Un Kelly sur un modèle mal calibré est ruineux.
- **Vérif.** : [R] et [TI] partiel.

---

## 2. Football : efficience des marchés, conversion des cotes, stratégies publiées

### 2.1 Les cotes comme prévisions (le benchmark à battre)

#### [F33] Forrest, Goddard & Simmons (2005) : les bookmakers, des prévisionnistes de plus en plus forts
- **Référence** : Forrest, D., Goddard, J., & Simmons, R. (2005). *Odds-setters as forecasters: The case of English football*. International Journal of Forecasting, 21(3), 551–564.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2005.03.003
- **Résumé** : Environ 10 000 matchs anglais. On compare les prévisions implicites des cotes à un modèle statistique riche (probit ordonné de type Goddard).
- **Résultat clé** : les cotes deviennent **de plus en plus efficaces** sur la période de 5 ans. Le modèle, même rééchantillonné (bootstrap), **ne surpasse pas** les experts, et ce progrès coïncide avec l'intensification de la concurrence.
- **Implication pratique pour nous** : les vieux résultats de « profits » (années 1990) sont **périmés**. Il faut toujours tester sur des données récentes.
- **Vérif.** : [R]

#### [F34] Spann & Skiera (2009) : marchés prédictifs, cotes et pronostiqueurs
- **Référence** : Spann, M., & Skiera, B. (2009). *Sports forecasting: a comparison of the forecast accuracy of prediction markets, betting odds and tipsters*. Journal of Forecasting, 28(1), 55–72.
- **Lien** : https://doi.org/10.1002/for.1091
- **Résumé** : Trois saisons de Bundesliga, soit 678 à 837 matchs selon la comparaison. Les auteurs comparent marchés prédictifs, cotes et « tipsters » (pronostiqueurs de presse).
- **Résultat clé** : marchés prédictifs et cotes sont **aussi précis** l'un que l'autre, et **nettement meilleurs que les pronostiqueurs**. Une combinaison par règles améliore sensiblement la précision.
- **Implication pratique pour nous** : les **pronostics d'experts ou tipsters** ne sont **pas** une source fiable. Si l'on combine des sources, il faut le faire statistiquement, par empilement (stacking) ou moyenne pondérée.
- **Vérif.** : [R], via la notice. Les chiffres viennent du résumé.

#### [F35] Štrumbelj & Robnik-Šikonja (2010) : toutes les cotes ne se valent pas
- **Référence** : Štrumbelj, E., & Robnik-Šikonja, M. (2010). *Online bookmakers' odds as forecasts: The case of European soccer leagues*. International Journal of Forecasting, 26(3), 482–488.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2009.10.005
- **Résumé** : 10 699 matchs de six grands championnats et les cotes de 10 bookmakers en ligne.
- **Résultat clé** :
  - certains bookmakers sont des prévisionnistes **meilleurs** que d'autres ;
  - la précision des cotes **augmente dans le temps** ;
  - elle varie selon les championnats.
- **Implication pratique pour nous** : comme référence de « vraie probabilité », il faut utiliser le bookmaker le plus précis, en pratique Pinnacle ou un consensus de marché ([F37]), et **pas** un book « soft ». C'est aussi pour cela que les écarts entre books sont exploitables ([F37], [F43]).
- **Vérif.** : [R], via le résumé de seconde main (RePEc). Les chiffres viennent de la notice.

#### [F36] Franck, Verbeek & Nüesch (2010) : l'exchange plus précis que les bookmakers
- **Référence** : Franck, E., Verbeek, E., & Nüesch, S. (2010). *Prediction accuracy of different market structures — bookmakers versus a betting exchange*. International Journal of Forecasting, 26(3), 448–459.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2010.01.004
- **Résumé** : 5 478 matchs des cinq grands championnats (dont la Ligue 1) sur trois saisons. Comparaison entre Betfair (exchange) et les bookmakers.
- **Résultat clé** : l'**exchange est plus précis**. Une stratégie simple qui choisit les paris où le bookmaker propose une cote **supérieure** à celle de l'exchange donne des rendements supérieurs à la moyenne, et **parfois positifs**.
- **Implication pratique pour nous** : c'est la base théorique du **« value betting par référence »**. On parie chez un book « soft » quand sa cote dépasse la cote juste d'un marché plus efficient (exchange ou Pinnacle). C'est **la stratégie la mieux documentée** ([F37]). En France l'exchange est interdit, mais ses cotes (ou celles de Pinnacle) restent consultables comme **référence**.
- **Vérif.** : [R], via la notice.

### 2.2 Inefficiences documentées et stratégies publiées

#### [F37] Kaunitz, Zhong & Kreiner (2017) : battre les bookmakers avec leurs propres cotes
- **Référence** : Kaunitz, L., Zhong, S., & Kreiner, J. (2017). *Beating the bookies with their own numbers – and how the online sports betting market is rigged*. arXiv:1710.02824 (non publié en revue).
- **Lien** : https://arxiv.org/abs/1710.02824 (code : https://github.com/Lisandro79/BeatTheBookie)
- **Résumé** : On calcule une probabilité « consensus » à partir de la **moyenne des cotes** de nombreux bookmakers (32 dans l'étude), corrigée d'une marge α (0,034 domicile, 0,057 nul, 0,037 extérieur). On parie lorsque la meilleure cote disponible excède la cote consensus ajustée (α = 0,05).
- **Résultat clé** :
  - **Simulation sur 10 ans aux cotes de clôture** : 56 435 paris, précision 44,4 %, **ROI +3,5 %**. Une stratégie aléatoire donne −3,32 %, soit 10,8 écarts-types d'écart.
  - **Simulation avec cotes 1 à 5 h avant le match** : 6 994 paris, **ROI +9,9 %**.
  - **Paper trading** sur 3 mois : 407 paris, ROI +5,5 %.
  - **Argent réel** sur 5 mois : 265 paris de 50 $, **ROI +8,5 %** (+957,50 $). Cumul 672 paris : +6,2 %.
  - Environ **30 % des cotes affichées avaient déjà bougé** au moment de miser.
  - Quelques mois après le début des paris réels, **limitation sévère des comptes** : mises plafonnées, « inspection manuelle », refus. L'expérience a dû être arrêtée.
- **Implication pratique pour nous** : c'est **la stratégie la plus robuste de la littérature** (value betting contre le consensus du marché). Elle est implémentable sans modèle sportif. Ses deux limites sont **l'exécution** (latence, cotes qui bougent) et **la limitation des comptes**, ce qui est critique chez les opérateurs français ([section 6](#6-pièges-méthodologiques)).
- **Vérif.** : [TI] (PDF lu).

#### [F38] Wheatcroft (2020a) : surréaction des cotes aux séries de résultats
- **Référence** : Wheatcroft, E. (2020). *Profiting from overreaction in soccer betting odds*. Journal of Quantitative Analysis in Sports, 16(3), 193–209.
- **Lien** : https://doi.org/10.1515/jqas-2019-0009
- **Résumé** : La statistique **COD** (*Combined Odds Distribution*) mesure la performance d'une équipe par rapport aux attentes implicites de ses cotes sur les matchs précédents. Données de **20 championnats sur 12 saisons**.
- **Résultat clé** : les équipes au COD faible (qui ont sous-performé leurs cotes) reçoivent des cotes **trop généreuses**. Selon l'auteur, c'est exploitable avec un **profit soutenu et robuste**. L'explication avancée est la **« hot hand fallacy »**.
- **Implication pratique pour nous** : c'est une stratégie **« contrarian »** simple à implémenter : parier sur les équipes qui ont récemment déçu par rapport aux attentes du marché. On la combine avec la variable « chance/malchance xG » ([F28]). **Attention** : Winkelmann et al. (2024, [F48]) montrent que beaucoup d'inefficiences ne persistent pas. Il faut un test hors échantillon récent.
- **Vérif.** : [R]

#### [F39] Wheatcroft (2020b) : un modèle rentable sur le marché over/under 2,5
- **Référence** : Wheatcroft, E. (2020). *A profitable model for predicting the over/under market in football*. International Journal of Forecasting, 36(3), 916–932.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2019.11.001
- **Résumé** : Ratings **GAP** (*Generalised Attacking Performance*) d'attaque et de défense, alimentés par les tirs, tirs cadrés et corners. Prévisions sur 10 championnats européens, avec deux stratégies de value betting.
- **Résultat clé** : utiliser tirs et corners (sans les buts) donne une meilleure valeur prédictive que les buts. **Profit moyen d'environ +0,8 % par pari sur 12 ans**, robuste face à une stratégie aléatoire.
- **Implication pratique pour nous** : le marché des **totaux de buts** est une cible crédible. L'edge est **minuscule** (0,8 %) et disparaît probablement avec les marges françaises : sur un TRJ de 85 à 93 %, la marge sur l'over/under dépasse souvent 5 %. C'est à tester avec les meilleures cotes disponibles uniquement.
- **Vérif.** : [R]

#### [F40] Wilkens (2026) : modèle xG simple et calibré sur la Bundesliga
- **Référence** : Wilkens, S. (2026). *Can simple models predict football — and beat the odds? Lessons from the German Bundesliga*. Journal of Sports Analytics (en ligne 2026).
- **Lien** : https://doi.org/10.1177/22150218261416681
- **Résumé** : xG récents → probabilités 1X2 via une **loi de Skellam**, avec **calibration par régression isotone**. Évaluation sur 11 saisons de Bundesliga (2014-15 à 2024-25).
- **Résultat clé** :
  - les cotes sont **mieux calibrées** que le modèle ;
  - le modèle capte pourtant des signaux absents des prix ;
  - en simulation, **ROI ≈ +10 %** aux cotes moyennes et **≈ +15 %** aux meilleures cotes ;
  - les profits viennent surtout des **victoires à domicile**, et les paris « extérieur » perdent systématiquement ;
  - la rentabilité varie fortement selon les saisons.
- **Implication pratique pour nous** : c'est une recette **simple et reproductible** (xG → Skellam → calibration isotone → seuil de value). À reproduire en priorité sur la Ligue 1 et les autres ligues. Les ROI à deux chiffres d'une simulation sur une seule ligue sont **suspects d'optimisme** (choix du modèle, cotes moyennes de clôture) : il faut un test strictement hors échantillon et le CLV.
- **Vérif.** : [R]

#### [F41] Direr (2013) : parier sur les très gros favoris
- **Référence** : Direr, A. (2013). *Are betting markets efficient? Evidence from European Football Championships*. Applied Economics, 45(3), 343–356.
- **Lien** : https://doi.org/10.1080/00036846.2011.602010
- **Résumé** : Cotes de 12 bookmakers sur 21 championnats européens, sur 11 ans.
- **Résultat clé** : choisir systématiquement les cotes **inférieures à un seuil**, c'est-à-dire les favoris dont la probabilité de victoire dépasse **90 %**, rapporte **+4,45 %** aux meilleures cotes et **+2,78 %** aux cotes moyennes. Le résultat est robuste aux données en temps réel et à différentes sous-périodes.
- **Implication pratique pour nous** : c'est l'illustration directe du **biais favori-outsider** ([section 7](#7-biais-comportementaux-exploitables)). Les gros favoris sont « moins mal » payés que les outsiders. C'est une stratégie à faible variance mais rare (peu de matchs). À retester sur données récentes et avec les marges françaises.
- **Vérif.** : [R]

#### [F42] Vlastakis, Dotsis & Markellos (2009) : arbitrages et stratégies simples en Europe
- **Référence** : Vlastakis, N., Dotsis, G., & Markellos, R. N. (2009). *How efficient is the European football betting market? Evidence from arbitrage and trading strategies*. Journal of Forecasting, 28(5), 426–444.
- **Lien** : https://doi.org/10.1002/for.1085
- **Résumé** : Cotes de 6 grands bookmakers sur les championnats européens. Les auteurs testent les paris combinés entre books (arbitrage), des règles heuristiques, des régressions et des tests d'englobement des prévisions.
- **Résultat clé** : arbitrages entre bookmakers **rares mais rémunérateurs**. Présence d'un **FLB**. Stratégies gagnantes sur les **très gros favoris, surtout à l'extérieur**.
- **Implication pratique pour nous** : c'est cohérent avec [F41]. Les gros favoris, notamment extérieurs, sont le segment le moins défavorable. L'arbitrage pur entre books français existe mais déclenche vite les limitations.
- **Vérif.** : [R], via la notice. Les chiffres détaillés n'ont pas été lus `[?]`.

#### [F43] Franck, Verbeek & Nüesch (2013) : arbitrage bookmaker contre exchange
- **Référence** : Franck, E., Verbeek, E., & Nüesch, S. (2013). *Inter-market arbitrage in betting*. Economica, 80(318), 300–325.
- **Lien** : https://doi.org/10.1111/ecca.12009
- **Résumé** : On combine un pari chez un bookmaker et une position inverse sur l'exchange.
- **Résultat clé** : arbitrage à **gain garanti dans 19,2 % des matchs** des cinq grands championnats. **Tous** les bookmakers étudiés offrent fréquemment des arbitrages, avec des marges moyennes **négatives** sur ces cotes. Les bookmakers fixent leurs prix en tenant compte du **comportement futur de leurs clients**, et non comme des market makers neutres.
- **Implication pratique pour nous** : les bookmakers « soft » proposent **sciemment** des cotes au-dessus de la valeur juste pour attirer une clientèle qu'ils comptent profiler. C'est ce qui rend possible le value betting… et la limitation des gagnants.
- **Vérif.** : [R], via la notice.

#### [F44] Angelini & De Angelis (2019) : efficience de 11 championnats européens
- **Référence** : Angelini, G., & De Angelis, L. (2019). *Efficiency of online football betting markets*. International Journal of Forecasting, 35(2), 712–721.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2018.07.008
- **Résumé** : Test d'efficience fondé sur les prévisions. Les données couvrent les cotes de **41 bookmakers**, sur **11 championnats** et **11 saisons**.
- **Résultat clé** : en sélectionnant **les meilleures cotes** entre bookmakers, **8 marchés sont efficients** et 3 présentent des inefficiences. D'après les sources secondaires consultées, il s'agirait de la Serie A italienne, de la Primeira Liga portugaise et de la Super League grecque `[S]`. Seules certaines de ces inefficiences seraient exploitables par les parieurs. L'approche permet d'estimer des **seuils de cote** rentables ex ante.
- **Implication pratique pour nous** : les grands championnats, dont la Ligue 1 dans la plupart des études, sont **globalement efficients aux meilleures cotes**. Les inefficiences sont **locales** (certaines ligues, certaines plages de cotes) et **instables**.
- **Vérif.** : [R]. La liste exacte des ligues est de seconde main `[S]`.

#### [F45] Hubáček & Šír (2023) : battre le marché avec un « mauvais » modèle
- **Référence** : Hubáček, O., & Šír, G. (2023). *Beating the market with a bad predictive model*. International Journal of Forecasting, 39(2), 691–719 `[?]` (pages).
- **Lien** : https://doi.org/10.1016/j.ijforecast.2022.02.001 (arXiv:2010.12508)
- **Résumé** : Les auteurs démontrent qu'on peut faire des profits systématiques avec un modèle **moins précis** que le marché, si on l'entraîne à être **décorrélé** des prix du bookmaker. On exploite ainsi des biais discrets et l'avantage structurel du **preneur de prix** (*market taker*), qui choisit ses paris. Les liens avec Kelly et l'optimisation de portefeuille sont discutés.
- **Résultat clé** : c'est une preuve théorique, illustrée sur des données réelles d'actions et de paris sportifs. Avec Kelly « pur », il faut un modèle meilleur que le marché. Avec d'autres stratégies, ce n'est pas nécessaire.
- **Implication pratique pour nous** : il faut ajouter à l'objectif d'entraînement un **terme de décorrélation** avec les probabilités implicites, ou au minimum mesurer la corrélation des erreurs. Les profits viennent des **désaccords informés** avec le marché, pas de la précision moyenne.
- **Vérif.** : [R] et [TI] partiel. Les pages sont à confirmer.

#### [F46] Goddard & Asimakopoulos (2004) : probit ordonné et paris de fin de saison
- **Référence** : Goddard, J., & Asimakopoulos, I. (2004). *Forecasting football results and the efficiency of fixed-odds betting*. Journal of Forecasting, 23(1), 51–66.
- **Lien** : https://doi.org/10.1002/for.877
- **Résumé** : Probit ordonné estimé sur 10 ans de football anglais. Les variables : résultats passés, **enjeu du match** pour le classement final, participation aux coupes et **distance géographique** entre les clubs.
- **Résultat clé** : l'efficience faible est testée. Une stratégie qui sélectionne les **paris de fin de saison** à espérance favorable selon le modèle semble pouvoir générer un **rendement positif**.
- **Implication pratique pour nous** : les variables **contextuelles** (enjeu, motivation, calendrier, coupe d'Europe, déplacement) apportent de l'information. Les fins de saison, avec des équipes sans enjeu, sont une niche à étudier. C'est un ancien résultat, à retester.
- **Vérif.** : [R], via la notice.

### 2.3 Efficience : tests, chocs d'information, in-play

#### [F47] Elaad, Reade & Singleton (2020) : cotes non biaisées, bookmakers individuellement inefficients
- **Référence** : Elaad, G., Reade, J. J., & Singleton, C. (2020). *Information, prices and efficiency in an online betting market*. Finance Research Letters, 35, 101291.
- **Lien** : https://doi.org/10.1016/j.frl.2019.09.006
- **Résumé** : Cotes de **51 bookmakers** sur plus de **16 000 matchs** anglais depuis 2010.
- **Résultat clé** : les cotes ne sont **globalement pas biaisées**, ni en FLB ni par type d'issue. En revanche, **chaque bookmaker individuellement n'est pas efficient** : ses cotes n'intègrent pas toute l'information contenue dans les cotes de ses **concurrents**.
- **Implication pratique pour nous** : c'est le fondement empirique du value betting « par consensus » ([F37]). On compare **chaque book français** au consensus ou à Pinnacle.
- **Vérif.** : [R]

#### [F48] Winkelmann, Ötting, Deutscher & Makarewicz (2024) : les inefficiences ne persistent pas
- **Référence** : Winkelmann, D., Ötting, M., Deutscher, C., & Makarewicz, T. (2024). *Are betting markets inefficient? Evidence from simulations and real data*. Journal of Sports Economics, 25(1), 54–97.
- **Lien** : https://doi.org/10.1177/15270025231204997
- **Résumé** : Des simulations montrent :
  - l'effet des petits échantillons sur la détection d'inefficiences ;
  - la fréquence de **périodes « inefficientes » au sein de marchés parfaitement efficients**.
  Une analyse empirique porte sur **14 saisons** de championnats de football.
- **Résultat clé** : des inefficiences apparaissent sur des saisons isolées mais **ne sont ni persistantes ni systématiques** entre ligues. Des effets significatifs sur une saison sont **attendus même sous efficience totale**.
- **Implication pratique pour nous** : c'est **la référence méthodologique clé**. Toute « anomalie » détectée sur 1 ou 2 saisons doit être considérée comme **probablement du bruit** tant qu'elle n'est pas répliquée hors échantillon sur plusieurs saisons et ligues, avec correction pour tests multiples.
- **Vérif.** : [R]

#### [F49] Hegarty & Whelan (2025) : structure de marché, bookmakers « sharp » et « soft »
- **Référence** : Hegarty, T., & Whelan, K. (2025). *Market structure and prices in online betting markets: Theory and evidence*. Working paper, University College Dublin (version révisée d'août 2025, à paraître selon les auteurs dans *Oxford Economic Papers* `[?]`).
- **Lien** : https://www.karlwhelan.com/Papers/OEP.pdf
- **Résumé** : Dans un modèle où les parieurs sont en désaccord mais en moyenne corrects, la demande sur les outsiders est **moins élastique** aux cotes. Un marché **imparfaitement concurrentiel**, celui des bookmakers « soft » européens, produit donc un FLB, alors qu'un marché concurrentiel, celui des « sharp » comme Pinnacle sur le handicap asiatique, n'en produit pas. Les données couvrent plus de 150 000 matchs européens (football-data.co.uk), dont 84 230 avec des cotes de handicap asiatique, et 55 998 matchs de tennis ATP/WTA de 2011 à 2022.
- **Résultat clé** :
  - sur le 1X2 aux cotes moyennes, **FLB marqué** : les pertes augmentent fortement quand la probabilité baisse ;
  - sur le **handicap asiatique**, les taux de perte sont **à peu près constants** d'un décile à l'autre, donc pas de FLB ;
  - en tennis, le FLB est **beaucoup plus faible chez Pinnacle**, sauf pour le décile le plus bas.
  - Les auteurs décrivent aussi le modèle « soft » : marges élevées, marketing, et **limitation ou exclusion des gagnants**, avec des références à Grant et al. 2018 et à Davies 2022.
- **Implication pratique pour nous** : Pinnacle et le handicap asiatique fournissent la **meilleure référence de probabilité**. Chez les books « soft », dont les opérateurs ANJ, les outsiders sont structurellement les plus surtaxés : il faut **éviter les outsiders** sauf edge démontré.
- **Vérif.** : [TI]. Le statut de publication est à confirmer.

#### [F50] Whelan (2024) : aversion au risque et FLB en cotes fixes
- **Référence** : Whelan, K. (2024). *Risk aversion and favourite–longshot bias in a competitive fixed-odds betting market*. Economica, 91(361), 188–209 `[?]` (pages).
- **Lien** : https://doi.org/10.1111/ecca.12500
- **Résumé** : Les explications classiques du FLB, issues du pari mutuel, ne s'appliquent pas aux cotes fixes. L'article montre que le **désaccord entre parieurs** et l'**aversion au risque des bookmakers** peuvent produire un FLB même en concurrence.
- **Résultat clé** : c'est un résultat théorique, cohérent avec les profils empiriques de FLB.
- **Implication pratique pour nous** : le FLB est **structurel** et non une anomalie passagère. Il faut toujours débiaiser les cotes (méthode de Shin ou méthode « power ») avant de les comparer à nos probabilités ([F57]–[F59]).
- **Vérif.** : [R]. Les pages sont à confirmer.

#### [F51] Winkelmann, Deutscher & Ötting (2021) : l'avantage du terrain disparu (COVID, Bundesliga)
- **Référence** : Winkelmann, D., Deutscher, C., & Ötting, M. (2021). *Bookmakers' mispricing of the disappeared home advantage in the German Bundesliga after the COVID-19 break*. Applied Economics, 53(26), 3054–3064.
- **Lien** : https://doi.org/10.1080/00036846.2021.1873234 (arXiv:2008.05417)
- **Résumé** : Après la reprise à huis clos en 2020, l'avantage du terrain s'érode, et les bookmakers tardent à ajuster leurs cotes.
- **Résultat clé** : ces difficultés d'ajustement ouvrent des opportunités de **stratégies rentables** (parier « extérieur ») pendant la période de transition.
- **Implication pratique pour nous** : les **chocs structurels** (huis clos, changement de règles, nouvelle compétition, promu atypique) créent des fenêtres d'inefficience **temporaires**. Le marché finit par s'adapter.
- **Vérif.** : [R]

#### [F52] Meier, Flepp & Franck (2021) : efficience semi-forte et matchs à huis clos
- **Référence** : Meier, P. F., Flepp, R., & Franck, E. (2021). *Are sports betting markets semi-strong efficient? Evidence from the COVID-19 pandemic*. International Journal of Sport Finance, 16(3), 111–126.
- **Lien** : https://doi.org/10.32731/IJSF.163.082021.01
- **Résumé** : Les matchs à huis clos des grands championnats européens servent de test d'information publique « propre ».
- **Résultat clé** : bookmakers **et** exchanges ont **surestimé** les chances de l'équipe à domicile au début des huis clos. L'effet est surtout porté par la Bundesliga, première ligue à reprendre. Une stratégie est rentable sur **un peu plus d'un mois**.
- **Implication pratique pour nous** : même conclusion que [F51]. Il y a un avantage au **réactif**, de courte durée. Il faut un module de « détection de rupture » (*change-point*) sur l'avantage du terrain et les tendances de buts.
- **Vérif.** : [R]

#### [F53] Bernardo, Ruberti & Verona (2019) : changement d'entraîneur sous-estimé
- **Référence** : Bernardo, G., Ruberti, M., & Verona, R. (2019). *Semi-strong inefficiency in the fixed odds betting market: Underestimating the positive impact of head coach replacement in the main European soccer leagues*. The Quarterly Review of Economics and Finance, 71, 239–246.
- **Lien** : https://doi.org/10.1016/j.qref.2018.08.007
- **Résumé** : Dans les quatre grands championnats européens, l'effet moyen d'un changement d'entraîneur sur la performance est positif. Une stratégie de pari est comparée à une distribution de Monte Carlo.
- **Résultat clé** : les cotes n'absorbent pas entièrement l'effet « nouvel entraîneur », ce qui indique une inefficience semi-forte.
- **Implication pratique pour nous** : la variable « changement d'entraîneur récent » est un candidat. Elle est cohérente avec la surréaction aux mauvaises séries ([F38]), car l'entraîneur est souvent limogé après une série négative. Une étude brésilienne de 2025 (Galdino, Soebbing & Wicker, *IJSF*) trouve des effets similaires sur certains matchs suivant le changement `[R]`.
- **Vérif.** : [R]

#### [F54] Croxson & Reade (2014) : les buts sont intégrés vite et complètement en direct
- **Référence** : Croxson, K., & Reade, J. J. (2014). *Information and efficiency: Goal arrival in soccer betting*. The Economic Journal, 124(575), 62–91.
- **Lien** : https://doi.org/10.1111/ecoj.12033
- **Résumé** : Les auteurs étudient les buts marqués juste avant la mi-temps, sur un exchange, pour tester l'efficience.
- **Résultat clé** : les prix se mettent à jour **rapidement et complètement**. L'information en cours de match est intégrée de façon efficiente.
- **Implication pratique pour nous** : le **pari en direct sur l'information publique** (un but vient d'être marqué) n'offre pas d'avantage, sauf avantage de **latence**, que les opérateurs neutralisent par des délais et des suspensions.
- **Vérif.** : [R], via les notices RePEc et ResearchGate.

#### [F55] Ötting, Deutscher, Singleton & De Angelis (2022) : parier sur le « momentum »
- **Référence** : Ötting, M., Deutscher, C., Singleton, C., & De Angelis, L. (2022). *Gambling on momentum*. arXiv:2211.06052 (document de travail ; publication ultérieure non vérifiée `[?]`).
- **Lien** : https://arxiv.org/abs/2211.06052
- **Résumé** : Données haute fréquence d'un grand bookmaker (cotes et montants misés) sur la Bundesliga en direct, après des buts égalisateurs.
- **Résultat clé** : les parieurs misent **environ 40 % de plus** sur l'équipe qui vient d'égaliser (« momentum »). Pourtant, ce momentum ne prédit pas le résultat, et parier dessus entraîne des **pertes substantielles**.
- **Implication pratique pour nous** : le « momentum » perçu en direct est un **biais du public**, pas un signal. Si on l'utilise, ce doit être **à contre-courant**, avec prudence.
- **Vérif.** : [R]

#### [F56] Lezana (2026) : « peur du nul » et heuristiques
- **Référence** : Lezana, B. (2026). *Fear of the draw, consumption and mistaken heuristics: Profit opportunities in the football betting market*. Journal of Sports Economics (en ligne 2026).
- **Lien** : https://doi.org/10.1177/15270025261438385
- **Résumé** : Premier League. Processus de Markov et logit ordonné pour estimer les probabilités, puis comparaison aux cotes.
- **Résultat clé** : rendements anormaux, **surtout sur les nuls et les victoires extérieures**, ce qui est attribué à des biais émotionnels et heuristiques (les parieurs évitent le nul).
- **Implication pratique pour nous** : c'est la piste du **biais contre le nul** ([section 7](#7-biais-comportementaux-exploitables)), sur une seule ligue. **À répliquer** avant usage.
- **Vérif.** : [R]

### 2.4 Convertir des cotes en probabilités (retirer la marge)

#### [F57] Shin (1991, 1993) : le modèle d'initiés
- **Référence** : Shin, H. S. (1993). *Measuring the incidence of insider trading in a market for state-contingent claims*. The Economic Journal, 103(420), 1141–1153. Voir aussi Shin, H. S. (1991). *Optimal betting odds against insider traders*. The Economic Journal, 101(408), 1179–1185.
- **Lien** : https://doi.org/10.2307/2234240
- **Résumé** : Le bookmaker fixe ses cotes en sachant qu'une fraction *z* des mises provient d'**initiés**. La marge est donc répartie de façon non proportionnelle : plus lourde sur les outsiders. Le modèle fournit un estimateur des probabilités « vraies » et de *z*.
- **Résultat clé** : c'est un fondement théorique du FLB côté offre.
- **Implication pratique pour nous** : la **méthode de Shin** est l'une des méthodes de dé-margination à implémenter (paquets `shin` en Python, `implied` en R).
- **Vérif.** : [R] pour les métadonnées.

#### [F58] Štrumbelj (2014) : Shin bat la normalisation
- **Référence** : Štrumbelj, E. (2014). *On determining probability forecasts from betting odds*. International Journal of Forecasting, 30(4), 934–943.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2014.02.008
- **Résumé** : Comparaison de la normalisation simple (proportionnelle), de modèles de régression et de la méthode de Shin pour extraire les probabilités des cotes.
- **Résultat clé** : les probabilités de **Shin** sont **plus précises** (RPS) que la normalisation et la régression.
- **Implication pratique pour nous** : par défaut, il faut éviter la normalisation multiplicative naïve.
- **Vérif.** : [R], via la notice. Les chiffres détaillés n'ont pas été lus.

#### [F59] Clarke, Kovalchik & Ingram (2017) : méthodes additive, multiplicative, Shin et « power »
- **Référence** : Clarke, S., Kovalchik, S., & Ingram, M. (2017). *Adjusting bookmaker's odds to allow for overround*. American Journal of Sports Science, 5(6), 45–49.
- **Lien** : https://doi.org/10.11648/j.ajss.20170506.12
- **Résumé** : Les défauts de chaque méthode :
  - l'additive peut donner des probabilités négatives ;
  - la normalisation ignore le FLB ;
  - Shin et la normalisation peuvent donner des probabilités supérieures à 1 lorsqu'on les applique « à l'envers ».
  La **méthode « power »** (probabilités implicites élevées à une puissance *k*) n'a pas ces défauts. Shin et l'additive sont **équivalentes à deux issues**. Trois grands jeux de données de trois sports sont utilisés.
- **Résultat clé** : la méthode **power bat universellement la multiplicative** et égale ou bat Shin.
- **Implication pratique pour nous** : on implémente **power et Shin**, et on choisit par log-loss sur nos données. En tennis (2 issues), Shin = additive.
- **Vérif.** : [R]

#### [F60] Koning & Zijm (2023) : Shin contre normalisation, au niveau du match
- **Référence** : Koning, R. H., & Zijm, R. (2023). *Betting market efficiency and prediction in binary choice models*. Annals of Operations Research, 325, 135–148.
- **Lien** : https://doi.org/10.1007/s10479-022-04722-3
- **Résumé** : Nouvelle méthode de comparaison au niveau du match (et non par classes de probabilités), qui permet un FLB résiduel et des variables spécifiques au match.
- **Résultat clé** : en **Premier League**, Shin donne des probabilités **non biaisées**. En **Liga**, les deux méthodes souffrent d'un **biais des favoris** : les favoris gagnent plus souvent que prévu.
- **Implication pratique pour nous** : le biais résiduel **varie selon les ligues**. Il faut calibrer la dé-margination **par ligue**, par exemple avec une régression isotone ou logistique sur les probabilités dé-marginées.
- **Vérif.** : [R]

#### [F61] Hegarty & Whelan (2024) : comment tester l'efficience
- **Référence** : Hegarty, T., & Whelan, K. (2024). *Comparing two methods for testing the efficiency of sports betting markets*. Sports Economics Review, 100042.
- **Lien** : https://doi.org/10.1016/j.serev.2024.100042
- **Résumé** : Deux méthodes de régression sont comparées : résultats sur les probabilités normalisées, et résultats sur l'inverse des cotes. Données de tennis et de football, plus des simulations.
- **Résultat clé** : la méthode des **probabilités normalisées** donne de bons tests. La méthode de l'**inverse des cotes** est **biaisée contre la détection du FLB**.
- **Implication pratique pour nous** : pour nos tests de biais, on régresse sur les **probabilités normalisées**.
- **Vérif.** : [R]

### 2.5 Compléments : modèles récents

#### [F62] Groll, Ley, Schauberger & Van Eetvelde (2019) : forêt aléatoire hybride (tournois)
- **Référence** : Groll, A., Ley, C., Schauberger, G., & Van Eetvelde, H. (2019). *A hybrid random forest to predict soccer matches in international tournaments*. Journal of Quantitative Analysis in Sports, 15(4), 271–287.
- **Lien** : https://doi.org/10.1515/jqas-2018-0060
- **Résumé** : Une forêt aléatoire sur des covariables d'équipes (marché des joueurs, classement FIFA, etc.) est enrichie d'un **paramètre de force estimé par Poisson** comme covariable. Évaluation sur les Coupes du monde 2002 à 2014, puis validation sur les 64 matchs de 2018.
- **Résultat clé** : l'hybride améliore nettement chaque brique. Sur 2018, il **bat toutes les méthodes y compris les cotes**, mais sur **64 matchs seulement**, un échantillon trop petit pour conclure.
- **Implication pratique pour nous** : la recette « **force estimée (Poisson ou Elo) comme variable d'un modèle ML** » est confirmée. Il faut se méfier des victoires sur les cotes obtenues sur de petits échantillons.
- **Vérif.** : [R]

#### [F63] Fischer & Heuer (2024) : ML contre Poisson
- **Référence** : Fischer, M., & Heuer, A. (2024). *Match predictions in soccer: Machine learning vs. Poisson approaches*. arXiv:2408.08331.
- **Lien** : https://arxiv.org/abs/2408.08331
- **Résumé** : Réseaux de neurones et forêts aléatoires sont comparés aux modèles de Poisson, sur 5 grands championnats européens.
- **Résultat clé** : le niveau des équipes ne varie pas systématiquement au cours d'une saison. Le **choix des variables et du modèle n'a qu'une influence mineure** sur la qualité de prédiction.
- **Implication pratique pour nous** : c'est cohérent avec [F8] et [F20]. Le plafond des approches fondées sur les résultats est atteint, et le gain doit venir de **nouvelles informations**.
- **Vérif.** : [R]

---

## 3. Tennis

Le tennis est un sport à **deux issues**, sans nul. On distingue deux grandes familles de modèles :
- les modèles « **point-based** » : on estime la probabilité de gagner un point au service, puis on la propage dans la structure jeu/set/match ;
- les modèles de **résultat direct** : Elo, Bradley-Terry, régressions, apprentissage automatique.

Le marché est **très liquide** sur les grands tournois. Il présente un **biais favori-outsider (FLB) robuste** chez les bookmakers grand public, et ce biais est plus faible chez Pinnacle.

#### [T1] Klaassen & Magnus (2001) : les points sont-ils i.i.d. ?
- **Référence** : Klaassen, F. J. G. M., & Magnus, J. R. (2001). *Are points in tennis independent and identically distributed? Evidence from a dynamic binary panel data model*. Journal of the American Statistical Association, 96(454), 500–509.
- **Lien** : https://doi.org/10.1198/016214501753168217
- **Résumé** : Étude de 86 298 points (481 matchs) de Wimbledon 1992 à 1995.
  - Gagner le point précédent augmente légèrement la probabilité de gagner le suivant.
  - Sur les points « importants », le serveur gagne un peu moins souvent.
- **Résultat clé** : l'hypothèse i.i.d. est **rejetée**, mais les **écarts sont faibles**. L'i.i.d. reste une **bonne approximation** dans beaucoup de cas.
- **Implication pratique pour nous** : on peut construire les modèles point-based sous hypothèse i.i.d., ce qui simplifie énormément les calculs pour les marchés jeux, sets, tie-break et handicap de jeux. Les effets de « momentum » sont faibles.
- **Vérif.** : [R] (résumé via IDEAS/RePEc).

#### [T2] Klaassen & Magnus (2003) : prévoir le vainqueur avant et pendant le match
- **Référence** : Klaassen, F. J. G. M., & Magnus, J. R. (2003). *Forecasting the winner of a tennis match*. European Journal of Operational Research, 148(2), 257–267.
- **Lien** : https://doi.org/10.1016/S0377-2217(02)00682-3 (le DOI est à confirmer `[?]` ; voir aussi https://ideas.repec.org/a/eee/ejores/v148y2003i2p257-267.html)
- **Résumé** : Les probabilités de gagner un point au service sont estimées à partir des classements et des données de Wimbledon. Elles sont propagées point par point par le programme TENNISPROB pour prévoir le vainqueur **avant et pendant** le match.
- **Résultat clé** : c'est le cadre de référence des modèles « in-play » au tennis.
- **Implication pratique pour nous** : ce cadre convient aux marchés **en direct** et aux marchés dérivés (nombre de jeux et de sets). Easton & Uylangco ([T3]) montrent toutefois que le marché le suit de très près.
- **Vérif.** : [R]

#### [T3] Easton & Uylangco (2010) : le marché in-play colle au modèle point par point
- **Référence** : Easton, S., & Uylangco, K. (2010). *Forecasting outcomes in tennis matches using within-match betting markets*. International Journal of Forecasting, 26(3), 564–575.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2009.10.004
- **Résumé** : Comparaison point par point entre le modèle de Klaassen-Magnus et les probabilités implicites des cotes en direct, pour les hommes et les femmes.
- **Résultat clé** :
  - **corrélation extrêmement élevée** entre modèle et marché, donc un **haut niveau d'efficience** ;
  - le marché anticipe un break **jusqu'à quatre points** avant la fin du jeu ;
  - **seule anomalie** : la tendance des joueurs à perdre plus de points que prévu juste après avoir concédé un break n'est pas intégrée instantanément dans les cotes.
- **Implication pratique pour nous** : le live tennis sur information publique est quasi efficient. L'anomalie « après un break concédé » est une **niche étroite**, probablement arbitrée depuis 2010, et inexploitable chez les opérateurs français à cause des délais de prise de pari.
- **Vérif.** : [R]

#### [T4] Barnett & Clarke (2005) : combiner les statistiques des joueurs
- **Référence** : Barnett, T., & Clarke, S. R. (2005). *Combining player statistics to predict outcomes of tennis matches*. IMA Journal of Management Mathematics, 16(2), 113–120.
- **Lien** : https://doi.org/10.1093/imaman/dpi001
- **Résumé** : Les statistiques ATP de service et de retour de chaque joueur sont combinées, en tenant compte de la moyenne du circuit, pour prédire les pourcentages de points gagnés au service dans un face-à-face donné. Ces pourcentages alimentent ensuite un modèle de Markov qui donne la probabilité de victoire et la durée du match, mise à jour en cours de partie.
- **Résultat clé** : c'est une méthode de référence (formule « Barnett-Clarke »), illustrée sur le match Roddick contre El Aynaoui (Open d'Australie 2003).
- **Implication pratique pour nous** : la formule de combinaison service/retour est **la brique de base** d'un modèle point-based. Kovalchik (2016, [T6]) montre cependant que les modèles point-based seuls sont moins bien calibrés que l'Elo.
- **Vérif.** : [R]

#### [T5] McHale & Morton (2011) : modèle de Bradley-Terry pour l'ATP
- **Référence** : McHale, I., & Morton, A. (2011). *A Bradley-Terry type model for forecasting tennis match results*. International Journal of Forecasting, 27(2), 619–630.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2010.04.004
- **Résumé** : Modèle de Bradley-Terry qui tient compte des résultats passés, de la surface et d'une pondération temporelle. Il est mis à jour chaque semaine et comparé à deux logit fondés sur le classement officiel et sur les points ATP.
- **Résultat clé** : il est **supérieur** sur les **cinq** critères évalués, dont **deux liés aux rendements de pari**.
- **Implication pratique pour nous** : un modèle de comparaison par paires, dépendant de la surface et pondéré dans le temps, est une base solide. Le classement ATP seul est insuffisant.
- **Vérif.** : [R]

#### [T6] Kovalchik (2016) : à la recherche du « GOAT » de la prédiction au tennis
- **Référence** : Kovalchik, S. A. (2016). *Searching for the GOAT of tennis win prediction*. Journal of Quantitative Analysis in Sports, 12(3), 127–138.
- **Lien** : https://doi.org/10.1515/jqas-2015-0059 (PDF : https://vuir.vu.edu.au/34652/)
- **Résumé** : 11 modèles publiés (régressions, point-based, comparaisons par paires) sont testés sur **2 395 matchs ATP de 2014**. Les bookmakers servent de référence via le modèle de consensus BCM.
- **Résultat clé** :
  - précision des modèles de **59 % à 72 %** ;
  - **le consensus des bookmakers (BCM) est le meilleur** : 72 % de précision et **log-loss la plus basse** ;
  - l'**Elo FiveThirtyEight** suit avec 70 % de précision, et 75 % sur les matchs entre joueurs les mieux classés, ce qui est compétitif avec les bookmakers ;
  - Elo et régressions sur le classement ont une log-loss d'environ **0,60** ;
  - les modèles point-based et Bradley-Terry sont **surconfiants et mal calibrés** : ils prévoient trop de surprises, avec un ratio de calibration de 0,80 pour Bradley-Terry ;
  - tous les modèles perdent 10 à 20 points de précision sur les joueurs moins bien classés.
- **Implication pratique pour nous** : la **baseline tennis doit être un Elo de type FiveThirtyEight**, dont le facteur K décroît avec le nombre de matchs, et qui est spécifique à la surface. Il faut mesurer **log-loss et calibration**. Les petits tournois (Challenger, ITF) sont plus difficiles à prédire mais probablement moins efficients, ce qui reste à tester.
- **Vérif.** : [TI] (PDF lu).

#### [T7] Kovalchik (2020) : Elo avec marge de victoire
- **Référence** : Kovalchik, S. (2020). *Extension of the Elo rating system to margin of victory*. International Journal of Forecasting, 36(4), 1329–1341.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2020.01.006
- **Résumé** : Quatre variantes d'un Elo avec marge de victoire (MOV) : linéaire, additive jointe, multiplicative et logistique. Elles sont appliquées au tennis masculin avec plusieurs définitions de la marge.
- **Résultat clé** : **toutes** les variantes MOV fondées sur les statistiques intra-set **améliorent** l'Elo standard. Seul le modèle **additif joint** donne des ratings non biaisés et de variance stable en simulation.
- **Implication pratique pour nous** : il faut intégrer la marge, c'est-à-dire les **jeux gagnés** et pas seulement la victoire, dans l'Elo tennis, en commençant par la variante additive jointe.
- **Vérif.** : [R]

#### [T8] Angelini, Candila & De Angelis (2022) : Weighted Elo (WElo)
- **Référence** : Angelini, G., Candila, V., & De Angelis, L. (2022). *Weighted Elo rating for tennis match predictions*. European Journal of Operational Research, 297(1), 120–132.
- **Lien** : https://doi.org/10.1016/j.ejor.2021.04.011 (package R `welo`)
- **Résumé** : La mise à jour Elo est pondérée par le **score du dernier match** (jeux ou sets gagnés). Données ATP de juillet 2005 à novembre 2020 (33 976 matchs après nettoyage) plus la WTA, soit plus de 60 000 matchs au total. La période **hors échantillon** va de 2012 à 2020. Le WElo est comparé à l'Elo, à Bradley-Terry et à d'autres modèles (tests de Diebold-Mariano).
- **Résultat clé** :
  - le WElo bat tous les concurrents en **Brier** et **log-loss** ;
  - stratégie de pari à 1 $ sur les **meilleures cotes parmi 11 bookmakers**, en excluant les outsiders (seuil q) : **ROI ≈ +3,56 %** chez les hommes et **+2,93 %** chez les femmes sur 2012-2020, contre **+1,31 %** pour l'Elo ;
  - **aux cotes moyennes ou aux seules cotes de Bet365, le ROI devient négatif.**
- **Implication pratique pour nous** : c'est un résultat **crucial pour un parieur français**. Le profit de ce type de modèle **dépend entièrement de la recherche de la meilleure cote** (*line shopping*) parmi de nombreux books. Avec 3 à 5 comptes ANJ, il faut s'attendre à un ROI ≤ 0. Le WElo reste une excellente variable. Il faut exclure les gros outsiders, à cause du FLB.
- **Vérif.** : [TI] (PDF lu).

#### [T9] Gorgi, Koopman & Lit (2019) : modèle dynamique de grande dimension
- **Référence** : Gorgi, P., Koopman, S. J., & Lit, R. (2019). *The analysis and forecasting of tennis matches by using a high dimensional dynamic model*. Journal of the Royal Statistical Society, Series A, 182(4), 1393–1415.
- **Lien** : https://doi.org/10.1111/rssa.12464
- **Résumé** : Les capacités de chaque joueur varient dans le temps **et selon la surface**. Le modèle couvre 17 ans de matchs et plus de 500 joueurs, soit plus de 2 000 niveaux de force dynamiques, avec peu de paramètres.
- **Résultat clé** : la variation temporelle **par surface** est essentielle. Le modèle **surpasse significativement** les modèles existants en prévision.
- **Implication pratique pour nous** : il faut des ratings **par surface** (dur, terre battue, gazon, indoor) avec partage d'information entre surfaces.
- **Vérif.** : [R]. Les pages sont à confirmer `[?]`.

#### [T10] Ingram (2019) : modèle bayésien hiérarchique point-based
- **Référence** : Ingram, M. (2019). *A point-based Bayesian hierarchical model to predict the outcome of tennis matches*. Journal of Quantitative Analysis in Sports, 15(4), 313–325.
- **Lien** : https://doi.org/10.1515/jqas-2018-0008
- **Résumé** : La probabilité de gagner un point au service dépend de la surface, du tournoi et de la date. Les compétences au service et au retour suivent une **marche aléatoire gaussienne**.
- **Résultat clé** : sur la saison ATP 2014, il **bat les autres modèles point-based** : **précision 68,8 % contre 66,3 %**, **log-loss 0,592 contre 0,641**. Il est compétitif avec les modèles qui prédisent directement le résultat.
- **Implication pratique pour nous** : c'est le meilleur compromis pour les **marchés dérivés** (jeux, sets, tie-breaks), qui exigent un modèle point-based. Implémentable en Stan ou PyMC.
- **Vérif.** : [R]

#### [T11] Sipko & Knottenbelt (2015) : ML pour le tennis professionnel
- **Référence** : Sipko, M. (2015). *Machine learning for the prediction of professional tennis matches*. MEng Computing final-year project, Imperial College London (superviseur W. Knottenbelt). Ce n'est **pas** une publication à comité de lecture.
- **Lien** : https://www.doc.ic.ac.uk/teaching/distinguished-projects/2015/m.sipko.pdf
- **Résumé** : 22 variables (dont fatigue et blessure), modèles de régression logistique et de réseau de neurones. Jeu de test de **6 315 matchs ATP en 2013-2014**, avec les cotes Pinnacle et Marathonbet.
- **Résultat clé** : le réseau de neurones obtient un **ROI de +4,35 %** contre le marché, soit environ 75 % de mieux que le modèle « Common-Opponent » de Knottenbelt.
- **Implication pratique pour nous** : c'est un résultat souvent cité mais **non évalué par des pairs**, avec une sélection d'hyperparamètres qui fait courir un risque de surapprentissage. Il faut le traiter comme une **hypothèse à répliquer**, pas comme une preuve.
- **Vérif.** : [TI] (PDF lu).

#### [T12] Lisi & Zanella (2017) : régression logistique et Grand Chelem
- **Référence** : Lisi, F., & Zanella, G. (2017). *Tennis betting: can statistics beat bookmakers?* Electronic Journal of Applied Statistical Analysis, 10(3), 790–808.
- **Lien** : https://doi.org/10.1285/i20705948v10n3p790
- **Résumé** : Régression logistique avec les points et le classement ATP, l'âge, le facteur domicile et l'information issue des cotes. Le modèle est estimé sur 2012, puis utilisé pour parier hors échantillon sur les **4 Grands Chelems 2013**, aux meilleures cotes.
- **Résultat clé** : **rendement cumulé +16,3 % après 501 matchs**. Les seuils de la procédure ont été **calibrés pour maximiser le rendement in-sample**, et le test ne couvre qu'une saison.
- **Implication pratique pour nous** : petit échantillon, une seule saison, seuils optimisés : c'est un exemple typique de résultat **fragile**. Des résumés secondaires citent des chiffres différents, ce qui montre l'importance de lire la source.
- **Vérif.** : [TI] (PDF lu).

#### [T13] Wilkens (2021) : le ML ne bat pas le marché au tennis
- **Référence** : Wilkens, S. (2021). *Sports prediction and betting models in the machine learning age: The case of tennis*. Journal of Sports Analytics, 7(2), 99–117.
- **Lien** : https://doi.org/10.3233/JSA-200463
- **Résumé** : C'est l'une des études ML les plus vastes sur le tennis masculin et féminin. Elle compare de nombreux algorithmes, des stratégies de gestion de mise variées, et des paris sur les favoris comme sur les outsiders.
- **Résultat clé** :
  - la précision moyenne **plafonne à environ 70 %** ;
  - **l'essentiel de l'information est déjà dans les cotes**, et ajouter des données de match ou de joueur n'apporte rien de significatif ;
  - les rendements sont **très volatils et majoritairement négatifs** à long terme ;
  - les **ensembles** de modèles sont l'option la plus prometteuse.
- **Implication pratique pour nous** : c'est **la référence de scepticisme** pour le tennis. Les marchés ATP et WTA principaux sont quasi efficients. Les pistes restantes sont les **ensembles**, les **tournois mineurs** et le **line shopping** ([T8]).
- **Vérif.** : [R]

#### [T14] Forrest & McHale (2007) : FLB positif dans tout l'éventail des cotes
- **Référence** : Forrest, D., & McHale, I. (2007). *Anyone for tennis (betting)?* The European Journal of Finance, 13(8), 751–768.
- **Lien** : https://doi.org/10.1080/13518470701705736
- **Résumé** : Grand jeu de données de matchs ATP et nouvelle approche économétrique de la relation entre rendement et cote.
- **Résultat clé** : **FLB positif sur toute la gamme des cotes** : plus la cote est élevée, plus le rendement espéré est mauvais. L'article discute les explications par les attitudes envers le risque et l'asymétrie (*skewness*).
- **Implication pratique pour nous** : au tennis, il faut **éviter les outsiders** sauf edge très fort. Les stratégies sur les favoris perdent moins, ce qui ne veut pas dire qu'elles gagnent.
- **Vérif.** : [R]

#### [T15] Abinzano, Muga & Santamaria (2016, 2019) : FLB sur l'exchange (Betfair)
- **Références** :
  - Abinzano, I., Muga, L., & Santamaria, R. (2016). *Game, set and match: the favourite-long shot bias in tennis betting exchanges*. Applied Economics Letters, 23(8), 605–608. https://doi.org/10.1080/13504851.2015.1093074
  - Abinzano, I., Muga, L., & Santamaria, R. (2019). *Hidden power of trading activity: The FLB in tennis betting exchanges*. Journal of Sports Economics, 20(2), 261–285. https://doi.org/10.1177/1527002517731875
- **Résumé** : Paris Betfair sur 28 595 matchs de simple de juin 2004 à juin 2013.
- **Résultat clé** :
  - FLB présent **même sur l'exchange**, sans bookmaker ;
  - le biais est plus fort entre joueurs mal classés, dans les tours avancés et dans les tournois médiatisés ;
  - l'erreur de prix augmente avec le **volume** et l'incertitude, et diminue avec la présence de **parieurs institutionnels**.
- **Implication pratique pour nous** : le FLB a aussi une origine **comportementale** (parieurs grand public), pas seulement la marge du bookmaker. Les matchs **très médiatisés**, où l'argent « récréatif » est abondant, sont ceux où les cotes s'écartent le plus de la juste valeur.
- **Vérif.** : [R] via notices et SSRN. Les chiffres viennent de la notice.

---

## 4. Autres sports : basket, football américain, baseball, hockey, rugby, handball, volley

### 4.1 Vue transversale

#### [S1] Lopez, Matthews & Baumer (2018) : quelle place pour le hasard selon les sports ?
- **Référence** : Lopez, M. J., Matthews, G. J., & Baumer, B. S. (2018). *How often does the best team win? A unified approach to understanding randomness in North American sport*. The Annals of Applied Statistics, 12(4), 2483–2516.
- **Lien** : https://doi.org/10.1214/18-AOAS1165 (arXiv:1701.05976)
- **Résumé** : Modèles bayésiens à espace d'états estimés **à partir des cotes** sur une décennie de NFL, NHL, NBA et MLB. Ils fournissent la force des équipes, leur variabilité entre saisons, au sein d'une saison et d'un match à l'autre, et l'avantage du terrain.
- **Résultat clé** : la **NBA** a la plus grande dispersion des talents et le plus fort avantage du terrain, donc le meilleur favori gagne le plus souvent. La **NHL et la MLB** sont les plus **aléatoires**.
- **Implication pratique pour nous** : la part d'aléa fixe le **plafond de précision** et la **variance** des stratégies. En NHL et MLB, il faut des échantillons beaucoup plus grands avant de conclure à un edge. Les cotes peuvent servir de source pour estimer les forces, comme dans [F14].
- **Vérif.** : [R]

#### [S2] Elo de FiveThirtyEight (NFL, NBA, tennis) : la référence des praticiens
- **Référence** : FiveThirtyEight (2014–2023). *How our NFL predictions work* / *How our NBA predictions work*. Pages de méthodologie, non évaluées par des pairs. Le code est publié sur GitHub (`fivethirtyeight/nfl-elo-game`). Le site a été fermé par ABC News en 2025 ; les pages restent accessibles via des archives `[?]`.
- **Lien** : https://fivethirtyeight.com/methodology/how-our-nfl-predictions-work/ ; https://github.com/fivethirtyeight/nfl-elo-game
- **Résumé** : Elo avec :
  - un facteur K d'environ 20 en NFL ;
  - un multiplicateur de marge de victoire, amorti pour les écarts larges ;
  - une régression vers la moyenne d'environ 1/3 entre deux saisons ;
  - des ajustements pour le quarterback titulaire, le déplacement et le repos.
- **Résultat clé** : c'est une baseline publique et transparente. En tennis, Kovalchik ([T6]) la classe parmi les meilleurs modèles hors marché.
- **Implication pratique pour nous** : c'est le **gabarit** d'un Elo multi-sports dans la bibliothèque : K, marge de victoire, retour vers la moyenne entre saisons, avantage du terrain, et ajustement des joueurs clés.
- **Vérif.** : [S], via des sources secondaires et le dépôt de code.

### 4.2 Basket (NBA, Euroleague)

#### [S3] Gandar, Dare, Brown & Zuber (1998) : parieurs informés et mouvements de ligne en NBA
- **Référence** : Gandar, J. M., Dare, W. H., Brown, C. R., & Zuber, R. A. (1998). *Informed traders and price variations in the betting market for professional basketball games*. The Journal of Finance, 53(1), 385–401.
- **Lien** : https://doi.org/10.1111/0022-1082.155346
- **Résumé** : Comparaison des spreads d'ouverture et de clôture en NBA.
- **Résultat clé** : les mouvements de ligne entre l'ouverture et la clôture **améliorent la précision**. La ligne de clôture est meilleure que l'ouverture, ce qui est compatible avec la présence de parieurs informés.
- **Implication pratique pour nous** : c'est le fondement académique du **CLV**. Battre la clôture revient à anticiper l'information des parieurs informés.
- **Vérif.** : [S]

#### [S4] Paul, Weinbach & Wilson (2004) : biais « under » sur les totaux NBA élevés
- **Référence** : Paul, R. J., Weinbach, A. P., & Wilson, M. (2004). *Efficient markets, fair bets, and profitability in NBA totals 1995–96 to 2001–02*. The Quarterly Review of Economics and Finance, 44(4), 624–632.
- **Lien** : https://doi.org/10.1016/S1062-9769(03)00033-4
- **Résumé** : Totaux de points NBA sur 7 saisons.
- **Résultat clé** : pour les **totaux élevés**, parier « under » gagne plus de 52,4 % des paris, seuil de rentabilité à −110. Le biais est attribué à la préférence du public pour l'« over ». Un commentaire publié en 2021 dans la même revue suggère que cette rentabilité **ne s'est pas maintenue** `[S]`.
- **Implication pratique pour nous** : le « biais over » du public sur les totaux est un **mécanisme plausible**, car le public aime voir des points et des buts. Mais l'**édge historique s'érode**. Il faut retester sur des données récentes, au basket comme au football.
- **Vérif.** : [S], via des sources secondaires.

#### [S5] Štrumbelj & Vračar (2012) : simulation markovienne d'un match de basket
- **Référence** : Štrumbelj, E., & Vračar, P. (2012). *Simulating a basketball match with a homogeneous Markov model and forecasting the outcome*. International Journal of Forecasting, 28(2), 532–542.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2011.01.004
- **Résumé** : Modèle de Markov par possession, estimé à partir des données play-by-play et des statistiques d'équipe. Il est comparé au logit, aux ratings et aux cotes des bookmakers.
- **Résultat clé** : le modèle est compétitif avec les autres approches statistiques, mais **les cotes des bookmakers restent meilleures** `[S]`.
- **Implication pratique pour nous** : la simulation par possession permet de dériver les marchés **totaux, handicaps et quart-temps**, mais elle n'apporte pas d'edge sur le vainqueur.
- **Vérif.** : [S]

#### [S6] Manner (2016) : modèle dynamique NBA et combinaison avec les cotes
- **Référence** : Manner, H. (2016). *Modeling and forecasting the outcomes of NBA basketball games*. Journal of Quantitative Analysis in Sports, 12(1), 31–41.
- **Lien** : https://doi.org/10.1515/jqas-2015-0088
- **Résumé** : Modèle de référence étendu avec hétéroscédasticité et forces d'équipes dynamiques (espace d'états). Prévisions sur de nombreux matchs de saison régulière et de playoffs.
- **Résultat clé** : il confirme qu'il est **difficile de battre le marché**. Une **combinaison** des prévisions du modèle avec les cotes apporte de **légères** améliorations.
- **Implication pratique pour nous** : en NBA, les modèles sont utiles en **combinaison** avec le marché, pas seuls.
- **Vérif.** : [R], via IDEAS/RePEc.

#### [S7] Hubáček, Šourek & Železný (2019b) : exploiter le marché NBA par le ML
- **Référence** : Hubáček, O., Šourek, G., & Železný, F. (2019). *Exploiting sports-betting market using machine learning*. International Journal of Forecasting, 35(2), 783–796.
- **Lien** : https://doi.org/10.1016/j.ijforecast.2019.01.001
- **Résumé** : Trois ingrédients :
  1. on entraîne le modèle en **réduisant sa corrélation avec les cotes**, en plus de maximiser sa précision ;
  2. un **réseau convolutif** exploite de nombreuses statistiques de joueurs ;
  3. la mise est allouée par **théorie moderne du portefeuille** (compromis espérance/variance).
- **Résultat clé** : **profits cumulés positifs** de manière systématique sur les saisons NBA **2007 à 2014**, contrairement aux méthodes alternatives testées.
- **Implication pratique pour nous** : c'est l'une des rares démonstrations sérieuses sur un marché majeur. Elle légitime le **terme de décorrélation** ([F45]) et l'allocation de portefeuille ([section 5](#5-théorie-du-pari-et-gestion-de-bankroll)). Les données sont anciennes (2007-2014) et les cotes ne sont pas forcément exécutables.
- **Vérif.** : [R]

### 4.3 Football américain (NFL)

#### [S8] Gandar, Zuber, O'Brien & Russo (1988) : rationalité du marché des spreads NFL
- **Référence** : Gandar, J., Zuber, R., O'Brien, T., & Russo, B. (1988). *Testing rationality in the point spread betting market*. The Journal of Finance, 43(4), 995–1008.
- **Lien** : https://doi.org/10.1111/j.1540-6261.1988.tb02617.x
- **Résumé** : Tests de rationalité du marché des spreads NFL, avec des règles de pari techniques et des stratégies fondées sur des probits.
- **Résultat clé** : profits **significatifs in-sample**, confirmés **en partie** hors échantillon `[S]`.
- **Implication pratique pour nous** : c'est un article fondateur, mais son résultat est ancien. Imbrogno & Staggs ([S12]) montrent que les règles historiques ne tiennent plus.
- **Vérif.** : [S]

#### [S9] Levitt (2004) : les bookmakers exploitent les biais au lieu d'équilibrer
- **Référence** : Levitt, S. D. (2004). *Why are gambling markets organised so differently from financial markets?* The Economic Journal, 114(495), 223–246.
- **Lien** : https://doi.org/10.1111/j.1468-0297.2004.00207.x
- **Résumé** : Données uniques d'environ **20 000 paris NFL** placés par **285 parieurs** lors d'un concours de pronostics à enjeux élevés (saison 2001). On observe à la fois les prix et les **quantités** misées.
- **Résultat clé** :
  - les bookmakers **ne cherchent pas à équilibrer** les mises : ils prédisent mieux que les parieurs et **fixent des prix biaisés** pour exploiter le penchant du public pour les **favoris** et, dans une moindre mesure, les équipes **à l'extérieur** ;
  - dans la partie médiane des matchs, environ 58 % des paris vont à l'équipe à domicile ;
  - dans le concours, les **outsiders à domicile couvrent le spread dans 57,7 % des cas** ;
  - sur 21 saisons (1980-2001, environ 5 000 matchs), les **favoris à l'extérieur** ne couvrent qu'à **46,7 %** ;
  - cette tarification augmente les marges brutes du bookmaker d'environ 20 à 30 %.
- **Implication pratique pour nous** : c'est le modèle mental à adopter. Les cotes des books grand public sont **biaisées dans le sens des préférences du public** : favoris, équipes populaires, « over ». La valeur se trouve **du côté impopulaire**, en particulier les outsiders à domicile dans les sports à handicap.
- **Vérif.** : [TI] (PDF lu).

#### [S10] Paul & Weinbach (2002) : biais « under » sur les totaux NFL élevés
- **Référence** : Paul, R. J., & Weinbach, A. P. (2002). *Market efficiency and a profitable betting rule: Evidence from totals on professional football*. Journal of Sports Economics, 3(3), 256–263.
- **Lien** : https://doi.org/10.1177/1527002502003003003
- **Résumé** : Totaux NFL de 1979 à 2000.
- **Résultat clé** : pour les totaux de **47,5 points ou plus**, parier « under » gagne **58,7 %** des paris, ce qui est significatif et au-dessus du seuil de 52,4 %. Les bookmakers fixeraient des totaux trop hauts pour exploiter le goût du public pour l'« over ».
- **Implication pratique pour nous** : même mécanisme que [S4]. Pour le football, il faut tester un éventuel « biais over » sur les matchs très médiatisés ou à fort total attendu.
- **Vérif.** : [S], via des sources secondaires.

#### [S11] Glickman & Stern (1998) : modèle à espace d'états pour la NFL
- **Référence** : Glickman, M. E., & Stern, H. S. (1998). *A state-space model for National Football League scores*. Journal of the American Statistical Association, 93(441), 25–35.
- **Lien** : https://doi.org/10.1080/01621459.1998.10474084 (PDF : https://www.glicko.net/research/nfl.pdf)
- **Résumé** : Les forces des équipes suivent un processus autorégressif d'ordre 1, avec une variation semaine à semaine et saison à saison. Le modèle est bayésien (MCMC) et estimé sur les données 1988-1993.
- **Résultat clé** : il est **aussi précis en moyenne que le spread de Las Vegas**, et légèrement meilleur sur un petit échantillon test (les 110 derniers matchs de 1993), ce qui ne permet pas de conclure.
- **Implication pratique pour nous** : c'est la référence des ratings dynamiques bayésiens, et la base du système Glicko.
- **Vérif.** : [S]

#### [S12] Boulier & Stekler (2003) et Song, Boulier & Stekler (2007) : marché contre experts contre modèles (NFL)
- **Références** :
  - Boulier, B. L., & Stekler, H. O. (2003). *Predicting the outcomes of National Football League games*. International Journal of Forecasting, 19(2), 257–270. https://doi.org/10.1016/S0169-2070(01)00144-3 `[?]`
  - Song, C., Boulier, B. L., & Stekler, H. O. (2007). *The comparative accuracy of judgmental and model forecasts of American football games*. International Journal of Forecasting, 23(3), 405–413. https://doi.org/10.1016/j.ijforecast.2007.05.003
- **Résumé** : Saisons NFL 1994 à 2000. Comparaison de probits sur les « power scores » du New York Times, d'un modèle naïf (l'équipe à domicile gagne), du marché des paris et de l'éditeur sportif du NYT.
- **Résultat clé** :
  - **le marché est le meilleur** (environ 66 % de bonnes prédictions) ;
  - les power scores suivent (environ 61 %) ;
  - l'**éditeur** (environ 60 %) fait **moins bien que le modèle naïf** `[S]`.
- **Implication pratique pour nous** : l'avis d'expert est sans valeur prédictive face au marché. Cela concorde avec Spann & Skiera ([F34]).
- **Vérif.** : [S]

#### [S13] Imbrogno & Staggs (2025) : les règles de pari NFL « rentables » ne tiennent pas
- **Référence** : Imbrogno, J., & Staggs, T. B. (2025). *Evaluating the efficiency of the National Football League betting market by testing the profitability of suggested gambling rules*. The Journal of Gambling Business and Economics, 17(1).
- **Lien** : https://doi.org/10.5750/jgbe.v17i1.2130
- **Résumé** : Six stratégies NFL publiées comme rentables dans la littérature des 40 dernières années sont retestées sur d'autres périodes.
- **Résultat clé** : **aucune** ne tient. Le marché est efficient vis-à-vis de ces situations, et les règles ne sont pas rentables à long terme.
- **Implication pratique pour nous** : c'est l'illustration parfaite du **biais de publication et de la dégradation des anomalies**. Toute règle « historique » doit être retestée hors période.
- **Vérif.** : [R]

### 4.4 Baseball (MLB)

#### [S14] Woodland & Woodland (1994) et Gandar et al. (2002) : FLB inversé en MLB… puis non confirmé
- **Références** :
  - Woodland, L. M., & Woodland, B. M. (1994). *Market efficiency and the favorite-longshot bias: The baseball betting market*. The Journal of Finance, 49(1), 269–279. https://doi.org/10.1111/j.1540-6261.1994.tb04429.x
  - Gandar, J. M., Zuber, R. A., Johnson, R. S., & Dare, W. (2002). *Re-examining the betting market on Major League Baseball games: is there a reverse favourite-longshot bias?* Applied Economics, 34(10), 1309–1317. https://doi.org/10.1080/00036840110095427
- **Résumé** : Woodland & Woodland trouvent un **FLB inversé** en MLB : les favoris sont surjoués et les outsiders légèrement sous-évalués. La réexamination de Gandar et al. **ne confirme pas** ce biais inversé.
- **Résultat clé** : la direction du biais **dépend du sport et du marché**. Les marchés américains « money line » ne présentent pas le FLB classique des books européens `[S]`.
- **Implication pratique pour nous** : il ne faut pas transposer mécaniquement « éviter les outsiders » d'un sport à l'autre. Le biais doit être **mesuré par sport, par marché et par bookmaker**.
- **Vérif.** : [S]

### 4.5 Hockey sur glace (NHL)

#### [S15] Woodland & Woodland (2001) : FLB inversé en NHL
- **Référence** : Woodland, L. M., & Woodland, B. M. (2001). *Market efficiency and profitable wagering in the National Hockey League: Can bettors score on longshots?* Southern Economic Journal, 67(4), 983–995.
- **Lien** : https://doi.org/10.2307/1061582
- **Résumé** : Conversion des money lines NHL en probabilités et comparaison avec les fréquences observées.
- **Résultat clé** : les outsiders gagnent **plus souvent** que ne l'impliquent les cotes (**FLB inversé**), ce qui laisse entrevoir des paris rentables sur les outsiders. Ce résultat a été contesté ensuite (Gandar et al., 2004) `[S]`.
- **Implication pratique pour nous** : en hockey, la tendance du public à surjouer les favoris peut rendre les outsiders intéressants. C'est à vérifier sur données récentes, avec l'aléa élevé de la NHL ([S1]).
- **Vérif.** : [S]

#### [S16] Buttrey (2016) : battre le marché NHL avec un modèle de Markov
- **Référence** : Buttrey, S. E. (2016). *Beating the market betting on NHL hockey games*. Journal of Quantitative Analysis in Sports, 12(2), 87–98.
- **Lien** : https://doi.org/10.1515/jqas-2015-0003
- **Résumé** : Combinaison d'un modèle de buts marqués et encaissés et d'un modèle de **pénalités** dans un calcul de type Markov et une simulation. On parie quand la probabilité du modèle diffère nettement de celle du marché.
- **Résultat clé** : **ROI positif et statistiquement significatif** selon l'auteur. Les chiffres et l'échantillon n'ont pas été vérifiés `[?]`.
- **Implication pratique pour nous** : les modèles **spécifiques au sport** (supériorité numérique, pénalités) peuvent capter de l'information que les ratings génériques ignorent. C'est une piste pour le hockey.
- **Vérif.** : [R], via la notice.

#### [S17] Weissbock & Inkpen (2014) : un plafond de précision d'environ 62 % en NHL
- **Référence** : Weissbock, J., & Inkpen, D. (2014). *Combining textual pre-game reports and statistical data for predicting success in the National Hockey League*. In *Advances in Artificial Intelligence (Canadian AI 2014)*, LNCS 8436, Springer, 251–262 `[?]`.
- **Lien** : https://doi.org/10.1007/978-3-319-06483-3_22 `[?]`
- **Résumé** : Les auteurs simulent des saisons NHL par Monte Carlo. La dispersion observée des pourcentages de victoires correspond à environ **24 % de compétence et 76 % de chance**. Ils en déduisent un plafond de précision d'environ 24 + 76/2 = **62 %**.
- **Résultat clé** : leur modèle atteint environ 60,25 % de précision (720 matchs). D'autres études restent sous 62 % `[S]`.
- **Implication pratique pour nous** : un modèle NHL affichant plus de 65 % de précision est **suspect** (fuite d'information). En NHL, il faut raisonner en calibration et en edge, pas en précision.
- **Vérif.** : [S]. Les références bibliographiques exactes sont à confirmer.

### 4.6 Rugby

#### [S18] O'Donoghue, Ball, Eustace, McFarlan & Nisotaki (2016) : modèles de la Coupe du monde 2015
- **Référence** : O'Donoghue, P., Ball, D., Eustace, J., McFarlan, B., & Nisotaki, M. (2016). *Predictive models of the 2015 Rugby World Cup: accuracy and application*. International Journal of Computer Science in Sport, 15(1), 37–58.
- **Lien** : https://doi.org/10.1515/ijcss-2016-0003
- **Résumé** : 12 modèles de régression linéaire de l'écart de score, fondés notamment sur les **points du classement mondial** et l'avantage du terrain relatif, sont comparés. Chaque modèle est simulé 10 000 fois.
- **Résultat clé** :
  - le meilleur modèle utilise **toutes les éditions précédentes** plutôt que les 3 dernières, et intègre les points du classement mondial ;
  - les équipes du top 7 ont sous-performé, et celles classées au-delà du 16e rang ont surperformé ;
  - il existe un petit effet des **jours de récupération**.
- **Implication pratique pour nous** : pour le rugby international, il faut un modèle simple fondé sur le classement World Rugby et l'écart de points, avec simulation. Ajouter un ajustement pour les jours de repos.
- **Vérif.** : [R]

#### [S19] Scarf, Parma & McHale (2019) : taux de score et incertitude en rugby
- **Référence** : Scarf, P., Parma, R., & McHale, I. (2019). *On outcome uncertainty and scoring rates in sport: The case of international rugby union*. European Journal of Operational Research, 273(2), 721–730.
- **Lien** : https://doi.org/10.1016/j.ejor.2018.08.021
- **Résumé** : Dans un cadre de « Poisson match », un taux de score plus élevé **réduit l'incertitude** du résultat. Le taux de score a fortement augmenté en rugby international en 50 ans.
- **Résultat clé** : en rugby, le meilleur gagne plus souvent qu'en football, d'où des favoris très marqués.
- **Implication pratique pour nous** : en rugby, le marché pertinent est le **handicap** ou l'écart de points, pas le 1X2. Un modèle d'écart de score, gaussien ou de type Skellam, est adapté.
- **Vérif.** : [R]

### 4.7 Handball

#### [S20] Groll, Heiner, Schauberger & Uhrmeister (2020) : sous-dispersion des scores en handball
- **Référence** : Groll, A., Heiner, J., Schauberger, G., & Uhrmeister, J. (2020). *Prediction of the 2019 IHF World Men's Handball Championship – A sparse Gaussian approximation model*. Journal of Sports Analytics, 6(3), 187–197.
- **Lien** : https://doi.org/10.3233/JSA-200384
- **Résumé** : Comparaison de modèles de Poisson (sous-dispersé), gaussiens et binomiaux négatifs sur les Mondiaux masculins de 2011 à 2017. Les covariables incluent les **cotes de vainqueur du tournoi** (ODDSET) converties en probabilités.
- **Résultat clé** : le **modèle gaussien** à faible variance est le meilleur. Les scores de handball sont **sous-dispersés** (variance inférieure à la moyenne), donc un **Poisson est inadapté**.
- **Implication pratique pour nous** : pour le handball, on modélise les scores avec une loi gaussienne ou sous-dispersée, et l'écart de buts directement ([S21]). Il ne faut pas réutiliser tel quel le Poisson du football.
- **Vérif.** : [R]

#### [S21] Karlis, Michels & Ötting (2025) : modéliser l'écart de buts en handball
- **Référence** : Karlis, D., Michels, R., & Ötting, M. (2025). *Modelling handball outcomes using univariate and bivariate approaches*. Statistical Methods & Applications, 35, 263–284 `[?]` (volume et pages selon la notice).
- **Lien** : https://doi.org/10.1007/s10260-025-00825-w (arXiv:2404.04213)
- **Résumé** : Régression de **Skellam** sur l'écart de buts, avec des versions gonflées en zéro, pour contourner la sous-dispersion. Des **copules bivariées** relient l'écart en seconde mi-temps à celui de la première. Données de Bundesliga allemande.
- **Résultat clé** : c'est un cadre adapté aux marchés **handicap** et **mi-temps** du handball.
- **Implication pratique pour nous** : c'est le modèle de référence pour un module handball, sport populaire en France avec la Starligue et l'équipe nationale.
- **Vérif.** : [R]

#### [S22] Felice & Ley (2023) : apprentissage « statistically enhanced » en handball
- **Référence** : Felice, F., & Ley, C. (2023). *Prediction of handball matches with statistically enhanced learning via estimated team strengths*. arXiv:2307.11777.
- **Lien** : https://arxiv.org/abs/2307.11777
- **Résumé** : Un modèle ML est augmenté de variables de **force estimée** statistiquement (SEL), sur des matchs de clubs féminins.
- **Résultat clé** : **précision supérieure à 80 %** annoncée. Ce chiffre n'est pas comparé aux cotes et concerne un contexte (handball féminin) où les écarts de niveau sont grands, donc la précision brute n'est pas un indicateur d'edge.
- **Implication pratique pour nous** : on confirme la recette « force estimée → variable ML » ([F62]). Il ne faut pas confondre précision et rentabilité ([F31]).
- **Vérif.** : [R]

### 4.8 Volley-ball

#### [S23] Egidi & Ntzoufras (2020) : modèle bayésien unifié pour le volley
- **Référence** : Egidi, L., & Ntzoufras, I. (2020). *A Bayesian quest for finding a unified model for predicting volleyball games*. Journal of the Royal Statistical Society, Series C, 69(5), 1307–1336.
- **Lien** : https://doi.org/10.1111/rssc.12436 (arXiv:1911.01815)
- **Résumé** : Modèle hiérarchique à deux niveaux :
  1. un logit pour le gagnant du set ;
  2. conditionnellement au gagnant, une **binomiale négative tronquée** pour les points du perdant, avec une composante de Poisson pour les **points supplémentaires** (règle des 2 points d'écart).
  Les capacités des équipes et l'avantage du terrain interviennent à tous les niveaux. Application à la SuperLega italienne 2017-18.
- **Résultat clé** : excellente reproduction du classement final et capacité prédictive satisfaisante.
- **Implication pratique pour nous** : c'est la base d'un module volley qui couvre les marchés **sets** (3-0, 3-1…), **handicap de points** et **total de points**.
- **Vérif.** : [R]

---

## 5. Théorie du pari et gestion de bankroll

> **Rappels mathématiques** (résultats standard, dérivables directement)
>
> **Mise de Kelly pour un pari simple.** Avec une probabilité estimée *p* et une cote décimale *o* :
>
> f\* = (p·o − 1) / (o − 1)
>
> C'est la fraction de bankroll qui maximise la croissance logarithmique attendue.
>
> **Kelly fractionnel.** Miser une fraction *c* de f\* (0 < c ≤ 1) donne, dans l'approximation usuelle :
> - une croissance d'environ (2c − c²) fois la croissance de Kelly ;
> - une volatilité d'environ *c* fois celle de Kelly.
>
> Le **demi-Kelly** conserve donc environ **75 %** de la croissance avec environ **la moitié** de la volatilité.
>
> **Surestimation de l'edge.** Si l'edge est surestimé d'un facteur 2, la mise « Kelly » réelle vaut 2 × f\* : la croissance attendue tombe alors à environ **zéro**, et au-delà elle devient **négative**.
>
> **Conclusion.** Comme nos probabilités sont estimées avec erreur, la mise de Kelly pleine est **toujours** trop agressive en pratique.

#### [K1] Kelly (1956) : le critère de Kelly
- **Référence** : Kelly, J. L. Jr. (1956). *A new interpretation of information rate*. Bell System Technical Journal, 35(4), 917–926.
- **Lien** : https://doi.org/10.1002/j.1538-7305.1956.tb03809.x
- **Résumé** : Un parieur disposant d'une information privilégiée bruitée maximise le taux de croissance exponentiel de son capital en misant une fraction fixe, proportionnelle à son avantage. Le lien est fait avec le débit d'information de Shannon.
- **Résultat clé** : maximiser E[log(richesse)] donne, asymptotiquement, plus de capital que toute autre stratégie, presque sûrement.
- **Implication pratique pour nous** : c'est le cadre de référence pour **dimensionner les mises**. Il n'est jamais utilisé « plein » (voir [K3]–[K5]).
- **Vérif.** : [S] pour les métadonnées. La citation est standard.

#### [K2] Thorp (1997, 2006/2008) : Kelly en blackjack, paris sportifs et bourse
- **Référence** : Thorp, E. O. (2008). *The Kelly criterion in blackjack, sports betting, and the stock market*. In S. A. Zenios & W. T. Ziemba (Eds.), *Handbook of Asset and Liability Management*, Vol. 1, Elsevier. La version originale est une communication de 1997.
- **Lien** : https://doi.org/10.1016/B978-044453248-0.50015-0
- **Résumé** : Synthèse pratique du critère de Kelly : propriétés, paris simultanés, Kelly fractionnel, risque de drawdown. Exemples tirés du blackjack, des paris sportifs et de la gestion du fonds de Thorp.
- **Résultat clé** : il recommande des **fractions de Kelly** pour se protéger de l'incertitude sur les probabilités et des drawdowns.
- **Implication pratique pour nous** : c'est la référence pédagogique pour la documentation du module « staking ».
- **Vérif.** : [R], via les métadonnées. Les pages exactes ne sont pas vérifiées `[?]`.

#### [K3] MacLean, Thorp & Ziemba (2010) : bonnes et mauvaises propriétés de Kelly
- **Référence** : MacLean, L. C., Thorp, E. O., & Ziemba, W. T. (2010). *Long-term capital growth: the good and bad properties of the Kelly and fractional Kelly capital growth criteria*. Quantitative Finance, 10(7), 681–687.
- **Lien** : https://doi.org/10.1080/14697688.2010.506108
- **Résumé** : Inventaire des propriétés du critère :
  - les **bonnes** : croissance asymptotique maximale, temps minimal pour atteindre un objectif ;
  - les **mauvaises** : très forte volatilité, mises énormes quand l'edge est grand, probabilité élevée de grosses pertes à moyen terme, **sur-mise désastreuse** si les probabilités sont surestimées.
  Le Kelly fractionnel est présenté comme compromis croissance/sécurité.
- **Résultat clé** : même avec un edge réel, le Kelly plein produit fréquemment des **drawdowns de plus de 50 %**. Le Kelly fractionnel réduit fortement ce risque au prix d'une croissance un peu plus faible.
- **Implication pratique pour nous** : par défaut, on mise entre **1/4 et 1/2 Kelly**, avec un plafond par pari.
- **Vérif.** : [S], résumé tiré de la littérature citante. Les ordres de grandeur sont standard.

#### [K4] Baker & McHale (2013) : Kelly « rétréci » sous incertitude des paramètres
- **Référence** : Baker, R. D., & McHale, I. G. (2013). *Optimal betting under parameter uncertainty: Improving the Kelly criterion*. Decision Analysis, 10(3), 189–199.
- **Lien** : https://doi.org/10.1287/deca.2013.0271
- **Résumé** : Le critère de Kelly ignore l'incertitude sur la probabilité estimée, et remplacer un paramètre par son estimation dégrade la performance hors échantillon. Les auteurs montrent qu'il faut **rétrécir** (*shrink*) la mise, et comparent plusieurs estimateurs du facteur de rétrécissement, en simulation et sur des **données de tennis**.
- **Résultat clé** : le Kelly rétréci **améliore** le Kelly « brut ». Une approximation « sur un coin de table » du facteur est proposée.
- **Implication pratique pour nous** : c'est la justification formelle du Kelly fractionnel. Le facteur doit **dépendre de l'incertitude** de notre estimation : écart-type de la probabilité, taille de l'échantillon d'entraînement, et dispersion entre modèles d'un ensemble.
- **Vérif.** : [R]

#### [K5] Uhrín, Šourek, Hubáček & Železný (2021) : revue expérimentale des stratégies de mise
- **Référence** : Uhrín, M., Šourek, G., Hubáček, O., & Železný, F. (2021). *Optimal sports betting strategies in practice: an experimental review*. IMA Journal of Management Mathematics, 32(4), 465–489.
- **Lien** : https://doi.org/10.1093/imaman/dpaa029 (arXiv:2107.08827)
- **Résumé** : Kelly, Markowitz (Sharpe maximal) et leurs variantes pratiques (Kelly fractionnel, plafond de mise, contrainte de drawdown, Kelly distributionnellement robuste) sont comparés sur trois jeux de données :
  - courses hippiques ;
  - **basket NBA** ;
  - **football** : 32 000 matchs, modèle de gradient boosting vainqueur du challenge 2017, cotes **Pinnacle d'ouverture**, marge d'environ 3 %, précision du modèle 52,3 % contre 53,7 % pour le bookmaker.
  Protocole strict : hyperparamètres choisis sur l'entraînement, évaluation sur le test, 1 000 trajectoires rééchantillonnées. Critère : richesse **médiane**, sous la contrainte d'éviter la ruine.
- **Résultat clé** :
  - Kelly « plein » et Sharpe maximal, appliqués tels quels, sont **infaisables** dans presque tous les scénarios réalistes : ils mènent souvent à la **ruine** ;
  - le **Kelly fractionnel** avec fraction bien réglée, notamment sa version **adaptative**, est le meilleur choix ou proche du meilleur partout ;
  - la contrainte de drawdown se comporte comme le Kelly fractionnel ;
  - le Kelly robuste est le plus sûr mais le moins rentable ;
  - le plafond de mise donne des résultats inconclusifs ;
  - des compromis raisonnables existent **même avec un modèle moins précis que le bookmaker**.
- **Implication pratique pour nous** : c'est **la référence pratique pour le module de mise**. Il faut implémenter le Kelly fractionnel avec une fraction calibrée par backtest, et une option drawdown. Les résultats doivent être rapportés en **médiane et en quantiles** de richesse, jamais seulement en moyenne.
- **Vérif.** : [TI] (PDF lu). Les pages sont à confirmer `[?]`.

#### [K6] Whitrow (2007) : Kelly pour de nombreux paris simultanés
- **Référence** : Whitrow, C. (2007). *Algorithms for optimal allocation of bets on many simultaneous events*. Journal of the Royal Statistical Society, Series C, 56(5), 607–623.
- **Lien** : https://doi.org/10.1111/j.1467-9876.2007.00594.x
- **Résumé** : Optimisation de nombreux paris simultanés en utilité logarithmique, par algorithmes de gradient stochastique comparés au simplexe. C'est une généralisation de Kelly à plusieurs paris, illustrée avec des cotes réelles de bookmakers.
- **Résultat clé** : il fournit des algorithmes pratiques pour le Kelly « portefeuille ». Les mises optimales simultanées diffèrent des mises Kelly calculées pari par pari.
- **Implication pratique pour nous** : un samedi de Ligue 1 ou de Premier League, il faut **optimiser conjointement** les mises sur les matchs simultanés et ne pas additionner des Kelly individuels, ce qui surexpose le capital.
- **Vérif.** : [R]

#### [K7] Grant, Johnstone & Kwon (2008) : stratégies optimales pour matchs simultanés
- **Référence** : Grant, A., Johnstone, D., & Kwon, O. K. (2008). *Optimal betting strategies for simultaneous games*. Decision Analysis, 5(1), 10–18.
- **Lien** : https://doi.org/10.1287/deca.1080.0106
- **Résumé** : Maximisation de la croissance logarithmique pour des paris sur des matchs joués en même temps, y compris via des combinaisons de paris `[S]`.
- **Résultat clé** : la solution optimale peut inclure des **combinés** qui couvrent les issues jointes `[S]`.
- **Implication pratique pour nous** : ce travail complète [K6]. Pour les combinés, il faut se méfier de la marge multipliée chez les books grand public.
- **Vérif.** : [S]. Le résumé n'a pas été consulté.

#### [K8] Busseti, Ryu & Boyd (2016) : Kelly sous contrainte de risque
- **Référence** : Busseti, E., Ryu, E. K., & Boyd, S. (2016). *Risk-constrained Kelly gambling*. The Journal of Investing, 25(3), 118–134.
- **Lien** : https://doi.org/10.3905/joi.2016.25.3.118 (arXiv:1603.06183)
- **Résumé** : On ajoute à Kelly une contrainte qui limite la probabilité de **drawdown** sous un seuil. Une borne convexe rend le problème soluble, et sa version quadratique est proche de Markowitz.
- **Résultat clé** : à même risque de drawdown ou à même croissance, il fait **mieux que le Kelly fractionnel**. Un seul paramètre d'aversion au risque est interprétable.
- **Implication pratique pour nous** : c'est une option avancée du module de mise (via `cvxpy`), pour qui veut contrôler explicitement « P(perdre 30 % de la bankroll) < 5 % ». Uhrín et al. ([K5]) trouvent toutefois des performances proches du Kelly fractionnel en pratique.
- **Vérif.** : [R]

#### [K9] Chu, Wu & Swartz (2018) : critères de Kelly modifiés
- **Référence** : Chu, D., Wu, Y., & Swartz, T. B. (2018). *Modified Kelly criteria*. Journal of Quantitative Analysis in Sports, 14(1), 1–11.
- **Lien** : https://doi.org/10.1515/jqas-2017-0122
- **Résumé** : Extension de Kelly dans un cadre de **théorie de la décision**, où la probabilité est incertaine. Des estimateurs de la fraction de mise sont dérivés pour différentes fonctions de perte.
- **Résultat clé** : les fractions recommandées **varient fortement selon la fonction de perte** choisie.
- **Implication pratique pour nous** : c'est une confirmation, avec [K4], que le choix de la fraction est une **décision de gestion du risque**, à documenter explicitement.
- **Vérif.** : [R], via la notice.

#### [K10] Rappel : allocation par portefeuille (Hubáček et al., 2019b)
- Voir [S7]. La **théorie moderne du portefeuille** (compromis espérance/variance) appliquée aux paris NBA donne des profits cumulés positifs en combinaison avec un modèle décorrélé du marché. Elle se compare à Kelly dans [K5].

---

## 6. Pièges méthodologiques

### 6.1 Surapprentissage du backtest, tests multiples, biais de publication

#### [M1] Bailey, Borwein, López de Prado & Zhu (2014) : « pseudo-mathématiques et charlatanisme financier »
- **Référence** : Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2014). *Pseudo-mathematics and financial charlatanism: The effects of backtest overfitting on out-of-sample performance*. Notices of the American Mathematical Society, 61(5), 458–471.
- **Lien** : https://doi.org/10.1090/noti1105 `[?]` (SSRN : https://doi.org/10.2139/ssrn.2308659)
- **Résumé** : Si l'on essaie suffisamment de configurations (paramètres, filtres, ligues, seuils), on trouve **toujours** un backtest brillant par pur hasard. Plus le nombre d'essais est grand par rapport à la longueur de l'historique, plus la performance hors échantillon de la meilleure configuration est mauvaise, et elle peut même devenir négative.
- **Résultat clé** : la longueur minimale de backtest nécessaire croît avec le **nombre d'essais**. La plupart des backtests publiés sont sous-dimensionnés.
- **Implication pratique pour nous** : la bibliothèque doit **journaliser le nombre de variantes testées** pour chaque stratégie (registre des essais), et l'utiliser pour corriger la significativité.
- **Vérif.** : [S]. Le contenu est connu, le DOI AMS est à confirmer.

#### [M2] Bailey, Borwein, López de Prado & Zhu (2017) : probabilité de surapprentissage du backtest (PBO)
- **Référence** : Bailey, D. H., Borwein, J., López de Prado, M., & Zhu, Q. J. (2017). *The probability of backtest overfitting*. Journal of Computational Finance, 20(4), 39–69.
- **Lien** : https://doi.org/10.21314/JCF.2016.322 `[?]` (SSRN : https://ssrn.com/abstract=2326253)
- **Résumé** : Méthode **CSCV** (*combinatorially symmetric cross-validation*). On découpe l'historique en blocs, on choisit la meilleure configuration sur une moitié des blocs et on regarde son rang sur l'autre moitié, pour toutes les combinaisons de découpage.
- **Résultat clé** : on obtient une **probabilité de surapprentissage** (PBO) estimable sans modèle.
- **Implication pratique pour nous** : on implémente le CSCV/PBO dans le module d'évaluation. Une stratégie avec PBO > 0,5 est rejetée.
- **Vérif.** : [S]

#### [M3] Bailey & López de Prado (2014) : le Sharpe ratio « dégonflé »
- **Référence** : Bailey, D. H., & López de Prado, M. (2014). *The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality*. The Journal of Portfolio Management, 40(5), 94–107.
- **Lien** : https://doi.org/10.3905/jpm.2014.40.5.094
- **Résumé** : Le Sharpe ratio observé du meilleur de N essais est corrigé pour trois effets : le **nombre d'essais**, la **non-normalité** (asymétrie et aplatissement des rendements, très marqués en paris à grosses cotes) et la longueur de l'échantillon.
- **Résultat clé** : on obtient la probabilité que le vrai Sharpe soit positif après correction.
- **Implication pratique pour nous** : chaque stratégie doit rapporter le **DSR**, calculé sur les rendements par pari ou par journée, en plus du ROI. L'asymétrie des paris sur outsiders gonfle les faux positifs.
- **Vérif.** : [S]

#### [M4] White (2000) et Harvey, Liu & Zhu (2016) : data snooping et seuil t > 3
- **Références** :
  - White, H. (2000). *A reality check for data snooping*. Econometrica, 68(5), 1097–1126. https://doi.org/10.1111/1468-0262.00152
  - Harvey, C. R., Liu, Y., & Zhu, H. (2016). *…and the cross-section of expected returns*. The Review of Financial Studies, 29(1), 5–68. https://doi.org/10.1093/rfs/hhv059
- **Résumé** :
  - White propose le « Reality Check », un test bootstrap de la meilleure règle parmi toutes celles essayées.
  - Harvey et al. montrent qu'avec des centaines de « facteurs » testés en finance, le seuil de significativité doit passer de **t > 2 à t > 3**.
- **Résultat clé** : sans correction, la majorité des « découvertes » sont des faux positifs.
- **Implication pratique pour nous** : on retient **|t| > 3**, ou une correction de type Holm ou Benjamini-Hochberg, pour qualifier une stratégie de « prometteuse ». On applique le Reality Check ou le test SPA de Hansen sur la famille de stratégies.
- **Vérif.** : [S]. Les références sont standard.

#### [M5] Vandenbruaene, De Ceuster & Annaert (2022) : 600 stratégies de handicap passées en revue
- **Référence** : Vandenbruaene, J., De Ceuster, M., & Annaert, J. (2022). *Efficient spread betting markets: A literature review*. Journal of Sports Economics, 23(7), 907–949.
- **Lien** : https://doi.org/10.1177/15270025211071042
- **Résumé** : Revue de **plus de 600 implémentations de stratégies** sur les marchés à handicap (spread).
- **Résultat clé** :
  - des **erreurs de prix prévisibles existent**, mais elles sont **trop petites pour être exploitées** une fois les coûts pris en compte, ce qui est cohérent avec l'efficience ;
  - la littérature sur les paris **ne contrôle pas le data mining** ;
  - les auteurs recommandent le seuil **|z| > 3**.
- **Implication pratique pour nous** : c'est la synthèse la plus directe. « Biais réel » ne veut pas dire « stratégie rentable ». Le seuil |z| > 3 est **adopté** dans la bibliothèque.
- **Vérif.** : [R]

#### [M6] Clegg & Cartlidge (2025) : réplication et correction de « Betting on a buzz »
- **Références** :
  - Ramirez, P., Reade, J. J., & Singleton, C. (2023). *Betting on a buzz: Mispricing and inefficiency in online sportsbooks*. International Journal of Forecasting, 39(3), 1413–1423. https://doi.org/10.1016/j.ijforecast.2022.07.011
  - Clegg, L., & Cartlidge, J. (2025). *Not feeling the buzz: Correction study of mispricing and inefficiency in online sportsbooks*. International Journal of Forecasting. https://doi.org/10.1016/j.ijforecast.2024.06.012 (arXiv:2306.01740)
- **Résumé** : L'étude originale construit un « buzz factor » à partir des vues des pages Wikipédia des joueurs de tennis, sur plus de 10 000 matchs. Ce facteur prédit les erreurs de prix des bookmakers et permet des profits « substantiels ». La réplication reproduit exactement les résultats, mais découvre qu'ils dépendent fortement d'**un seul pari** (le pari « Hercog »), pris à une **cote erronée**.
- **Résultat clé** :
  - une fois cette donnée corrigée, **la plupart des profits disparaissent** ;
  - une seule stratégie (matchs « compétitifs ») reste significative sur la période originale ;
  - **après 2020, elle ne rapporte plus rien**, et les coefficients ne prédisent plus les erreurs de prix.
- **Implication pratique pour nous** : c'est un cas d'école. Il faut **nettoyer les cotes aberrantes** (cotes « palp » annulées par les bookmakers), tester la **sensibilité aux 1 % de paris les plus rentables** (ROI sans les k meilleurs paris), et **continuer le test après la publication**.
- **Vérif.** : [R]

#### [M7] Winkelmann et al. (2024) : petits échantillons et faux positifs
- Voir [F48]. Sous efficience parfaite, des « inefficiences » significatives apparaissent régulièrement sur une saison. **Règle adoptée** : aucune conclusion sur moins de plusieurs saisons et plusieurs ligues.

#### [M8] Gneiting & Raftery (2007) : règles de score strictement propres
- **Référence** : Gneiting, T., & Raftery, A. E. (2007). *Strictly proper scoring rules, prediction, and estimation*. Journal of the American Statistical Association, 102(477), 359–378.
- **Lien** : https://doi.org/10.1198/016214506000001437
- **Résumé** : Théorie des règles de score **strictement propres** (log, Brier, CRPS…). Elles sont minimisées en espérance seulement si l'on annonce ses vraies croyances.
- **Résultat clé** : la précision et le ROI ne sont pas des règles propres. La log-loss et le Brier le sont.
- **Implication pratique pour nous** : la sélection de modèles se fait **uniquement** sur des règles propres (log-loss en priorité, voir [F30]), complétées par des diagrammes de calibration ([F32]).
- **Vérif.** : [S]. La référence est standard.

### 6.2 Biais de backtest spécifiques aux paris

- **Look-ahead bias** (fuite d'information future). Exemples typiques :
  - variables calculées avec des données postérieures au coup d'envoi : statistiques de la saison complète, classement final, xG du match lui-même ;
  - normalisation sur tout l'échantillon ;
  - validation croisée **aléatoire** au lieu de temporelle.
  
  Bunker & Thabtah ([F23]) et Bunker & Susnjak ([F24]) insistent sur la validation **chronologique**. Règle à suivre : *walk-forward*, avec réentraînement à date fixe et gel des données à l'heure de la prise de pari.
- **Cotes de clôture irréalistes.** Beaucoup d'études parient « à la clôture » ou à la **meilleure cote parmi des dizaines de bookmakers**. Or :
  - Kaunitz et al. ([F37]) constatent qu'environ **30 % des cotes affichées avaient déjà changé** au moment de miser ;
  - Angelini et al. ([T8]) montrent que le profit du WElo **disparaît** aux cotes moyennes ou chez un seul bookmaker.
  
  **Règle** : backtester uniquement avec des cotes **horodatées, réellement disponibles chez les opérateurs accessibles** (ANJ), au moment simulé de la mise, avec une marge de glissement.
- **Cotes « palp » et données aberrantes.** Clegg & Cartlidge ([M6]) montrent qu'**un** pari à cote erronée peut fabriquer l'essentiel d'un profit publié. Il faut filtrer les cotes très au-dessus du consensus, que l'opérateur annulerait de toute façon.
- **ROI ≠ qualité.** Voir Wunderlich & Memmert ([F31]) : un ROI positif peut être obtenu par hasard ou par un modèle moins précis.

### 6.3 Limitation des comptes gagnants

#### [M9] Preuves de la limitation des comptes par les bookmakers « soft »
- **Références** :
  - Kaunitz, Zhong & Kreiner (2017) ([F37]) : restrictions sévères quelques mois après le début des paris réels (mises plafonnées, « inspection manuelle », refus), qui ont mis fin à l'expérience.
  - Grant, A., Oikonomidis, A., Bruce, A. C., & Johnson, J. E. V. (2018). *New entry, strategic diversity and efficiency in soccer betting markets: the creation and suppression of arbitrage opportunities*. The European Journal of Finance, 24(18), 1799–1816. https://doi.org/10.1080/1351847X.2016.1265568 `[?]` (notice : https://irep.ntu.ac.uk/id/eprint/35180/).
    - Les cotes de bookmakers concurrents créent des arbitrages (**545 « surebets » sur 2 132 matchs** de six grands championnats en 2012-13) que les **pratiques de gestion des bookmakers empêchent d'exploiter**.
    - Ils distinguent les « **position-takers** », qui bougent peu leurs cotes mais **restreignent activement les parieurs informés**, et les « **book-balancers** », qui ajustent leurs cotes et restreignent peu.
  - Hegarty & Whelan (2025) ([F49]) : modèle « soft » européen, avec limitation et exclusion des gagnants, contre le modèle « sharp » (Pinnacle), qui accepte les parieurs informés et utilise leurs mises pour fixer ses prix.
  - Davies, R. (2022). *Revealed: how bookies clamp down on successful gamblers and exploit the rest*. The Guardian (enquête journalistique sur le « stake factoring »).
  - Contexte français, voir le document réglementaire ANJ du projet : la délibération ANJ n° 2021-C-01 pose qu'un opérateur « ne peut refuser ou limiter les mises […] sauf à disposer d'un motif légitime ». En pratique, les limitations restent courantes, et aucune sanction publique spécifique n'a été identifiée.
- **Implication pratique pour nous** : **la limitation est le premier risque opérationnel** de toute stratégie gagnante chez des bookmakers grand public. La bibliothèque doit :
  1. considérer la **capacité** (mise maximale, durée de vie du compte) comme une **contrainte du backtest** ;
  2. privilégier des stratégies dont le **profil de mise ressemble à celui d'un parieur récréatif** : marchés principaux, pas uniquement des cotes « en retard », mises arrondies ;
  3. documenter chaque limitation.
- **Vérif.** : [TI] pour Kaunitz et Hegarty-Whelan. [R] et [S] pour Grant et al., dont le DOI est à confirmer.

### 6.4 Closing line value (CLV) : la meilleure mesure de compétence

#### [M10] La ligne de clôture comme estimateur le plus précis, et le CLV comme métrique
- **Fondements académiques** :
  - Gandar et al. (1998, [S3]) : les mouvements de ligne améliorent la précision, et la clôture est meilleure que l'ouverture.
  - Franck et al. (2010, [F36]) : le marché le plus liquide est le plus précis.
  - Hegarty & Whelan (2025, [F49]) : absence de FLB sur le handicap asiatique des books « sharp ».
  - Kovalchik (2016, [T6]) et Baboota & Kaur (2019, [F22]) : les cotes du marché battent les modèles.
- **Littérature de praticiens** (non évaluée par des pairs) :
  - Buchdahl, J. (2016). *Squares & Sharps, Suckers & Sharks: The Science, Psychology & Philosophy of Gambling*. Oldcastle Books `[S]` ;
  - articles « Betting Resources » de Pinnacle sur le CLV `[S]`.
  
  Thèse : si la clôture de Pinnacle approxime la vraie probabilité, alors l'écart moyen (cote prise / cote de clôture dé-marginée − 1) **estime l'espérance de gain**, avec une variance bien plus faible que le ROI réalisé.
- **Résultat clé** : il n'existe pas, à notre connaissance, d'étude académique à comité de lecture qui valide **formellement** le CLV comme prédicteur du profit individuel. C'est une conséquence logique de l'efficience de la clôture, largement admise par les praticiens `[?]`.
- **Implication pratique pour nous** :
  - le **CLV moyen contre Pinnacle** (ou contre le consensus dé-marginé) est la **métrique principale de compétence** de chaque stratégie : il converge en quelques centaines de paris, alors qu'il en faut des milliers pour un ROI significatif ;
  - un ROI positif avec un CLV ≤ 0 doit être considéré comme de la **chance** ;
  - le CLV a toutefois ses limites : les marchés peu liquides ont une clôture moins fiable, et un parieur qui bat la clôture se fait **limiter** ([M9]).
- **Vérif.** : [S] pour la littérature des praticiens. [TI] et [R] pour les fondements académiques.

---

## 7. Biais comportementaux exploitables

### 7.1 Biais favori-outsider (FLB)

#### [B1] Thaler & Ziemba (1988) : les anomalies des paris mutuels
- **Référence** : Thaler, R. H., & Ziemba, W. T. (1988). *Anomalies: Parimutuel betting markets: Racetracks and lotteries*. Journal of Economic Perspectives, 2(2), 161–174.
- **Lien** : https://doi.org/10.1257/jep.2.2.161
- **Résumé** : Revue des anomalies des courses hippiques, dont le **FLB** : les outsiders rapportent beaucoup moins que les favoris. Les explications avancées sont la surestimation des petites probabilités, le goût du risque et les effets de fin de journée.
- **Résultat clé** : le rendement espéré décroît avec la cote. Sur les très gros favoris, il peut approcher zéro ou devenir légèrement positif.
- **Implication pratique pour nous** : c'est la base du biais le plus robuste de la littérature.
- **Vérif.** : [S]. La référence est standard.

#### [B2] Snowberg & Wolfers (2010) : goût du risque ou mauvaise perception des probabilités ?
- **Référence** : Snowberg, E., & Wolfers, J. (2010). *Explaining the favorite–long shot bias: Is it risk-love or misperceptions?* Journal of Political Economy, 118(4), 723–746.
- **Lien** : https://doi.org/10.1086/655844
- **Résumé** : Les deux théories du FLB sont départagées en testant leur capacité à expliquer aussi les paris composés (exactas, trifectas) dans les courses hippiques américaines.
- **Résultat clé** : les données favorisent les **mauvaises perceptions des probabilités** (pondération de type « prospect theory ») plutôt que le goût du risque.
- **Implication pratique pour nous** : si le biais vient de la perception, il est **durable**, car il est humain, et il est **plus fort sur les événements rares** : gros outsiders, scores exacts, combinés.
- **Vérif.** : [R]

#### [B3] Cain, Law & Peel (2000) : le FLB dans le football britannique
- **Référence** : Cain, M., Law, D., & Peel, D. A. (2000). *The favourite-longshot bias and market efficiency in UK football betting*. Scottish Journal of Political Economy, 47(1), 25–36.
- **Lien** : https://doi.org/10.1111/1467-9485.00151
- **Résumé** : Test du FLB sur les cotes fixes du football britannique, y compris les marchés de score exact `[S]`.
- **Résultat clé** : il existe un FLB dans les cotes du football britannique `[S]`.
- **Implication pratique pour nous** : c'est une confirmation ancienne du FLB en football, cohérente avec [B4] et [F49].
- **Vérif.** : [S]. Les détails ne sont pas consultés.

#### [B4] Buhagiar, Cortis & Newall (2018) : pourquoi certains parieurs perdent plus que d'autres
- **Référence** : Buhagiar, R., Cortis, D., & Newall, P. W. S. (2018). *Why do some soccer bettors lose more money than others?* Journal of Behavioral and Experimental Finance, 18, 85–93.
- **Lien** : https://doi.org/10.1016/j.jbef.2018.01.010 (version auteur : http://wrap.warwick.ac.uk/101329)
- **Résumé** : **163 992 cotes** de football sur **dix championnats européens**.
- **Résultat clé** :
  - le **FLB est confirmé** ;
  - autre résultat surprenant : au **score de Brier**, les cotes prédisent **mieux** les outsiders que les favoris. Parier sur les outsiders est donc doublement perdant (marge plus lourde **et** moins d'erreurs de prix exploitables).
- **Implication pratique pour nous** : on **évite les outsiders** chez les books grand public. Les éventuelles erreurs de prix exploitables se situent plutôt sur les **favoris et les issues de probabilité moyenne**.
- **Vérif.** : [TI] (résumé et introduction lus).

#### [B5] Newall & Cortis (2021) : biais vers les outsiders, les favoris, ou les deux ?
- **Référence** : Newall, P. W. S., & Cortis, D. (2021). *Are sports bettors biased toward longshots, favorites, or both? A literature review*. Risks, 9(1), 22.
- **Lien** : https://doi.org/10.3390/risks9010022
- **Résumé** : Revue de la littérature sur le FLB et le **biais inverse** (vers les favoris).
- **Résultat clé** :
  - les marchés à **deux issues**, où le favori a une probabilité supérieure à 0,5 (tennis, money lines américaines), produisent souvent un **biais vers les favoris**, donc un FLB inversé ;
  - les marchés à **plusieurs issues**, où le favori a généralement une probabilité inférieure à 0,5 (1X2, courses), produisent plutôt un **biais vers les outsiders** ;
  - le parieur moyen aurait **les deux biais**.
- **Implication pratique pour nous** : cela explique les résultats contradictoires (Woodland en MLB et NHL contre les études sur le football européen). On **mesure le biais par type de marché**, sans le supposer.
- **Vérif.** : [R]

### 7.2 Biais domicile, popularité et sentiment

#### [B6] Forrest & Simmons (2008) : sentiment dans le football espagnol
- **Référence** : Forrest, D., & Simmons, R. (2008). *Sentiment in the betting market on Spanish football*. Applied Economics, 40(1), 119–126.
- **Lien** : https://doi.org/10.1080/00036840701522895
- **Résumé** : Plus de 3 000 paris sur la Liga, plus un échantillon écossais.
- **Résultat clé** : les cotes dépendent du **nombre relatif de supporters** de chaque club. Les supporters du club le plus populaire se voient offrir des **conditions plus favorables**, et **parier sur les équipes populaires était rentable**. Ce résultat va à l'**opposé** du marché américain décrit par Levitt ([S9]). Les auteurs l'attribuent à la **concurrence** entre bookmakers pour attirer les supporters.
- **Implication pratique pour nous** : le sens du biais de popularité **dépend de la structure concurrentielle**. En France, avec des opérateurs en concurrence et des cotes boostées sur les gros clubs (PSG, OM), il faut **tester** si les cotes sur les clubs populaires sont plus généreuses.
- **Vérif.** : [R], via la notice IDEAS.

#### [B7] Franck, Verbeek & Nüesch (2011) : préférences sentimentales et structure du marché
- **Référence** : Franck, E., Verbeek, E., & Nüesch, S. (2011). *Sentimental preferences and the organizational regime of betting markets*. Southern Economic Journal, 78(2), 502–518.
- **Lien** : https://doi.org/10.4284/0038-4038-78.2.502
- **Résumé** : Plus de 16 000 matchs anglais.
- **Résultat clé** : des **cotes plus favorables** sont proposées sur les **clubs populaires**, et l'effet est **amplifié le week-end**, quand les parieurs « sentimentaux » sont plus nombreux. Selon les auteurs, le marché à cotes fixes permet au bookmaker d'exploiter ces préférences, ce qui expliquerait pourquoi il coexiste avec l'exchange.
- **Implication pratique pour nous** : cela confirme [B6] en Angleterre. Les cotes d'**appel** sur les clubs populaires, surtout le week-end, sont à surveiller comme source de value. Cela rejoint le constat [F43] selon lequel les bookmakers proposent sciemment des cotes généreuses.
- **Vérif.** : [R], via la notice.

#### [B8] Feddersen, Humphreys & Soebbing (2017) : sentiment mesuré par les réseaux sociaux
- **Référence** : Feddersen, A., Humphreys, B. R., & Soebbing, B. P. (2017). *Sentiment bias and asset prices: Evidence from sports betting markets and social media*. Economic Inquiry, 55(2), 1119–1129.
- **Lien** : https://doi.org/10.1111/ecin.12404
- **Résumé** : Les « likes » Facebook servent de mesure de la popularité des équipes, dans cinq championnats européens, la NBA et la NFL.
- **Résultat clé** : les bookmakers proposent des cotes **moins favorables** sur les équipes sujettes au sentiment. C'est l'inverse de [B6] et [B7].
- **Implication pratique pour nous** : les résultats sur le biais de popularité sont **contradictoires** selon les périodes, les marchés et les méthodes. **Pas de règle a priori** : la variable « popularité » (followers, audience) se teste comme feature, avec un signe libre.
- **Vérif.** : [R], via la notice.

#### [B9] Braun & Kvasnička (2013) : sentiment national
- **Référence** : Braun, S., & Kvasnička, M. (2013). *National sentiment and economic behavior: Evidence from online betting on European football*. Journal of Sports Economics, 14(1), 45–64.
- **Lien** : https://doi.org/10.1177/1527002511414718 `[?]`
- **Résumé** : Cotes de bookmakers en ligne de 12 pays européens sur les matchs de leurs **équipes nationales**.
- **Résultat clé** : il existe des **biais systématiques dans le prix de la sélection nationale**, explicables par des biais de perception ou de loyauté. On observe un **biais pro-domicile dans 3 pays** et l'inverse dans 2 pays sur 12. Les bookmakers locaux peuvent exploiter ces biais par leurs prix.
- **Implication pratique pour nous** : pour les matchs de l'**équipe de France** chez les books français, il faut tester un biais de loyauté, les cotes pouvant être moins généreuses sur la France. La value se trouve plutôt sur l'adversaire, si le biais est confirmé.
- **Vérif.** : [R], via les notices. Le DOI est à confirmer.

#### [B10] Vergin & Sosik (1999) : avantage du terrain dans les matchs médiatisés (NFL)
- **Référence** : Vergin, R. C., & Sosik, J. J. (1999). *No place like home: an examination of the home field advantage in gambling strategies in NFL football*. Journal of Economics and Business, 51(1), 21–31.
- **Lien** : https://doi.org/10.1016/S0148-6195(98)00025-3
- **Résumé** : NFL de 1981 à 1996. Globalement, l'avantage du terrain est bien prix dans le spread : les équipes à domicile couvrent environ 50 % du temps.
- **Résultat clé** : lors des matchs **à forte exposition médiatique** (Monday Night, playoffs), l'équipe à domicile couvre à **59,2 %**, et les **outsiders à domicile** à **65,6 %** `[S]`.
- **Implication pratique pour nous** : les **affiches télévisées** (grosses affiches de Ligue 1 et de Ligue des champions) attirent l'argent récréatif. C'est une hypothèse à tester : value sur l'outsider à domicile lors des grandes affiches. C'est cohérent avec Levitt ([S9]).
- **Vérif.** : [S], via des sources secondaires.

### 7.3 Surréaction, récence, momentum

#### [B11] Moskowitz (2021) : momentum et value dans les paris sportifs
- **Référence** : Moskowitz, T. J. (2021). *Asset pricing and sports betting*. The Journal of Finance, 76(6), 3153–3209.
- **Lien** : https://doi.org/10.1111/jofi.13082
- **Résumé** : Les paris sportifs servent de laboratoire pour tester les anomalies d'*asset pricing* (momentum, value, taille). Ils n'ont pas de risque systématique et leur valeur terminale est exogène. L'étude couvre plus de **100 000 contrats** liquides sur **trois décennies** et **quatre sports** professionnels américains.
- **Résultat clé** :
  - **momentum fort** dans les mouvements de lignes, cohérent avec une **surréaction retardée**, corrigée ensuite par le résultat ;
  - faible effet « value » ;
  - les rendements sont une **fraction** de ceux des marchés financiers et **ne couvrent pas les coûts de transaction** (la marge).
- **Implication pratique pour nous** : la surréaction existe mais est **trop petite pour battre la marge** sur les marchés américains liquides. Cela relativise [F38]. Il faut l'exploiter seulement là où la marge est faible (meilleures cotes) ou en combinaison avec d'autres signaux.
- **Vérif.** : [R], via les notices.

#### [B12] Pope & Peel (1989) : premières inefficiences sur le nul
- **Référence** : Pope, P. F., & Peel, D. A. (1989). *Information, prices and efficiency in a fixed-odds betting market*. Economica, 56(223), 323–341.
- **Lien** : https://doi.org/10.2307/2554281 `[?]`
- **Résumé** : Cotes de quatre bookmakers britanniques sur le football anglais en 1981-82.
- **Résultat clé** : il y a des indices d'inefficience, **en particulier sur le nul**. Les pronostics d'experts n'apportent pas de rendement exploitable `[S]`.
- **Implication pratique pour nous** : le **nul** est historiquement l'issue la plus mal prix, ce que reprennent Lezana ([F56]) et Hegarty & Whelan ([F49]) : les nuls à probabilité élevée ont parmi les taux de perte les plus faibles. **Le pari sur le nul dans les matchs serrés** est une piste à tester.
- **Vérif.** : [S]

#### Autres références de cette section déjà présentées
- **Surréaction aux séries** : Wheatcroft ([F38]), avec une explication par la « hot hand fallacy ».
- **Momentum en direct** : Ötting et al. ([F55]). Le public surjoue l'équipe qui vient d'égaliser, et suivre ce momentum entraîne des pertes.
- **Biais « over » sur les totaux** : Paul & Weinbach ([S4], [S10]).
- **Biais favoris et extérieur du public NFL, et exploitation par les bookmakers** : Levitt ([S9]).
- **Changement d'entraîneur** : Bernardo et al. ([F53]).
- **Chocs d'avantage du terrain (COVID)** : Winkelmann et al. ([F51]), Meier et al. ([F52]).
- **FLB au tennis** : Forrest & McHale ([T14]) et Abinzano et al. ([T15]), y compris sur l'exchange.
- **Gros favoris** : Direr ([F41]), Vlastakis et al. ([F42]).
- **Structure de marché et FLB** : Whelan ([F50]), Hegarty & Whelan ([F49]).

---

## 8. Synthèse : ce que dit la science, consensus et stratégies les plus prometteuses

### 8.1 Les sept points de consensus

1. **Les cotes sont le meilleur prévisionniste disponible**, surtout celles des marchés liquides et « sharp » (Pinnacle, exchange) à la clôture.
   - C'est vrai en football ([F11], [F22], [F33], [F35], [F36]), au tennis ([T6], [T13]), en NFL ([S12]) et en NBA ([S5], [S6]).
   - Ordre de grandeur en football 1X2 : un bon modèle ML public obtient un RPS d'environ **0,215**, contre environ **0,201** pour Pinnacle et Bet365 sur la même période ([F22]).
   - Au tennis, le consensus des bookmakers atteint environ **72 %** de précision et la log-loss la plus basse, contre environ 70 % de précision et une log-loss d'environ 0,60 pour le meilleur Elo ([T6]).

2. **Les modèles fondés uniquement sur les scores ont atteint un plafond.**
   - Poisson, Dixon-Coles, Elo, pi-ratings et GBM donnent des prédictions très proches ([F8], [F20], [F63]).
   - Les gains marginaux viennent de **nouvelles informations** : tirs et xG ([F26], [F39], [F40]), compositions et notes des joueurs ([F16]), information contenue dans les cotes ([F10], [F14]).
   - La sophistication algorithmique compte peu ([F20], [F21]).

3. **Le biais favori-outsider est l'anomalie la plus robuste**, mais il **ne suffit pas** à rendre une stratégie rentable.
   - Il est présent chez les books grand public, dans les marchés à plusieurs issues ([F41], [F49], [B1]–[B5], [T14], [T15]).
   - Il est faible ou absent chez Pinnacle et sur le handicap asiatique ([F49]).
   - Il peut s'inverser dans les marchés à deux issues ([B5], [S14], [S15]).
   - En pratique : il indique surtout **quoi éviter** (les outsiders chez les books grand public).

4. **Les inefficiences publiées sont petites, instables et souvent non répliquées.**
   - Exemples : [F48], [M5], [S13], [M6], [B11].
   - Des « anomalies » significatives sur une saison sont attendues même en marché parfaitement efficient ([F48]).
   - Sur plus de 600 stratégies de handicap, les erreurs de prix prévisibles sont trop petites pour couvrir la marge ([M5]).
   - Le seuil de preuve raisonnable est **|z| > 3** après correction pour les essais multiples ([M4], [M5]).

5. **Les bookmakers grand public ne sont pas des teneurs de marché neutres.**
   - Ils fixent leurs prix pour exploiter les biais du public ([S9], [B7], [B8], [F43]).
   - Ils **limitent les gagnants** ([F37], [M9]).
   - Leurs cotes ne sont donc pas « efficientes » individuellement ([F47]). Cette inefficience **n'est pas durablement exploitable** à cause des limitations.

6. **La calibration compte plus que la précision.**
   - Il faut sélectionner les modèles par log-loss, Brier et calibration, jamais par précision ([F30], [F32], [M8]).
   - Le ROI n'est pas une mesure de qualité d'un modèle ([F31]).

7. **Le Kelly plein mène à la ruine** dès que les probabilités sont estimées.
   - Le **Kelly fractionnel**, avec une fraction réglée selon l'incertitude, est le meilleur choix pratique ([K3], [K4], [K5]).
   - Pour plusieurs matchs joués en même temps, il faut une optimisation conjointe ([K6]).

### 8.2 Classement des approches par force de la preuve

| Rang | Approche | Preuves principales | Force de la preuve | ROI documenté (conditions) | Principale limite |
|---|---|---|---|---|---|
| **A1** | **Value betting contre une référence efficiente** : consensus du marché dé-marginé, ou cote Pinnacle ou exchange. On parie chez un book grand public quand sa cote dépasse la cote juste. | [F37], [F36], [F43], [F47], [M9] | **Forte** : simulations sur 10 ans, argent réel, mécanisme compris | +3,5 % (clôture, meilleure cote parmi 32 books, 10 ans) ; +8,5 % en réel sur 265 paris ([F37]) | **Limitation des comptes** en quelques mois ; latence (environ 30 % des cotes déjà bougées) |
| **A2** | **Chercher la meilleure cote** (*line shopping*) et éviter les outsiders | [F44], [T8], [F41], [F42], [B4] | **Forte** comme condition nécessaire, mais pas suffisante | WElo : +3,6 % avec la meilleure cote parmi 11 books, **négatif** avec un seul book ([T8]) ; gros favoris : +4,45 % avec la meilleure cote ([F41]) | Peu de books ANJ ; cotes souvent corrélées entre opérateurs |
| **A3** | **Kelly fractionnel rétréci**, et optimisation conjointe des matchs simultanés | [K4], [K5], [K6], [K8] | **Forte** (théorie et expériences) | Ne crée pas d'edge : évite la ruine, maximise la croissance médiane | Suppose des probabilités calibrées |
| **B1** | **Modèles nourris d'informations au-delà des scores** : tirs, xG, compositions, notes des joueurs | [F26], [F39], [F40], [F16], [F27] | **Moyenne** : plusieurs études concordantes, mais backtests d'auteurs | +0,8 %/pari sur l'over/under sur 12 ans ([F39]) ; ≈ +10 à 15 % en simulation sur la Bundesliga ([F40]) ; « significatif » ([F16]) | Données xG désormais publiques, donc intégrées par le marché ; résultats par saison très variables |
| **B2** | **Intégrer le marché dans le modèle** (prior ou variable fondé sur les cotes) et **décorréler** les erreurs | [F10], [F14], [F45], [S7] | **Moyenne** : démonstration théorique et NBA 2007-2014 | Profits cumulés positifs en NBA ([S7]) | Données anciennes ; réglage délicat |
| **B3** | **Surréaction et stratégies à contre-courant** (séries, changement d'entraîneur, chocs structurels) | [F38], [F53], [F51], [F52], [B11] | **Moyenne à faible** : réel, mais petit et transitoire | « Profit soutenu » ([F38]) ; fenêtres d'environ un mois (COVID) | Moskowitz : ne couvre pas la marge sur les marchés américains ([B11]) |
| **B4** | **Biais de popularité, de sentiment et de nul** | [B6]–[B10], [B12], [F56] | **Faible** : résultats contradictoires selon les études | Variable | Le signe du biais change selon le marché et la période |
| **C1** | ML « pur » sur des données publiques de résultats | [F22], [T13], [F20], [F21] | La preuve est **négative** : ça ne bat pas le marché | ROI ≤ 0 à long terme ([T13]) | Le marché intègre déjà cette information |
| **C2** | Pronostiqueurs et experts | [F34], [S12] | La preuve est **négative** | Inférieurs au marché, voire au modèle naïf | — |
| **C3** | Paris en direct sur l'information publique, et « momentum » | [F54], [T3], [F55] | La preuve est **négative** | Pertes dans le cas du momentum ([F55]) | Seul un avantage de latence fonctionnerait, et il est neutralisé par les opérateurs |
| **C4** | « Systèmes » historiques publiés (règles NFL, totaux, petits échantillons) | [S13], [S4], [T11], [T12], [M6] | La preuve est **négative ou fragile** | Disparaît hors période | Biais de publication et surapprentissage |

### 8.3 Un profit durable est-il réaliste ? Réponse honnête

**Face aux lignes de clôture de Pinnacle : très difficile.**
- La clôture d'un marché liquide et « sharp » est le meilleur estimateur connu de la probabilité d'un événement ([M10], [F36], [F49]).
- La quasi-totalité des « profits » publiés repose sur l'une de ces quatre conditions :
  1. battre des books **grand public**, et non la clôture « sharp » ;
  2. disposer de la **meilleure cote parmi des dizaines de bookmakers** ;
  3. des cotes d'**ouverture** ou des **anciennes** périodes ;
  4. de **petits échantillons** non répliqués.
- Nous n'avons trouvé **aucune** étude à comité de lecture qui démontre un profit durable et **net de frictions** contre la clôture de Pinnacle sur les grands marchés.
- Les modèles publics les plus sérieux obtiennent, au mieux, un edge de **0 à 3 %** dans des conditions d'exécution idéalisées.

**Contre des bookmakers grand public : un profit est possible, mais borné.**
- La preuve la plus solide est la stratégie « consensus » de Kaunitz et al. ([F37]) : profitable en simulation (+3,5 % à la clôture sur 10 ans, +9,9 % avec des cotes prises quelques heures avant le match) **et** en argent réel (+6,2 % sur 672 paris en paper trading et en réel).
- Mais elle a été **arrêtée par la limitation des comptes**. Le profit est donc borné par la **capacité** (mises maximales × durée de vie des comptes), pas par l'edge.

**Ce qui distingue les « professionnels ».**
- Selon la littérature économique ([F49], [M9]), les parieurs gagnants durables opèrent sur des marchés « sharp » à fort volume (handicap asiatique), avec un **avantage informationnel ou de vitesse**, et souvent sous forme de syndicats.
- Ce modèle est **inaccessible** à un particulier en France.

### 8.4 Ce qui marche le mieux pour un parieur français limité aux opérateurs agréés ANJ (sans exchange)

**Contraintes structurelles.** Voir le document réglementaire du projet (`anj_reglementation_body.md`).
- **TRJ plafonné à 85 %** des mises en moyenne annuelle par opérateur. Les marges sur les marchés principaux sont donc plus élevées que chez Pinnacle (environ 2 à 3 %), et beaucoup plus élevées sur les marchés secondaires.
- **Pas d'exchange** ni de bookmaker « sharp » accessible légalement.
- Nombre limité d'opérateurs, dont les cotes sont souvent corrélées (fournisseurs de cotes communs `[?]`).
- **Limitation des comptes gagnants** courante, malgré la doctrine de l'ANJ (délibération 2021-C-01).

**Recommandations, par ordre de priorité, déduites de la littérature.**

1. **Utiliser Pinnacle ou l'exchange comme *référence de prix*, pas comme lieu de pari.**
   - Leurs cotes sont consultables. On les dé-margine (méthode **power** ou **Shin**, [F57]–[F59]) pour obtenir une « probabilité juste ».
   - On ne parie chez les opérateurs ANJ **que si** la cote proposée dépasse la cote juste d'une marge de sécurité, par exemple **edge ≥ 2 à 3 %** après prise en compte de l'incertitude.
   - C'est la transposition directe de [F37] et [F36], c'est-à-dire **la stratégie la mieux étayée**.
   - Indicateur de suivi : le **CLV contre la clôture Pinnacle** ([M10]).
2. **Exploiter les promotions** : cotes boostées, freebets, offres de bienvenue.
   - Ce n'est pas une stratégie académique, mais une **espérance positive arithmétiquement vérifiable** quand la cote boostée dépasse la cote juste de référence.
   - C'est probablement la **source d'EV positive la plus fiable** pour un parieur ANJ (budget promotionnel encadré par le TRJ, voir le document réglementaire). Elle se mesure exactement avec la même référence que le point 1.
3. **Chercher la meilleure cote sur tous les comptes ANJ** et **éviter les outsiders**, à cause du FLB ([B4], [F49], [T14]).
   - Sans line shopping, même un bon modèle est perdant ([T8]).
   - On privilégie les marchés où la marge française est la plus faible (en général le 1X2 et les vainqueurs de matchs de tennis sur les grands événements `[?]`, à mesurer).
4. **Ajouter un modèle « informationnel » seulement là où il apporte une information orthogonale au marché.**
   - Football : xG et tirs ([F40], [F26]), compositions et absences ([F16]), chocs structurels ([F51]–[F53]).
   - Tennis : WElo ou Elo avec marge de victoire par surface ([T7], [T8], [T9]).
   - Ce modèle sert de **filtre** combiné au signal de marché (point 1), et non de source unique. Il faut le valider par walk-forward, |z| > 3, DSR et PBO ([M1]–[M5]).
5. **Gestion de la mise.**
   - Kelly fractionnel **¼ à ½**, rétréci selon l'incertitude ([K4], [K5]).
   - Plafond par pari d'environ 1 à 2 % de la bankroll.
   - Optimisation conjointe des matchs simultanés ([K6]).
   - Suivi du drawdown ([K8]).
6. **Gérer la capacité.**
   - On répartit les mises entre opérateurs et on évite les schémas « sharp » évidents : uniquement des cotes en retard, des marchés obscurs, des mises au centime près.
   - On documente chaque limitation ([M9]).
   - Il faut accepter que **la durée de vie d'un compte gagnant soit finie**.

**Attentes réalistes.**
- Une approche disciplinée (points 1, 2, 3 et 5) peut viser un **ROI faiblement positif** (quelques %) sur un **volume limité**, principalement porté par les promotions et les écarts ponctuels entre books.
- Ce n'est **pas** une source de revenu fiable.
- Un modèle sportif seul, parié aux cotes d'un ou deux opérateurs ANJ, a une **espérance négative** selon l'essentiel de la littérature ([T8], [T13], [F22], [F44]).

### 8.5 Protocole minimal pour toute stratégie de la bibliothèque

| Étape | Règle | Références |
|---|---|---|
| Baselines obligatoires | (i) probabilités implicites dé-marginées (Shin et power) ; (ii) Elo ; (iii) Dixon-Coles pondéré ; (iv) pi-ratings + GBM ou CatBoost | [F2], [F11], [F12], [F21], [F57]–[F59] |
| Métriques de prévision | **Log-loss** (principale), Brier, RPS, calibration (ECE, diagrammes de fiabilité) | [F29], [F30], [F32], [M8] |
| Métriques de pari | CLV contre la clôture Pinnacle ; ROI avec intervalle bootstrap ; ROI sans les 1 % de meilleurs paris ; richesse médiane et quantiles ; drawdown maximal | [M10], [M6], [K5] |
| Significativité | Registre des essais ; \|z\| > 3 ; Deflated Sharpe ; PBO (CSCV) ; Reality Check ou SPA | [M1]–[M5] |
| Backtest | Walk-forward chronologique ; cotes **horodatées et exécutables chez les opérateurs ANJ** ; glissement ; mise maximale ; durée de vie des comptes ; filtrage des cotes aberrantes | [F23], [F37], [T8], [M6], [M9] |
| Robustesse | Plusieurs saisons et plusieurs ligues ; suivi **après** la mise en production ; comparaison à une stratégie aléatoire de même profil de cotes | [F48], [F37], [M6] |

---

## 9. Index des fiches

| ID | Fiche | Section |
|---|---|---|
| F1 | Maher (1982) : le Poisson indépendant attaque/défense | 1 |
| F2 | Dixon & Coles (1997) : correction des faibles scores et pondération temporelle | 1 |
| F3 | Rue & Salvesen (2000) : modèle bayésien dynamique | 1 |
| F4 | Karlis & Ntzoufras (2003) : Poisson bivarié et inflation des nuls | 1 |
| F5 | Karlis & Ntzoufras (2009) : loi de Skellam sur la différence de buts | 1 |
| F6 | Koopman & Lit (2015) : Poisson bivarié dynamique (espace d'états) | 1 |
| F7 | Ley, Van de Wiele & Van Eetvelde (2019) : comparaison de 10 modèles de force | 1 |
| F8 | Hubáček, Šourek & Železný (2021) : quarante ans de modèles fondés sur les scores | 1 |
| F9 | Goddard (2005) : modèles « buts » contre modèles « résultats » | 1 |
| F10 | Egidi, Pauli & Torelli (2018) : combiner historique et cotes dans un Poisson bayésien | 1 |
| F11 | Hvattum & Arntzen (2010) : Elo et logit ordonné | 1 |
| F12 | Constantinou & Fenton (2013) : pi-ratings | 1 |
| F13 | Constantinou, Fenton & Neil (2012, 2013) : réseaux bayésiens (pi-football) | 1 |
| F14 | Wunderlich & Memmert (2018) : Elo nourri par les cotes | 1 |
| F15 | Robberechts & Davis (2019) : ratings résultats contre buts (Coupe du monde) | 1 |
| F16 | Holmes & McHale (2024) : modèle fondé sur les notes des joueurs | 1 |
| F17 | Dubitzky, Lopes, Davis & Berrar (2019) : base ouverte et Soccer Prediction Challenge 2017 | 1 |
| F18 | Hubáček, Šourek & Železný (2019a) : gradient boosting relationnel (vainqueur 2017) | 1 |
| F19 | Berrar, Lopes & Dubitzky (2019) : connaissances métier en ML | 1 |
| F20 | Berrar, Lopes & Dubitzky (2024) : Soccer Prediction Challenge 2023 | 1 |
| F21 | Yeung, Bunker, Umemoto & Fujii (2024) : CatBoost et pi-ratings face au deep learning | 1 |
| F22 | Baboota & Kaur (2019) : ML sur la Premier League | 1 |
| F23 | Bunker & Thabtah (2019) : cadre méthodologique ML (SRP-CRISP-DM) | 1 |
| F24 | Bunker & Susnjak (2022) : revue du ML en sports collectifs | 1 |
| F25 | Wunderlich & Memmert (2021) : revue narrative de la prévision sportive | 1 |
| F26 | Wheatcroft (2021) : prédire les statistiques de match pour prédire le résultat | 1 |
| F27 | Mead, O'Hare & McMenemy (2023) : améliorer les modèles xG | 1 |
| F28 | Brechot & Flepp (2020) : l'aléa des résultats et l'xG | 1 |
| F29 | Constantinou & Fenton (2012) : le RPS comme règle de score | 1 |
| F30 | Wheatcroft (2021) : contre le RPS | 1 |
| F31 | Wunderlich & Memmert (2020) : le ROI n'est pas une mesure de précision | 1 |
| F32 | Walsh & Joshi (2024) : calibration plutôt que précision pour sélectionner le modèle | 1 |
| F33 | Forrest, Goddard & Simmons (2005) : les bookmakers, des prévisionnistes de plus en plus forts | 2 |
| F34 | Spann & Skiera (2009) : marchés prédictifs, cotes et pronostiqueurs | 2 |
| F35 | Štrumbelj & Robnik-Šikonja (2010) : toutes les cotes ne se valent pas | 2 |
| F36 | Franck, Verbeek & Nüesch (2010) : l'exchange plus précis que les bookmakers | 2 |
| F37 | Kaunitz, Zhong & Kreiner (2017) : battre les bookmakers avec leurs propres cotes | 2 |
| F38 | Wheatcroft (2020a) : surréaction des cotes aux séries de résultats | 2 |
| F39 | Wheatcroft (2020b) : un modèle rentable sur le marché over/under 2,5 | 2 |
| F40 | Wilkens (2026) : modèle xG simple et calibré sur la Bundesliga | 2 |
| F41 | Direr (2013) : parier sur les très gros favoris | 2 |
| F42 | Vlastakis, Dotsis & Markellos (2009) : arbitrages et stratégies simples en Europe | 2 |
| F43 | Franck, Verbeek & Nüesch (2013) : arbitrage bookmaker contre exchange | 2 |
| F44 | Angelini & De Angelis (2019) : efficience de 11 championnats européens | 2 |
| F45 | Hubáček & Šír (2023) : battre le marché avec un « mauvais » modèle | 2 |
| F46 | Goddard & Asimakopoulos (2004) : probit ordonné et paris de fin de saison | 2 |
| F47 | Elaad, Reade & Singleton (2020) : cotes non biaisées, bookmakers individuellement inefficients | 2 |
| F48 | Winkelmann, Ötting, Deutscher & Makarewicz (2024) : les inefficiences ne persistent pas | 2 |
| F49 | Hegarty & Whelan (2025) : structure de marché, bookmakers « sharp » et « soft » | 2 |
| F50 | Whelan (2024) : aversion au risque et FLB en cotes fixes | 2 |
| F51 | Winkelmann, Deutscher & Ötting (2021) : l'avantage du terrain disparu (COVID, Bundesliga) | 2 |
| F52 | Meier, Flepp & Franck (2021) : efficience semi-forte et matchs à huis clos | 2 |
| F53 | Bernardo, Ruberti & Verona (2019) : changement d'entraîneur sous-estimé | 2 |
| F54 | Croxson & Reade (2014) : les buts sont intégrés vite et complètement en direct | 2 |
| F55 | Ötting, Deutscher, Singleton & De Angelis (2022) : parier sur le « momentum » | 2 |
| F56 | Lezana (2026) : « peur du nul » et heuristiques | 2 |
| F57 | Shin (1991, 1993) : le modèle d'initiés | 2 |
| F58 | Štrumbelj (2014) : Shin bat la normalisation | 2 |
| F59 | Clarke, Kovalchik & Ingram (2017) : méthodes additive, multiplicative, Shin et « power » | 2 |
| F60 | Koning & Zijm (2023) : Shin contre normalisation, au niveau du match | 2 |
| F61 | Hegarty & Whelan (2024) : comment tester l'efficience | 2 |
| F62 | Groll, Ley, Schauberger & Van Eetvelde (2019) : forêt aléatoire hybride (tournois) | 2 |
| F63 | Fischer & Heuer (2024) : ML contre Poisson | 2 |
| T1 | Klaassen & Magnus (2001) : les points sont-ils i.i.d. ? | 3 |
| T2 | Klaassen & Magnus (2003) : prévoir le vainqueur avant et pendant le match | 3 |
| T3 | Easton & Uylangco (2010) : le marché in-play colle au modèle point par point | 3 |
| T4 | Barnett & Clarke (2005) : combiner les statistiques des joueurs | 3 |
| T5 | McHale & Morton (2011) : modèle de Bradley-Terry pour l'ATP | 3 |
| T6 | Kovalchik (2016) : à la recherche du « GOAT » de la prédiction au tennis | 3 |
| T7 | Kovalchik (2020) : Elo avec marge de victoire | 3 |
| T8 | Angelini, Candila & De Angelis (2022) : Weighted Elo (WElo) | 3 |
| T9 | Gorgi, Koopman & Lit (2019) : modèle dynamique de grande dimension | 3 |
| T10 | Ingram (2019) : modèle bayésien hiérarchique point-based | 3 |
| T11 | Sipko & Knottenbelt (2015) : ML pour le tennis professionnel | 3 |
| T12 | Lisi & Zanella (2017) : régression logistique et Grand Chelem | 3 |
| T13 | Wilkens (2021) : le ML ne bat pas le marché au tennis | 3 |
| T14 | Forrest & McHale (2007) : FLB positif dans tout l'éventail des cotes | 3 |
| T15 | Abinzano, Muga & Santamaria (2016, 2019) : FLB sur l'exchange (Betfair) | 3 |
| S1 | Lopez, Matthews & Baumer (2018) : quelle place pour le hasard selon les sports ? | 4 |
| S2 | Elo de FiveThirtyEight (NFL, NBA, tennis) : la référence des praticiens | 4 |
| S3 | Gandar, Dare, Brown & Zuber (1998) : parieurs informés et mouvements de ligne en NBA | 4 |
| S4 | Paul, Weinbach & Wilson (2004) : biais « under » sur les totaux NBA élevés | 4 |
| S5 | Štrumbelj & Vračar (2012) : simulation markovienne d'un match de basket | 4 |
| S6 | Manner (2016) : modèle dynamique NBA et combinaison avec les cotes | 4 |
| S7 | Hubáček, Šourek & Železný (2019b) : exploiter le marché NBA par le ML | 4 |
| S8 | Gandar, Zuber, O'Brien & Russo (1988) : rationalité du marché des spreads NFL | 4 |
| S9 | Levitt (2004) : les bookmakers exploitent les biais au lieu d'équilibrer | 4 |
| S10 | Paul & Weinbach (2002) : biais « under » sur les totaux NFL élevés | 4 |
| S11 | Glickman & Stern (1998) : modèle à espace d'états pour la NFL | 4 |
| S12 | Boulier & Stekler (2003) et Song, Boulier & Stekler (2007) : marché contre experts contre modèles (NFL) | 4 |
| S13 | Imbrogno & Staggs (2025) : les règles de pari NFL « rentables » ne tiennent pas | 4 |
| S14 | Woodland & Woodland (1994) et Gandar et al. (2002) : FLB inversé en MLB… puis non confirmé | 4 |
| S15 | Woodland & Woodland (2001) : FLB inversé en NHL | 4 |
| S16 | Buttrey (2016) : battre le marché NHL avec un modèle de Markov | 4 |
| S17 | Weissbock & Inkpen (2014) : un plafond de précision d'environ 62 % en NHL | 4 |
| S18 | O'Donoghue, Ball, Eustace, McFarlan & Nisotaki (2016) : modèles de la Coupe du monde 2015 | 4 |
| S19 | Scarf, Parma & McHale (2019) : taux de score et incertitude en rugby | 4 |
| S20 | Groll, Heiner, Schauberger & Uhrmeister (2020) : sous-dispersion des scores en handball | 4 |
| S21 | Karlis, Michels & Ötting (2025) : modéliser l'écart de buts en handball | 4 |
| S22 | Felice & Ley (2023) : apprentissage « statistically enhanced » en handball | 4 |
| S23 | Egidi & Ntzoufras (2020) : modèle bayésien unifié pour le volley | 4 |
| K1 | Kelly (1956) : le critère de Kelly | 5 |
| K2 | Thorp (1997, 2006/2008) : Kelly en blackjack, paris sportifs et bourse | 5 |
| K3 | MacLean, Thorp & Ziemba (2010) : bonnes et mauvaises propriétés de Kelly | 5 |
| K4 | Baker & McHale (2013) : Kelly « rétréci » sous incertitude des paramètres | 5 |
| K5 | Uhrín, Šourek, Hubáček & Železný (2021) : revue expérimentale des stratégies de mise | 5 |
| K6 | Whitrow (2007) : Kelly pour de nombreux paris simultanés | 5 |
| K7 | Grant, Johnstone & Kwon (2008) : stratégies optimales pour matchs simultanés | 5 |
| K8 | Busseti, Ryu & Boyd (2016) : Kelly sous contrainte de risque | 5 |
| K9 | Chu, Wu & Swartz (2018) : critères de Kelly modifiés | 5 |
| K10 | Rappel : allocation par portefeuille (Hubáček et al., 2019b) | 5 |
| M1 | Bailey, Borwein, López de Prado & Zhu (2014) : « pseudo-mathématiques et charlatanisme financier » | 6 |
| M2 | Bailey, Borwein, López de Prado & Zhu (2017) : probabilité de surapprentissage du backtest (PBO) | 6 |
| M3 | Bailey & López de Prado (2014) : le Sharpe ratio « dégonflé » | 6 |
| M4 | White (2000) et Harvey, Liu & Zhu (2016) : data snooping et seuil t > 3 | 6 |
| M5 | Vandenbruaene, De Ceuster & Annaert (2022) : 600 stratégies de handicap passées en revue | 6 |
| M6 | Clegg & Cartlidge (2025) : réplication et correction de « Betting on a buzz » | 6 |
| M7 | Winkelmann et al. (2024) : petits échantillons et faux positifs | 6 |
| M8 | Gneiting & Raftery (2007) : règles de score strictement propres | 6 |
| M9 | Preuves de la limitation des comptes par les bookmakers « soft » | 6 |
| M10 | La ligne de clôture comme estimateur le plus précis, et le CLV comme métrique | 6 |
| B1 | Thaler & Ziemba (1988) : les anomalies des paris mutuels | 7 |
| B2 | Snowberg & Wolfers (2010) : goût du risque ou mauvaise perception des probabilités ? | 7 |
| B3 | Cain, Law & Peel (2000) : le FLB dans le football britannique | 7 |
| B4 | Buhagiar, Cortis & Newall (2018) : pourquoi certains parieurs perdent plus que d'autres | 7 |
| B5 | Newall & Cortis (2021) : biais vers les outsiders, les favoris, ou les deux ? | 7 |
| B6 | Forrest & Simmons (2008) : sentiment dans le football espagnol | 7 |
| B7 | Franck, Verbeek & Nüesch (2011) : préférences sentimentales et structure du marché | 7 |
| B8 | Feddersen, Humphreys & Soebbing (2017) : sentiment mesuré par les réseaux sociaux | 7 |
| B9 | Braun & Kvasnička (2013) : sentiment national | 7 |
| B10 | Vergin & Sosik (1999) : avantage du terrain dans les matchs médiatisés (NFL) | 7 |
| B11 | Moskowitz (2021) : momentum et value dans les paris sportifs | 7 |
| B12 | Pope & Peel (1989) : premières inefficiences sur le nul | 7 |

## 10. Limites de cette revue

- **Vérification.**
  - Les fiches marquées `[TI]` ont été lues en texte intégral : Kaunitz et al., Levitt, Kovalchik, Angelini et al. (WElo), Sipko, Lisi & Zanella, Uhrín et al., Hegarty & Whelan, Buhagiar et al., Walsh & Joshi, Hubáček & Šír.
  - Les fiches `[R]` reposent sur le résumé officiel.
  - Les fiches `[S]` reposent sur des citations secondaires. **Leurs chiffres doivent être revérifiés avant toute citation publique.**
  - Exemple de l'utilité de cette prudence : deux résumés secondaires de Lisi & Zanella donnaient des chiffres faux (« +4,6 % » et « +15,9 % »). Le texte de l'article indique **+16,3 % sur 501 matchs** ([T12]).
- **Publications non consultées en entier.** Plusieurs articles d'éditeurs payants (Elsevier, Wiley, Springer) n'ont pas pu être lus en texte intégral. Les détails des seuils, échantillons et pages y sont signalés par `[?]`.
- **CLV.** La validation du CLV comme prédicteur du profit repose surtout sur la littérature de praticiens et sur la logique de l'efficience. Nous n'avons pas trouvé d'étude académique qui le teste directement sur des comptes de parieurs.
- **Biais de publication.** Les études qui trouvent un profit sont plus souvent publiées. Les réplications négatives ([S13], [M6], [F48]) suggèrent que le taux réel de stratégies gagnantes est inférieur à ce que laisse croire la littérature.
- **Périmètre.** Les courses hippiques, l'e-sport, le cricket et le MMA ne sont pas couverts en détail. Des références récentes existent, par exemple sur le FLB en MMA (2026) et en e-sport (2024).
