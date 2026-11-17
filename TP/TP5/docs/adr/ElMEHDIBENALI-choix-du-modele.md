# ADR 004 : Choix du modèle et du seuil d'alerte de MaintAI

Date : 17/11/2026 · Auteurs : El Mehdi Benali

## Contexte
MaintAI doit prévenir avant une panne. Une panne manquée (faux négatif) coûte bien plus cher qu'une fausse alerte (faux positif) : la métrique prioritaire est donc le **recall**, avec une precision qui reste acceptable. Les entraînements sont maintenant suivis dans MLflow (expérience `maintai`), ce qui permet de comparer les réglages sur les mêmes données.

## Options étudiées
Tous les runs ci-dessous sont entraînés sur les données v1 (`data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15`, 5000 lignes).

| Option | recall | precision | accuracy |
|---|---|---|---|
| 1. Régression logistique, C = 1.0, seuil 0.3 | 0.750 | 0.622 | 0.904 |
| 2. Régression logistique, C = 0.01, seuil 0.3 | 0.691 | 0.653 | 0.908 |
| 3. Régression logistique, C = 1.0, seuil 0.2 | 0.838 | 0.543 | 0.882 |
| 4. Forêt aléatoire, seuil 0.3 | 0.728 | 0.562 | 0.886 |
| 5. Régression logistique, C = 1.0, seuil 0.15 | 0.875 | 0.500 | 0.864 |

1. Seuil 0.3 : bon compromis, mais une panne sur quatre est manquée.
2. C = 0.01 : meilleure precision, mais le recall baisse : plus de pannes manquées.
3. Seuil 0.2 : recall nettement meilleur (84 %), precision encore au-dessus de 50 %.
4. Forêt aléatoire : plus complexe, et moins bonne que la régression logistique sur le recall comme sur la precision.
5. Seuil 0.15 : recall le plus haut, mais une alerte sur deux est fausse, et l'accuracy tombe au niveau du modèle de base (0.864), qui ne prédit jamais de panne.

## Décision
**Régression logistique, C = 1.0, seuil d'alerte 0.2.** C'est le réglage qui détecte la grande majorité des pannes (recall 0.838) sans dégrader la precision au point de rendre les alertes peu crédibles.

- Run MLflow : `4924e7d84c0248a2baa73d89b68f5f42`
- Données : `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15` (v1, commit `5aa6497`, 5000 lignes)

## Conséquences
- On accepte **plus de fausses alertes** : environ 46 % des alertes ne correspondront pas à une vraie panne (precision 0.543). Les techniciens feront donc des contrôles inutiles.
- Le modèle est simple (régression logistique), donc rapide et facile à expliquer.
- Le modèle est reproductible : le run MLflow garde les paramètres, les métriques et les versions exactes des bibliothèques (scikit-learn 1.8.0), et DVC permet de retrouver les données exactes grâce au md5.
- À surveiller : la dérive des données. Le seuil devra être revérifié à chaque nouvelle version des données (par exemple la v2), en comparant les runs sur un même jeu de test.
