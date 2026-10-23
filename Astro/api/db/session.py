"""Ouverture de la base SQLite : moteur, création des tables et fabrique de sessions."""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from api.db.base import Base
from config import DATABASE_PATH, logger


def _activer_cles_etrangeres(connexion_sqlite, _):
    # SQLite ne vérifie les clés étrangères (et n'applique ON DELETE CASCADE) que si on le lui demande,
    # et ce réglage est à refaire à chaque nouvelle connexion
    connexion_sqlite.execute("PRAGMA foreign_keys = ON")


def creer_engine(chemin_base: Path = DATABASE_PATH) -> Engine:
    """Le moteur : il sait se connecter au fichier SQLite et garde un réservoir de connexions."""
    chemin_base = Path(chemin_base)
    chemin_base.parent.mkdir(parents=True, exist_ok=True)
    # FastAPI traite les requêtes dans plusieurs threads. Chaque session prend sa propre connexion,
    # mais par défaut le pilote SQLite refuse qu'une connexion serve dans un autre thread que celui qui l'a créée.
    engine = create_engine(f"sqlite:///{chemin_base}", connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _activer_cles_etrangeres)
    return engine


def creer_fabrique_sessions(chemin_base: Path = DATABASE_PATH) -> sessionmaker[Session]:
    """Ouvre la base, crée les tables qui n'existent pas encore et renvoie de quoi ouvrir des sessions."""
    import api.db.models  # noqa: F401 — inscrit les modèles dans Base.metadata avant create_all

    engine = creer_engine(chemin_base)
    Base.metadata.create_all(engine)
    logger.info(f"Base des parties prête : {chemin_base}")
    # expire_on_commit=False : les objets restent lisibles après le commit, quand la route les renvoie
    return sessionmaker(engine, expire_on_commit=False)
