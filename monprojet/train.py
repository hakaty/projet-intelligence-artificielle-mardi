
"""Entraîne chaque modèle candidat, l'évalue et les compare.

Usage : python -m monprojet.train
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from monprojet import config
from monprojet.data import load_data, split
from monprojet.models import candidates


HIGHER_IS_BETTER = {
    "accuracy": True,
    "recall": True,
    "precision": True,
    "f1": True,
    "mae": False,
    "rmse": False,
    "r2": True,
}


# ==========================================
# 1. PREPARATION DES DONNEES
# ==========================================

def build_preprocessing(X: pd.DataFrame) -> ColumnTransformer:
    """Prépare les données pour les modèles."""

    text = [config.TEXT_COLUMN] if config.TEXT_COLUMN else []

    numeric = [
        c for c in X.columns
        if c not in text
        and pd.api.types.is_numeric_dtype(X[c])
    ]

    categorical = [
        c for c in X.columns
        if c not in text and c not in numeric
    ]

    steps = []

    # Colonnes numériques
    if numeric:
        steps.append((
            "nombres",
            make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler()
            ),
            numeric
        ))

    # Colonnes catégorielles
    if categorical:
        steps.append((
            "categories",
            make_pipeline(
                SimpleImputer(strategy="most_frequent"),
                OneHotEncoder(handle_unknown="ignore")
            ),
            categorical
        ))

    # Colonnes textuelles
    if text:
        steps.append((
            "texte",
            TfidfVectorizer(),
            config.TEXT_COLUMN
        ))

    return ColumnTransformer(
        steps,
        sparse_threshold=0
    )


# ==========================================
# 2. EVALUATION DES MODELES
# ==========================================

def evaluate(model, X_test, y_test) -> dict:
    """Calcule les métriques du modèle."""

    # Prédictions
    y_pred = model.predict(X_test)

    if config.TASK == "classification":

        # Classification binaire ou multiclasse
        if len(np.unique(y_test)) == 2:
            average = "binary"
        else:
            average = "macro"

        scores = {
            "accuracy": accuracy_score(
                y_test, y_pred
            ),

            "recall": recall_score(
                y_test,
                y_pred,
                average=average,
                zero_division=0
            ),

            "precision": precision_score(
                y_test,
                y_pred,
                average=average,
                zero_division=0
            ),

            "f1": f1_score(
                y_test,
                y_pred,
                average=average,
                zero_division=0
            )
        }

    elif config.TASK == "regression":

        scores = {
            "mae": mean_absolute_error(
                y_test, y_pred
            ),

            "rmse": np.sqrt(
                mean_squared_error(y_test, y_pred)
            ),

            "r2": r2_score(
                y_test, y_pred
            )
        }

    else:
        raise ValueError(
            f"Type de tâche inconnu : {config.TASK}"
        )

    # Arrondir les résultats
    return {
        nom: round(float(valeur), 3)
        for nom, valeur in scores.items()
    }


# ==========================================
# 3. ENTRAINEMENT ET COMPARAISON
# ==========================================

def main() -> None:
    """Entraîne les modèles, compare et sauvegarde."""

    # Charger les données
    df = load_data()

    # Séparer entraînement et test
    X_train, X_test, y_train, y_test = split(df)

    resultats = {}
    modeles = {}

    print("\n===== ENTRAINEMENT DES MODELES =====\n")

    # Entraîner les modèles
    for nom, estimateur in candidates().items():

        print(f"Entraînement : {nom}")

        model = Pipeline([
            (
                "preparation",
                build_preprocessing(X_train)
            ),
            (
                "modele",
                estimateur
            )
        ])

        # Entraînement
        model.fit(X_train, y_train)

        # Évaluation
        scores = evaluate(
            model,
            X_test,
            y_test
        )

        # Stocker les résultats
        resultats[nom] = scores
        modeles[nom] = model

    # ======================================
    # 4. COMPARER LES MODELES
    # ======================================

    comparaison = pd.DataFrame(resultats).T

    # Trier selon la métrique principale
    comparaison = comparaison.sort_values(
        by=config.MAIN_METRIC,
        ascending=not HIGHER_IS_BETTER[
            config.MAIN_METRIC
        ]
    )

    # ======================================
    # 5. AFFICHER SEULEMENT 3 MODELES
    # ======================================

    # Masquer la baseline dans le tableau
    tableau = comparaison.drop(
        index="baseline",
        errors="ignore"
    )

    if config.TASK == "classification":

        # Afficher uniquement les 3 métriques
        tableau = tableau[
            ["accuracy", "recall", "precision"]
        ]

    else:
        tableau = tableau[
            ["mae", "rmse", "r2"]
        ]

    print("\n========================================")
    print(" COMPARAISON DES 3 MODELES ")
    print("========================================\n")

    # Afficher toutes les colonnes sans ...
    print(tableau.to_string())

    # ======================================
    # 6. SELECTIONNER LE MEILLEUR MODELE
    # ======================================

    meilleur_nom = comparaison.index[0]
    meilleur_modele = modeles[meilleur_nom]

    print("\n========================================")
    print(" MEILLEUR MODELE ")
    print("========================================")

    print(f"\nMeilleur modèle : {meilleur_nom}")

    print(
        f"{config.MAIN_METRIC} : "
        f"{resultats[meilleur_nom][config.MAIN_METRIC]}"
    )

    # ======================================
    # 7. SAUVEGARDER LE MODELE
    # ======================================

    dossier = Path(config.MODELS_DIR)

    dossier.mkdir(
        parents=True,
        exist_ok=True
    )

    # Sauvegarder le modèle
    joblib.dump(
        meilleur_modele,
        dossier / "model.joblib"
    )

    # Sauvegarder toutes les métriques
    donnees = {
        "main_metric": config.MAIN_METRIC,
        "best": meilleur_nom,
        "results": resultats
    }

    with open(
        dossier / "metrics.json",
        "w",
        encoding="utf-8"
    ) as fichier:

        json.dump(
            donnees,
            fichier,
            indent=4,
            ensure_ascii=False
        )

    print("\nModèle et métriques sauvegardés avec succès.")


# ==========================================
# EXECUTION
# ==========================================

if __name__ == "__main__":
    main()
