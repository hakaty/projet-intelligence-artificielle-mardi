# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Membre :** El Mehdi Benali · **Groupe :** 5IADAG2 · **Date :** 17/11/2026

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
================== 5 failed, 27 passed, 2 warnings in 21.86s ==================
```

**Quels tests échouent, et pourquoi ?**
Les 5 tests de `tests/test_tracking.py` échouent avec « aucun run MLflow : log_run n'a rien enregistré ». La fonction `log_run` de `maintai/tracking.py` n'était pas encore écrite : elle renvoyait seulement `""`, donc aucun run n'était enregistré dans MLflow (on voyait « Run MLflow : » sans identifiant).

**Avant `pip install -e .`, où pointait le package `maintai` ? Et après ?**
Avant, `maintai` pointait vers le code du TP précédent (TP4), ou n'était pas installé dans ce nouvel environnement. Après `pip install -e .`, il pointe vers le dossier TP5 : c'est une installation « éditable », donc toute modification du code de TP5 est prise en compte sans réinstaller.

## 2. Sprint 1 : MLflow

Fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )
    return run.info.run_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
======================= 32 passed, 4 warnings in 20.88s =======================
```

Runs relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --threshold 0.15` | 0.875 | 0.500 | 0.864 |

**Quel run choisir pour MaintAI, et pourquoi ?**
La régression logistique avec le seuil 0.2 (run `4924e7d84c0248a2baa73d89b68f5f42`). Une panne manquée coûte plus cher qu'une fausse alerte, donc on privilégie le recall : 0.838 au lieu de 0.750 avec le seuil par défaut. La precision baisse (0.543), donc plus de fausses alertes, mais elle reste acceptable. Le seuil 0.15 a un recall encore plus haut (0.875), mais une alerte sur deux est fausse et son accuracy tombe au niveau du modèle de base (0.864). La forêt aléatoire n'est pas meilleure : son recall et sa precision sont inférieurs à ceux de la régression logistique.

**Version de scikit-learn dans le `requirements.txt` d'un modèle, et problème du TP4 réglé ?**
`scikit-learn==1.8.0`. Au TP4, `model.joblib` pouvait être rechargé avec une autre version de scikit-learn que celle de l'entraînement, ce qui peut provoquer des erreurs ou des prédictions différentes. MLflow enregistre maintenant avec chaque modèle les versions exactes des bibliothèques : on sait quoi installer pour le recharger.

**Où MLflow enregistre-t-il les runs ? Vont-ils dans Git ?**
Dans `mlflow.db` (base SQLite : paramètres, métriques) et dans le dossier `mlruns/` (modèles et fichiers), dans le dossier TP5. Ils ne vont pas dans Git : ils sont lourds, changent à chaque entraînement et sont propres à chaque machine. Le `.gitignore` les exclut.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```

**Comparaison du `md5` avec le paramètre `data_md5` du dernier run MLflow.**
Les deux valeurs sont identiques (`73e0b7cb3c…`). Le `data_md5` enregistré par MLflow est l'empreinte des données utilisées : à partir d'un run, on retrouve le reçu DVC (donc le commit Git) correspondant, et on récupère exactement ces données avec `dvc checkout` ou `dvc pull`.

**Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?**
Un fichier de données peut être très lourd, et Git garde chaque version pour toujours : le dépôt deviendrait énorme. DVC garde le fichier hors de Git (cache et stockage) et ne met dans Git qu'un petit reçu (`.dvc`) avec le md5 et la taille. Git versionne le reçu, DVC versionne le fichier.

**Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?**

```
data\sensors.csv.dvc:
        changed outs:
                modified:           data\sensors.csv
```

| Version | Commit Git | md5 (8 premiers caractères) | Lignes |
|---|---|---|---|
| v1 | `5aa6497` Données v1 | `73e0b7cb` | 5000 |
| v2 | à compléter (commit « Données v2 ») | à compléter | 8000 |

**Retour à la v1, puis à la v2.**
Après `git checkout 5aa6497 -- data/sensors.csv.dvc` et `dvc checkout`, `data/sensors.csv` contient 5000 lignes. Après `git checkout HEAD -- data/sensors.csv.dvc` et `dvc checkout`, on retrouve les 8000 lignes de la v2.

**Suppression de `data/sensors.csv` et de `.dvc/cache`, puis `dvc pull`.**
`dvc pull` télécharge le fichier depuis le stockage (`%USERPROFILE%\dvc-stockage`) et le remet dans `data/sensors.csv` : on retrouve les 8000 lignes. C'est ce que ferait un coéquipier qui clone le dépôt : Git lui donne le reçu, `dvc pull` lui donne les données.

## 4. Relier modèle et données

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | `73e0b7cb` | 4000 | 0.750 | 0.622 |
| v2 | à compléter | 6400 | 0.741 | 0.650 |

**Le modèle v2 est-il « meilleur » ?**
Non. Le recall v2 (0.741) est même légèrement inférieur à celui de la v1 (0.750), et la precision un peu meilleure. Surtout, les deux runs ne sont pas évalués sur le même jeu de test (1000 lignes pour la v1, 1600 pour la v2, générées différemment) : les écarts peuvent venir des données de test et non du modèle. Pour comparer deux modèles, il faut les évaluer sur les mêmes données de test.

## 5. Décision : l'ADR 004

Voir [docs/adr/004-choix-du-modele.md](docs/adr/004-choix-du-modele.md) : régression logistique, C = 1.0, seuil 0.2. Run `4924e7d84c0248a2baa73d89b68f5f42`, `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15` (données v1).

## 6. Questions de compréhension

1. **Différence entre Git, DVC et MLflow ?**
   Git versionne le code et le petit reçu `.dvc` des données. DVC versionne les fichiers de données eux-mêmes (cache et stockage). MLflow garde la trace de chaque entraînement : paramètres, métriques, empreinte des données (`data_md5`) et modèle avec les versions des bibliothèques.
2. **Pourquoi le stockage DVC est-il ajouté avec `--local` ? Que faudrait-il pour partager les données avec le groupe ?**
   Le stockage est un dossier de notre PC (`%USERPROFILE%\dvc-stockage`) : ce chemin n'a de sens que sur notre machine et ne doit pas aller dans Git. `--local` l'écrit dans `.dvc/config.local`, ignoré par Git. Pour partager, il faudrait un stockage commun accessible à tous (S3, Google Drive, serveur), ajouté sans `--local` pour que sa configuration soit dans Git.
3. **Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles ?**
   Le code : dans Git (et le wheel du TP4). Les données : dans DVC, avec le reçu dans Git et le fichier dans le stockage. Le modèle avec ses versions exactes : dans MLflow (un run, son identifiant, et le `requirements.txt` du modèle).

## 7. Le rendu Git

- Lien de la pull request : à compléter
- Le tag `tp5` existe sur GitHub : à compléter
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` et `.dvc/cache` n'apparaissent pas (exclus par le `.gitignore` et `.dvc/.gitignore`).

## 8. Ce qui reste flou

- À compléter.
