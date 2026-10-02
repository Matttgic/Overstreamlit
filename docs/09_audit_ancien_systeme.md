# Audit de l'ancien système (« FootPredictor Pro », app.py jusqu'à février 2026)

> Objectif : comprendre **pourquoi** l'ancien robot perdait, pour ne pas reproduire ses
> erreurs. Les chiffres viennent de `historique_paris.csv` (86 paris enregistrés du
> 03/01/2026 au 06/02/2026 par la GitHub Action quotidienne).

## 1. Résultats réels

| Indicateur | Valeur |
|---|---|
| Paris réglés | 83 (39 gagnés, 44 perdus, 3 jamais réglés) |
| Mise totale | 1 660 € (20 € par pari, toujours) |
| Profit | **−115,40 €** |
| ROI | **−6,95 %** |
| Taux de réussite observé | 47,0 % |
| Probabilité **annoncée** moyenne | 66,9 % |
| Probabilité implicite des cotes (1/cote) | 51,1 % |
| Brier score du modèle | 0,300 |
| Brier score du marché (cotes) | 0,250 (meilleur) |

**Le modèle annonçait 67 % de réussite et en a obtenu 47 %.** Si ses probabilités avaient
été justes, obtenir 39 succès ou moins sur 83 aurait eu une probabilité de **0,015 %**.
Ce n'est pas de la malchance : le modèle était massivement **sur-confiant**.

Calibration par tranche de probabilité annoncée :

| Proba annoncée | n | Réussite observée |
|---|---|---|
| < 60 % (moy. 52 %) | 22 | 36 % |
| 60-70 % (moy. 65 %) | 28 | 61 % |
| > 70 % (moy. 78 %) | 33 | **42 %** |

Les paris jugés « les plus sûrs » ont été les pires.

## 2. Les causes (lecture du code)

1. **Mauvaises équipes** : les noms de l'API (api-sports) étaient rapprochés des noms
   football-data par `difflib.get_close_matches(cutoff=0.4)`, un seuil très permissif.
   Les notes n'étant calculées que sur 2023/24 et 2024/25, les **promus 2025/26
   n'existaient pas** et étaient associés à une autre équipe. Exemples dans l'historique :
   « Tottenham vs **Salernitana** », « Genoa vs **Paris SG** », « Fiorentina vs
   **Clermont** », « Lens vs **Fulham** », « Strasbourg vs **Bayern Munich** »,
   « Lens vs **Nott'm Forest** ». Une partie des paris portait donc sur des probabilités
   calculées pour **un autre match**.
2. **Données périmées** : saisons codées en dur (`["2425", "2324"]`, `season: 2025`).
   En janvier 2026, la saison en cours n'était pas utilisée pour les notes.
3. **Modèle sur-ajusté** : 5 passes de descente de gradient sur les mêmes matchs, sans
   validation, sans pondération temporelle ; correction des 0-0 ad hoc (×0,9).
4. **Pas de référence de marché** : l'« edge » `p − 1/cote ≥ 5 %` comparait une
   probabilité sur-confiante à la cote. Avec un modèle biaisé de +15 points, presque tout
   devient un « value bet ».
5. **Kelly inopérant** : `min(kelly × 0,25 ; 2 %)` plafonnait toujours à 2 % → mise fixe
   de 20 €, sans lien avec l'avantage estimé.
6. **Erreurs silencieuses** : `except: continue` partout ; trois paris jamais réglés.
7. **Dépendance à une clé API** (api-sports, quota limité) alors que football-data
   fournit gratuitement les matchs à venir avec leurs cotes.

## 3. Rejouer la même idée proprement

La stratégie « Over 2.5 quand le modèle voit ≥ 5 points d'edge » a été rejouée sur
20 ans avec un Dixon-Coles **correct** (walk-forward, bonnes équipes, pondération
temporelle) : voir `results/football/grille_strategies_over_under.csv`, ligne
« ANCIEN SYSTÈME ». Elle reste **perdante** (voir [07_resultats_football.md](07_resultats_football.md)) :
même bien implémenté, un modèle de buts seul ne bat pas le marché des Over/Under.

## 4. Ce que le nouveau système change

| Ancien | Nouveau |
|---|---|
| Correspondance floue des noms | Mêmes noms partout (football-data → football-data), aucune correspondance floue |
| Modèle seul | Probabilité de référence = **marché sharp** (Betfair Exchange / Pinnacle), modèle en option |
| Edge vs cote brute | EV vs **probabilité sans marge** du marché sharp |
| Mise fixe 20 € | Kelly ¼ plafonné à 2 % (paramétrable) |
| Over 2.5 seulement, 5 ligues | 1N2 sur 22 championnats (+ extension possible) |
| Clé API payante/quotas | 100 % gratuit, sans clé |
| Pas de backtest | Backtest 2012-2026 avec IC, CLV, dev/test |
| Erreurs silencieuses | Erreurs visibles, tests unitaires |
