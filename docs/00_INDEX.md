# Bibliothèque — index de la documentation

| # | Document | Contenu |
|---|---|---|
| 01 | [Réglementation ANJ](01_reglementation_ANJ.md) | Liste des 48 sports et 619 compétitions autorisés, types de paris, TRJ 85 %, opérateurs agréés (2026), fiscalité, limitation des comptes, bonus |
| 02 | [Études scientifiques](02_etudes_scientifiques.md) | Revue de littérature : modèles, efficience des marchés, tennis, autres sports, Kelly, pièges méthodologiques |
| 03 | [Sources de données](03_sources_de_donnees.md) | Catalogue des données gratuites par sport, URLs vérifiées, sources bloquées et contournements |
| 04 | [Dépôts open source](04_depots_open_source.md) | 60+ projets GitHub/CRAN/PyPI évalués (penaltyblog, implied, sports-betting…) |
| 05 | [Méthodologie](05_methodologie.md) | Protocole anti-biais : walk-forward, dev/test, IC bootstrap, CLV, limites |
| 06 | [Modèles](06_modeles.md) | Elo, pi-ratings, Dixon-Coles, LightGBM, Elo multi-sports, dé-margination, Kelly |
| 07 | [Résultats football](07_resultats_football.md) | 22 championnats, 2000-2026 : qualité des modèles, carte des biais, grille de 300+ stratégies |
| 08 | [Résultats autres sports](08_resultats_autres_sports.md) | Tennis ATP/WTA, NBA, NHL, NFL, MLB, UFC |
| 09 | [Audit de l'ancien système](09_audit_ancien_systeme.md) | Pourquoi l'ancien robot Over 2.5 perdait (−6,95 %) |
| 10 | [Autocritique](10_autocritique.md) | Ce qui peut être faux dans ce travail, et comment le vérifier |
| 11 | [Guide d'utilisation](11_guide_utilisation.md) | Installer, lancer le scanner, l'app, les backtests ; routine du parieur |
| 12 | [Plan d'automatisation](12_plan_automatisation.md) | Tableau de bord « quoi parier aujourd'hui » : architecture, 5 actions à faire une fois, routine de 2 minutes, feuille de route |

## Fiches stratégies (`strategies/`)

| Fiche | Verdict |
|---|---|
| [S01 — Value betting « sharp vs soft » / comparaison de cotes](strategies/S01_value_betting_sharp_vs_soft.md) | ✅ **Recommandée** (football, tennis) |
| [S02 — Consensus du marché (Kaunitz et al.)](strategies/S02_consensus_marche.md) | ✅ variante de S01 |
| [S03 — Modèles statistiques seuls (Elo, Dixon-Coles, ML)](strategies/S03_modeles_statistiques.md) | ❌ perdante contre le marché |
| [S04 — Mélange modèle + marché](strategies/S04_melange_modele_marche.md) | ⚠️ pas d'amélioration robuste |
| [S05 — Biais du marché (favoris, nuls, domicile)](strategies/S05_biais_du_marche.md) | ⚠️ réels mais non exploitables seuls |
| [S06 — Over/Under 2.5 (ancien système)](strategies/S06_over_under.md) | ❌ perdante |
| [S07 — Gestion de bankroll (Kelly)](strategies/S07_gestion_bankroll_kelly.md) | ✅ Kelly ¼ plafonné |
| [S08 — Closing Line Value](strategies/S08_closing_line_value.md) | ✅ indicateur de suivi |
| [S09 — Bonus, freebets, cotes boostées](strategies/S09_bonus_freebets_cotes_boostees.md) | ✅ EV positive, faible volume |
| [S10 — Arbitrage (surebets)](strategies/S10_arbitrage_surebets.md) | ⚠️ rare en France |

## Résultats bruts générés

- [resultats/football.md](resultats/football.md) — toutes les tables football
- [resultats/autres_sports.md](resultats/autres_sports.md) — toutes les tables multi-sports
- [resultats/international.md](resultats/international.md) — Elo des sélections nationales
- CSV et graphiques : dossier `results/`
- Données de référence : `docs/donnees_reference/` (liste ANJ complète en YAML/CSV, URLs vérifiées)
