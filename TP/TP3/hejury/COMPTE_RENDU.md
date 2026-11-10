# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :ia g2 …  ·  **Membres :*hajar el alaoui* …  ·  **Date :** 10/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
5 failed, 18 passed, 1 warning in 2.69s
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

- `tests/test_client.py` (3 tests) : `NotImplementedError: TP3 sprint 2 : MaintaiClient.predict`. La méthode `predict` du client n'est pas encore écrite.
- `tests/test_ui.py` (2 tests) : `IndexError: list index out of range`. La page n'affiche encore aucun `st.metric`, donc `at.metric[0]` n'existe pas.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
ModuleNotFoundError: No module named 'maintai'
Traceback:
  File "C:\Users\user\Desktop\TP3_complet\maintai-starter-tp3\ui\app.py", line 9, in <module>
    from maintai.client import APIError, MaintaiClient
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

Python cherche les modules dans les dossiers de `sys.path`. Avec `streamlit run ui/app.py`, il y ajoute le dossier du script (`ui/`), où il n'y a pas de dossier `maintai/`. Avec `python -m streamlit ...`, Python ajoute en plus le **dossier courant** (`TP/TP3`) à `sys.path`, et `maintai/` s'y trouve. L'import fonctionne donc. Au TP4, on installera `maintai` comme package pour que l'import marche quelle que soit la commande.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
c1, c2, c3 = st.columns(3)
c1.metric("Relevés", len(df))
c2.metric("Taux de panne", f"{df.failure.mean():.1%}")
c3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

variable = st.selectbox("Variable", FEATURES)

tranches = pd.cut(df[variable], bins=10)
taux = df.groupby(tranches, observed=True).failure.mean()
taux.index = [round(i.mid, 1) for i in taux.index]   # des nombres, pas du texte
st.subheader(f"Taux de panne par tranche de {variable}")
st.bar_chart(taux)

st.subheader("Température et vibration")
nuage = df.assign(panne=df.failure.map({0: "non", 1: "oui"}))
st.scatter_chart(nuage, x="temperature_c", y="vibration_mm_s", color="panne")
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13.6% |
| Température moyenne | 59.8 °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Le taux de panne augmente fortement avec la vibration : environ 2 % vers 1 mm/s, 10 % vers 3,4 mm/s, 32 % vers 5,6 mm/s, 66 % vers 7,8 mm/s, 84 % vers 10 mm/s, puis 100 % au-delà de 12 mm/s. Pour la température, il monte plus lentement, de 0 % vers 27 °C à environ 37 % vers 85-90 °C. **La vibration est la variable qui compte le plus.**

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

« relance » s'affiche dans le terminal à chaque interaction avec un widget, par exemple quand on change la variable dans la liste déroulante. Cela montre que Streamlit réexécute **tout le script**, de la première à la dernière ligne, à chaque interaction. Les curseurs de l'onglet « Prédiction » sont dans un `st.form` : les déplacer n'affiche rien, seul le bouton « Prédire » relance le script.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Il garde en mémoire le résultat de `charger(path)`. Le CSV n'est lu qu'au premier appel ; aux relances suivantes, Streamlit renvoie le DataFrame en cache au lieu de relire le fichier. Sans lui, le CSV serait relu à chaque clic et la page serait lente.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
    headers = {"X-API-Key": self.api_key} if self.api_key else {}
    r = self.http.post("/v1/predict", json=reading, headers=headers)
    if r.status_code != 200:
        try:
            detail = r.json().get("detail")
        except ValueError:  # réponse qui n'est pas du JSON
            detail = r.text
        raise APIError(r.status_code, detail)
    return r.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
========= 23 passed in 4.88s ==========
```

Avec l'API lancée (`python -m uvicorn maintai.api.main:app --reload --env-file .env`, clé `MAINTAI_API_KEY` définie dans `.env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | « Probabilité de panne : 95 % », puis en rouge : « ALERTE : risque de panne (seuil 30%). Planifier une intervention. » |
| valeurs par défaut, fausse clé | En jaune : « L'API a refusé la requête (erreur 401) : Clé API absente ou invalide ». Uvicorn affiche `POST /v1/predict HTTP/1.1" 401 Unauthorized` |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | En rouge : « API injoignable : vérifiez qu'uvicorn tourne sur http://localhost:8000 » |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

CORS est une règle **du navigateur** : il bloque le JavaScript d'une page qui appelle une autre origine non autorisée. Avec Streamlit, ce n'est pas le navigateur qui appelle l'API. C'est le **serveur Python de Streamlit** qui envoie la requête avec `httpx`, de serveur à serveur. Le navigateur ne parle qu'à Streamlit, sur le port 8501. Aucune règle CORS ne s'applique donc. La protection qui reste est la clé API.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   Au TP2, c'est le **navigateur**, avec le `fetch` du JavaScript de la page. Il est donc soumis à CORS. Dans Streamlit, c'est le **processus Python de Streamlit**, côté serveur, avec `MaintaiClient`, qui utilise `httpx`. Le navigateur ne reçoit que la page générée.
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   On passe au client un `TestClient` de FastAPI par le paramètre `http=`. Ce client appelle directement l'objet `app` en mémoire, sans réseau ni serveur. C'est pour cela que `predict` doit utiliser `self.http.post` et non `httpx.post` : le même code sert en production et dans les tests.
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   Pour une **démonstration**, je choisirais Streamlit : on l'écrit en Python en quelques dizaines de lignes, avec des graphiques et des formulaires prêts à l'emploi, et on peut la modifier rapidement. Pour **l'application d'un technicien**, utilisée tous les jours, je choisirais une page HTML/JS (ou une vraie application web). On contrôle l'interface (mobile, ergonomie), la page est légère et peut être servie statiquement, et on évite qu'un serveur Python relance tout le script à chaque clic pour chaque utilisateur. En contrepartie, il faut gérer CORS et plus de code.

## 6. Le rendu Git

- Lien de la pull request : …
- Le tag `tp3` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? non (exclus par `.gitignore`)

## 7. Ce qui reste flou

- Uvicorn lit `.env` **une seule fois, au démarrage**. Après avoir changé la clé dans `.env`, nous avions encore des erreurs 401 tant qu'uvicorn n'avait pas été relancé (Ctrl+C puis relance).
- Sous PowerShell, les commentaires `::` de cmd ne marchent pas, et `activate.bat` doit être remplacé par `Activate.ps1`.
