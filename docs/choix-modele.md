# Choix du modèle

Date : [jj/mm/aaaa] · Groupe : [noms]

## Contexte
[Le problème en deux phrases ; la métrique principale et pourquoi (section 5 de l'étude de conception).]

## Données et découpage
[Fichier, nombre de lignes, colonnes utilisées, découpage aléatoire ou chronologique, taille du jeu de test.]

## Résultats sur le jeu de test

| Modèle | Métrique principale | Autres métriques |
|---|---|---|
| Baseline | | |
| | | |
| | | |

## Décision
[Le modèle retenu et la raison principale. Bat-il la baseline ? De combien ? Le critère d'acceptation est-il atteint ?]

## Limites
[Ce que ces chiffres ne disent pas : taille du jeu de test, données manquantes, cas mal couverts.]
## CantineAI : choix du modèle

| Modèle | MAE | RMSE | R² |
|---|---|---|---|
| baseline (semaine précédente) | ≈ 79 | | |
| linear_regression | 22,2 | 28,2 | 0,88 |
| random_forest | 31,8 | 41,5 | 0,75 |
| decision_tree | 46,0 | 59,7 | 0,48 |

**Modèle retenu : régression linéaire.**
- MAE la plus faible : environ 22 repas d'erreur par jour, contre environ 79 pour la baseline.
- Modèle simple, rapide et facile à expliquer au gestionnaire.
- Critère d'acceptation (MAE ≤ 40 sur les 20 % de jours les plus récents, meilleure que la baseline) : **atteint**.

Split chronologique : on teste sur les jours les plus récents, sans tirage au hasard, pour éviter de prédire le passé avec le futur.
