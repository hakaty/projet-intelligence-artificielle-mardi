# TP0 : MaintAI

**Nom :** youssef hakati · **Groupe :** G2

## Le problème

Prédire une panne à partir de 4 capteurs (température, vibration, charge, heures de fonctionnement) ; une panne manquée arrête une ligne de production pendant une journée, alors qu'une fausse alerte ne coûte qu'une heure d'inspection.

## Résultats sur le jeu de test

| Modèle | Accuracy | Rappel | Précision |
|---|---|---|---|
| baseline | 0.824 | 0.000 | 0.000 |
| régression logistique | 0.839 | 0.847 | 0.527 |
| arbre de décision | 0.839 | 0.597 | 0.538 |
| random forest | 0.880 | 0.534 | 0.712 |

## Mon choix, et pourquoi

Je choisis la **régression logistique**, car elle a le **meilleur rappel (0,847)** : elle détecte environ 85 % des vraies pannes.

Le random forest a la meilleure accuracy (0,880), mais il rate presque une panne sur deux (rappel de 0,534). Or une panne manquée coûte beaucoup plus cher qu'une fausse alerte : une journée de production perdue contre une heure d'inspection. C'est donc le rappel qui compte, pas l'accuracy.

La baseline montre le piège de l'accuracy : en prédisant toujours « pas de panne », elle obtient 82,4 % d'accuracy sans détecter **aucune** panne.

La précision de la régression logistique (0,527) veut dire qu'environ une alerte sur deux est fausse. C'est acceptable, car une inspection inutile coûte peu.

## Le critère (rappel >= 0,75) est-il atteint ?

**Oui.** Le rappel de la régression logistique est de **0,847**, ce qui est supérieur à 0,75. Le critère est atteint sur le jeu de test.

En revanche, l'arbre de décision (0,597) et le random forest (0,534) ne l'atteignent pas.

## Ce qui reste flou

- **Fausses alertes :** avec une précision de 0,527, l'équipe inspecte environ deux machines pour une vraie panne. Il faudrait vérifier si l'équipe a le temps pour ce nombre d'inspections chaque matin.
- **Données synthétiques :** les résultats viennent de données générées pour le cours. Il faudrait les confirmer sur de vrais relevés de l'usine.
- **Seuil de décision :** le modèle utilise le seuil par défaut (0,5). Un autre seuil pourrait changer l'équilibre entre rappel et précision.
- **Stabilité :** le résultat vient d'un seul découpage train/test (graine 42). Avec une validation croisée, on saurait si le rappel reste au-dessus de 0,75.