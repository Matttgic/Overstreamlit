# Résultats — tennis, basket (NBA), hockey (NHL), football américain (NFL), baseball (MLB), MMA (UFC)

> Tableaux complets : [resultats/autres_sports.md](resultats/autres_sports.md) (générés
> automatiquement). Scripts : `scripts/multisport.py`, `scripts/tennis_strategies.py`.
> Tous ces sports figurent sur la liste ANJ (voir [01_reglementation_ANJ.md](01_reglementation_ANJ.md)) :
> tennis ATP/WTA (hors ITF et petits Challengers), NBA, NHL, NFL, MLB, UFC (cartes principales).

## 1. Données utilisées (gratuites, vérifiées le 02/10/2026)

| Sport | Source | Période | Cotes |
|---|---|---|---|
| Tennis ATP | miroir GitHub de tennis-data.co.uk | 2000-09/2026 (≈ 67 000 matchs) | Pinnacle, bet365, max, moyenne, Betfair Exchange |
| Tennis WTA | idem | 2007-09/2026 | idem |
| NBA | archive SportsbookReview + wippa-nba-data | 2011-2025 | moneyline de clôture |
| NHL | archive SportsbookReview | 2011-2021 | moneyline ouverture **et** clôture |
| NFL | nflverse | 2006-2026 | moneyline de clôture |
| MLB | Oddsportal (Hugging Face) | 2006-2024 | moneyline |
| UFC | ultimate_ufc_dataset | 2010-03/2026 | moneyline |

## 2. Le marché bat systématiquement le modèle Elo

Log-loss sur la période de test (plus bas = meilleur) :

| Sport | Elo calibré | Marché sans marge | Mélange marché + Elo |
|---|---|---|---|
| Tennis ATP | 0,609 | **0,579** | 0,579 |
| Tennis WTA | 0,619 | **0,589** | 0,589 |
| NBA | 0,629 | **0,600** | 0,599 |
| NHL | 0,675 | **0,665** | 0,665 |
| NFL | 0,635 | **0,609** | 0,610 |
| MLB | 0,678 | **0,671** | 0,671 |
| UFC | 0,679 | **0,604** | 0,604 |

Le mélange (régression logistique sur les deux) n'améliore pas le marché : **l'Elo
n'apporte aucune information que les cotes n'ont pas déjà**. Conséquence directe :
les stratégies « value betting avec l'Elo » perdent dans tous les sports (ROI de −2 % à
−9 % en test). C'est exactement ce que prédit la littérature (Kovalchik 2016 pour le
tennis, Hubáček et al. 2019 pour la NBA).

## 3. Ce qui fonctionne : comparer les cotes (« line shopping ») contre un marché sharp

### Tennis — la stratégie la plus solide de tout le projet hors football

Règle : probabilité juste = cotes Pinnacle sans marge (Betfair Exchange depuis 02/2026) ;
on parie quand la **meilleure cote disponible** donne une EV > 2 %.

| | Période dev | Période test |
|---|---|---|
| ATP | +3,4 % (IC 95 % 0,0 à +6,5 %, n = 6 246) | **+5,0 %** (IC +2,7 à +7,3 %, n = 9 719) |
| WTA | +4,1 % (IC +0,9 à +7,2 %, n = 5 869) | +2,3 % (IC −0,2 à +4,7 %, n = 8 350) |

- positive **14 années sur 17** (2010-2026), sur terre battue (+5,3 %), gazon (+6,6 %)
  et dur (+2,1 %) ;
- **contre bet365 seul**, le même filtre ne gagne rien de significatif (ATP test
  +2,9 %, IC −4,2 à +10,3 % ; WTA −3,0 %). L'avantage vient du fait de pouvoir choisir
  **la meilleure cote parmi beaucoup de bookmakers**.
- Autocritique : avec un seuil d'EV de 5 % (le meilleur sur la période dev), le WTA
  devient nul en test (−0,3 %). Le seuil de 2 % est plus robuste. La sélection d'un
  seuil sur la période dev a donc un coût : c'est documenté, pas caché.

Simulation de bankroll (période test, 1 000 € au départ, mises plafonnées à 50 €) :

| Gestion | Paris | ROI | Bankroll finale | Drawdown max |
|---|---|---|---|---|
| Mise fixe 10 € | 18 023 | +3,6 % | 7 441 € | **94 %** |
| Kelly ¼ (≤ 2 %, ≤ 50 €) | 18 023 | +4,4 % | 30 227 € | 68 % |
| Kelly ½ (≤ 5 %, ≤ 50 €) | 18 023 | +4,2 % | 31 616 € | 92 % |

Le drawdown de 94 % n'est pas une erreur de calcul : entre 2014 et 2016 la stratégie
n'avait plus d'avantage, et la bankroll est descendue de 1 132 € à 69 € (avril 2016)
avant de remonter. **Une stratégie gagnante peut quand même vous ruiner si la mise est
trop forte.**

### NHL — la CLV prédit le profit

Avec les cotes d'ouverture et de clôture : parier à l'ouverture le côté dont la cote
**va baisser** de plus de 2 % rapporte **+6,7 %** en test (IC +1,0 à +12,3 %, n = 1 569) ;
le côté dont la cote va monter perd −7,1 % (n = 8 071). Ce n'est pas une stratégie
(on ne connaît pas le futur), c'est la **preuve que battre la cote de clôture = gagner**.
Cela justifie d'utiliser la CLV comme indicateur principal de vos paris réels.

## 4. Biais favori / outsider (FLB) : réel, mais pas exploitable seul

| Sport | Gros favoris (cote < 1,3), test | Gros outsiders (cote > 4), test |
|---|---|---|
| Tennis ATP | −0,6 % | **−14,8 %** |
| Tennis WTA | −0,4 % | **−19,5 %** |
| NFL | −1,8 % | −13,6 % |
| UFC | +2,1 % (IC −0,9 à +5,1 %) | **−38,9 %** |
| NBA | −4,9 % | −2,4 % |

Les outsiders sont systématiquement sur-payés par les parieurs (et donc mal payés par
les cotes). Parier les favoris perd **moins**, mais ne gagne pas de façon significative
(à l'exception possible des gros favoris UFC, p = 0,09 : à surveiller, pas à jouer).
**Leçon pratique : éviter les grosses cotes et les combinés d'outsiders.**

## 5. Conclusions par sport

| Sport | Verdict | Ce qu'il faut faire |
|---|---|---|
| Tennis | ✅ line shopping vs Pinnacle/Betfair rentable | Comparer les cotes de plusieurs bookmakers ANJ contre la cote juste Betfair |
| NHL / NBA / NFL / MLB | ⚠️ aucune stratégie modèle rentable | Utiliser uniquement la comparaison de cotes ; viser la CLV |
| UFC | ⚠️ FLB extrême | Ne jamais jouer les gros outsiders |
| Tous | ❌ modèles Elo seuls | Ne pas parier sur la base d'un Elo/ML contre le marché |
