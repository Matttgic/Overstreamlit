# S01 — Value betting « sharp vs soft » (comparaison des cotes contre une référence efficiente)

> Statut : ✅ **stratégie recommandée** — la seule qui gagne de façon répétée dans nos
> données, sur plusieurs sports et périodes, et la mieux étayée par la littérature.
> Code : `sportpred/strategies.py` (famille `sharp`), `sportpred/live/scanner.py`.

## Principe

1. Prendre les cotes d'un bookmaker **sharp** (qui accepte les gros parieurs et ajuste
   ses prix sur eux) : Pinnacle, ou Betfair Exchange depuis la fermeture de l'API
   Pinnacle (juillet 2025).
2. Retirer la marge (méthode power) → probabilité « juste » `p`.
3. Comparer aux cotes des bookmakers **soft** (grand public, dont les opérateurs ANJ).
4. Parier si `p × cote_soft − 1 ≥ seuil` (2 à 5 %), avec un plafond d'EV à 30 %
   (au-delà, probable erreur de cote).

On ne prédit rien soi-même : on exploite le retard ou la générosité d'un bookmaker par
rapport au prix le plus efficient du marché.

## Preuves

| Données | Période test | ROI | IC 95 % | Paris |
|---|---|---|---|---|
| Tennis ATP — Pinnacle juste vs meilleure cote, EV > 2 % | 2015-2026 | **+5,0 %** | [+2,7 ; +7,3] | 9 719 |
| Tennis WTA — idem | 2016-2026 | +2,3 % | [−0,2 ; +4,7] | 8 350 |
| Football 16 championnats extra — clôture Pinnacle vs meilleure clôture, EV > 2 % | 2019-2026 | **+5,8 %** | [+3,1 ; +8,6] | 13 311 |
| idem | 2012-2018 | +4,0 % | [+1,6 ; +6,5] | 17 640 |
| Football 22 championnats — Pinnacle ouverture vs meilleure cote, EV ≥ 5 % | 2019-2026 | +4,2 % | [−2,8 ; +11,1] | 2 347 |
| idem | 2012-2019 (dev) | +13,0 % | [+7,7 ; +18,3] | 4 224 |

Littérature : Kaunitz, Zhong & Kreiner (2017) +3,5 % sur 10 ans puis +6,2 % en argent
réel ; Angelini et al. (2022) en tennis : profit avec la meilleure cote parmi 11
bookmakers, **perte chez bet365 seul** ; Buchdahl (football-data) +2 à +5 % contre les
cotes justes de Pinnacle. Voir [02_etudes_scientifiques.md](../02_etudes_scientifiques.md).

## Les trois conditions de réussite

1. **Comparer beaucoup de bookmakers.** Contre un seul (bet365), le même filtre n'est
   pas significatif : tennis ATP +2,9 % [−4,2 ; +10,3], WTA −3,0 %. Avec bet365 + bwin
   (« FR ») en football : +7,6 % en test mais +0,4 % en dev → instable.
2. **Une référence vraiment sharp.** La moyenne du marché fonctionne aussi (S02), mais
   les modèles maison non (S03).
3. **Des marchés où les soft books sont en retard** : championnats secondaires,
   divisions inférieures, tennis. En Premier League, l'avantage a fortement diminué
   depuis 2021.

## Mise en œuvre en France

- Ouvrir des comptes chez plusieurs des 16 opérateurs agréés (liste dans
  [01_reglementation_ANJ.md](../01_reglementation_ANJ.md)).
- Le scanner (`scripts/daily_scan.py`) calcule la cote juste Betfair et repère les écarts
  sur bet365/bwin ; vérifier ensuite manuellement les autres opérateurs.
- Seuil conseillé : EV ≥ 3 % contre la cote juste ; cote ≤ 10 ; Kelly ¼ ≤ 2 % (S07).
- Suivre la CLV (S08). Si elle est négative après ~200 paris, arrêter.

## Risques

- Limitation des comptes gagnants (pratique courante, même si l'ANJ l'encadre).
- Les cotes .fr peuvent être plus basses que les cotes .com de nos données.
- L'avantage diminue dans le temps sur les marchés très suivis.
- Betfair Exchange est moins liquide que Pinnacle sur les petits championnats : la
  « cote juste » y est plus bruitée.
