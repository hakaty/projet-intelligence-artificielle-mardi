# TP0 : MaintAI

**Nom :** El Mehdi Benali · **Groupe :** 5IADAG2

## Le problème

Prédire à l'avance les pannes d'un équipement à partir de 4 relevés de capteurs (température, vibration, charge, heures de fonctionnement). Le jeu de données compte 5 000 relevés et seulement 17,6 % de pannes : les classes sont très déséquilibrées. Une panne manquée arrête une ligne de production pendant une journée, alors qu'une fausse alerte ne coûte qu'une heure d'inspection. Le coût des deux erreurs n'est donc pas le même.

## Résultats sur le jeu de test

Découpage aléatoire 80 % / 20 % (graine 42).

| Modèle | Accuracy | Rappel | Précision |
|---|---|---|---|
| baseline (toujours « pas de panne ») | 0.824 | 0.000 | 0.000 |
| régression logistique | 0.839 | 0.847 | 0.527 |
| arbre de décision | 0.839 | 0.597 | 0.538 |
| random forest | 0.880 | 0.534 | 0.712 |

## Mon choix, et pourquoi

Je retiens la **régression logistique**, car elle a le meilleur rappel (0,847) : elle détecte environ 85 % des vraies pannes.

L'accuracy est trompeuse ici. La baseline, qui répond toujours « pas de panne », obtient 82,4 % d'accuracy sans détecter aucune panne. Le random forest a la meilleure accuracy (0,880), mais il laisse passer presque une panne sur deux (rappel 0,534). Comme une panne manquée coûte bien plus cher qu'une fausse alerte, la métrique métier est le **rappel**.

Le prix à payer est la précision (0,527) : environ une alerte sur deux est une fausse alerte. C'est acceptable, car une inspection inutile coûte peu.

Côté code, `data.py` et `train.py` lisent tout depuis `config.py`. Pour passer d'un autre sujet (par exemple une régression sur une série temporelle), il suffit de changer `TASK`, `TARGET`, `MAIN_METRIC`, `SPLIT` et `TIME_COLUMN`, sans réécrire le reste.

## Le critère (rappel >= 0,75) est-il atteint ?

**Oui** pour la régression logistique : 0,847 > 0,75. Non pour l'arbre de décision (0,597) et le random forest (0,534).

## Ce qui reste flou

- **Fausses alertes :** avec une précision de 0,527, l'équipe inspecte environ deux machines pour une vraie panne. Il faut vérifier qu'elle a le temps de le faire chaque matin.
- **Données synthétiques :** les résultats viennent de données générées pour le cours, à confirmer sur de vrais relevés.
- **Seuil de décision :** le seuil par défaut (0,5) n'est pas forcément le meilleur compromis rappel / précision.
- **Stabilité :** un seul découpage train/test a été utilisé. Une validation croisée dirait si le rappel reste au-dessus de 0,75.
