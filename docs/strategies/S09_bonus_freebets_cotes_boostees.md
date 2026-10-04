# S09 — Bonus, freebets et cotes boostées : la seule espérance positive « garantie »

> Statut : **stratégie mathématiquement positive, à faible volume**. Non backtestée
> (pas d'historique public des promotions), mais l'espérance se calcule exactement.
> Cadre légal : voir [01_reglementation_ANJ.md](../01_reglementation_ANJ.md) — l'ANJ
> recommande de plafonner l'offre de bienvenue à 100 € ; les promotions comptent dans le
> TRJ plafonné à 85 % des opérateurs.

## 1. Valeur d'un freebet (mise offerte, mise non remboursée)

Un freebet de montant F placé à la cote o rapporte `F × (o − 1)` si le pari gagne, 0
sinon. Avec la probabilité juste p (issue du marché sharp sans marge) :

```
EV(freebet) = p × F × (o − 1)
```

Si la cote est « juste » (p = 1/o) : `EV = F × (1 − 1/o)`. La valeur d'un freebet
**augmente avec la cote** : 50 % de F à cote 2, 75 % à cote 4, 90 % à cote 10.
→ **Placer les freebets sur des cotes élevées (3 à 6) mais justes**, idéalement là où le
bookmaker offre une cote ≥ cote juste (outil : `sportpred.betting.odds.fair_odds`).

Exemple : freebet de 10 € à 4,0 sur un résultat dont la cote juste (Betfair, sans
marge) est 4,2 → p = 0,238 ; EV = 0,238 × 10 × 3 = **7,14 €**.

## 2. Valeur d'une cote boostée

Une cote boostée o_b sur une issue de cote juste o_j a une espérance par euro misé
`o_b / o_j − 1`. Exemple : PSG gagne boosté de 1,50 à 2,00, cote juste 1,55 :
EV = 2,00/1,55 − 1 = **+29 %** (mais mise maximale souvent limitée à 10-20 €).

Règle : **jouer tous les boosts dont la cote boostée dépasse la cote juste**, à la mise
maximale autorisée. Ne PAS jouer un boost qui reste sous la cote juste (fréquent sur les
combinés « boostés »).

## 3. Remboursement en freebet si le pari perd (« pari remboursé »)

Si la mise S est remboursée en freebet en cas de perte, et qu'on valorise le freebet à
une fraction v de sa valeur (≈ 0,7 si on le joue vers cote 3-4) :

```
EV = p × S × (o − 1) − (1 − p) × S + (1 − p) × v × S
```

## 4. Risques et limites

- Ces offres sont limitées en montant (bienvenue ≤ 100 € recommandé) et en fréquence.
- Les conditions (cote minimale, délai, mise de conversion) changent l'EV : lire les CGU.
- La pratique « sans aléa » (couvrir un freebet sur un autre opérateur) est une **zone
  grise** fiscale et contractuelle (voir dossier ANJ, §10) ; les opérateurs peuvent
  fermer les comptes « chasseurs de bonus ».
- Jouer de façon responsable : l'intérêt d'un bonus ne justifie pas d'augmenter ses
  mises habituelles.

## 5. Évaluation automatique des cotes boostées (tableau de bord, section « Cotes boostées »)

Code : `sportpred/live/boosts.py`, grille des scores `sportpred/models/score_grid.py`.

1. **Lecture des boosts** : Unibet.fr (page publique `/cotes-boostees`, lue par GitHub : cote
   d'origine, cote boostée et mise maximale sont dans le libellé, ex. « Roosters gagne et X
   marque un essai (2,10 -> 2,50 / Mise max 25 €) ») ; Winamax lu par le téléphone à chaque
   collecte (rubrique « Cotes boostées », sport 100000 : libellé, cote d'origine `previousOdd`,
   cote boostée, mise max dans le titre du pari, une douzaine de boosts par jour, tous sports).
   Betclic : la page ne contient pas les boosts au chargement (04/10/2026), lecture à l'étude.
2. **Libellé → jambes** : « X gagne », « victoire de X », « match nul », « X ne perd pas »,
   « X gagne à la mi-temps et à la fin du match », « X marque dans les deux mi-temps »,
   « les deux équipes marquent », « plus / moins de N,5 buts », « au moins k buts », « X gagne
   avec k buts d'écart », « X gagne sans encaisser de but », « X marque » (équipe ou joueur),
   « X marque k buts ou + », « doublé », reliées par « et » / « & ». Surnoms courants reconnus
   (OM, OL, LOSC, PSG, Barça, Juve…) et noms de pays traduits (« Pays-Bas » → Netherlands).
   Libellé non reconnu → « non évaluable » (jamais deviné).
3. **Probabilité juste**, dans cet ordre :
   - le même pari chez Pinnacle (vainqueur, nul, total, les deux marquent) ;
   - un combiné que Pinnacle publie lui-même (victoire + les deux marquent, victoire / nul +
     plus ou moins de 2,5, les deux marquent + plus de 2,5, écart, victoire sans encaisser,
     buts d'une équipe) ;
   - sinon la **grille des scores** : deux lois de Poisson avec correction de Dixon-Coles,
     calées sur P(dom), P(nul) et les totaux Pinnacle ; avec un joueur, sa part des buts de
     l'équipe vient du modèle buteurs ([S12](S12_buteurs_football.md), « si titulaire ») et
     P(joueur marque | l'équipe marque k buts) = 1 − (1 − 0,97·s)^k.
4. **Verdict** : « à jouer » si cote boostée ≥ cote juste × 1,03 (Pinnacle) ou × 1,08 (grille
   ou modèle) ; ajouté à « À jouer maintenant » avec une mise Kelly ¼ plafonnée à 2 % de la
   bankroll **et** à la mise maximale du boost.

Contrôle de la grille (03/10/2026, 16 matchs des 5 grands championnats) : face aux combinés
publiés par Pinnacle, écart absolu moyen 0,4 à 1,7 point de probabilité (score exact, victoire
+ total, écart, nombre de buts) ; « les deux équipes marquent » sous-estimé de 1,8 point en
moyenne, d'où la priorité donnée aux prix Pinnacle quand ils existent.

Premier relevé Winamax (04/10/2026, 12 boosts) : les deux boosts évaluables étaient **sous** la
cote juste — « Pays-Bas gagne et les deux équipes marquent » 2,35 → 2,50 pour une cote juste
Pinnacle de 2,73 (EV −8,5 %), « Allemagne marque dans les deux mi-temps » 2,35 → 2,65 pour 2,75
(EV −3,8 %). Un boost n'est donc pas une valeur en soi : seule la comparaison à la cote juste
compte. Les 10 autres (joueurs en NFL, MLB, rugby, WNBA, combinés multi-matchs, hockey)
restent non évalués.
