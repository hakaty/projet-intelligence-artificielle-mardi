# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** …  ·  **Membres :** …  ·  **Date :** 24/11/2026

> Les lignes marquées ⚠️ sont des sorties à recopier depuis **votre** PC (durées, tailles, identifiants) :
> les valeurs indiquées sont celles attendues.

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) : ⚠️

```
Hello from Docker!
Client:
 Version:           29.x.x
Server: Docker Desktop
 Engine:
  Version:          29.x.x
```

Dernière ligne de `python -m pytest` après la mise en place :

```
5 failed, 33 passed
```

## 2. Image et conteneur (pendant le premier build)

1. **Quelle différence entre une image et un conteneur ?**
   L'image est le résultat figé et nommé de la recette (le Dockerfile) : système, Python, bibliothèques et
   code, en lecture seule (`maintai:0.4.0`). Un conteneur est une copie de cette image **qui tourne**, isolée
   (ses propres fichiers, son réseau, ses processus). Une image peut donner plusieurs conteneurs : ici `api`
   et `ui` viennent de la même image.
2. **Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?**
   Chaque instruction crée une couche, et Docker réutilise toutes les couches jusqu'à la première qui change.
   Les bibliothèques (installation lente, rarement modifiées) passent donc avant le code (modifié souvent) :
   une modification du code ne relance pas `pip install`, qui reste en cache.
3. **Pourquoi `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?**
   Le modèle `model.joblib` est un objet sérialisé par scikit-learn 1.8.0 ; le recharger avec une autre
   version peut échouer ou donner d'autres résultats (TP4). `>=1.5` installerait la dernière version au jour
   du build : deux builds du même Dockerfile donneraient deux images différentes. `==` rend l'image
   reproductible et compatible avec le modèle.
4. **Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?**
   L'image sert MaintAI (API et interface) : on n'y entraîne pas, on n'y versionne pas les données et on n'y
   lance pas les tests. Ces outils sont lourds (MLflow surtout) : ils allongeraient le build, grossiraient
   l'image et ajouteraient des dépendances (donc des failles possibles) inutiles.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
# Image de MaintAI : le code et ses bibliothèques, sans les données ni le modèle.
# Construire : docker build -t maintai:0.4.0 .

# 1. L'image de départ : la même version de Python que sur les PC, en version légère
FROM python:3.11-slim

# 2. Le dossier de travail dans l'image
WORKDIR /app

# 3. Les bibliothèques AVANT le code : cette étape lente reste en cache
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# 4. Le code (change souvent : il vient après les bibliothèques)
COPY maintai ./maintai
COPY ui ./ui

# 5. Où trouver le modèle et les données : ils arrivent au lancement, par des volumes
ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

# 6. Le port de l'API, et la commande lancée par défaut (à l'écoute de toutes les adresses)
EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`.dockerignore` (lignes ajoutées) :

```
data/
models/
.env
mlflow.db
mlruns/
.dvc/
```

`python -m pytest` après le Dockerfile et le `.dockerignore` : `2 failed, 36 passed` (restent compose et ui).

| Build | Durée ⚠️ | Taille de l'image (`docker images`) ⚠️ |
|---|---|---|
| premier build | ≈ 5 min (téléchargement de python:3.11-slim + `pip install`) | ≈ 1 Go |
| après une modification de `maintai/predict.py` | quelques secondes | identique |

**Que signifie `CACHED` dans le journal du second build ?**
Docker a réutilisé la couche du build précédent au lieu de rejouer l'instruction : `FROM`, `WORKDIR`,
`COPY requirements-docker.txt` et `RUN pip install` sont `CACHED` car rien n'a changé avant eux. Seul
`COPY maintai` (le fichier modifié) et les instructions suivantes sont rejoués : d'où quelques secondes au
lieu de 5 minutes.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "%cd%\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | `200` · `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | `401` · `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict` avec la clé | `200` · `{"failure_probability":0.9475,"alert":true,"threshold":0.3,"model_version":"…"}` |

(relevé : `temperature_c=72, vibration_mm_s=6, load_pct=85, runtime_hours=15000`)

**Piège 1.** Sans l'option `-v ...models...` :
`/health` répond `{"status":"ok","model_loaded":false}` et `/v1/predict` (avec la clé) répond **503**
`Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API`.
Pourquoi : `models/` est exclu par `.dockerignore`, donc l'image ne contient pas le modèle. Dans le conteneur,
`MAINTAI_MODELS_DIR=/app/models` pointe vers un dossier vide : `Predictor.load` lève `FileNotFoundError`,
l'API démarre quand même mais sans modèle. C'est voulu : le modèle arrive au lancement, par le volume.

**Piège 2.** Avec `--host 127.0.0.1` :
`docker logs test` affiche `Uvicorn running on http://127.0.0.1:8000` — l'API a démarré normalement — mais
`http://localhost:8002/health` ne répond pas (« La connexion a été réinitialisée » / page inaccessible).
Pourquoi : dans un conteneur, `127.0.0.1` désigne **le conteneur lui-même**. Le trafic publié par
`-p 8002:8000` arrive par l'interface réseau du conteneur, pas par sa boucle locale : uvicorn ne l'écoute pas.
Il faut écouter partout, `--host 0.0.0.0` (comme dans le `CMD`). (Le modèle manque aussi ici, sans `-v`,
mais on n'atteint même pas l'API.)

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
# MaintAI en deux conteneurs : l'API et l'interface Streamlit.
# Lancer : docker compose up --build      Arrêter : docker compose down

services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env                     # MAINTAI_API_KEY, comme au TP2
    ports:
      - "8000:8000"                    # PC:conteneur
    volumes:
      - ./models:/app/models:ro        # le modèle vient du PC, en lecture seule

  ui:
    image: maintai:0.4.0               # la même image, une autre commande
    command: ["python", "-m", "streamlit", "run", "ui/app.py",
              "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000 # l'API vue depuis ce conteneur : le nom du service
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro            # les données de l'onglet « Données »
    depends_on:
      - api
```

`ui/app.py`, barre latérale :

```python
url = st.text_input("URL de l'API", os.getenv("MAINTAI_API_URL", "http://localhost:8000"))
```

Sortie de `docker compose ps` : ⚠️

```
NAME          IMAGE           COMMAND                  SERVICE   STATUS         PORTS
tp6-api-1     maintai:0.4.0   "uvicorn maintai.api…"   api       Up 30 seconds  0.0.0.0:8000->8000/tcp
tp6-ui-1      maintai:0.4.0   "python -m streamlit…"   ui        Up 30 seconds  0.0.0.0:8501->8501/tcp, 8000/tcp
```

**Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?**
`http://api:8000`. Elle vient de la variable d'environnement `MAINTAI_API_URL`, définie dans `compose.yaml`
pour le service `ui` et lue par `os.getenv` dans `ui/app.py`. Hors Docker (variable absente), la valeur
par défaut `http://localhost:8000` reste en place. Avec la clé de `.env`, « Prédire » affiche 95 % et l'alerte.

Résultat des deux commandes `docker compose exec ui ...` :

```
> docker compose exec ui python -c "import httpx; print(httpx.get('http://api:8000/health').text)"
{"status":"ok","model_loaded":true}

> docker compose exec ui python -c "import httpx; print(httpx.get('http://localhost:8000/health').text)"
Traceback (most recent call last):
  ...
httpx.ConnectError: [Errno 111] Connection refused
```

Pourquoi la seconde échoue : la commande s'exécute **dans le conteneur `ui`**, où `localhost` désigne le
conteneur `ui` lui-même ; rien n'y écoute sur le port 8000 (l'API est dans un autre conteneur). Dans le
navigateur, `localhost` est le PC, où Docker publie le port 8000 de l'API (`ports: "8000:8000"`). Entre
conteneurs, Compose fournit un réseau commun où chaque service se joint par son nom : `api`.

**`docker compose down`** arrête et supprime les deux conteneurs et le réseau créé par Compose
(`tp6_default`). Elle ne supprime ni l'image `maintai:0.4.0`, ni les dossiers `models/` et `data/` du PC
(volumes « bind », ils ne sont que montés).

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
38 passed
```

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Le modèle n'est pas dans l'image : il arrive par un volume en lecture
seule, pour pouvoir le ré-entraîner et le remplacer sans reconstruire l'image (au prix d'un `-v` à ne pas
oublier, et d'un scikit-learn figé à 1.8.0). `.dockerignore` laisse dehors le secret (`.env`), le modèle,
les données, les fichiers MLflow/DVC et tout ce qui est local au PC, pour une image légère, partageable
et sans fuite.

## 7. Questions de compréhension

1. **Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ?**
   - Dans l'image (`docker build`) : Python 3.11 (`FROM python:3.11-slim`), les bibliothèques
     (`RUN pip install -r requirements-docker.txt`), le code `maintai/` et `ui/` (`COPY`), les chemins par
     défaut (`ENV`) et la commande (`CMD`).
   - Au lancement : le modèle (volume `-v ./models:/app/models:ro`), les données pour l'interface
     (volume `./data:/app/data:ro`), la clé API et les origines CORS (`--env-file .env` / `env_file`),
     l'URL de l'API pour l'interface (`environment: MAINTAI_API_URL`), les ports (`-p` / `ports`).
2. **Pourquoi la clé API n'est-elle jamais dans l'image ?**
   Une image se partage (registre, collègues, serveur) et chaque couche se lit (`docker history`, extraction) :
   une clé dedans est publique pour quiconque a l'image, et ne se change qu'en reconstruisant. Au lancement,
   chaque environnement a sa propre clé, et la changer ne demande qu'un redémarrage.
3. **Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?**
   Au TP4/TP5 on livrait le code (wheel), le modèle, des versions figées et la trace de l'entraînement
   (MLflow, DVC). Docker ajoute **l'environnement d'exécution lui-même** : le système, la version de Python
   et les bibliothèques installées, figés dans une image `maintai:0.4.0` qui tourne à l'identique sur tout
   PC ou serveur avec Docker — plus la façon de lancer (commande, port, volumes, variables), écrite dans le
   Dockerfile et `compose.yaml`.

## 8. Le rendu Git

- Lien de la pull request : ⚠️ …
- Le tag `tp6` existe sur GitHub : ⚠️ oui
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? **non** (ils sont dans
  `.gitignore`, comme `mlflow.db` et `mlruns/`)

## 9. Ce qui reste flou

… (à compléter par le groupe)
