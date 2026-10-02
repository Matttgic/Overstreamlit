# Méthodologie : comment on évalue une stratégie sans se mentir

> Ce document explique le protocole utilisé dans tout le dépôt. Il vaut mieux le lire avant
> les résultats : la plupart des « systèmes gagnants » publiés en ligne échouent sur l'un
> des pièges décrits ici. L'ancien `app.py` du dépôt tombait dans plusieurs d'entre eux
> (voir [09_audit_ancien_systeme.md](09_audit_ancien_systeme.md)).

## 1. La seule question qui compte

Un pari a une espérance positive si et seulement si

```
p_vraie × cote − 1 > 0
```

Personne ne connaît `p_vraie`. Toute stratégie revient donc à **estimer p mieux que le
bookmaker**, ou à trouver un bookmaker qui l'estime **moins bien que les autres**.
Le marché le plus efficace (Pinnacle, Betfair Exchange) sert de juge de paix : si votre
estimation ne bat pas ses probabilités sans marge, elle ne battra pas un bookmaker
français dont la marge est plus élevée.

## 2. Protocole anti-biais appliqué partout

| Règle | Pourquoi | Implémentation |
|---|---|---|
| **Walk-forward strict** | Un modèle ne doit jamais voir le futur | Dixon-Coles ré-estimé chaque semaine sur les 3 années précédentes ; LightGBM et logit ordonné ré-entraînés chaque saison sur les saisons passées ; notes Elo/pi mises à jour après chaque match (test `test_ratings_use_only_past`) |
| **Cotes réellement disponibles** | Parier à la cote de clôture alors qu'on décide plus tôt est un biais | Football : cotes « d'ouverture » football-data (relevées vendredi/mardi), CLV mesurée contre la clôture |
| **Séparation dev / test** | Choisir les paramètres sur la période qu'on évalue = surapprentissage | Football : dev 2012/13-2018/19, test 2019/20-2026/27. Les seuils sont choisis sur dev ; le test n'est regardé qu'ensuite |
| **Comptage des essais** | Tester 300 configurations en garantit quelques-unes « significatives » par hasard | Le nombre de configurations testées est publié (`results/football/meta.json`) ; on exige cohérence dev **et** test |
| **Intervalles de confiance** | Un ROI de +8 % sur 200 paris ne prouve rien | Bootstrap (1 000 à 2 000 tirages) du ROI ; p(ROI ≤ 0) |
| **Plafond d'EV** | Une EV > 30 % est presque toujours une erreur de cote (annulée par le bookmaker) | `MAX_EV = 0.30` |
| **Un pari par match** | Parier H et A d'un même match crée des corrélations | On garde la sélection de plus forte EV |
| **CLV** | Le ROI est très bruité (il faut des milliers de paris) ; la CLV converge 10 à 50 fois plus vite | `clv = cote_prise / cote_juste_de_clôture − 1` |

## 3. Les métriques

### Qualité des probabilités

- **RPS** (Ranked Probability Score, Epstein 1969 ; Constantinou & Fenton 2012) : score
  propre qui respecte l'ordre domicile < nul < extérieur. C'est la référence en football.
  Plus bas = meilleur. Ordre de grandeur : 0,19 à 0,21 pour les meilleurs modèles.
- **Log-loss** : pénalise fortement les certitudes erronées.
- **Brier** : erreur quadratique.

Une différence de RPS de 0,001 est **petite mais réelle** sur 50 000 matchs. Le marché
de clôture Pinnacle est la référence à battre.

### Rentabilité

- **ROI** (= yield) : profit / total misé, à mise fixe (comparaison équitable).
- **IC 95 % bootstrap** et **p(ROI ≤ 0)**.
- **CLV moyenne** : si elle est positive sur des milliers de paris, la stratégie a un
  avantage réel même si le ROI observé est encore bruité.
- **Drawdown maximal** de la bankroll pour les simulations Kelly.

### Ordre de grandeur du bruit

Avec des cotes moyennes de 2,0, l'écart-type du ROI après n paris vaut environ
`1/√n` : 10 % après 100 paris, 3 % après 1 000, 1 % après 10 000. **Il faut plusieurs
milliers de paris pour distinguer un avantage de 2 % du hasard.**

## 4. Suppression de la marge (« dé-margination »)

Les cotes contiennent la marge du bookmaker : 1/cote_H + 1/cote_N + 1/cote_A > 1.
Méthodes implémentées dans `sportpred/betting/odds.py` :

| Méthode | Idée | Remarque |
|---|---|---|
| multiplicative | normalisation proportionnelle | biaisée : sous-estime les favoris |
| additive | retire la même quantité à chaque issue | peut donner des probabilités négatives |
| **power** | p = (1/cote)^k | corrige bien le biais favori/outsider, **choix par défaut** |
| Shin | modèle de parieurs initiés (Shin 1993) | proche de power, standard académique |
| odds ratio | Cheung (2015) | proche de power |

Clarke, Kovalchik & Ingram (2017) et Štrumbelj (2014) montrent que power/Shin battent la
méthode multiplicative en log-loss.

## 5. Ce que le backtest ne capture pas (limites honnêtes)

1. **Limitation des comptes gagnants** : en France elle est en principe encadrée
   (délibération ANJ 2021-C-01) mais reste courante en pratique. Une stratégie gagnante
   finit souvent limitée à quelques euros de mise.
2. **Cotes françaises ≠ cotes du fichier** : football-data donne bet365.com et bwin.com,
   pas bet365.fr / bwin.fr. Les cotes .fr sont souvent un peu plus basses (plafond de TRJ
   à 85 %). On approxime par `FR = max(B365, BW)` et on documente la sensibilité.
3. **« Max » n'est pas atteignable** : la meilleure cote parmi ~40 bookmakers mondiaux
   inclut des opérateurs non agréés en France. C'est une borne haute.
4. **Disponibilité** : la cote affichée peut avoir bougé quand on veut parier, et les
   mises maximales peuvent être faibles sur les petits championnats.
5. **Pinnacle a disparu** des données publiques fin 2025 (API fermée en juillet 2025) ;
   la référence sharp devient Betfair Exchange, avec moins d'historique.
