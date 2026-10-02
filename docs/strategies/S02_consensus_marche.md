# S02 — Consensus du marché (« Beating the bookies with their own numbers »)

> Statut : ✅ variante de S01 utilisable **sans** bookmaker sharp : la référence est la
> moyenne de tous les bookmakers. Code : `strategies.kaunitz_probs`, famille `consensus`.

## Principe (Kaunitz, Zhong & Kreiner, 2017)

La cote moyenne de ~40 bookmakers est une excellente prévision (« sagesse des foules »).
Probabilité de consensus : `p = 1/cote_moyenne − α` (α ≈ 0,034, marge moyenne), ou la
moyenne sans marge (méthode power). On parie quand un bookmaker offre une cote dont l'EV
contre ce consensus dépasse un seuil.

## Résultats (football, 22 championnats, cotes d'ouverture)

| Variante (choisie sur 2012-2019) | dev | test 2019-2026 |
|---|---|---|
| Moyenne sans marge vs meilleure cote, EV ≥ 0 %, cote ≤ 3,5 | +1,3 % (n = 28 790) | **+2,4 %** (n = 19 336, IC +1,0/+3,9) |
| Moyenne sans marge vs meilleure cote, EV ≥ 5 %, cote ≤ 3,5 | +15,5 % (n = 883) | +17,2 % (n = 327, IC +3,4/+31,2) |
| Kaunitz (α = 0,034) vs meilleure cote, EV ≥ 5 %, cote ≤ 10 | +18,8 % (n = 410) | +38,4 % (n = 154, IC +12,9/+63,6) |
| Moyenne sans marge vs bet365/bwin, EV ≥ 0 %, cote ≤ 3,5 | −1,1 % (n = 3 293) | +5,7 % (n = 1 905, IC +0,5/+11,3) |

## Interprétation critique

- La version à gros volume (EV ≥ 0 %) donne l'ordre de grandeur crédible : **+1 à +3 %**.
- Les versions à seuil élevé (+17 % à +38 %) portent sur peu de paris, souvent à des
  cotes « Max » aberrantes qu'un bookmaker aurait annulées : à ne pas extrapoler.
- Contre les seuls bookmakers « FR », le résultat change de signe entre dev et test :
  pas assez robuste seul.
- Kaunitz et al. ont été **limités par les bookmakers** après quelques mois de gains.

## Quand l'utiliser

Pour les compétitions où Betfair Exchange est peu liquide (pas de cote sharp fiable) :
prendre la moyenne des cotes de nombreux bookmakers comme référence, et ne jouer que les
écarts nets (EV ≥ 3-5 %) sur des cotes ≤ 3,5.
