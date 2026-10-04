# Modèle buteurs football : résultats

> Généré par `scripts/football_buteurs.py`. Données Understat (5 grands championnats),
> apprentissage 2019-20 → 2022-23, **test hors échantillon 2023-24 → 2026-27** ;
> buts attendus des équipes tirés des cotes de clôture sans marge (football-data.co.uk).

## 1. Répartition des buts d'une équipe entre ses joueurs (sachant le nombre de buts)

Log-loss par but (plus bas = mieux)  159 541 lignes joueur-match :

| Méthode | Log-loss |
|---|---|
| modèle | 2.2386 |
| minutes × xG/90 (sans β) | 2.2630 |
| minutes seulement | 2.6265 |

Coefficients (β, appris sur 2019-20 → 2022-23) :

| Variable | β |
|---|---|
| log(minutes / 90) | +0.682 |
| log(xG/90 attendu, penaltys compris) | +1.131 |
| log(finition : buts / xG, rétréci) | +0.319 |
| défenseur | +0.187 |
| milieu | +0.175 |
| milieu offensif / ailier | +0.066 |
| moins de 5 matchs d'historique | -0.010 |

## 2. Probabilité de marquer (minutes réelles, λ de clôture)

159 480 joueurs-matchs :

| Méthode | Log-loss | Brier |
|---|---|---|
| modèle | 0.2510 | 0.0702 |
| minutes × xG/90 | 0.2532 | 0.0703 |
| minutes seulement | 0.2850 | 0.0770 |

Calibration (modèle) :

| Prédit (tranche) | Joueurs | Prédit | Observé |
|---|---|---|---|
| (0.0, 0.05] | 77709 | 2.6 % | 2.7 % |
| (0.05, 0.1] | 37523 | 7.1 % | 6.9 % |
| (0.1, 0.15] | 16380 | 12.3 % | 12.1 % |
| (0.15, 0.2] | 10439 | 17.3 % | 17.0 % |
| (0.2, 0.25] | 6873 | 22.3 % | 22.2 % |
| (0.25, 0.3] | 4416 | 27.3 % | 28.7 % |
| (0.3, 0.4] | 4282 | 34.1 % | 35.7 % |
| (0.4, 0.5] | 1333 | 44.0 % | 45.1 % |
| (0.5, 0.7] | 517 | 56.1 % | 59.0 % |
| (0.7, 1.0] | 8 | 73.4 % | 75.0 % |

## 3. Cote « si titulaire » (ce que le site affiche)

Titulaires réels, minutes **attendues** quand ils sont titulaires (rôle récent), remplaçants
résumés par la masse moyenne du banc (15.4 % des titulaires) ; 110 116 titulaires.
Log-loss 0.2896, Brier 0.0832.

| Prédit (tranche) | Joueurs | Prédit | Observé |
|---|---|---|---|
| (0.0, 0.05] | 41491 | 3.1 % | 3.1 % |
| (0.05, 0.1] | 28643 | 7.0 % | 6.6 % |
| (0.1, 0.15] | 13201 | 12.3 % | 12.1 % |
| (0.15, 0.2] | 9441 | 17.4 % | 17.0 % |
| (0.2, 0.25] | 6839 | 22.3 % | 21.5 % |
| (0.25, 0.3] | 4410 | 27.3 % | 27.8 % |
| (0.3, 0.4] | 4330 | 34.1 % | 33.2 % |
| (0.4, 0.5] | 1300 | 44.0 % | 43.4 % |
| (0.5, 0.7] | 455 | 55.6 % | 57.4 % |
| (0.7, 1.0] | 6 | 72.1 % | 66.7 % |

Par poste habituel :

| Poste | Joueurs | Prédit | Observé |
|---|---|---|---|
| milieux offensifs / ailiers | 17238 | 17.4 % | 16.9 % |
| défenseurs | 41087 | 4.0 % | 3.9 % |
| attaquants | 14581 | 27.1 % | 26.7 % |
| milieux | 37210 | 8.1 % | 7.8 % |

Par championnat :

| Championnat | Joueurs | Prédit | Observé |
|---|---|---|---|
| Bundesliga | 19060 | 11.6 % | 11.5 % |
| Premier League | 23800 | 11.2 % | 11.1 % |
| La Liga | 24237 | 9.8 % | 9.5 % |
| Ligue 1 | 19239 | 10.6 % | 10.3 % |
| Serie A | 23780 | 9.8 % | 9.3 % |

Buts contre son camp : 3.0 % des buts (aucun buteur crédité).

## 4. Réglage (ajustement 2019-20 → 2020-21, validation 2021-22 → 2022-23)

Retenu : demi-vie 20 matchs, 900 minutes fictives au taux du poste, 3 buts fictifs pour la finition.

| Demi-vie | Minutes fictives | Buts fictifs | Log-loss buteur | Log-loss par but |
|---|---|---|---|---|
| 20 | 900 | 3 | 0.25013 | 2.2068 |
| 20 | 900 | 6 | 0.25014 | 2.2068 |
| 20 | 900 | 12 | 0.25014 | 2.2069 |
| 38 | 900 | 6 | 0.25015 | 2.2071 |
| 38 | 900 | 12 | 0.25015 | 2.2071 |
| 38 | 900 | 3 | 0.25016 | 2.2071 |
| 38 | 1800 | 6 | 0.25016 | 2.2072 |
| 38 | 1800 | 12 | 0.25016 | 2.2072 |
| 38 | 1800 | 3 | 0.25017 | 2.2073 |
| 20 | 1800 | 3 | 0.25017 | 2.2073 |
