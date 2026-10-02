# S07 — Gestion de bankroll : Kelly fractionné et plafonné

> Statut : ✅ **recommandé : Kelly ¼, plafonné à 2 % de la bankroll et à une mise
> absolue réaliste**. Code : `sportpred/betting/kelly.py`, `sportpred/backtest/engine.py`.

## 1. Le critère de Kelly

Pour une probabilité p et une cote o, la fraction de bankroll qui maximise la croissance
à long terme est

```
f* = (p × o − 1) / (o − 1)
```

Exemple : p = 0,55, o = 2,0 → f* = 10 % de la bankroll.

## 2. Pourquoi jamais Kelly complet

- **p est estimée avec erreur.** Baker & McHale (2013) montrent qu'en présence
  d'incertitude sur p, la mise optimale est un Kelly « rétréci » (fraction < 1).
- Kelly complet donne une probabilité d'environ 1/2 de voir la bankroll divisée par 2
  avant de la doubler (Thorp 2006). Kelly ½ ramène les fluctuations à un niveau
  supportable pour ~75 % de la croissance ; Kelly ¼ divise encore la variance.
- Uhrín et al. (2021) testent de nombreuses variantes sur données réelles : les
  versions fractionnées et plafonnées sont les plus robustes.

## 3. Ce que montrent nos simulations

Tennis ATP+WTA, stratégie S01 (EV > 2 %, meilleure cote), période test, 1 000 € de départ,
**mise plafonnée à 50 €** (sans plafond, Kelly produit des bankrolls de plusieurs millions,
ce qui n'a aucun sens face aux limites des bookmakers) :

| Gestion | ROI | Bankroll finale | Drawdown max |
|---|---|---|---|
| Mise fixe 10 € (1 %) | +3,6 % | 7 441 € | 94 % |
| Kelly ¼ (≤ 2 %) | +4,4 % | 30 227 € | 68 % |
| Kelly ½ (≤ 5 %) | +4,2 % | 31 616 € | 92 % |

Football : voir [07_resultats_football.md](../07_resultats_football.md) (tableau
« gestion de mise »).

Enseignements :

1. Même une stratégie **réellement gagnante** subit des chutes de 70 à 90 % si la mise
   est trop forte ou si l'avantage disparaît temporairement (tennis 2014-2016).
2. Kelly ¼ capte presque toute la croissance de Kelly ½ avec un risque bien plus faible.
3. Kelly mise davantage sur les EV élevées, qui sont aussi les plus souvent fausses : le
   **plafond d'EV à 30 %** et le **plafond de mise à 2 %** sont indispensables.

## 4. Règles concrètes

- Bankroll = argent dédié, que vous acceptez de perdre entièrement.
- Mise = min(¼ × f*, 2 %) × bankroll, recalculée chaque jour (pas après chaque pari).
- Exposition journalière maximale : 30 % de la bankroll.
- Paris simultanés indépendants : `simultaneous_kelly()` résout le problème exact
  (maximisation de E[log W]) ; à défaut, réduire proportionnellement.
- Ne jamais « se refaire » : la mise dépend de l'avantage, pas des pertes passées
  (la martingale mène mathématiquement à la ruine).
