# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** 5IADAG2 ·  **Membres :** AZALIM Malak ·  **Date :** 10 novembre 2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
================== 5 failed, 18 passed, 1 warning in 28.78s ===================
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

- `tests/test_client.py` (3 tests) : `NotImplementedError: TP3 sprint 2 : MaintaiClient.predict` — la méthode `predict` du client n'est pas encore écrite dans le starter (elle se contente de `raise NotImplementedError`).
- `tests/test_ui.py` (2 tests) : `IndexError: list index out of range` — la page n'affiche encore que des `st.info(...)`, il n'y a aucun `st.metric` à lire (`at.metric[0]` n'existe pas).

Ce sont exactement les 5 tests des deux sprints à réaliser ; les 18 tests du TP1/TP2 passent déjà.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
ModuleNotFoundError: No module named 'maintai'

Traceback (most recent call last):
  File "...\TP3\ui\app.py", line 9, in <module>
    from maintai.client import APIError, MaintaiClient
ModuleNotFoundError: No module named 'maintai'
```

La page affiche le bloc d'exception rouge (avec le bouton « Rerun » en haut à droite) : l'import de `maintai` échoue.

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

Python cherche les modules dans `sys.path`, et cette liste dépend de la façon de lancer.
- `streamlit run` exécute l'exécutable `streamlit.exe` (dans `.venv\Scripts`) : le premier dossier de `sys.path` est alors `.venv\Scripts`, et non le dossier du projet → `import maintai` échoue.
- `python -m streamlit` lance le module depuis Python : `-m` ajoute le **dossier courant** au début de `sys.path` → le dossier du projet est parcouru, `maintai` est trouvé.

La solution durable (partie 3 du polycopié) est d'installer le projet comme un package (`pyproject.toml` + `pip install -e .`) : `maintai` devient importable quel que soit le mode de lancement.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

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

À la fin du sprint 1 : `python -m pytest` → `4 failed, 19 passed` (le test `test_ui_shows_the_data` passe maintenant).

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13.6% |
| Température moyenne | 59.8 °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Le taux de panne augmente très fortement avec la vibration : environ 2 % vers 1 mm/s, 10 % vers 3.4 mm/s, 32 % vers 5.6 mm/s, 66 % vers 7.8 mm/s, 84 % vers 10 mm/s, puis 100 % au-delà de 12 mm/s. La croissance est quasi exponentielle. C'est la **vibration** qui compte le plus : le taux de panne monte de 2 % à 100 % entre 1 et 12 mm/s, alors que la température ne fait varier le taux que progressivement autour de la moyenne — dans le nuage de points, les pannes (« oui ») se concentrent surtout dans les vibrations élevées, à toutes les températures.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

Le terminal affiche `relance` à chaque manipulation d'un widget (curseur déplacé, variable choisie, bouton cliqué). Cela montre que Streamlit **relance tout le script de haut en bas à chaque interaction** : l'exécution n'est pas ponctuelle, la page est entièrement recalculée à chaque « rerun » (d'où le bouton « Rerun » et la nécessité de mettre en cache ce qui est coûteux).

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Elle met en cache le résultat de `charger(path)`. Comme Streamlit relance tout le script à chaque interaction, sans cache le CSV serait relu à chaque clic de curseur. Avec `@st.cache_data`, la lecture n'a lieu qu'une seule fois (au premier appel) et les exécutions suivantes récupèrent le DataFrame en cache.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
    def predict(self, reading: dict) -> dict:
        """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
        headers = {"X-API-Key": self.api_key} if self.api_key else None
        r = self.http.post("/v1/predict", json=reading, headers=headers)
        if r.status_code != 200:
            raise APIError(r.status_code, r.json().get("detail"))
        return r.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
======================= 23 passed, 1 warning in 23.12s ========================
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | la métrique « Probabilité de panne : 95 % », puis en rouge « ALERTE : risque de panne élevé (au-dessus du seuil de 30%) » (l'API répond `failure_probability: 0.9475`, `alert: true`) |
| valeurs par défaut, fausse clé | en orange « Erreur 401 : Clé API absente ou invalide » |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | en rouge « API injoignable : vérifiez l'URL et lancez l'API (uvicorn). » (httpx lève `ConnectError`, une `httpx.HTTPError`) |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

Parce que la requête vers l'API n'est plus envoyée par le **navigateur**. En TP2, c'était le JavaScript de la page (`fetch`) exécuté par le navigateur à l'adresse `localhost:5501` : le CORS — un mécanisme de sécurité **des navigateurs** — bloquait donc les réponses, car 5501 n'était pas dans les origines autorisées. En TP3, la requête `httpx` est envoyée par le **processus serveur Python de Streamlit** (serveur → serveur) : le CORS ne s'applique pas au code serveur. Le navigateur, lui, ne parle qu'au serveur Streamlit (port 8501), jamais directement à l'API.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   - TP2 : le **navigateur** de l'utilisateur — le JavaScript de `web/index.html` appelle `fetch(".../v1/predict")`, la requête part donc de la machine du client.
   - TP3 : le **serveur Python de Streamlit** — `ui/app.py` utilise `MaintaiClient` (httpx), la requête part du processus serveur, le navigateur ne fait qu'afficher le résultat renvoyé par Streamlit.

2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   Parce qu'ils injectent leur propre client HTTP : `MaintaiClient(api_key="test-key", http=client)` passe le `TestClient` de FastAPI (fourni par la fixture `client` de `conftest.py`). La requête va **directement à l'objet `app` FastAPI en mémoire**, sans réseau ni serveur uvicorn. De même, `test_ui.py` exécute la page avec `AppTest` (sans navigateur) et remplace l'appel à l'API par une réponse connue avec `monkeypatch` : il teste la page, pas l'API.

3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   - Démonstration à un client : la page **HTML + JavaScript**, car elle donne un contrôle total sur le design (charte graphique, identité visuelle, responsive), se charge instantanément dans n'importe quel navigateur sans installer Python, et donne une image professionnelle et personnalisable.
   - Application du technicien : **Streamlit**, car elle s'écrit en quelques dizaines de lignes de Python (pas de HTML/CSS/JS à maintenir), offre directement formulaires, curseurs, tableaux et graphiques interactifs, et évolue facilement quand le modèle ou les données changent — le technicien n'a rien à installer : il ouvre l'URL.

## 6. Le rendu Git

- Lien de la pull request :  https://github.com/hakaty/projet-intelligence-artificielle-mardi/pull/1
- Le tag `tp3` existe sur GitHub : oui 
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? **non** — ils sont couverts par le `.gitignore` (`.env`, `data/*.csv`, `models/`), seuls les fichiers de code modifiés (`ui/app.py`, `maintai/client.py`, `COMPTE_RENDU.md`) sont à committer.

## 7. Ce qui reste flou

- La partie « package » du polycopié (`pyproject.toml`, `pip install -e .`, wheel) n'est pas dans le starter : à mettre en pratique pour comprendre pourquoi `streamlit run` seul échoue alors que `python -m streamlit run` fonctionne.
- La différence exacte entre `APIError` (l'API a répondu, mais pas 200) et `httpx.HTTPError` (l'API n'a pas répondu du tout) — visible dans les essais 2 et 3 du tableau ci-dessus.
