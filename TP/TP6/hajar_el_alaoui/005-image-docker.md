# ADR 005 : Ce qui entre dans l'image Docker de MaintAI

Date : 24/11/2026 · Auteurs : Hajar El Alaoui (G2)

## Contexte
MaintAI doit tourner sur un serveur où personne ne prépare de `.venv` : on livre une image Docker
(`maintai:0.4.0`) qui contient Python, les bibliothèques et le code. Il faut décider ce qui est figé dans
l'image et ce qui arrive au lancement : le modèle (ré-entraîné régulièrement, séance 7), les données,
la clé API, et les outils de développement (MLflow, DVC, pytest).

## Décision 1 : le modèle arrive par un volume, il n'est pas dans l'image

### Options étudiées
1. **Modèle dans l'image** (`COPY models ./models`)
   - Gagne : une image autonome, un seul objet à déployer ; le couple code + modèle est figé et
     reproductible ; pas de dossier à préparer sur le serveur ; pas de 503 « modèle non chargé ».
   - Perd : chaque ré-entraînement impose un nouveau build et une nouvelle version d'image ; l'image
     grossit ; le modèle (potentiellement sensible) est partagé avec l'image.
2. **Modèle par un volume** (`-v ./models:/app/models:ro`, `MAINTAI_MODELS_DIR=/app/models`)
   - Gagne : on change de modèle sans toucher au code ni reconstruire (séance 7) ; l'image reste
     générique et légère ; lecture seule (`:ro`) : le conteneur ne peut pas abîmer le modèle.
   - Perd : l'image seule ne suffit pas ; oublier le `-v` donne `"model_loaded": false` puis 503 ;
     il faut garantir à part que le modèle a été écrit par la même version de scikit-learn
     (1.8.0, figée dans `requirements-docker.txt`).

### Décision
Option 2 : le modèle arrive par un volume en lecture seule. Le modèle change plus souvent que le code,
et le séparer de l'image permet de le remplacer sans nouveau build. Le risque d'incompatibilité est
contenu par la version figée de scikit-learn dans l'image et dans `requirements.txt`.

## Décision 2 : ce que `.dockerignore` laisse dehors

| Laissé dehors | Pourquoi | Ce que l'autre option ferait gagner / perdre |
|---|---|---|
| `.env` | secret : une image se partage (registre, collègues), `docker history` et les couches la révèlent ; la clé arrive par `--env-file` / `env_file` | l'inclure éviterait le `--env-file`, mais quiconque a l'image a la clé ; changer de clé imposerait un build |
| `models/` | décision 1 : volume | voir décision 1 |
| `data/` | lourd, change sans le code ; l'API n'en a pas besoin ; l'interface le reçoit par volume | l'inclure rendrait l'onglet « Données » autonome, au prix d'une image plus lourde et figée sur une version des données |
| `mlflow.db`, `mlruns/`, `.dvc/` | outils et historique d'entraînement, pas de service ; lourds et locaux | les inclure n'apporte rien au service et ferait grossir l'image |
| `.venv/`, `__pycache__/`, `.pytest_cache/`, `.git/`, `dist/`, `build/`, `*.egg-info/` | propres au PC (Windows), lourds ; les bibliothèques sont installées dans l'image par `pip` | les copier casserait l'image (binaires Windows dans un Linux) et l'alourdirait |
| `tests/` | on ne teste pas dans l'image de production | les inclure permettrait de tester dans le conteneur, au prix de pytest dans l'image |

De même, `requirements-docker.txt` ne contient ni mlflow, ni dvc, ni pytest, ni build : seulement ce qui
sert à **servir** (API et interface), avec des versions figées.

## Conséquences
- Facilite : remplacer le modèle sans rebuild ; partager l'image sans fuite de secret ; builds rapides
  (bibliothèques en cache, contexte de build réduit).
- Rend plus difficile : le lancement demande des options (`-v`, `--env-file`) — d'où `compose.yaml` qui
  les écrit une fois pour toutes ; le serveur doit recevoir `models/` et `.env` par un autre canal.
- À surveiller : `/health` (`model_loaded`) après chaque déploiement ; la cohérence entre la version de
  scikit-learn de l'image et celle qui a entraîné le modèle (`model_info.json`) ; ne jamais ajouter
  `COPY . .` sans vérifier `.dockerignore`.
