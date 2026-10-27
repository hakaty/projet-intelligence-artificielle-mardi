# TP0 : MaintAI

# TP0 : MaintAI

**Nom :** Malak AZALIM · **Groupe :** 5iada g2

## Le problème

L'objectif industriel initial (S3) est de détecter de manière anticipée les pannes d'un équipement à partir de relevés de 4 capteurs. Sur un volume de 5 000 observations (nettoyées via `dropna()`), le jeu de données est fortement déséquilibré avec seulement 17,6 % de pannes. C'est un enjeu critique : une panne manquée entraîne l'arrêt de la ligne de production. 

Ce projet s'inscrit dans une démarche MLOps avec un pipeline complet et reproductible. L'intérêt de ce squelette de code est sa flexibilité : il nous a permis aujourd'hui (S4) de passer d'un problème de classification à un problème de régression avec série temporelle (`cantine_repas.csv`), sans avoir à réécrire la logique principale.

## Résultats sur le jeu de test

| Modèle | Accuracy | Rappel | Précision | 
| ----- | ----- | ----- | ----- | 
| baseline (DummyClassifier) | 0.824 | 0.000 | 0.000 | 
| random forest | 0.881 | 0.557 | 0.705 | 
| régression logistique | 0.889 | 0.574 | 0.737 | 
| gradient boosting | 0.888 | 0.608 | 0.713 | 

## Mon choix, et pourquoi

Pour la classification, j'ai retenu le modèle **Gradient Boosting**. L'accuracy étant trompeuse (la Baseline atteint 82,4 % mais ne détecte aucune panne), le Rappel a été désigné comme métrique métier. Le Gradient Boosting offre le meilleur Rappel (0.608) avec un score F1 très solide.

Au-delà du choix de l'algorithme, mon choix architectural s'est porté sur un code modulaire où `data.py` et `train.py` lisent tout depuis `config.py`. C'est ce qui a permis la transition vers la S4 de manière fluide : pour adapter `main()` au nouveau jeu de données, il a suffi de paramétrer la configuration (`TASK = "regression"`, `TARGET = "repas_servis"`, `MAIN_METRIC = "mae"`, `SPLIT = "chronologique"`, `TIME_COLUMN = "date"`) et d'ajuster `models.py` (retrait du `random_state` de `DummyRegressor` pour sklearn), sans toucher au reste.

## Le critère (rappel >= 0,75) est-il atteint ?

Non, le critère n'est pas atteint. Le meilleur modèle retenu (Gradient Boosting) plafonne à un rappel de 0.608, ce qui reste inférieur à l'objectif de 0.75.

## Ce qui reste flou

La principale limite sur la classification reste la gestion du fort déséquilibre des classes, qui nécessitera d'appliquer des poids (`class_weight`) ou d'utiliser SMOTE pour espérer dépasser les 0.75 de rappel. 

Par ailleurs, bien que la méthode de validation utilisée en S4 soit claire et efficace (adapter la config en premier, regarder les erreurs, corriger au plus juste, puis relancer `pytest -v` jusqu'à obtenir 8/8 tests passés), la gestion fine des séries temporelles et des splits chronologiques dans des pipelines de données plus complexes pourrait nécessiter des approfondissements.
