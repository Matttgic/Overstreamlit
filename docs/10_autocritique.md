# Autocritique : ce qui peut être faux dans ce travail

> Demande explicite du propriétaire du dépôt : « vérifie ce que tu fais, critique-toi ».
> Ce document liste les faiblesses connues, du plus grave au moins grave, avec ce qui a
> été fait pour les limiter et ce qu'il reste à faire.

## 1. Le plus grand risque : les cotes « Max » ne sont pas celles d'un parieur français

Les stratégies gagnantes (S01, S02) parient à la **meilleure cote du marché mondial**
(colonne `Max` : meilleur prix parmi ~40 bookmakers, dont beaucoup ne sont pas agréés en
France). Contre un seul bookmaker (bet365, bwin), l'avantage devient faible ou nul.

- Ce qui a été fait : tests systématiques « Max » vs « FR = max(bet365, bwin) » vs
  « bet365 seul » ; les résultats des trois sont publiés.
- Ce qu'il reste à faire : **collecter les cotes réelles des 16 opérateurs ANJ** (il
  faut une IP française : Winamax, Betclic et Unibet bloquent les IP de datacenter) et
  mesurer combien de fois la meilleure cote FR dépasse la cote juste Betfair. Le scanner
  quotidien mesure cette performance sur bet365 et bwin, avec la CLV de chaque pari.

### Confirmation externe (ajoutée le 02/10/2026)

Un test indépendant sur les 5 opérateurs ANJ couverts par The Odds API (ryan00x/Bet-Model,
août 2026, 4 342 cotes, 99 matchs) n'a trouvé **aucune** cote à +2 % d'EV contre
Pinnacle ; la meilleure cote française valait 0,936 × Pinnacle en médiane. Le risque n°1
ci-dessus est donc réel : en France, l'avantage mesuré sur la « meilleure cote mondiale »
ne se transpose presque pas aux marchés principaux. Il reste les cotes boostées, les
promotions, les paris joueurs et la réactivité à l'information.

## 2. Erreurs de cotes et cotes périmées

Une partie des « value bets » à la cote Max sont des cotes erronées ou périmées qui
auraient été annulées ou refusées. Le plafond `EV ≤ 30 %` en retire une partie, pas tout.
Le ROI réel serait donc plus faible que le ROI backtesté.

## 3. Tests multiples

Plus de 300 configurations ont été testées sur le football. Avec un seuil de 5 %, on
attend ~15 « succès » par pur hasard. Défenses mises en place :

- séparation dev (2012-2019) / test (2019-2026), choix des paramètres sur dev seulement ;
- échantillon **totalement indépendant** (16 championnats extra, ~63 000 matchs) ;
- cohérence entre sports (tennis ATP et WTA, football principal et extra).

Ce n'est pas une correction formelle (Bonferroni exigerait p < 0,00017). Les résultats
S01 sur l'échantillon extra et en tennis ATP (p(ROI ≤ 0) < 0,001 sur des milliers de
paris) passeraient néanmoins ce seuil ; les autres non.

## 4. L'échantillon de conception n'est pas vierge

Les familles de stratégies testées viennent de la littérature (Kaunitz et al. 2017,
Buchdahl), qui a elle-même utilisé des données proches (football-data, 2005-2015). Notre
période test 2019-2026 est postérieure à ces publications, ce qui en fait un vrai test
hors échantillon de leurs idées — mais pas de leurs données de 2005-2015.

## 5. Non-stationnarité

En tennis, l'avantage a disparu en 2014-2016, puis est revenu. Rien ne garantit qu'il
existera en 2027. La disparition de Pinnacle (API fermée en juillet 2025) change aussi la
structure du marché : la référence devient Betfair Exchange, moins liquide sur les petits
championnats. **Le backtest « Betfair comme référence » ne couvre que 2024-2026.**

## 6. Les modèles statistiques sont standards, pas « état de l'art »

Elo, pi-ratings, Dixon-Coles et LightGBM sur statistiques de match sont des modèles
solides mais classiques. Des modèles avec compositions d'équipes, blessures, xG par
joueur ou données de tracking pourraient faire mieux. Ils n'ont pas été testés faute de
données gratuites historiques. Mais la littérature (Hubáček 2019, Wunderlich & Memmert
2020, Walsh & Joshi 2024) indique que même les meilleurs modèles publiés battent
rarement le marché de clôture.

## 7. Limites de mise et fermeture de comptes

Aucune simulation ne peut modéliser précisément quand un bookmaker limite un compte. Les
simulations Kelly plafonnent la mise (50 à 100 €) mais un compte gagnant peut être limité
à quelques euros après quelques semaines (cf. Kaunitz et al., limités après 5 mois).

## 8. Choix de modélisation discutables

- Tennis : matchs avec abandon exclus (les règles de règlement varient selon les
  bookmakers) → léger biais.
- Football : la colonne « ouverture » de football-data est relevée le vendredi ; selon
  l'heure à laquelle vous pariez, la cote disponible diffère.
- Extra-championnats : on parie à la cote de clôture Max contre la clôture Pinnacle, ce
  qui suppose de parier à la dernière minute.
- NBA : deux sources fusionnées (SBR jusqu'à 2020, wippa ensuite), noms d'équipes
  harmonisés à la main.

## 9. La recherche documentaire a été faite en partie par des agents automatiques

Les dossiers 01 à 04 ont été produits par des agents de recherche (avec liens vers les
sources primaires, niveau de fiabilité indiqué, incertitudes listées). Des erreurs de
détail sont possibles : **vérifier les sources avant toute décision**, en particulier
juridique ou fiscale.

## 10. Vérifications effectuées

- 15 tests unitaires (dé-margination, Kelly, RPS, gradient Dixon-Coles vérifié
  numériquement, absence de fuite d'information dans Elo/pi-ratings, simulateur).
- Variables de forme vérifiées contre un calcul manuel (PSG, écart 0,0).
- L'ancien système a été audité et sa stratégie rejouée proprement (toujours perdante).
- Les résultats « trop beaux » (Kelly → millions d'euros) ont été identifiés comme
  artefacts et corrigés par un plafond de mise.
