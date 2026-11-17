# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Membre :** El Mehdi Benali · **Groupe :** 5IADAG2 · **Date :** 10 novembre 2026

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
5 failed, 18 passed
```

Les 5 tests en échec sont exactement ceux des deux sprints à réaliser ; les 18 tests du TP1 / TP2 passent déjà.

- `tests/test_client.py` (3 tests) : `NotImplementedError` — `MaintaiClient.predict` n'est pas écrite dans le starter.
- `tests/test_ui.py` (2 tests) : `IndexError: list index out of range` — la page n'affiche que des `st.info(...)`, il n'y a aucun `st.metric` à lire.

## 2. Lancer Streamlit

`streamlit run ui/app.py` affiche un bloc d'exception rouge : `ModuleNotFoundError: No module named 'maintai'`.

`python -m streamlit run ui/app.py` fonctionne. La raison tient à `sys.path` :

- `streamlit run` lance l'exécutable `streamlit.exe` : le premier dossier de `sys.path` est `.venv\Scripts`, pas le dossier du projet, donc `import maintai` échoue.
- `python -m streamlit` ajoute le **dossier courant** au début de `sys.path` : `maintai` est trouvé.

La solution durable est d'installer le projet comme package (`pyproject.toml` + `pip install -e .`), ce qui est fait au TP4.

## 3. Sprint 1 : l'onglet « Données »

```python
col1, col2, col3 = st.columns(3)
col1.metric("Relevés", len(df))
col2.metric("Taux de panne", f"{df.failure.mean():.1%}")
col3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

variable = st.selectbox("Variable", FEATURES)

tranches = pd.cut(df[variable], bins=10)
taux_par_tranche = df.groupby(tranches, observed=True).failure.mean()
taux_par_tranche.index = [round(i.mid, 1) for i in taux_par_tranche.index]
st.subheader(f"Taux de panne par tranche de {variable}")
st.bar_chart(taux_par_tranche)

st.subheader("Température / vibration, selon la panne")
st.scatter_chart(
    df.assign(panne=df.failure.map({0: "non", 1: "oui"})),
    x="temperature_c",
    y="vibration_mm_s",
    color="panne",
)
```

À la fin du sprint 1, `python -m pytest` donne `4 failed, 19 passed` : `test_ui_shows_the_data` passe.

**Évolution du taux de panne avec la vibration :** il augmente très fortement, de quelques % pour les faibles vibrations jusqu'à près de 100 % pour les plus fortes. La vibration est la variable la plus discriminante : dans le nuage de points, les pannes se concentrent dans les vibrations élevées, quelle que soit la température.

**`print("relance")` en haut de `ui/app.py` :** le message s'affiche à chaque interaction avec un widget. Streamlit **relance tout le script de haut en bas** à chaque interaction.

**`@st.cache_data` sur `charger` :** il met en cache le résultat. Comme le script est relancé à chaque clic, sans cache le CSV serait relu à chaque fois ; avec le cache, il n'est lu qu'au premier appel.

## 4. Sprint 2 : l'onglet « Prédiction »

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
    headers = {"X-API-Key": self.api_key} if self.api_key else None
    r = self.http.post("/v1/predict", json=reading, headers=headers)
    if r.status_code != 200:
        raise APIError(r.status_code, r.json().get("detail"))
    return r.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 : `23 passed`.

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | la métrique « Probabilité de panne » (environ 95 %) et une alerte rouge, car la probabilité dépasse le seuil |
| valeurs par défaut, fausse clé | message orange « Erreur 401 : Clé API absente ou invalide » |
| API arrêtée | message rouge « API injoignable » (`httpx` lève une `HTTPError`) |

**Pourquoi le port 8501 n'a-t-il pas besoin d'être dans `MAINTAI_CORS_ORIGINS` ?**
Au TP2, la requête partait du **navigateur** (JavaScript `fetch`), donc soumise au CORS, mécanisme de sécurité des navigateurs. Au TP3, la requête `httpx` part du **serveur Python de Streamlit** : le CORS ne s'applique pas au code serveur. Le navigateur ne parle qu'à Streamlit.

## 5. Questions de compréhension

1. **Qui envoie la requête à l'API ?** TP2 : le navigateur (JavaScript). TP3 : le serveur Python de Streamlit via `MaintaiClient`.
2. **Pourquoi `test_client.py` n'a pas besoin d'uvicorn ?** Le client reçoit un `TestClient` FastAPI en injection (`MaintaiClient(api_key="test-key", http=client)`) : la requête va directement à l'objet `app` en mémoire, sans réseau. `test_ui.py` utilise `AppTest` et remplace l'appel à l'API par `monkeypatch`.
3. **HTML + JavaScript ou Streamlit ?** Pour une démonstration client : HTML + JavaScript (contrôle total du design, rien à installer). Pour l'application d'un technicien : Streamlit (quelques dizaines de lignes de Python, formulaires et graphiques prêts à l'emploi, facile à faire évoluer).

## 6. Le rendu Git

- Lien de la pull request : à compléter
- Le tag `tp3` existe sur GitHub : à compléter
- `.env`, `data/` et `models/` n'apparaissent pas dans `git status` : ils sont couverts par le `.gitignore`.

## 7. Ce qui reste flou

- La différence entre `APIError` (l'API a répondu, mais pas 200) et `httpx.HTTPError` (l'API n'a pas répondu du tout).
- Le détail du packaging, repris au TP4.
