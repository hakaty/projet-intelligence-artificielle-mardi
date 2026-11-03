# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** Malak AZALIM · **Membres :** Malak AZALIM · **Date :** 03/11/2026

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
10 passed, 3 failed
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit :

- `test_health` : la route `/health` et le schéma de sortie `HealthOut` sont déjà fournis.
- `test_openapi_documents_predict` : la route `/v1/predict` est déjà déclarée, donc elle apparaît dans `/openapi.json` même si son corps n'est pas encore écrit.
- `test_out_of_range_value_is_rejected` : il attend un code 422.
- `test_missing_field_is_rejected` : il attend aussi un code 422.

Les deux tests qui attendent un 422 passent « pour une mauvaise raison » : dans l'état initial, `SensorReading` ne déclare encore aucun champ, mais il garde `extra="forbid"`. Le corps envoyé contient les quatre champs `temperature_c`, `vibration_mm_s`, `load_pct` et `runtime_hours` : Pydantic les considère donc tous comme des champs inconnus et répond 422 pour « extra fields not permitted ». Le 422 vient de la présence des champs, et non de la valeur 500 °C ni du champ `load_pct` manquant. Les deux tests passent, mais ils ne testent pas encore ce qu'ils sont censés tester.

Les trois tests qui échouent sont ceux qui ont réellement besoin de `predict()` : `test_predict_returns_probability`, `test_high_risk_reading_raises_alert` et `test_503_when_model_missing`.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | -40 | 150 | Température d'une machine industrielle : -40 °C correspond au froid extrême de stockage, 150 °C à une surchauffe déjà anormale et dangereuse. Au-delà, la mesure n'est plus plausible. |
| `vibration_mm_s` | `float` | 0 | 50 | Vitesse de vibration : 0 mm/s pour une machine arrêtée ; au-delà de 50 mm/s l'installation est en vibration destructive, donc la valeur est douteuse. |
| `load_pct` | `float` | 0 | 100 | C'est un pourcentage de charge nominale : il ne peut être ni négatif ni supérieur à 100 %. |
| `runtime_hours` | `float` | 0 | 100 000 | Heures de fonctionnement cumulées : 0 pour une machine neuve ; 100 000 h correspond à plus de dix ans en continu, au-delà le compteur est probablement erroné ou remis à zéro. |

Après avoir écrit `schemas.py` seul, `python -m pytest` donne encore :

```
10 passed, 3 failed
```

Mais le message d'erreur des tests qui échouent a changé : ils ne parlent plus de validation Pydantic. Les requêtes valides passent maintenant le schéma et arrivent dans `predict()`, qui n'est pas encore implémentée (`NotImplementedError`). C'est un bon signe : la porte d'entrée (validation) fonctionne, il ne reste plus qu'à écrire la logique de prédiction.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(status_code=503, detail="Modèle indisponible, entraînez-le d'abord.")
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Le 500 signifie « erreur interne du serveur » : le code a un bug. Ici, le serveur fonctionne, mais une dépendance externe (le modèle entraîné) n'est pas disponible. Le code 503 « Service Unavailable » décrit exactement cette situation : le service est temporairement incapable de traiter la requête tant que le modèle n'a pas été entraîné et chargé. Le client comprend qu'il doit réessayer après avoir lancé `python -m maintai.train`.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Le chargement de `model.joblib` avec joblib est coûteux (lecture disque, désérialisation). Le faire à chaque requête ajouterait de la latence et consommerait inutilement de la mémoire. Le chargement dans le `lifespan` de FastAPI garantit aussi que toutes les requêtes utilisent la même version du modèle, et que l'API démarre même si le modèle est absent (elle répond alors 503 au lieu de planter).

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
14 passed, 1 warning in 13.66s
```

Répartition des 14 tests :

- `tests/test_api.py` : 7 tests (santé, prédiction, alerte, validation, modèle manquant, OpenAPI).
- `tests/test_client.py` : 1 test ajouté en plus, `test_500_degres_est_refuse`, qui vérifie qu'une température de 500 °C renvoie bien 422.
- `tests/test_data.py` : 3 tests (colonnes du jeu de données, colonne manquante refusée, conservation du taux de panne après découpage).
- `tests/test_train.py` : 3 tests (écriture des artefacts, contrat d'entrée `model_info.json`, modèle meilleur que la baseline).

Les tests vérifient donc les trois étages du projet : les données, l'entraînement et l'API. Le test `test_model_beats_baseline` est important : la baseline qui prédit toujours « pas de panne » obtient un rappel de 0,0, tandis que le modèle obtient un rappel de 0,75 (accuracy 0,904, précision 0,622, seuil 0,3). Le modèle apporte donc une vraie valeur par rapport à la baseline.

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, puis lancement de `uvicorn maintai.api.main:app --reload`, voici les résultats obtenus :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-03T17:35:21Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans la section du schéma `SensorReading` (partie « Schemas » de la documentation interactive), chaque champ affiche son type et ses contraintes `minimum` / `maximum`, qui correspondent aux `ge` et `le` du `Field(...)`. L'exemple fourni dans `json_schema_extra` apparaît également dans la requête d'essai.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un style d'architecture (ressources identifiées par des URL, méthodes HTTP, échanges sans état). FastAPI est un framework Python qui permet d'implémenter ce style facilement, avec validation Pydantic et documentation OpenAPI automatique.

2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   Il valide les données d'entrée, il sérialise et documente les données de sortie, et il génère automatiquement le schéma OpenAPI utilisé par `/docs`.

3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` est l'hôte (la machine locale), `8000` est le port d'écoute du serveur uvicorn, et `/v1/predict` est le chemin de la ressource sur ce serveur.

4. Pourquoi `/v1` dans l'adresse ?
   Pour versionner l'API : si le contrat change plus tard, on peut publier `/v2` sans casser les clients qui utilisent encore `/v1`.

5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le chemin du module Python à importer, et `app` est le nom de la variable FastAPI à l'intérieur de ce module.

## 7. Le rendu Git

- Lien de la pull request : à compléter
- Le tag `tp1` existe sur GitHub : à compléter
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  à compléter

> Remarque : le dossier local n'est pas encore un dépôt Git, il faudra l'initialiser et créer la pull request pour compléter cette partie.

## 8. Ce qui reste flou

Le choix du seuil (0,3) mériterait d'être justifié plus finement : il privilégie le rappel au détriment de la précision, ce qui est raisonnable pour de la maintenance prédictive, mais il faudrait le valider sur des données réelles. La qualité du modèle dépend aussi fortement des données synthétiques : sur de vraies mesures, il faudra surveiller la dérive des données et réentraîner régulièrement le modèle. Enfin, la protection de l'API par clé et la gestion du CORS seront abordées dans le TP2.
