# S04 — Mélanger modèle et marché

> Statut : ⚠️ **pas d'amélioration robuste**. À n'utiliser qu'avec un poids faible.

## Variantes testées

1. **Pool logarithmique** `p ∝ p_modèle^w · p_marché^(1−w)`, w = 0,2 ou 0,4
   (LightGBM ou Dixon-Coles mélangé au marché sharp).
2. **LightGBM hybride** : les probabilités du marché moyen sont des variables du modèle.
3. **Régression logistique** sur logit(p_marché) et logit(p_modèle) (multi-sports).

## Résultats

| Variante | dev | test | Commentaire |
|---|---|---|---|
| Pool 20 % LightGBM vs meilleure cote, EV ≥ 5 % | +3,9 % (n = 10 578) | **−1,4 %** (n = 6 168) | s'effondre en test |
| Pool 20 % Dixon-Coles vs meilleure cote, EV ≥ 5 % | +3,2 % | −3,4 % | idem |
| LightGBM hybride vs meilleure cote, EV ≥ 5 %, cote ≤ 3,5 | +3,0 % (n = 14 986) | +4,8 % (n = 11 456) | positif, mais ne bat ni la moyenne ni Pinnacle |
| Régression logistique marché + Elo (6 sports) | — | log-loss identique au marché | le modèle n'apporte rien |

## Conclusion

Le mélange n'ajoute pas d'information exploitable au marché. Le seul résultat positif
(LightGBM hybride vs meilleure cote) fonctionne parce que le modèle a appris à repérer
les écarts entre meilleure cote et consensus, c'est-à-dire S02. Dans le scanner, le
paramètre `--model-weight` est donc à 0 par défaut.
