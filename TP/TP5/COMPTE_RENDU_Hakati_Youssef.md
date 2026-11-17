# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

\*\*Groupe :*gp2* …  ·  **Membres :** Hakati Youssef  ·  **Date :** 17/11/2026

\---

## 1\. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
================== 5 failed, 27 passed, 2 warnings in 21.86s ==================
```

Quels tests échouent, et pourquoi ?

Les 5 tests de `tests/test\_tracking.py` échouent avec « aucun run MLflow : log\_run n'a rien enregistré ». La fonction `log\_run` de `maintai/tracking.py` n'était pas encore écrite : elle renvoyait seulement `""`, donc aucun run n'était enregistré dans MLflow (on voyait d'ailleurs « Run MLflow : » sans identifiant).

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant, `maintai` pointait vers le code du TP précédent (TP4), ou n'était pas installé dans ce nouvel environnement. Après `pip install -e .`, il pointe vers le dossier TP5 : c'est une installation « éditable », donc toute modification du code de TP5 est prise en compte sans réinstaller.

## 2\. Sprint 1 : MLflow

Votre fonction `log\_run` (`maintai/tracking.py`) :

```python
def log\_run(params: dict, metrics: dict, model, X\_example, data\_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    mlflow.set\_experiment(EXPERIMENT)
    with mlflow.start\_run() as run:
        mlflow.log\_params(params)
        mlflow.log\_param("data\_md5", file\_md5(data\_path))
        mlflow.log\_metrics(metrics)
        mlflow.sklearn.log\_model(
            model,
            name="model",
            input\_example=X\_example,
            skops\_trusted\_types=TRUSTED\_TYPES,
        )
    return run.info.run\_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
======================= 32 passed, 4 warnings in 20.88s =======================
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

|Commande|recall|precision|accuracy|
|-|-|-|-|
|`python -m maintai.train`|0.750|0.622|0.904|
|`python -m maintai.train --C 0.01`|0.691|0.653|0.908|
|`python -m maintai.train --threshold 0.2`|0.838|0.543|0.882|
|`python -m maintai.train --model forest`|0.728|0.562|0.886|
|`python -m maintai.train --threshold 0.15`|0.875|0.500|0.864|

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

La régression logistique avec le seuil 0.2 (run `4924e7d84c0248a2baa73d89b68f5f42`). Une panne manquée coûte plus cher qu'une fausse alerte, donc on privilégie le recall : 0.838 au lieu de 0.750 avec le seuil par défaut. La precision baisse (0.543), ce qui veut dire plus de fausses alertes, mais elle reste acceptable. Le seuil 0.15 a un recall encore plus haut (0.875), mais une alerte sur deux est fausse et son accuracy tombe au niveau du modèle de base (0.864). La forêt aléatoire n'est pas meilleure : son recall et sa precision sont tous les deux inférieurs à ceux de la régression logistique.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

`scikit-learn==1.8.0`. Au TP4, le modèle `model.joblib` pouvait être rechargé avec une autre version de scikit-learn que celle de l'entraînement, ce qui peut provoquer des erreurs ou des prédictions différentes. MLflow enregistre maintenant avec chaque modèle les versions exactes des bibliothèques : on sait quoi installer pour le recharger.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Dans `mlflow.db` (base SQLite : paramètres, métriques) et dans le dossier `mlruns/` (les modèles et leurs fichiers), dans le dossier TP5. Ils ne vont pas dans Git : ils sont lourds, changent à chaque entraînement et sont propres à chaque machine. Le `.gitignore` les exclut.

## 3\. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data\_md5` de votre dernier run MLflow. Que constatez-vous ?

Les deux valeurs sont identiques (`73e0b7cb3c…`). Le `data\_md5` enregistré par MLflow est l'empreinte des données utilisées : à partir d'un run, on peut retrouver le reçu DVC (donc le commit Git) qui correspond, et récupérer exactement ces données avec `dvc checkout` ou `dvc pull`.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

Un fichier de données peut être très lourd, et Git garde chaque version pour toujours : le dépôt deviendrait énorme. DVC garde le fichier hors de Git (dans son cache et dans le stockage) et ne met dans Git qu'un petit reçu (`.dvc`) avec le md5 et la taille. Git versionne le reçu, DVC versionne le fichier.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data\\sensors.csv.dvc:
        changed outs:
                modified:           data\\sensors.csv
```

|Version|Commit Git (`git log --oneline`)|md5 (8 premiers caractères)|Nombre de lignes|
|-|-|-|-|
|v1|`5aa6497` Données v1|`73e0b7cb`|5000|
|v2|`a8e184a` Données v2|`\_\_\_\_\_\_\_\_`|8000|

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

Après `git checkout 5aa6497 -- data/sensors.csv.dvc` et `dvc checkout`, `data/sensors.csv` contient 5000 lignes. Après `git checkout HEAD -- data/sensors.csv.dvc` et `dvc checkout`, on retrouve les 8000 lignes de la v2.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

`dvc pull` télécharge le fichier depuis le stockage (`%USERPROFILE%\\dvc-stockage`) et le remet dans `data/sensors.csv` : on retrouve les 8000 lignes. C'est ce que ferait un coéquipier qui clone le dépôt : Git lui donne le reçu, `dvc pull` lui donne les données.

## 4\. Relier modèle et données

|Run|data\_md5 (8 caractères)|n\_train|recall|precision|
|-|-|-|-|-|
|v1 (`1689914c…`)|`73e0b7cb`|4000|0.750|0.622|
|v2 (`25174ec3…`)|`\_\_\_\_\_\_\_\_`|6400|0.741|0.650|

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Non. Le recall v2 (0.741) est même légèrement inférieur au recall v1 (0.750), et la precision un peu meilleure. Surtout, les deux runs ne sont pas évalués sur le même jeu de test (1000 lignes pour la v1, 1600 pour la v2, générées différemment) : les écarts peuvent venir des données de test et non du modèle. Pour comparer deux modèles, il faut les évaluer sur les mêmes données de test.

## 5\. Décision : l'ADR 004

Voir `docs/adr/004-choix-du-modele.md` : régression logistique, C = 1.0, seuil 0.2. Run `4924e7d84c0248a2baa73d89b68f5f42`, `data\_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15` (données v1).

## 6\. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
Git versionne le code, et le petit reçu `.dvc` des données. DVC versionne les fichiers de données eux-mêmes (dans un cache et un stockage). MLflow garde la trace de chaque entraînement : paramètres, métriques, empreinte des données (`data\_md5`) et modèle avec les versions des bibliothèques.
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
Le stockage est un dossier de notre PC (`%USERPROFILE%\\dvc-stockage`) : ce chemin n'a de sens que sur notre machine, il ne doit donc pas aller dans Git. `--local` l'écrit dans `.dvc/config.local`, ignoré par Git. Pour partager les données avec tout le groupe, il faudrait un stockage commun accessible par tous (S3, Google Drive, un serveur), ajouté sans `--local` pour que sa configuration soit dans Git.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
Le code : dans Git (et le wheel du TP4). Les données : dans DVC, avec le reçu dans Git et le fichier dans le stockage. Le modèle avec ses versions exactes : dans MLflow (un run, son identifiant, et le `requirements.txt` du modèle).

## 7\. Le rendu Git

* Lien de la pull request : …
* Le tag `tp5` existe sur GitHub : oui / non
* `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? non (exclus par le `.gitignore` et `.dvc/.gitignore`)

## 8\. Ce qui reste flou



\- Lien de la pull request : https://github.com/hakaty/projet-intelligence-artificielle-mardi/pull/XX

\- Le tag `tp5` existe sur GitHub : oui

\- `git status` avant le commit : ... non (exclus par le `.gitignore` et `.dvc/.gitignore`)



…

