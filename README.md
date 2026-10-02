# Overstreamlit — bibliothèque de prédiction sportive et de stratégies de paris (France / ANJ)

> **En une phrase :** sur plus de 500 000 matchs (football, tennis, NBA, NHL, NFL, MLB,
> UFC), **aucun modèle statistique ne bat les cotes du marché**. La seule méthode qui
> gagne de façon robuste consiste à **comparer les cotes de plusieurs bookmakers à la cote
> « juste » d'un marché sharp** (Pinnacle, Betfair Exchange) et à ne parier que lorsqu'un
> bookmaker est trop généreux. Ce dépôt le démontre, l'outille et le documente.

⚠️ Les paris sportifs comportent un risque de perte. Rien ici n'est une garantie de gain.
Jeu responsable : Joueurs Info Service, 09 74 75 13 13.

---

## Les résultats clés

| Stratégie | Sport / données | Période de test (jamais utilisée pour régler) | Verdict |
|---|---|---|---|
| **Meilleure cote vs cote juste Pinnacle/Betfair** (EV > 2 %) | Tennis ATP | **+5,0 %** ROI, IC 95 % [+2,7 ; +7,3], 9 719 paris | ✅ |
| idem | Tennis WTA | +2,3 %, IC [−0,2 ; +4,7], 8 350 paris | ✅ (faible) |
| idem | Football, 16 championnats extra (échantillon indépendant) | **+5,8 %**, IC [+3,1 ; +8,6], 13 311 paris | ✅ |
| idem (EV ≥ 5 %) | Football, 22 championnats principaux | +4,2 %, IC [−2,8 ; +11,1], 2 347 paris (dev : +13,0 %) | ✅ mais avantage en baisse depuis 2021 |
| Consensus du marché vs meilleure cote (EV ≥ 0 %) | Football, 22 championnats | +2,4 %, IC [+1,0 ; +3,9], 19 336 paris | ✅ |
| Même filtre mais **un seul** bookmaker (bet365) | Tennis, football | non significatif | ⚠️ il faut comparer plusieurs bookmakers |
| Modèles seuls (Elo, Dixon-Coles, pi-ratings, LightGBM) | tous sports | ROI −2 % à −10 %, RPS football 0,2076 vs 0,2041 pour le marché | ❌ |
| Ancien système (Over 2.5, modèle maison) | réel, janv.-févr. 2026 | **−6,95 %** (83 paris) | ❌ ([audit](docs/09_audit_ancien_systeme.md)) |
| Biais favori/outsider | tous sports | les gros outsiders perdent 15 à 39 % | ⚠️ à éviter, pas à exploiter |

Détails et intervalles de confiance : [docs/07](docs/07_resultats_football.md),
[docs/08](docs/08_resultats_autres_sports.md), tables brutes dans [docs/resultats/](docs/resultats/).

## Le tableau de bord quotidien

**Site :** https://matttgic.github.io/Overstreamlit/ (mis à jour toutes les 2 h par GitHub
Actions, après activation de GitHub Pages — voir [docs/12](docs/12_plan_automatisation.md)).

- **À jouer maintenant** : paris où bet365, bwin, Winamax, Betclic, Unibet, PMU ou NetBet
  paient plus que la cote juste Pinnacle/Betfair, avec la mise conseillée.
- **Cotes minimum à prendre** : pour chaque match des 36 prochaines heures (football,
  tennis, NBA, NHL, NFL, MLB, handball, rugby, MMA, volley), la cote à partir de laquelle
  un pari a de la valeur — à comparer dans votre appli.
- **Paris joueurs** : buteurs, points, tirs (les jours de match).
- **Suivi** : CLV de chaque pari proposé. Notifications Telegram en option.

## Ce que contient le dépôt

1. **Une bibliothèque de recherche** (`docs/`) :
   - [la réglementation ANJ 2026](docs/01_reglementation_ANJ.md) : 48 sports, 619
     compétitions, types de paris autorisés, TRJ plafonné à 85 %, 16 opérateurs agréés…
   - [une revue de la littérature scientifique](docs/02_etudes_scientifiques.md) ;
   - [un catalogue des données gratuites](docs/03_sources_de_donnees.md) (URLs vérifiées) ;
   - [un catalogue de 60+ dépôts open source](docs/04_depots_open_source.md) ;
   - [la méthodologie](docs/05_methodologie.md), [les modèles](docs/06_modeles.md),
     [10 fiches stratégies](docs/00_INDEX.md#fiches-stratégies-strategies) et
     [une autocritique](docs/10_autocritique.md).
2. **Une bibliothèque Python** (`sportpred/`) : téléchargement et normalisation des
   données, Elo, pi-ratings, Dixon-Coles (gradient analytique), LightGBM, 5 méthodes de
   dé-margination, Kelly (fractionné, simultané), backtest walk-forward, métriques (RPS,
   log-loss, Brier, ROI bootstrap, CLV).
3. **Des pipelines reproductibles** (`scripts/`) et leurs résultats (`results/`).
4. **Un scanner quotidien gratuit** (`scripts/daily_scan.py` + GitHub Action) : matchs
   à venir, cote juste Betfair Exchange, value bets sur bet365/bwin (agréés ANJ), mise
   Kelly ¼, règlement automatique et calcul de la CLV. **Aucune clé API.**
5. **Une application Streamlit** (`app.py`).

## Démarrage rapide

```bash
pip install -r requirements.txt
python -m pytest -q tests                 # vérifier l'installation
python scripts/daily_scan.py              # value bets du jour -> picks/latest.csv
streamlit run app.py                      # tableau de bord
```

Tout reproduire (données → modèles → backtests → rapports) : voir
[docs/11_guide_utilisation.md](docs/11_guide_utilisation.md).

## La méthode recommandée pour un parieur en France

1. Ouvrir des comptes chez **plusieurs** opérateurs agréés ANJ.
2. Calculer la cote juste à partir de Betfair Exchange (le scanner le fait).
3. Ne parier que si la meilleure cote française dépasse la cote juste d'au moins 2-3 %.
4. Miser Kelly ¼, plafonné à 2 % de la bankroll.
5. Suivre la **CLV** (closing line value) plutôt que le ROI à court terme.
6. Profiter des cotes boostées et freebets quand ils dépassent la cote juste.
7. Ne jamais parier sur un « pronostic » de modèle seul, ni sur les gros outsiders.

Pourquoi : voir [S01](docs/strategies/S01_value_betting_sharp_vs_soft.md),
[S07](docs/strategies/S07_gestion_bankroll_kelly.md), [S08](docs/strategies/S08_closing_line_value.md).

## Honnêteté

Ce dépôt publie aussi ce qui **ne marche pas** et ce qui **peut être faux** :
[docs/10_autocritique.md](docs/10_autocritique.md). Les limites principales : la
« meilleure cote » mondiale n'est pas accessible depuis la France, les bookmakers
limitent les gagnants, et l'avantage varie dans le temps.
