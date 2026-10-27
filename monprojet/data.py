
"""Chargement et découpage des données."""

import math
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.utils.multiclass import type_of_target

from monprojet import config


def load_data(path=None) -> pd.DataFrame:
    """Lit le fichier CSV et renvoie un DataFrame."""

    # Utiliser le chemin fourni ou celui de config
    fichier = path if path is not None else config.DATA_PATH

    # Charger les données
    df = pd.read_csv(fichier)

    # Vérifier que la colonne cible existe
    if config.TARGET not in df.columns:
        raise ValueError(
            f"La colonne cible '{config.TARGET}' est absente du fichier CSV."
        )

    # Supprimer les lignes où la cible est manquante
    df = df.dropna(subset=[config.TARGET])

    return df


def feature_columns(df: pd.DataFrame) -> list:
    """Renvoie les colonnes utilisées comme variables d'entrée."""
    if config.FEATURES is not None:
        return list(config.FEATURES)

    excluded = {config.TARGET, config.TIME_COLUMN}
    return [c for c in df.columns if c not in excluded]


def split(df: pd.DataFrame):
    """Renvoie X_train, X_test, y_train, y_test."""

    # Séparer les variables explicatives et la cible
    X = df[feature_columns(df)]
    y = df[config.TARGET]

    # 1. Découpage aléatoire
    if config.SPLIT == "random":

        # Déterminer si le problème est une classification
        task = getattr(
            config, "TASK",
            getattr(config, "PROBLEM_TYPE", None)
        )

        if task is not None:
            is_classification = str(task).lower() == "classification"
        else:
            is_classification = type_of_target(y) in (
                "binary", "multiclass"
            )

        return train_test_split(
            X,
            y,
            test_size=config.TEST_SIZE,
            random_state=config.SEED,
            stratify=y if is_classification else None
        )

    # 2. Découpage chronologique
    elif config.SPLIT == "chronologique":

        # Trier les données par date (ancienne -> récente)
        dates = pd.to_datetime(df[config.TIME_COLUMN])
        ordre = dates.to_numpy().argsort(kind="stable")

        X = X.iloc[ordre]
        y = y.iloc[ordre]

        # Calculer la taille de l'ensemble de test
        if isinstance(config.TEST_SIZE, float):
            n_test = math.ceil(len(df) * config.TEST_SIZE)
        else:
            n_test = int(config.TEST_SIZE)

        # Séparer les données
        X_train = X.iloc[:-n_test]
        X_test = X.iloc[-n_test:]

        y_train = y.iloc[:-n_test]
        y_test = y.iloc[-n_test:]

        return X_train, X_test, y_train, y_test

    else:
        raise ValueError(
            f"Type de découpage inconnu : {config.SPLIT}"
        )
