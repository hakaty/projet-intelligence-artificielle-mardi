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
