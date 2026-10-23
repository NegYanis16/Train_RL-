"""Les modèles (tables) de la base. Importer ce package inscrit toutes les tables dans Base.metadata."""

from api.db.models.partie import Partie
from api.db.models.pas import COLONNES_ETAT, Pas

__all__ = ["COLONNES_ETAT", "Partie", "Pas"]
