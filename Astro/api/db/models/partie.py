"""Table parties : une ligne par partie jouée, avec son résumé."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import Base

if TYPE_CHECKING:  # seulement pour l'éditeur : à l'exécution, la relation désigne Pas par son nom
    from api.db.models.pas import Pas


class Partie(Base):
    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(default=datetime.now)
    # Identifiant commun aux parties d'un même /evaluate ; None pour une partie jouée seule (/episodes)
    lot: Mapped[str | None] = mapped_column(index=True)
    seed: Mapped[int]  # situation de départ : la même graine rejoue exactement la même partie
    recompense: Mapped[float]
    duree: Mapped[int]  # en pas
    carburant: Mapped[float]
    issue: Mapped[str]  # posé, crash, sorti de l'écran, temps écoulé
    reussite: Mapped[bool]
    video: Mapped[str | None]  # nom du fichier MP4 dans le dossier des vidéos ; None si jouée sans vidéo

    # Une partie a plusieurs pas, rangés dans l'ordre. cascade : supprimer une partie supprime aussi ses pas
    pas: Mapped[list["Pas"]] = relationship(
        back_populates="partie", cascade="all, delete-orphan", order_by="Pas.numero"
    )
