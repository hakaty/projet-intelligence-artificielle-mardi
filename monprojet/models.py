
"""Les modèles à comparer."""

from monprojet import config

from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor


def candidates() -> dict:
    """Renvoie un dictionnaire de modèles non entraînés."""

    if config.TASK == "classification":
        return {
            "baseline": DummyClassifier(
                strategy="most_frequent"
            ),

            "logistic_regression": LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=config.SEED
            ),

            "random_forest": RandomForestClassifier(
                n_estimators=100,
                class_weight="balanced",
                random_state=config.SEED
            ),

            "decision_tree": DecisionTreeClassifier(
                random_state=config.SEED
            )
        }

    elif config.TASK == "regression":
        return {
            "baseline": DummyRegressor(
                strategy="mean"
            ),

            "linear_regression": LinearRegression(),

            "random_forest": RandomForestRegressor(
                n_estimators=100,
                random_state=config.SEED
            ),

            "decision_tree": DecisionTreeRegressor(
                random_state=config.SEED
            )
        }

    else:
        raise ValueError(
            f"Type de tâche inconnu : {config.TASK}"
        )
