# S06 — Over/Under 2.5 buts (stratégie de l'ancien système)

> Statut : ❌ **perdante avec un modèle**, ✅ possible en « sharp vs soft » (S01).

## Rejouer l'ancien système correctement

Règle d'origine : parier « Over 2.5 » quand `p_modèle − 1/cote ≥ 5 points`.
Rejouée avec un Dixon-Coles walk-forward correct (bonnes équipes, pondération
temporelle) aux cotes bet365, 2019-2026 : **−3,0 %** sur 4 445 paris
(IC 95 % −5,7 % à −0,1 %). En réel (janvier-février 2026, modèle buggé) : −6,95 %.

## Toutes les variantes « modèle »

| Modèle | vs bet365 | vs Pinnacle | vs meilleure cote |
|---|---|---|---|
| Dixon-Coles | −5,7 % à −5,9 % | −4,7 % à −4,9 % | −2,5 % à −2,9 % |
| LightGBM Over/Under | −4,7 % à −7,1 % | −3,9 % à −5,6 % | −1,7 % à −2,6 % |

(période test, seuils d'EV 2 %, 5 %, 10 %)

## La variante qui fonctionne

Cote juste **Pinnacle Over/Under** (sans marge) contre la **meilleure cote** Over/Under,
EV > 2 % : **+3,4 %** (IC +0,1 à +6,9 %, 2 879 paris, 2019-2026). Même mécanisme que S01 ;
historique court (les cotes Pinnacle Over/Under ne sont dans les données que depuis 2019).
