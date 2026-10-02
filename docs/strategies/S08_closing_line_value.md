# S08 — La Closing Line Value (CLV) : l'indicateur qui dit si vous êtes bon

## Définition

```
CLV = cote_obtenue / cote_juste_de_clôture − 1
```

où la cote juste de clôture est la dernière cote du marché sharp (Pinnacle, ou Betfair
Exchange depuis 2025) **sans marge**. Une CLV moyenne de +3 % signifie que vous avez
battu le prix final du marché de 3 %.

## Pourquoi c'est plus utile que le ROI

- Le ROI demande des **milliers** de paris pour sortir du bruit (écart-type ≈ 1/√n).
- La CLV a une variance bien plus faible : quelques centaines de paris suffisent.
- La cote de clôture du marché sharp est le meilleur prédicteur connu (voir les tableaux
  de qualité : le marché de clôture a le meilleur RPS de tous les modèles).

## Preuves dans nos données

- **NHL (2017-2021)** : le côté dont la cote baisse entre ouverture et clôture rapporte
  +6,7 % (IC +1,0 à +12,3 %) ; celui dont la cote monte perd −7,1 %.
- **Football** : dans la grille de stratégies, les familles à CLV positive (sharp, consensus)
  sont celles qui gagnent ; les modèles statistiques ont une CLV négative et perdent
  (voir [07_resultats_football.md](../07_resultats_football.md)).

## Comment l'utiliser

1. Notez pour chaque pari réel la cote obtenue et l'heure.
2. Après le match, relevez la cote de clôture Betfair Exchange (ou la colonne `BFEC*`
   du fichier football-data publié le lundi/jeudi).
3. Suivez la CLV moyenne : si elle est négative après 200 paris, arrêtez la stratégie,
   même si le ROI est positif (c'est probablement de la chance).

Le scanner (`scripts/daily_scan.py`) le fait **automatiquement** : au règlement de
chaque pari, il lit la cote de clôture Betfair Exchange (`BFEC*`) dans les résultats
football-data, calcule la CLV et l'affiche dans `picks/bilan.md`.
