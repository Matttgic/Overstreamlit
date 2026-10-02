# S03 — Parier avec un modèle statistique seul (Elo, pi-ratings, Dixon-Coles, ML)

> Statut : ❌ **perdant dans tous les sports testés**. Les modèles restent utiles pour
> comprendre, simuler et détecter des anomalies, pas pour parier contre les cotes.

## Ce qui a été testé

| Sport | Modèles | Matchs (test) | Meilleur modèle vs marché |
|---|---|---|---|
| Football (22 champ.) | Elo, pi-ratings, Dixon-Coles hebdo, LightGBM (stats de match) | 48 394 | RPS 0,2076 vs 0,2041 (marché ouverture) |
| Tennis ATP / WTA | Elo dynamique + Elo surface + classement | 26 451 / 22 272 | log-loss 0,609 vs 0,579 |
| NBA, NHL, NFL, MLB | Elo (avantage terrain, régression saisonnière, marge NFL) | 2 800 à 20 300 | toujours moins bon |
| UFC | Elo dynamique | 3 821 | log-loss 0,679 vs 0,604 |

## Rentabilité (value betting avec le modèle, période test)

- Football : −2 % à −10 % selon la cote utilisée, CLV négative partout.
- Tennis : −7,0 % à −9,1 % ; NBA −0,2 % à −1,8 % ; NHL −4,4 % à −5,5 % ; NFL −7,1 % à
  −8,1 % ; MLB −3,7 % à −4,6 % ; UFC −3,1 % à −5,9 %.

## Pourquoi

Les cotes intègrent tout ce que contiennent nos modèles (résultats, buts, tirs, forme)
**plus** ce qu'ils ignorent : compositions d'équipe, blessures, motivation, météo,
argent des parieurs informés. Les « value bets » d'un modèle sont donc surtout ses
**erreurs** : le modèle s'écarte du marché, et c'est le marché qui a raison. C'est
exactement ce qui est arrivé à l'ancien système ([audit](../09_audit_ancien_systeme.md)).

La littérature va dans le même sens : Soccer Prediction Challenges 2017 et 2023,
Hubáček et al. (2019, 2022), Kovalchik (2016) en tennis, Walsh & Joshi (2024) et son
corrigendum (2025).

## Ce que les modèles apportent quand même

- Une **probabilité pour les marchés sans cote sharp** (sélections nationales : l'Elo
  des sélections atteint un RPS de 0,174 contre 0,228 pour une prédiction naïve).
- Des simulations (classements finaux, qualifications).
- Un contrôle de cohérence : un écart énorme entre modèle et marché signale souvent une
  information (blessure, rotation) à vérifier, pas un pari.
