# Plan d'automatisation : « quoi parier aujourd'hui » en un coup d'œil

> Objectif : chaque jour, sans rien lancer à la main, voir sur son téléphone les paris où un
> bookmaker agréé ANJ paie plus que la cote juste, et pour tout le reste la **cote minimum
> à prendre**. Coût : **0 €** (GitHub Actions et GitHub Pages sont gratuits pour un dépôt
> public, The Odds API et Telegram ont des offres gratuites).

## 1. Architecture

```
            toutes les 2 h (GitHub Actions, gratuit)
┌──────────────────────────────────────────────────────────────────────┐
│ 1. Pinnacle (API publique, sans clé)  -> cotes justes, tous sports    │
│ 2. football-data.co.uk (sans clé)     -> bet365, bwin, Betfair (foot) │
│ 3. The Odds API (clé gratuite)        -> Betclic, Winamax, Unibet,    │
│                                          PMU, NetBet (3 relevés/jour)  │
│ 4. Appariement strict des matchs (heure + noms + unicité)             │
│ 5. Value bets (EV ≥ 3 %), cotes minimum, paris joueurs, suivi CLV     │
└──────────────┬───────────────────────────────┬───────────────────────┘
               │                               │
   site/data/today.json             branche « dashboard-data »
               │                    (historique, CLV, notifications)
     ┌─────────┴──────────┐
     │                    │
 GitHub Pages        Telegram (optionnel)      Artefact claude.ai
 matttgic.github.io  nouveau value bet ->      lit today.json via le
 /Overstreamlit/     message sur le téléphone  connecteur GitHub
```

Code : `sportpred/live/` (pinnacle, oddsapi, matching, dashboard, notify),
`scripts/build_dashboard.py`, `scripts/build_site.py`, `site/`,
`.github/workflows/dashboard.yml`.

## 2. Ce que vous devez faire (une seule fois, ~15 minutes)

| # | Action | Où | Obligatoire ? |
|---|---|---|---|
| 1 | **Fusionner la branche** `ccr-db761a32-14x613` dans `main` (pull request) | GitHub | Oui |
| 2 | **Activer GitHub Pages** : Settings → Pages → Source : « GitHub Actions » | GitHub | Oui (pour le site) |
| 3 | **Clé The Odds API** : s'inscrire sur the-odds-api.com (offre gratuite 500 crédits/mois), puis Settings → Secrets and variables → Actions → `THE_ODDS_API_KEY` | the-odds-api.com + GitHub | Recommandé : sans elle, seuls bet365/bwin (football) sont comparés automatiquement |
| 4 | **Telegram** : @BotFather → /newbot → jeton ; écrire au bot ; lire le chat id sur `https://api.telegram.org/bot<JETON>/getUpdates` ; secrets `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` | Telegram + GitHub | Optionnel |
| 5 | Lancer une première fois : Actions → « Tableau de bord » → Run workflow | GitHub | Oui |

Ensuite tout tourne seul : 9 mises à jour par jour (05:07 → 21:07 UTC).

## 3. La routine quotidienne (2 minutes)

1. Ouvrir le site (ou la notification Telegram).
2. **Bloc « À jouer maintenant »** : vérifier la cote dans l'appli du bookmaker indiqué.
   Si elle est toujours ≥ à la cote affichée, miser le pourcentage indiqué (Kelly ¼,
   plafonné à 2 % de la bankroll).
3. **Tableau « Cotes minimum à prendre »** : pour les matchs qui vous intéressent, ouvrir
   Winamax / Betclic / Unibet… et ne parier que si la cote affichée est ≥ la valeur
   surlignée. C'est la même règle que le bloc 2, appliquée à la main sur tous les
   opérateurs, y compris ceux qu'aucune API ne couvre.
4. **Paris joueurs** (NHL, NBA, football, les jours de match) : même règle avec les cotes
   minimum des buteurs, points, tirs.
   **Buteurs NHL** : la section dédiée donne une cote juste pour tous les joueurs ; ceux
   marqués « modèle » (non cotés par Pinnacle) demandent une cote ≥ +10 % (voir S11).
   Unibet est comparé automatiquement : ses paris joueurs au-dessus du seuil arrivent seuls
   dans « À jouer maintenant ».
5. Une fois par semaine : regarder la **CLV moyenne** dans « Suivi ». Si elle reste
   négative après ~200 paris, arrêter et revoir la méthode.

## 4. Gestion du quota The Odds API

Réglage actuel (abonnement de **20 000 crédits/mois**) : relevé des cotes françaises à
chaque mise à jour (9 par jour), jusqu'à 25 sports, vainqueur/1N2 **et totaux** (2 crédits
par sport) : au plus 450 crédits par jour, soit ~14 000 par mois, avec arrêt automatique
sous 2 000 crédits restants (`ODDS_API_RESERVE`). Les crédits restants s'affichent en bas
du tableau de bord.

Pour l'offre gratuite (500 crédits/mois), remettre dans le workflow :
`ODDS_API_HOURS: '7,13,17'`, `ODDS_API_MAX_CALLS: '5'`, `ODDS_API_MARKETS: 'h2h'`.

### Ancien réglage (offre gratuite)

- Les appels qui listent les sports et les matchs sont gratuits ; seuls les appels de
  cotes coûtent (1 crédit par sport et par marché pour la région « fr »).
- Le workflow n'interroge The Odds API qu'à 3 heures fixes (07:07, 13:07, 17:07 UTC), au
  maximum 5 sports par passage, et seulement pour les sports qui ont des matchs dans les
  36 h : environ 15 crédits par jour, soit ~465 par mois.
- Entre deux relevés, le site réutilise les cotes FR de moins de 6 h et affiche leur heure.
- Réglages : variables `ODDS_API_HOURS` et `ODDS_API_MAX_CALLS` dans le workflow.

## 5. Garde-fous intégrés

| Risque | Garde-fou |
|---|---|
| Mauvais match apparié (le bug « Salernitana » de l'ancien système) | Heures de début à ± 3 h, similarité ≥ 0,8 sur les deux équipes, abstention si deux candidats sont proches ; tests unitaires |
| Erreur de cote (EV énorme) | EV plafonnée à 30 % : au-delà, le pari est ignoré |
| Marchés différents sous le même nom (hockey, handball : 1N2 temps réglementaire chez Betclic/Winamax/Unibet/PMU, vainqueur à 2 issues chez Pinnacle) | Comparaison seulement si les deux marchés ont les mêmes issues (avec ou sans « Nul ») ; test unitaire. Bug vu au premier passage (02/10/2026 : 15 faux value bets NHL/handball à +4 à +27 %), corrigé et retiré du suivi |
| Référence Pinnacle peu fiable | Marchés dont la marge Pinnacle dépasse 8 % exclus |
| Marchés non autorisés en France | Cartons, corners, ITF, Challengers, WTA 125 exclus ; compétitions suivies alignées sur la liste ANJ |
| Grosses cotes | Cote maximale 10 (le biais favori/outsider rend les grosses cotes perdantes) |
| Mise excessive | Kelly ¼ plafonné à 2 % de la bankroll |
| Illusion de gain | Suivi CLV automatique de chaque pari proposé, horodaté et public |

## 6. Feuille de route

| Phase | Contenu | Statut |
|---|---|---|
| 1 | Tableau de bord multi-sports, cotes minimum, value bets bet365/bwin/FR, CLV, Pages, Telegram, artefact | ✅ fait |
| 2 | **Résultats et bilan financier** : scores ESPN (gratuit) pour régler automatiquement chaque pari (football, NBA, NHL, NFL, MLB, tennis, UFC) et afficher le ROI à côté de la CLV | ✅ fait |
| 3a | **Paris joueurs NHL/NBA** : cotes justes Pinnacle (buteur, tirs cadrés, points, passes, arrêts ; NBA points/rebonds/passes dès le 20/10) affichées avec la cote minimum à prendre, filtres par type de stat | ✅ fait |
| 3b | **Archive quotidienne des cotes Pinnacle** (marchés principaux + paris joueurs, branche `dashboard-data`, dossier `archive/`) : il n'existe aucun historique gratuit de cotes de paris joueurs, on le construit | ✅ fait |
| 3c | **Modèle buteurs NHL ancré sur le marché** : buts attendus de l'équipe tirés des cotes Pinnacle, seule la répartition entre joueurs est modélisée (temps de jeu, supériorité numérique, tirs, réussite). Calibré sur 8 saisons hors échantillon ; section « Buteurs NHL » du site avec une cote juste pour tous les joueurs ; prédictions archivées et comparées à Pinnacle au fil des matchs ([S11](strategies/S11_buteurs_nhl.md)) | ✅ fait (indicatif) |
| 3d | **Cotes joueurs Unibet.fr comparées automatiquement** (buteur, points, passes NHL) : lues sur le site d'Unibet, comparées à Pinnacle (+3 %) ou au modèle (+10 %), paris au-dessus du seuil ajoutés à « À jouer maintenant », réglés avec les feuilles de match NHL ([S11](strategies/S11_buteurs_nhl.md)) | ✅ fait |
| 3e | Composition officielle (DailyFaceoff / feuille de match) et gardien partant dans le modèle buteurs ; décision sur la marge exigée après ~1 500 joueurs comparés à Pinnacle | à faire |
| 4 | **Cotes Winamax et Betclic** : ces deux sites bloquent tous les serveurs (GitHub, cloud ; testé depuis GitHub Actions le 03/10/2026), y compris leurs versions étrangères, et aucune API gratuite ne fournit leurs cotes joueurs (The Odds API : bookmakers US ; OddsPapi : rien reçu ; odds-api.io : payant). Solution : le **téléphone Android** (Termux) télécharge les pages depuis la connexion de l'utilisateur et les dépose sur la branche `cotes-telephone` ; GitHub lit et compare (`telephone/`, mode d'emploi pas à pas). Étape 1 : sonde | en cours |
| 5 | Alertes de cotes boostées (S09) : comparer chaque boost à la cote juste | à étudier |

## 7. Ce qu'il ne faut pas attendre

- Un flux constant de paris : avec deux bookmakers comparés automatiquement, il y a
  souvent 0 à 3 value bets par jour. L'essentiel de la valeur vient de la comparaison
  manuelle de vos propres opérateurs grâce au tableau des cotes minimum.
- Beaucoup de value bets sur les marchés principaux des opérateurs français : une mesure
  indépendante (ryan00x/Bet-Model, août 2026) n'a trouvé **aucune** cote ANJ à +2 % d'EV
  sur 4 342 prix ; la meilleure cote française valait 0,936 × Pinnacle en médiane.
  Priorité pratique : **cotes boostées, promotions, paris joueurs** (calculateur intégré
  au tableau de bord), puis comparaison manuelle de plusieurs opérateurs.
- Des paris joueurs français automatiquement comparés : aucune API gratuite ne fournit les
  cotes joueurs de Winamax/Betclic/Unibet.fr ; on compare soi-même grâce aux cotes minimum.
- Des gains garantis : l'avantage mesuré est de quelques pourcents, avec de longues
  séries négatives possibles (voir S07) et un risque de limitation des comptes.
