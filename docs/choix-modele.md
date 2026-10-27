# Choix du modèle

Ce document compare les modèles entraînés pour les deux prototypes et justifie le modèle retenu.

---

## MaintAI : prédire les pannes de machines

**Type de problème :** classification (panne : oui / non)
**Métrique principale :** recall
**Données :** `data/exemple_pannes.csv` (5 000 relevés, 17,6 % de pannes)
**Découpage :** aléatoire, 80 % entraînement / 20 % test (graine 42)

### Résultats sur le jeu de test

| Modèle | Accuracy | Recall | Precision |
|---|---|---|---|
| baseline (toujours « pas de panne ») | ≈ 0,824 | 0,000 | — |
| **logistic_regression** | 0,839 | **0,847** | 0,527 |
| decision_tree | 0,839 | 0,597 | 0,538 |
| random_forest | 0,880 | 0,534 | 0,712 |

### Modèle retenu : régression logistique

- **Meilleur recall (0,847)** : le modèle détecte environ 85 % des vraies pannes.
- Le random forest a la meilleure accuracy (0,880), mais il rate près d'une panne sur deux (recall 0,534). Une panne manquée arrête une ligne de production pendant une journée, alors qu'une fausse alerte ne coûte qu'une heure d'inspection. On privilégie donc le recall.
- La precision (0,527) signifie qu'environ une alerte sur deux est une fausse alerte. C'est acceptable, car une inspection coûte beaucoup moins cher qu'une panne.

### Pourquoi l'accuracy ne convient pas

Un modèle qui ne prédit jamais de panne aurait une accuracy d'environ **82,4 %** (100 % − 17,6 %), alors qu'il ne détecte **aucune** panne (recall = 0). Les classes sont déséquilibrées et les deux erreurs n'ont pas le même coût : l'accuracy cache ce problème.

### Critère d'acceptation

> Recall ≥ 0,80 sur le jeu de test, avec une precision ≥ 0,40.

**Résultat : recall = 0,847 et precision = 0,527.** Le critère est **atteint**.

---

## CantineAI : prévoir le nombre de repas

**Type de problème :** régression sur une série temporelle (nombre de repas)
**Métrique principale :** MAE (erreur absolue moyenne, en nombre de repas)
**Données :** `data/cantine_repas.csv` (340 jours d'école, septembre 2024 à juin 2026)
**Découpage :** chronologique, les 80 % de jours les plus anciens pour l'entraînement et les 20 % les plus récents pour le test

### Résultats sur le jeu de test

| Modèle | MAE | RMSE | R² |
|---|---|---|---|
| baseline (même jour, semaine précédente) | ≈ 79 | — | — |
| **linear_regression** | **22,2** | 28,2 | 0,883 |
| random_forest | 31,8 | 41,5 | 0,746 |
| decision_tree | 46,0 | 59,7 | 0,475 |

*La baseline a été calculée sur les jours de test où la valeur de la semaine précédente existe (elle est vide après les vacances).*

### Modèle retenu : régression linéaire

- **MAE la plus faible (22,2)** : le modèle se trompe en moyenne de 22 repas par jour, contre environ 79 pour la méthode actuelle du gestionnaire.
- Cela représente environ **57 repas d'erreur en moins par jour**, soit jusqu'à environ 850 DH de gaspillage évité par jour (à 15 DH le repas).
- Modèle simple, rapide et facile à expliquer : chaque variable (menu, examens, sortie scolaire…) a un effet lisible.
- Le random forest et l'arbre de décision font moins bien. Avec seulement 340 jours, les modèles complexes ont tendance à apprendre par cœur l'entraînement.

### Pourquoi un découpage chronologique

Si on tirait les jours de test au hasard, le modèle s'entraînerait sur des jours futurs pour prédire des jours passés. Ce serait une fuite d'information, et le score serait trop optimiste. En réalité, le gestionnaire ne connaît que le passé : on teste donc sur les jours les plus récents.

### Critère d'acceptation

> MAE ≤ 40 repas sur le jeu de test (les 20 % de jours les plus récents), et meilleure que la baseline.

**Résultat : MAE = 22,2, inférieure à 40 et inférieure à la baseline (≈ 79).** Le critère est **atteint**.