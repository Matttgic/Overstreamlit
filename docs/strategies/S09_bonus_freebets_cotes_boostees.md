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
