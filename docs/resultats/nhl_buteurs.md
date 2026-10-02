# Modèle buteurs NHL : résultats (généré par `scripts/nhl_buteurs.py`)

Modèle : `sportpred/models/nhl_scorers.py`. Buts attendus de l'équipe tirés du marché, seule la répartition entre joueurs est modélisée (logit conditionnel).

## 1. Réglage (ajustement 2011-12 → 2015-16, validation 2016-17 → 2017-18)

| demi-vie longue | demi-vie temps de jeu | k minutes | k tirs | log-vrais. / but (valid.) |
|---|---|---|---|---|
| 41 | 2 | 300 | 150 | -2.6972 |
| 41 | 2 | 300 | 300 | -2.6973 |
| 41 | 2 | 300 | 100 | -2.6973 |
| 82 | 2 | 300 | 150 | -2.6973 |
| 41 | 2 | 150 | 150 | -2.6973 |
| 41 | 2 | 600 | 150 | -2.6973 |

Retenu : demi-vie 41 matchs (tirs, buts), 2 matchs (temps de jeu), rétrécissement 300 minutes / 150 tirs.

Coefficients β (ajustés sur 2011-12 → 2017-18) :

| variable | β | sens |
|---|---|---|
| `l_toi` | +1.021 | log temps de jeu attendu |
| `l_pp` | +0.146 | log temps en supériorité |
| `l_spm` | +1.061 | log tirs par minute (rétréci) |
| `l_sh` | +0.768 | log réussite au tir (rétrécie) |
| `is_d` | -0.125 | défenseur |
| `new` | -0.009 | moins de 10 matchs d'historique |

## 2. Test hors échantillon 2018-19 → 2025-26, sachant le nombre de buts de l'équipe

P(joueur marque | l'équipe marque G buts) = 1 − (1 − part)^G. Mesure la qualité de la **répartition** seule.

| répartition | log-vrais. / but | log-loss | Brier |
|---|---|---|---|
| Uniforme (1/18) | -2.8901 | 0.3959 | 0.1216 |
| Buts récents (pondérés) | -2.7246 | 0.3691 | 0.1125 |
| Temps × tirs/min × réussite (sans β) | -2.6779 | 0.3616 | 0.1113 |
| Modèle (logit conditionnel) | -2.6719 | 0.3605 | 0.1111 |

## 3. Test ancré marché 2018-19 → 2021-22 (3985 matchs, 143417 joueur-matchs)

λ équipe = cotes de clôture (vainqueur + total, sans marge, deux lois de Poisson). Facteur buts « joueurs » / λ marché (tirs au but exclus) estimé sur 2011-12 → 2017-18 : 0.980.

| variante | log-loss | Brier |
|---|---|---|
| λ marché + part uniforme | 0.4194 | 0.1263 |
| λ moyen ligue + part modèle | 0.3894 | 0.1185 |
| λ marché + part modèle | 0.3876 | 0.1180 |

Joueurs à P ≥ 20 % (ceux que les bookmakers proposent en priorité, n = 37901) :

| variante | log-loss | Brier |
|---|---|---|
| λ marché + part uniforme | 0.6358 | 0.2142 |
| λ moyen ligue + part modèle | 0.5840 | 0.1978 |
| λ marché + part modèle | 0.5806 | 0.1964 |

Calibration (λ marché + part modèle) :

| tranche | n | prédit | observé |
|---|---|---|---|
| (0.0, 0.05] | 18700 | 3.8 % | 3.9 % |
| (0.05, 0.1] | 35411 | 7.6 % | 7.8 % |
| (0.1, 0.15] | 31480 | 12.3 % | 12.2 % |
| (0.15, 0.2] | 19925 | 17.4 % | 17.5 % |
| (0.2, 0.25] | 15280 | 22.4 % | 21.9 % |
| (0.25, 0.3] | 11414 | 27.3 % | 27.7 % |
| (0.3, 0.35] | 6685 | 32.2 % | 32.5 % |
| (0.35, 0.4] | 3044 | 37.1 % | 38.6 % |
| (0.4, 0.5] | 1366 | 43.2 % | 42.6 % |
| (0.5, 1.0] | 112 | 52.5 % | 44.6 % |

## 4. Modèle de production

β réajusté sur 2011-12 → 2025-26, enregistré dans `data/processed/nhl_scorer_model.json` :

| variable | β |
|---|---|
| `l_toi` | +1.047 |
| `l_pp` | +0.131 |
| `l_spm` | +1.044 |
| `l_sh` | +0.752 |
| `is_d` | -0.160 |
| `new` | -0.041 |

## 5. Limites

- Aucun historique gratuit de cotes buteurs : la comparaison avec Pinnacle se construit jour après jour (archive `dashboard-data`, voir docs/12). Tant qu'elle n'a pas montré que le modèle apporte quelque chose **en plus** de Pinnacle, il reste indicatif.
- Composition d'équipe : en direct, l'alignement est estimé (dernier match / effectif), pas lu sur la feuille de match ; un joueur absent fausse sa ligne et un peu les autres.
- Gardien adverse, rencontres consécutives (back-to-back) et blessures en cours de match ne sont pas modélisés : ils passent par λ (le marché les intègre) mais pas par les parts.
