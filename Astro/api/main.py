"""Point d'entrée de l'API Eagle-1 : crée l'application et branche les routes.

Lancement, depuis le dossier Astro, venv activé :
    uvicorn api.main:app --reload
Documentation interactive : http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import episodes, evaluation, play, statistiques, systeme
from api.services.agent import get_agent
from config import MODEL_VERSION, logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Le modèle est chargé au démarrage plutôt qu'à la première requête, qui serait sinon lente.
    # S'il manque, l'API démarre quand même : /health le signale et les routes qui en ont besoin répondent 503.
    try:
        get_agent()
    except Exception as erreur:
        logger.error(f"Démarrage sans modèle : {erreur}")
    logger.info("API Eagle-1 démarrée")
    yield
    logger.info("API Eagle-1 arrêtée")


app = FastAPI(
    title="Eagle-1 : pilote automatique",
    description="Un agent PPO entraîné sur LunarLander-v3 pose le module Eagle-1. "
                "L'API joue les parties, les enregistre et en calcule les statistiques.",
    version=MODEL_VERSION,
    lifespan=lifespan,
)

for module in (systeme, play, episodes, evaluation, statistiques):
    app.include_router(module.router)
