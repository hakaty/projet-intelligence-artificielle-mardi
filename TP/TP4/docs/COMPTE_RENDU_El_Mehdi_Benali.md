# Compte rendu · TP4 : un package Python pour MaintAI

**Membre :** El Mehdi Benali · **Groupe :** 5IADAG2 · **Date :** 10/11/2026

---

## 1. Mise en place (dans `TP/TP4`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
2 failed, 25 passed
```

Les deux tests de `tests/test_package.py` échouent :

- `test_package_is_installed` : `importlib.metadata.version("maintai")` ne trouve pas le package, car il n'est pas encore installé ;
- `test_command_is_installed` : la commande `maintai-predict` n'existe pas, car son `.exe` n'est créé que par `pip install`.

**Pourquoi un `.venv` séparé pour le TP4 ?** Installer un package modifie l'environnement. Installer `maintai` du TP4 dans le `.venv` d'un autre TP ferait pointer `import maintai` vers le TP4 même en travaillant ailleurs.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

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

**Pourquoi ces dépendances, et pas pytest, ruff, fastapi ni streamlit ?**
Ce sont les bibliothèques importées par le code de `maintai/` : `numpy` et `pandas` (données), `scikit-learn` et `joblib` (entraînement, modèle), `httpx` (client). `fastapi` / `uvicorn` ne servent qu'à l'API (groupe `api`), `streamlit` qu'à l'interface (groupe `ui`), `pytest`, `ruff` et `build` qu'au développement (groupe `dev`). Un utilisateur de la commande n'en a pas besoin.

Après `pip install -e .`, `pip show maintai` indique la version `0.2.0` et `maintai-predict 72 6 85 15000` affiche :

```
Probabilité de panne : 95 % (ALERTE)
```

`python -m pytest` donne alors `27 passed`.

- **Depuis un autre dossier :** la commande marche, tant que le `.venv` est activé. `maintai.__file__` pointe vers `...\TP\TP4\maintai\__init__.py` : l'installation éditable n'a pas copié le code, elle a posé un lien vers notre dossier.
- **`streamlit run ui/app.py` sans `python -m` :** ça marche maintenant, car `maintai` est installé dans le `.venv` et trouvé quelle que soit la façon de lancer le script.
- **Modifier le message de `cli.py` sans réinstaller :** le nouveau message s'affiche tout de suite. On ne réinstalle que si `pyproject.toml` change (nouvelle commande, nouvelle dépendance).

## 3. Sprint 2 : construire et livrer le wheel

`python -m build` se termine par :

```
Successfully built maintai-0.2.0.tar.gz and maintai-0.2.0-py3-none-any.whl
```

**Contenu du wheel :** les modules de `maintai/` (`cli.py`, `client.py`, `config.py`, `data.py`, `dataset.py`, `predict.py`, `train.py`, `api/`) et les métadonnées `dist-info` (dont `entry_points.txt`, qui déclare `maintai-predict`). Il ne contient ni le modèle (`models/`), ni les données, ni `tests/`, ni `ui/`, ni `web/`, car `packages.find` n'inclut que `maintai*`.

**Essai d'un collègue dans un environnement neuf, avec le wheel seul :**

| Essai | Message obtenu |
|---|---|
| premier lancement | « Modèle introuvable » et l'indication d'utiliser `MAINTAI_MODELS_DIR` |
| avec `MAINTAI_MODELS_DIR` mais une autre version de scikit-learn | `InconsistentVersionWarning` (modèle écrit en 1.8.0, relu avec une version plus récente), puis la prédiction |
| après `pip install scikit-learn==1.8.0` | la prédiction, sans avertissement |

La ligne `"sklearn_version": "1.8.0"` de `models/model_info.json` explique l'avertissement : le wheel demande seulement `scikit-learn>=1.5`, donc pip installe la version la plus récente, différente de celle qui a écrit le modèle. Les résultats d'un modèle relu avec une autre version ne sont pas garantis.

## 4. Questions de compréhension

1. **Pourquoi `>=` dans `pyproject.toml` et `==` dans `requirements.txt` ?** `pyproject.toml` décrit un package qui doit cohabiter avec d'autres bibliothèques : une version minimale laisse pip choisir. `requirements.txt` fige l'environnement d'entraînement, car un modèle joblib se relit avec la version qui l'a écrit.
2. **`pip install -e .` ou le wheel ?** `-e` pour développer (lien vers le dossier, modifications visibles tout de suite). Le wheel pour livrer (copie figée, installable sans notre dossier).
3. **Que livrer en plus du wheel ?** Le modèle (`models/model.joblib`, `model_info.json`, `metrics.json`), indiqué par `MAINTAI_MODELS_DIR`, et les versions exactes (`requirements.txt`, au moins `scikit-learn==1.8.0`). Livrer un modèle, c'est le code, le modèle et les versions.

## 5. Le rendu Git

- Lien de la pull request : à compléter
- Le tag `tp4` existe sur GitHub : à compléter
- `dist/`, `build/`, `maintai.egg-info/` et `.venv` n'apparaissent pas dans `git status` : ils sont exclus par le `.gitignore`.

## 6. Ce qui reste flou

- Pourquoi joblib ne garantit pas de relire un modèle avec une autre version de scikit-learn, et comment mieux le contrôler (`model_info.json`, versions figées).
