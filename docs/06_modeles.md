# Les modèles implémentés

Tous les modèles sont dans `sportpred/models/`. Chacun est testé (`tests/test_core.py`)
et utilisé en mode walk-forward (aucune information future).

## 1. Elo football — `models/elo.py`

Variante « World Football Elo » (eloratings.net), étudiée par Hvattum & Arntzen (2010) :

- `E = 1 / (1 + 10^(-(R_dom + HFA - R_ext)/400))`, HFA = 65 points ;
- `ΔR = K × G(écart) × (résultat - E)`, K = 20, G = 1 ; 1,5 ; (11+N)/8 selon l'écart ;
- une équipe nouvelle (promue) démarre au 20e centile des notes de son pays ;
- les notes sont partagées entre divisions d'un même pays (E0 → EC, etc.).

L'écart Elo est converti en probabilités 1N2 par un **logit ordonné**
(`models/ordered.py`) ré-estimé chaque saison sur les 6 saisons précédentes.

## 2. Pi-ratings — `models/pi_ratings.py`

Constantinou & Fenton (2013). Deux notes par équipe (domicile, extérieur). L'écart de
buts attendu face à une équipe moyenne vaut `ψ(R) = sign(R)(10^{|R|/3} - 1)`. L'erreur
entre écart observé et attendu met à jour les notes (λ = 0,035, γ = 0,7). Les pi-ratings
sont parmi les meilleures variables du Soccer Prediction Challenge (Hubáček et al. 2019).

## 3. Dixon-Coles — `models/dixon_coles.py`

Dixon & Coles (1997) : buts ~ Poisson avec forces d'attaque/défense, avantage du
terrain et correction ρ des scores faibles (0-0, 1-0, 0-1, 1-1). Améliorations :

- **pondération temporelle** exp(-ξ·jours), ξ = 0,0019 ;
- **gradient analytique** (vérifié numériquement) → un ajustement prend ~10 ms ;
- **pénalité ridge** (identifiabilité + rétrécissement des équipes peu vues) ;
- **ajustement par pays, toutes divisions ensemble** (les promus ont un historique) ;
- ré-estimation **chaque semaine** sur une fenêtre de 3 ans.

Sorties : 1N2, Over/Under 2.5, BTTS, buts attendus λ et μ, matrice des scores.

## 4. LightGBM — `scripts/football_pipeline.py`

Gradient boosting multiclasse, ré-entraîné chaque saison sur les 8 saisons précédentes
(early stopping sur la dernière saison d'entraînement). Variables (toutes décalées) :

- Elo, pi-ratings, probabilités et buts attendus Dixon-Coles ;
- formes EWMA (5 et 20 matchs) : buts, tirs, tirs cadrés, corners, points marqués/encaissés ;
- jours de repos, nombre de matchs joués, championnat.

Deux versions : **pure** (sans cotes) et **hybride** (+ probabilités du marché moyen).
Un modèle binaire Over/Under 2.5 est aussi entraîné.

## 5. Elo générique deux issues — `models/team_elo.py`

Pour tennis, NBA, NHL, NFL, MLB, MMA : avantage du terrain, K fixe ou dynamique
(FiveThirtyEight `K = 250/(n+5)^0.4`, tennis/MMA), régression vers la moyenne entre
saisons, multiplicateur de marge (NFL), Elo par surface (tennis). Calibration par
régression logistique ré-estimée chaque saison (+ log ratio des classements ATP/WTA).

## 6. Le marché comme modèle — `betting/odds.py`

Les probabilités sans marge des cotes (méthode power) sont traitées comme un modèle à
part entière : Pinnacle ouverture, Pinnacle clôture, moyenne du marché, Betfair Exchange.
C'est le **meilleur modèle disponible** dans tous nos tests (voir résultats), ce qui est
cohérent avec toute la littérature.

## 7. Mélanges modèle + marché — `strategies.py`

- `logit_blend` : pool logarithmique `p ∝ p_modèle^w · p_marché^(1-w)` ;
- régression logistique sur `logit(p_marché)` et `logit(p_modèle)` (multi-sports) :
  si le coefficient du modèle est nul, le modèle n'apporte **aucune information** au-delà
  du marché.

## 8. Kelly — `betting/kelly.py`

Kelly simple, fractionné (¼ recommandé, Baker & McHale 2013), plafonné, et Kelly
**simultané** pour plusieurs paris indépendants (maximisation exacte de E[log W]).
