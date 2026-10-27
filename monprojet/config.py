"""Configuration du projet : c'est le seul fichier à adapter à votre sujet."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Vos données -------------------------------------------------------------
DATA_PATH = ROOT / "data" / "cantine_repas.csv"     # CantineAI : 340 jours d'école
TARGET = "repas_servis"                              # la colonne à prédire
FEATURES = [                 # tout ce qu'on connaît la veille à 10 h (sans la date)
    "jour",
    "inscrits",
    "menu",
    "temperature_c",
    "pluie_mm",
    "examens",
    "sortie_scolaire",
    "veille_vacances",
    "repas_semaine_precedente",
]
TEXT_COLUMN = None           # pas de colonne de texte libre

# --- Type de problème --------------------------------------------------------
TASK = "regression"          # on prédit un nombre de repas
MAIN_METRIC = "mae"          # erreur moyenne en nombre de repas (≈ 15 DH par repas en trop)

# --- Découpage entraînement / test -------------------------------------------
SPLIT = "chronologique"      # série temporelle : on teste sur les jours les plus récents
TIME_COLUMN = "date"         # colonne de date utilisée pour trier avant le découpage
TEST_SIZE = 0.2              # les 20 % de jours les plus récents servent au test
SEED = 42                    # graine : mêmes résultats à chaque lancement

MODELS_DIR = ROOT / "models"