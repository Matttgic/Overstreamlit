# S11 — Buteurs NHL : une cote juste pour tous les joueurs

> Statut : **⚠️ indicatif**. Le modèle est bien calibré sur 8 saisons hors échantillon
> et très proche de Pinnacle, mais il n'a pas encore été comparé à Pinnacle sur des
> matchs réels (l'archive se remplit depuis le 02/10/2026). Il sert à **trouver la cote
> juste des joueurs que Pinnacle ne cote pas**, pas à contredire Pinnacle.
> Résultats complets : [resultats/nhl_buteurs.md](../resultats/nhl_buteurs.md).

## 1. Le problème

Pinnacle, la référence de cote juste, ne publie qu'environ 8 buteurs par match NHL, et
seulement quelques heures avant le match. Winamax, Betclic ou Unibet proposent les
36 joueurs, avec des marges élevées. Sans cote juste, impossible de savoir si une cote
buteur à 6,50 sur un joueur de troisième ligne vaut le coup.

## 2. La méthode (idée reprise de Jejeh040/marqueurs-xiii)

Ne pas refaire le travail du marché : **le nombre de buts attendus de chaque équipe est
pris dans les cotes Pinnacle** (vainqueur + total de buts, sans marge, deux lois de
Poisson). Seule la **répartition** de ces buts entre les joueurs est modélisée :

```
part du joueur i  = exp(η_i) / Σ_j exp(η_j)        (18 joueurs de champ de l'équipe)
η_i = 1,05·log(temps de jeu attendu) + 0,13·log(temps en supériorité numérique)
    + 1,04·log(tirs par minute) + 0,75·log(réussite au tir) − 0,16·défenseur − 0,04·débutant
P(i marque) = 1 − exp(−λ_équipe × 0,98 × part_i)    (0,98 : buts en tirs au but exclus)
```

- Tirs par minute et réussite au tir : moyennes pondérées des matchs précédents
  (demi-vie 41 matchs), ramenées vers la moyenne du poste (300 minutes et 150 tirs
  « fictifs »). Le temps de jeu attendu suit le rôle actuel (demi-vie 2 matchs).
- Coefficients ajustés par maximum de vraisemblance (logit conditionnel) sur
  2011-12 → 2017-18, réajustés sur 2011-12 → 2025-26 pour la production.
- Données : API publique de la NHL (690 000 lignes joueur-match, 2010-11 → 2026-27).

## 3. Résultats

| Test (hors échantillon) | Résultat |
|---|---|
| Répartition seule, 2018-19 → 2025-26 (sachant les buts de l'équipe) | log-loss 0,3605, contre 0,3616 (formule simple temps × tirs × réussite), 0,3691 (buts récents), 0,3959 (part égale) |
| Ancré sur les cotes de clôture, 2018-19 → 2021-22 (3 985 matchs) | log-loss 0,3876, contre 0,3894 sans les cotes (λ moyen) et 0,4194 avec part égale |
| Calibration (même test) | prédit 22,4 % → observé 21,9 % ; 27,3 % → 27,7 % ; 32,2 % → 32,5 % ; 37,1 % → 38,6 % |
| Comparaison avec Pinnacle, 02/10/2026 (24 buteurs cotés) | écart moyen +0,3 point, écart absolu moyen 2,5 points, corrélation 0,89 |

## 4. Utilisation (tableau de bord, section « Buteurs NHL »)

1. Joueur coté par Pinnacle : la cote juste est celle de Pinnacle ; à prendre si la cote
   du bookmaker est **≥ cote juste × 1,03** (règle générale du site).
2. Joueur non coté par Pinnacle (étiquette « modèle ») : cote juste du modèle ; à prendre
   si **≥ cote juste × 1,10**. La marge est plus large parce que l'erreur du modèle
   (±2,5 points de probabilité, soit ~9 % sur une cote de 3,5) est bien supérieure à
   celle de Pinnacle.
3. Vérifier que le joueur est dans la composition (la page l'estime à partir du dernier
   match ou de l'effectif) : un joueur absent rend le pari remboursé chez la plupart des
   opérateurs, mais fausse aussi les parts de ses coéquipiers.
4. Mise : Kelly ¼ plafonné à 2 % (voir [S07](S07_gestion_bankroll_kelly.md)) ; les
   buteurs sont des paris à forte variance (cotes 3 à 10).

## 5. Le vrai test, en cours

Chaque mise à jour archive les prédictions (`archive/nhl_buteurs_AAAA-MM-JJ.csv.gz` sur
la branche `dashboard-data`). Le site affiche le bilan au fil des matchs : log-loss du
modèle, de Pinnacle et du mélange des deux sur les mêmes joueurs. Décision après
**au moins 1 500 joueurs cotés par les deux** (environ un mois de saison) :

- mélange meilleur que Pinnacle → le modèle apporte de l'information, on peut resserrer
  la marge exigée ;
- sinon → le modèle reste un outil pour les joueurs non cotés par Pinnacle.

## 6. Limites

- Composition estimée, pas lue sur la feuille de match (DailyFaceoff n'est pas encore
  branché) ; gardien adverse et blessures en cours de match non modélisés.
- La cote du modèle pour les joueurs non cotés ne peut pas encore être vérifiée contre un
  marché sharp : seule la calibration historique la garantit.
- Les cotes buteurs des opérateurs français ne sont dans aucune API gratuite :
  la comparaison reste manuelle.
