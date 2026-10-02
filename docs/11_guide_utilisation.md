# Guide d'utilisation

## 1. Installation (gratuite)

```bash
git clone https://github.com/matttgic/Overstreamlit.git
cd Overstreamlit
pip install -r requirements.txt
python -m pytest -q tests          # 15 tests unitaires
```

Python 3.10+ recommandé. Aucune clé API n'est nécessaire.

## 2. Usage quotidien : le scanner de value bets

```bash
python scripts/daily_scan.py --min-ev 0.03 --books B365,BW --bankroll 1000
```

- télécharge les matchs à venir (22 championnats) avec leurs cotes depuis football-data ;
- calcule la probabilité juste à partir de **Betfair Exchange sans marge** ;
- liste les paris où bet365 ou bwin (agréés ANJ) offrent une EV ≥ 3 % ;
- propose une mise Kelly ¼ plafonnée à 2 % de la bankroll ;
- règle automatiquement les paris passés et calcule leur **CLV** ;
- écrit `picks/latest.csv`, `picks/history.csv`, `picks/bilan.md`.

Option `--model-weight 0.2` : mélange 20 % de Dixon-Coles (non recommandé par le
backtest, voir S04).

La GitHub Action `.github/workflows/daily_scan.yml` exécute ce scan tous les jours à
07:00 UTC et commit les résultats : le suivi est public et horodaté (impossible de
« tricher » après coup).

## 3. L'application Streamlit

```bash
streamlit run app.py
```

Onglets : value bets du jour (réglages EV, bookmakers, poids du modèle, bankroll), suivi
des paris, résultats de recherche (tables et graphiques), bibliothèque.

## 4. Routine recommandée du parieur (France)

1. **Ouvrir des comptes chez plusieurs opérateurs agréés ANJ** (la liste est dans
   [01_reglementation_ANJ.md](01_reglementation_ANJ.md)) : l'avantage mesuré vient de la
   **comparaison des cotes**, pas d'un seul bookmaker.
2. Chaque jour : lancer le scanner (ou lire `picks/latest.csv`), puis **vérifier la cote
   réelle** sur votre bookmaker français ; ne parier que si `cote_FR ≥ cote_juste × (1 + EV_min)`.
3. Mise : Kelly ¼, plafonnée à 2 % de la bankroll, **jamais plus**.
4. Suivre la **CLV** : c'est elle qui dit si la méthode fonctionne pour vous.
5. Utiliser bonus, freebets et cotes boostées quand ils dépassent la cote juste (S09).
6. Ne jamais : parier sur un modèle seul, suivre les gros outsiders, faire des combinés
   « pour la cote », augmenter les mises après une perte.

Jeu responsable : fixez un budget que vous pouvez perdre. Joueurs Info Service :
09 74 75 13 13 (appel non surtaxé).

## 5. Reproduire toute la recherche

```bash
python scripts/download_football.py --first 2000 --last 2026   # ~15 min, 65 Mo
python scripts/download_other_sports.py                        # tennis, NBA, NHL, NFL, MLB, UFC
python scripts/football_pipeline.py --workers 4                # ~25-30 min (Dixon-Coles hebdomadaire)
python scripts/football_strategies.py                          # grille de stratégies, IC, CLV
python scripts/football_extra_leagues.py                       # 16 championnats extra
python scripts/multisport.py                                   # autres sports
python scripts/tennis_strategies.py                            # tennis approfondi
python scripts/international_elo.py                            # sélections nationales
python scripts/build_reports.py                                # régénère docs/resultats/*.md
```

## 6. Structure du dépôt

```
sportpred/            bibliothèque Python
  data/               téléchargement et normalisation (football-data, tennis, NBA…)
  models/             Elo, pi-ratings, Dixon-Coles, logit ordonné, Elo multi-sports
  betting/            dé-margination (5 méthodes), Kelly (simple, fractionné, simultané)
  backtest/           métriques (RPS, log-loss, Brier, ROI bootstrap, CLV) + simulateur
  live/               scanner quotidien
  features.py         variables sans fuite d'information
  strategies.py       catalogue de stratégies
scripts/              pipelines reproductibles
results/              sorties CSV/PNG des backtests
docs/                 la bibliothèque (études, données, dépôts, ANJ, stratégies, résultats)
picks/                paris proposés par le robot (créé par la GitHub Action)
archives/             historique de l'ancien système
tests/                tests unitaires
```
