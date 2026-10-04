# S12 — Buteurs football : une cote juste « si titulaire » pour chaque joueur

> Statut : **⚠️ indicatif**. Le modèle est bien calibré hors échantillon (4 saisons, 110 000
> titulaires des 5 grands championnats), mais Pinnacle ne cote pas les buteurs de football :
> aucune référence « sharp » ne permet de le vérifier joueur par joueur. Marge exigée
> élevée (+12 %) et suivi automatique des résultats sur le site.
> Résultats complets : [resultats/football_buteurs.md](../resultats/football_buteurs.md).

## 1. Le problème

Les opérateurs français proposent « buteur » pour tous les joueurs de chaque match de
Ligue 1, Premier League, Liga, Serie A et Bundesliga, avec des marges de 15 à 30 %. Pinnacle
ne publie pas ces marchés : sans cote juste, impossible de savoir si une cote de 3,60 sur un
ailier vaut le coup.

## 2. La méthode (même principe que les buteurs NHL, [S11](S11_buteurs_nhl.md))

Ne pas refaire le travail du marché : **les buts attendus de chaque équipe sont tirés des
cotes Pinnacle** (1N2 et plus/moins, grille de scores de Dixon-Coles). Seule la
**répartition** de ces buts entre les joueurs est modélisée, à partir des données gratuites
d'Understat (xG de chaque tir, minutes, penaltys, depuis 2014) :

```
part du joueur i = exp(η_i) / Σ_j exp(η_j)          (joueurs de champ de l'équipe)
η_i = 0,68·log(minutes/90) + 1,13·log(xG/90 attendu) + 0,32·log(finition) + effets de poste
xG/90 attendu = xG hors penalty par 90 min (moyenne pondérée, demi-vie 20 matchs, ramenée
                vers la moyenne du poste avec 900 minutes « fictives »)
              + part des penaltys de l'équipe tirés par le joueur (dans son club actuel)
                × xG de penalty de l'équipe par match
finition = (buts hors penalty + 3) / (xG hors penalty + 3)
P(i marque) = 1 − exp(−λ_équipe × 0,97 × part_i)     (0,97 : 3 % de buts contre son camp)
```

**Cote « si titulaire »** : minutes = minutes habituelles du joueur quand il est titulaire
(rôle récent) ; remplaçants résumés par la masse moyenne du banc (15 % de celle des
titulaires). La composition probable vient des 8 derniers matchs de l'équipe (les plus
récents comptent davantage) ; la colonne « Titulaire » du site en donne la probabilité.

## 3. Résultats (test hors échantillon 2023-24 → 2026-27, β appris sur 2019-20 → 2022-23)

| Test | Résultat |
|---|---|
| Répartition seule (sachant les buts de l'équipe), log-loss par but | modèle 2,239 ; minutes × xG/90 sans β 2,263 ; minutes seules 2,627 |
| Probabilité de marquer, minutes réelles, λ de clôture (159 480 joueurs) | log-loss 0,2510 (naïf 0,2532, minutes seules 0,2850) |
| **« Si titulaire »** (minutes attendues, 110 116 titulaires) | prédit 22,3 % → observé 21,5 % ; 34,1 % → 33,2 % ; 44,0 % → 43,4 % ; 55,6 % → 57,4 % |
| Par poste (si titulaire) | attaquants 27,1 % → 26,7 % ; ailiers / milieux offensifs 17,4 % → 16,9 % ; milieux 8,1 % → 7,8 % ; défenseurs 4,0 % → 3,9 % |
| Par championnat (si titulaire) | écart de 0,1 à 0,5 point |

Léger excès de 0,3 à 0,5 point en moyenne : prudent pour l'usage (cote juste un peu basse).

## 4. Utilisation (tableau de bord, section « Buteurs football »)

1. **Attendre la composition officielle** (~1 h avant le match). La cote juste ne vaut que si
   le joueur est titulaire. Un joueur absent rend le pari remboursé, mais un remplaçant qui
   entre en jeu, non. Dès qu'ESPN publie les compositions (matchs des 2 h 30 suivantes), le site
   les lit : badge « compo officielle », colonne « Titulaire » = oui, non-titulaires retirés,
   parts recalculées sur le vrai onze, paris marqués « titulaire confirmé ».
2. Jouer si la cote de l'opérateur est **≥ cote juste × 1,12** (colonne « À prendre si ≥ »).
   La marge est plus large que pour Pinnacle : erreur du modèle, compositions et blessures
   de dernière minute non modélisées.
3. Unibet est comparé automatiquement (cotes « Buteur », « Buteur 2+ », « Buteur 3+ »). Les
   paris au-dessus du seuil s'ajoutent à « À jouer maintenant » pour les titulaires quasi sûrs
   (≥ 85 % de titularisations récentes) ; Winamax et Betclic suivront via le téléphone.
4. Mise : Kelly ¼ plafonné à 2 % ([S07](S07_gestion_bankroll_kelly.md)).
5. Suivi : chaque relevé est archivé (`archive/foot_buteurs_*.csv.gz`) puis comparé aux
   feuilles de match Understat. Les paris joués sont réglés automatiquement : titulaire →
   gagné / perdu ; entré en cours de jeu → « non joué » ; absent → remboursé.

## 5. Limites

- Composition estimée tant qu'ESPN ne l'a pas publiée (les mises à jour du site ne tombent pas
  toujours dans l'heure qui précède le match) ; blessures et rotations de coupe d'Europe non
  modélisées ; transferts récents : le joueur garde son taux xG mais sa part des
  penaltys repart de zéro dans son nouveau club.
- Gardien adverse, contexte tactique, rôle exact (ailier gauche vs droit) non modélisés.
- Pas de référence sharp : la calibration historique est la seule garantie. Si le suivi
  montre un écart durable, relever la marge exigée.
