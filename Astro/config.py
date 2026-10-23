"""Configuration du projet Eagle-1 : variables d'environnement, chemins et logs.

Chaque valeur peut être changée dans un fichier .env (ou .env.local) à la racine du projet,
sans toucher au code. Voir .env.example pour la liste des variables.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# config.py est à la racine du projet (Astro/) : la racine est donc son propre dossier
BASE_DIR = Path(__file__).resolve().parent

# Charger les variables d'environnement depuis la racine du projet
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.local", override=True)


def _abs(rel: str) -> Path:
    """Résout un chemin relatif depuis la racine du projet."""
    p = Path(rel)
    return p if p.is_absolute() else BASE_DIR / p


# ── Logging ───────────────────────────────────────────────────────────────
LOG_LEVEL    = os.getenv("LOG_LEVEL",    "INFO")
# Les logs de l'API vont dans logs/api/ : logs/ contient aussi les courbes TensorBoard de l'entraînement
API_LOG_FILE = _abs(os.getenv("API_LOG_FILE", "logs/api/api.log"))

format_config = {
    "format": "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
}
logger.add(API_LOG_FILE, rotation="10 MB", retention="7 days", level=LOG_LEVEL, encoding="utf-8", **format_config)

# ── Environnement de simulation ───────────────────────────────────────────
ENV_ID = os.getenv("ENV_ID", "LunarLander-v3")

# ── Modèle ────────────────────────────────────────────────────────────────
# Le .zip est accompagné d'un .json du même nom qui indique l'algorithme (PPO ou DQN)
MODEL_PATH    = _abs(os.getenv("MODEL_PATH", "models/eagle1_final.zip"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")

# ── Données de l'API ──────────────────────────────────────────────────────
DATABASE_PATH = _abs(os.getenv("DATABASE_PATH", "data/parties.db"))   # base SQLite des parties jouées
VIDEOS_PATH   = _abs(os.getenv("VIDEOS_PATH",   "data/videos"))       # une vidéo MP4 par partie
VIDEO_FPS     = int(os.getenv("VIDEO_FPS", "50"))                     # LunarLander tourne à 50 images par seconde

# Limite du nombre de parties jouées par un seul appel à /evaluate (protège la RAM et le temps de réponse)
MAX_EPISODES_EVALUATE = int(os.getenv("MAX_EPISODES_EVALUATE", "200"))

# ── Serveur API ───────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
# Adresse que le GUI et le tableau de bord utilisent pour appeler l'API
API_URL  = os.getenv("API_URL", f"http://{API_HOST}:{API_PORT}")
