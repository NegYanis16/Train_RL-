"""Fixtures communes : un client de test branché sur une base et un dossier de vidéos temporaires."""

import pytest
from fastapi.testclient import TestClient

from api.db.session import creer_fabrique_sessions
from api.dependencies import get_dossier_videos, get_fabrique_sessions, get_session
from api.main import app


@pytest.fixture
def dossier_videos(tmp_path):
    return tmp_path / "videos"


@pytest.fixture
def client(tmp_path, dossier_videos):
    """Un client HTTP de test. Chaque test part d'une base vide, créée dans un dossier temporaire de pytest."""
    fabrique = creer_fabrique_sessions(tmp_path / "parties.db")

    def session_de_test():
        with fabrique() as session:
            yield session

    # Les routes demandent get_session et get_dossier_videos : on leur donne les versions temporaires
    app.dependency_overrides[get_session] = session_de_test
    app.dependency_overrides[get_dossier_videos] = lambda: dossier_videos

    with TestClient(app) as client:  # le with déclenche le lifespan : le modèle est chargé comme en vrai
        yield client

    app.dependency_overrides.clear()
    fabrique.kw["bind"].dispose()  # ferme les connexions, sinon Windows garde le fichier .db verrouillé
    assert get_fabrique_sessions.cache_info().currsize == 0, "un test a ouvert la vraie base data/parties.db"
