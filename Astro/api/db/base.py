"""Classe mère commune à tous les modèles SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Chaque modèle qui hérite de Base est inscrit dans Base.metadata, la liste des tables à créer."""
