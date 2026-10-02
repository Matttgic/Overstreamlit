# S10 — Arbitrage (« surebets ») entre bookmakers français

> Statut : **théoriquement sans risque, pratiquement limité**. Non backtesté : nous
> n'avons pas d'historique simultané des cotes des bookmakers ANJ.

## Principe

Un arbitrage existe quand, en prenant la meilleure cote de chaque issue chez des
bookmakers différents, `Σ 1/cote_max < 1`. Exemple tennis : joueur A à 2,10 chez X,
joueur B à 2,05 chez Y → 1/2,10 + 1/2,05 = 0,964 → gain garanti de 3,7 % du total misé
avec des mises proportionnelles à 1/cote.

```
mise_i = Budget × (1/cote_i) / Σ_j (1/cote_j)
```

## Pourquoi c'est rare en France

- Le plafond de TRJ à 85 % pousse les marges vers le haut (≈ 5-15 % selon les marchés) :
  il faut un écart énorme entre deux opérateurs pour qu'un arbitrage apparaisse.
- Beaucoup d'opérateurs utilisent les mêmes fournisseurs de cotes (Kambi, Sportradar…),
  donc leurs cotes bougent ensemble. Depuis la fusion de ParionsSport en ligne dans
  Unibet (24/03/2026), il y a un opérateur indépendant de moins.
- Les surebets apparaissent surtout sur les cotes boostées et en direct (live), où les
  cotes peuvent être annulées (« erreur manifeste »).

## Risques

- Annulation d'une jambe (erreur de cote, retrait du joueur au tennis) → exposition.
- Limitation rapide des comptes « arbitragistes ».
- Délais : la cote change avant que la seconde mise soit placée.

## Outil

`sportpred.betting.odds.overround(odds)` < 1 détecte un arbitrage ; `sportpred.betting.kelly`
n'est pas nécessaire (répartition déterministe ci-dessus).
