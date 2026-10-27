# TP0 : MaintAI

**Nom :** Hajar El Alaoui · **Groupe :** G2

## Le problème

L'objectif est de prévoir si une machine va tomber en panne, à partir de quatre mesures de capteurs : la température, la vibration, la charge et les heures de fonctionnement. Rater une panne est grave, car la ligne de production s'arrête toute une journée. Une fausse alerte est moins grave : elle coûte seulement une heure d'inspection.

## Résultats sur le jeu de test

| Modèle | Accuracy | Rappel | Précision |
|---|---|---|---|
| baseline | 0.824 | 0.000 | 0.000 |
| régression logistique | 0.839 | 0.847 | 0.527 |
| arbre de décision | 0.839 | 0.597 | 0.538 |
| random forest | 0.880 | 0.534 | 0.712 |

## Mon choix, et pourquoi

Je retiens la **régression logistique**. C'est le modèle qui trouve le plus de vraies pannes : son rappel est de **0,847**, soit environ 85 pannes repérées sur 100.

- Le random forest a la meilleure accuracy (0,880), mais il laisse passer presque la moitié des pannes. Pour l'usine, c'est le pire scénario.
- La baseline a 82,4 % d'accuracy alors qu'elle ne trouve aucune panne. Cela prouve que l'accuracy n'est pas la bonne mesure ici, parce qu'il y a beaucoup plus de machines en bon état que de pannes.
- La précision de 0,527 signifie que près d'une alerte sur deux est inutile. Je l'accepte, car inspecter une machine pour rien coûte bien moins cher qu'une journée d'arrêt.

## Le critère (rappel >= 0,75) est-il atteint ?

**Oui**, avec la régression logistique : son rappel de **0,847** dépasse le seuil de 0,75.

Les deux autres modèles échouent : 0,597 pour l'arbre de décision et 0,534 pour le random forest.

## Ce qui reste flou

- Je ne sais pas si l'équipe de maintenance peut gérer autant d'alertes chaque matin, puisqu'une sur deux est fausse.
- Les données sont synthétiques : il faudrait tester le modèle sur de vraies données d'usine.
- On pourrait changer le seuil de décision du modèle pour trouver un meilleur équilibre entre rappel et précision.
- Le résultat vient d'un seul découpage des données. Il faudrait vérifier qu'il reste stable avec d'autres découpages, par exemple avec une validation croisée.