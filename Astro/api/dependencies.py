"""Ce que les routes reçoivent en paramètre : l'agent, une session de base, le dossier des vidéos.

Les routes ne créent rien elles-mêmes, elles le demandent avec Depends. Les tests remplacent ces fonctions
(app.dependency_overrides) pour travailler sur une base et un dossier temporaires, sans toucher au code des routes.
"""

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, sessionmaker

from api.db.session import creer_fabrique_sessions
from api.services.agent import Agent, get_agent
from config import VIDEOS_PATH, logger


@lru_cache(maxsize=1)
def get_fabrique_sessions() -> sessionmaker[Session]:
    """Ouvre la vraie base au premier besoin (et pas à l'import : les tests ne la créent jamais)."""
    return creer_fabrique_sessions()


def get_session() -> Iterator[Session]:
    """Une session par requête, fermée à la fin de la requête même en cas d'erreur."""
    with get_fabrique_sessions()() as session:
        yield session


def get_dossier_videos() -> Path:
    return VIDEOS_PATH


def get_agent_charge() -> Agent:
    """L'agent, ou une erreur 503 si le modèle n'a pas pu être chargé (fichier absent, abîmé...)."""
    try:
        return get_agent()
    except Exception as erreur:
        logger.error(f"Modèle indisponible : {erreur}")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Modèle non chargé : voir GET /health") from erreur


# Raccourcis pour les signatures des routes : def route(session: SessionDep, agent: AgentDep)
SessionDep = Annotated[Session, Depends(get_session)]
AgentDep = Annotated[Agent, Depends(get_agent_charge)]
DossierVideosDep = Annotated[Path, Depends(get_dossier_videos)]
