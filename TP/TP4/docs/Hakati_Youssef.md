# Compte rendu · TP4 : un package Python pour MaintAI

**Groupe :** IA 2  ·  **Membres :** Hakati Youssef  ·  **Date :** 10/11/2026

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
2 failed, 25 passed, 1 warning
```

Quels tests échouent, et pourquoi ?

Les deux tests de `tests/test_package.py` échouent :
- `test_package_is_installed` : `importlib.metadata.version("maintai")` ne trouve pas le package, car `maintai` n'est pas encore installé ;
- `test_command_is_installed` : la commande `maintai-predict` n'existe pas encore. Le `.exe` n'est créé que par `pip install`.

Pourquoi un `.venv` séparé pour le TP4 ?

Installer un package modifie l'environnement. Si on installait `maintai` du TP4 dans le `.venv` du TP1, `import maintai` pointerait vers le TP4, même quand on travaille dans le dossier d'un autre TP.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Les deux TODO complétés :

```toml
dependencies = [
    "numpy>=2.0",
    "pandas>=2.2",
    "scikit-learn>=1.5",
    "joblib>=1.4",
    "httpx>=0.27",
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

Pourquoi ces dépendances, et pas pytest, ruff, fastapi ni streamlit ?

Ce sont les bibliothèques importées par le code de `maintai/` : `numpy` (dataset.py), `pandas` (data.py, predict.py, dataset.py), `scikit-learn` (data.py, train.py), `joblib` (train.py, predict.py) et `httpx` (client.py). `fastapi` et `uvicorn` ne servent qu'à l'API : ils sont dans le groupe `api`. `streamlit` ne sert qu'à l'interface (groupe `ui`). `pytest`, `ruff` et `build` ne servent qu'au développement (groupe `dev`). Un utilisateur de la commande n'en a pas besoin.

Sortie de `pip show maintai` :

```
Name: maintai
Version: 0.2.0
Summary: Prédiction de panne à partir de relevés de capteurs
```

Sortie de `maintai-predict 72 6 85 15000` :

```
Probabilité de panne : 95 % (ALERTE)
```

Dernière ligne de `python -m pytest` après l'installation :

```
27 passed, 1 warning
```

Depuis un autre dossier (`cd /d %TEMP%`), `maintai-predict 72 6 85 15000` marche-t-il ? Où Python trouve-t-il le code (`python -c "import maintai; print(maintai.__file__)"`) ?

Oui, la commande marche depuis n'importe quel dossier, tant que le `.venv` est activé. `maintai.__file__` affiche le chemin **de notre dossier de travail** : `...\TP\TP4\maintai\__init__.py`. L'installation éditable n'a pas copié le code. Elle a posé un lien vers notre dossier.

`streamlit run ui/app.py` marche-t-il maintenant sans `python -m` ? Pourquoi ?

Oui. Au TP3, `maintai` n'était trouvé que si le dossier courant était dans `sys.path`, ce que fait `python -m`. Maintenant `maintai` est installé dans le `.venv` : il est trouvé quelle que soit la façon de lancer le script.

On modifie le message de `maintai/cli.py`, puis on relance la commande sans réinstaller. Que constate-t-on ?

Le nouveau message s'affiche tout de suite (par exemple « Risque de panne : 95 % (ALERTE) »). Avec `pip install -e .`, l'environnement lit directement nos fichiers : une modification est visible sans réinstaller. Il ne faut réinstaller que si on change `pyproject.toml`, par exemple pour ajouter une commande ou une dépendance.

## 3. Sprint 2 : construire et livrer le wheel

Sortie de `python -m build` (dernière ligne) :

```
Successfully built maintai-0.2.0.tar.gz and maintai-0.2.0-py3-none-any.whl
```

Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`) :

```
maintai/__init__.py
maintai/cli.py
maintai/client.py
maintai/config.py
maintai/data.py
maintai/dataset.py
maintai/predict.py
maintai/train.py
maintai/api/__init__.py
maintai/api/main.py
maintai/api/schemas.py
maintai/api/security.py
maintai-0.2.0.dist-info/METADATA
maintai-0.2.0.dist-info/WHEEL
maintai-0.2.0.dist-info/entry_points.txt
maintai-0.2.0.dist-info/top_level.txt
maintai-0.2.0.dist-info/RECORD
```

Le modèle est-il dans le wheel ? Les tests ? `ui/` ?

Non. Le wheel ne contient que le code du dossier `maintai/` (`packages.find` avec `include = ["maintai*"]`) et les métadonnées (`dist-info`). Il n'y a ni `models/` (le modèle), ni `data/`, ni `tests/`, ni `ui/`, ni `web/`. La commande `maintai-predict` est déclarée dans `entry_points.txt`.

Essai du collègue, dans un environnement neuf (`%TEMP%\essai`) avec le wheel seul :

| Essai | Message obtenu |
|---|---|
| premier lancement | `Modèle introuvable dans ...\essai\.venv\Lib\site-packages\models` puis `Lancez python -m maintai.train, ou indiquez le dossier du modèle : set MAINTAI_MODELS_DIR=<chemin du dossier models>` |
| après `set MAINTAI_MODELS_DIR=<votre TP\TP4\models>` | `InconsistentVersionWarning: Trying to unpickle estimator StandardScaler from version 1.8.0 when using version 1.9.1` (même avertissement pour LogisticRegression et Pipeline), puis `Probabilité de panne : 95 % (ALERTE)` |
| après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)`, sans avertissement |

Ouvrez `models/model_info.json`. Quelle ligne explique le deuxième message ?

```json
"sklearn_version": "1.8.0"
```

Le modèle a été écrit avec scikit-learn 1.8.0. Le wheel demande seulement `scikit-learn>=1.5`, donc pip a installé la version la plus récente (1.9.1) dans l'environnement neuf. Relire un modèle avec une autre version que celle qui l'a écrit déclenche l'avertissement, et les résultats ne sont pas garantis. Installer la version exacte de `requirements.txt` fait disparaître l'avertissement.

## 4. Questions de compréhension

1. `pyproject.toml` dit `>=`, `requirements.txt` dit `==`. Pourquoi les deux ?
   `pyproject.toml` décrit un **package** qui doit pouvoir s'installer à côté d'autres bibliothèques : on donne une version minimale pour laisser pip choisir. `requirements.txt` décrit **notre environnement** de travail et d'entraînement : on fige les versions exactes, car un modèle sauvegardé avec joblib se relit avec la version qui l'a écrit.
2. `pip install -e .` ou le wheel : lequel pour développer, lequel pour livrer ?
   `pip install -e .` pour **développer** : c'est un lien vers notre dossier, et les modifications sont visibles tout de suite. Le **wheel** pour **livrer** : c'est une copie figée du code, qu'un collègue installe sans avoir notre dossier.
3. Qu'est-ce qui n'est pas dans le wheel, et que faut-il livrer avec ?
   Le modèle (`models/model.joblib`, `model_info.json`, `metrics.json`), les données, les tests et l'interface. Livrer un modèle, c'est trois choses : **le code** (le wheel), **le modèle** (le dossier `models/`, indiqué par `MAINTAI_MODELS_DIR`) et **les versions exactes** (`requirements.txt`, au moins `scikit-learn==1.8.0`).

## 5. Le rendu Git

- Lien de la pull request : https://github.com/hakaty/projet-intelligence-artificielle-mardi/pull/2
- Le tag `tp4` existe sur GitHub : oui
- `git status` avant le commit : `dist/`, `build/`, `maintai.egg-info/` ou `.venv` apparaissaient-ils ? non (exclus par `.gitignore`)

## 6. Ce qui reste flou

- La gestion des versions du modèle : pourquoi joblib ne garantit pas de relire un modèle avec une autre version de scikit-learn que celle qui l'a écrit (d'où l'utilité de `model_info.json` et des versions figées dans `requirements.txt`).
