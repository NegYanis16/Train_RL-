"""Table pas : une ligne par pas de chaque partie, avec l'état vu, l'action choisie et ce qu'elle a rapporté."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import Base

if TYPE_CHECKING:
    from api.db.models.partie import Partie

# Les 8 valeurs de l'état LunarLander, dans l'ordre de l'observation
COLONNES_ETAT = ["x", "y", "vx", "vy", "angle", "v_angle", "pied_gauche", "pied_droit"]


class Pas(Base):
    __tablename__ = "pas"

    # Clé primaire double (partie, numéro) : un numéro de pas n'est unique qu'à l'intérieur de sa partie.
    # Comme partie_id vient en premier, elle sert aussi d'index pour retrouver vite tous les pas d'une partie.
    partie_id: Mapped[int] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True)
    numero: Mapped[int] = mapped_column(primary_key=True)

    # L'état vu au moment de la décision, une colonne par valeur plutôt qu'un texte JSON :
    # on peut ainsi filtrer et calculer dessus en SQL (par exemple, la vitesse moyenne près du sol)
    x: Mapped[float]
    y: Mapped[float]
    vx: Mapped[float]
    vy: Mapped[float]
    angle: Mapped[float]
    v_angle: Mapped[float]
    pied_gauche: Mapped[float]
    pied_droit: Mapped[float]

    action: Mapped[int]  # 0 rien, 1 moteur gauche, 2 moteur principal, 3 moteur droit
    recompense: Mapped[float]  # récompense de ce pas seulement
    carburant: Mapped[float]  # cumulé depuis le début de la partie
    situation: Mapped[str] = mapped_column(index=True)  # haute altitude, approche, près du sol, au sol

    partie: Mapped["Partie"] = relationship(back_populates="pas")

    @property
    def etat(self) -> list[float]:
        """Les 8 colonnes de l'état remises sous la forme d'une observation LunarLander."""
        return [getattr(self, colonne) for colonne in COLONNES_ETAT]
