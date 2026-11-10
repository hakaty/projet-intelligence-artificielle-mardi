"""Commande maintai-predict : une prédiction depuis le terminal, sans lancer l'API.

Usage : maintai-predict TEMPERATURE VIBRATION CHARGE HEURES
Exemple : maintai-predict 72 6 85 15000
"""
import argparse
import sys

from maintai.config import FEATURES, get_settings
from maintai.predict import Predictor


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="maintai-predict",
        description="Probabilité de panne pour un relevé de capteurs.",
    )
    parser.add_argument("temperature_c", type=float, help="température du moteur (°C)")
    parser.add_argument("vibration_mm_s", type=float, help="vitesse de vibration (mm/s)")
    parser.add_argument("load_pct", type=float, help="charge (%% de la capacité nominale)")
    parser.add_argument("runtime_hours", type=float, help="heures de fonctionnement cumulées")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    settings = get_settings()
    try:
        predictor = Predictor.load(settings)
    except FileNotFoundError:
        print(
            f"Modèle introuvable dans {settings.models_dir}\n"
            "Lancez python -m maintai.train, ou indiquez le dossier du modèle : "
            "set MAINTAI_MODELS_DIR=<chemin du dossier models>",
            file=sys.stderr,
        )
        return 1

    reading = {name: getattr(args, name) for name in FEATURES}
    result = predictor.predict(reading)
    pct = round(result["failure_probability"] * 100)
    etat = "ALERTE" if result["alert"] else "normal"
    print(f"Probabilité de panne : {pct} % ({etat})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
