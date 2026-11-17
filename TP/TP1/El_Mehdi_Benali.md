# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Membre :** El Mehdi Benali · **Groupe :** 5IADAG2 · **Date :** 03/11/2026

---

## 1. Mise en place

Dernière ligne de `python -m pytest` juste après la mise en place (rien n'est encore écrit) :

```
10 passed, 3 failed
```

Dans `tests/test_api.py`, certains tests passent déjà alors que rien n'est écrit :

- `test_health` : la route `/health` et le schéma `HealthOut` sont déjà fournis.
- `test_openapi_documents_predict` : la route `/v1/predict` est déclarée, elle apparaît donc dans `/openapi.json` même si son corps est vide.
- `test_out_of_range_value_is_rejected` et `test_missing_field_is_rejected` : ils attendent un code 422 et l'obtiennent, mais **pour une mauvaise raison**. `SensorReading` ne déclare encore aucun champ et garde `extra="forbid"` : Pydantic considère les quatre champs envoyés comme inconnus et répond 422. Le 422 ne vient ni de la valeur 500 °C ni du champ manquant.

Les trois tests qui échouent ont réellement besoin de `predict()` : `test_predict_returns_probability`, `test_high_risk_reading_raises_alert` et `test_503_when_model_missing`.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique |
|---|---|---|---|---|
| `temperature_c` | `float` | -40 | 150 | -40 °C : froid extrême de stockage ; 150 °C : surchauffe déjà dangereuse, au-delà la mesure n'est plus plausible. |
| `vibration_mm_s` | `float` | 0 | 50 | 0 pour une machine arrêtée ; au-delà de 50 mm/s la vibration est destructive, donc la valeur est douteuse. |
| `load_pct` | `float` | 0 | 100 | Pourcentage de charge nominale : ni négatif ni supérieur à 100 %. |
| `runtime_hours` | `float` | 0 | 100 000 | 0 pour une machine neuve ; 100 000 h représentent plus de dix ans en continu, au-delà le compteur est probablement faux. |

Les bornes viennent de la physique du capteur, pas du min / max observé dans les données.

Après avoir écrit `schemas.py` seul, `python -m pytest` donne encore `10 passed, 3 failed`, mais l'erreur des tests en échec a changé : les requêtes valides passent maintenant la validation et arrivent dans `predict()`, qui lève encore `NotImplementedError`. La validation d'entrée fonctionne.

## 3. La fonction `predict()` (`maintai/api/main.py`)

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(status_code=503, detail="Modèle indisponible, entraînez-le d'abord.")
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

**Pourquoi 503 et pas 500 quand le modèle manque ?**
Le 500 signifie « bug dans le serveur ». Ici le serveur fonctionne, mais une dépendance (le modèle entraîné) est absente. Le 503 « Service Unavailable » dit exactement cela : le service est temporairement indisponible, le client doit réessayer après `python -m maintai.train`.

**Pourquoi charger le modèle une seule fois, au démarrage ?**
Charger `model.joblib` coûte (lecture disque, désérialisation) : le refaire à chaque requête ajouterait de la latence et de la mémoire. Le chargement dans le `lifespan` garantit aussi que toutes les requêtes utilisent la même version du modèle, et que l'API démarre même sans modèle (elle répond alors 503 au lieu de planter).

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
14 passed, 1 warning
```

- `tests/test_api.py` : 7 tests (santé, prédiction, alerte, validation, modèle manquant, OpenAPI).
- `tests/test_client.py` : 1 test ajouté, `test_500_degres_est_refuse` (500 °C renvoie 422).
- `tests/test_data.py` : 3 tests (colonnes, colonne manquante refusée, taux de panne conservé après découpage).
- `tests/test_train.py` : 3 tests (artefacts écrits, contrat d'entrée de `model_info.json`, modèle meilleur que la baseline).

Les tests couvrent les trois étages : données, entraînement, API. `test_model_beats_baseline` est le plus important : la baseline a un rappel de 0, le modèle atteint un rappel de 0,75 (seuil 0,3).

## 5. L'API en marche

| Requête | Code | Réponse |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `failure_probability` d'environ 0,95, `alert: true`, `threshold: 0.3` |
| `POST /v1/predict` avec une température de 500 | 422 | `Input should be less than or equal to 150` |
| `POST /v1/predicte` (faute de frappe) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, les bornes apparaissent dans le schéma `SensorReading` (section « Schemas ») : chaque champ affiche son `minimum` et son `maximum`, qui viennent des `ge` / `le` de `Field(...)`.

## 6. Questions de compréhension

1. **REST et FastAPI ?** REST est un style d'architecture (ressources, URL, méthodes HTTP, sans état). FastAPI est un framework Python qui permet de l'implémenter, avec validation Pydantic et documentation OpenAPI automatique.
2. **Les trois rôles du schéma Pydantic ?** Valider l'entrée, sérialiser et documenter la sortie, générer le schéma OpenAPI utilisé par `/docs`.
3. **`http://localhost:8000/v1/predict` ?** `localhost` : la machine locale ; `8000` : le port d'écoute d'uvicorn ; `/v1/predict` : le chemin de la ressource.
4. **Pourquoi `/v1` ?** Pour versionner l'API : un futur `/v2` ne casse pas les clients qui utilisent `/v1`.
5. **`uvicorn maintai.api.main:app` ?** `maintai.api.main` est le module Python à importer ; `app` est la variable FastAPI dans ce module.

## 7. Le rendu Git

- Lien de la pull request : à compléter
- Le tag `tp1` existe sur GitHub : à compléter
- Relecteur et commentaire : à compléter

## 8. Ce qui reste flou

- Le choix du seuil (0,3) : il favorise le rappel au détriment de la précision, ce qui est raisonnable en maintenance prédictive, mais il faudrait le valider sur des données réelles.
- Les données sont synthétiques : en production il faudra surveiller la dérive des données et réentraîner le modèle.
- La protection de l'API (clé, CORS) est vue au TP2.
