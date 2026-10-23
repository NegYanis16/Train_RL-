"""Format de POST /play : un état de LunarLander entre, une action sort."""

from typing import Annotated

from pydantic import BaseModel, Field, computed_field, field_validator

from api.db.models import COLONNES_ETAT
from api.services.agent import NOMS_ACTIONS

# Bornes de observation_space de LunarLander-v3 : un état en dehors ne peut pas venir du jeu,
# et l'agent n'a jamais rien vu de tel pendant l'entraînement
BORNES_ETAT = {
    "x": (-2.5, 2.5),
    "y": (-2.5, 2.5),
    "vx": (-10.0, 10.0),
    "vy": (-10.0, 10.0),
    "angle": (-6.2831855, 6.2831855),  # ± 2π
    "v_angle": (-10.0, 10.0),
    "pied_gauche": (0.0, 1.0),
    "pied_droit": (0.0, 1.0),
}

# allow_inf_nan=False : NaN et l'infini sont refusés, le réseau de neurones en ferait n'importe quoi
Valeur = Annotated[float, Field(allow_inf_nan=False)]


class EtatEntree(BaseModel):
    etat: list[Valeur] = Field(
        min_length=8,
        max_length=8,
        description="Les 8 valeurs observées : " + ", ".join(COLONNES_ETAT),
        examples=[[0.0, 1.4, 0.0, -0.1, 0.0, 0.0, 0.0, 0.0]],
    )

    @field_validator("etat")
    @classmethod
    def verifier_bornes(cls, etat: list[float]) -> list[float]:
        """Refuse un état hors des bornes du jeu, en nommant la valeur fautive."""
        for nom, valeur in zip(COLONNES_ETAT, etat):
            bas, haut = BORNES_ETAT[nom]
            if not bas <= valeur <= haut:
                raise ValueError(f"{nom} = {valeur} hors des bornes de LunarLander [{bas}, {haut}]")
        return etat


class ActionSortie(BaseModel):
    action: int = Field(ge=0, le=3, description="0 rien, 1 moteur gauche, 2 moteur principal, 3 moteur droit")
    probabilites: list[float] | None = Field(
        description="Probabilité de chaque action, dans l'ordre 0 à 3 (PPO seulement ; None pour DQN)"
    )

    @computed_field  # calculé à partir d'action et ajouté à la réponse JSON : la route n'a rien à faire
    @property
    def nom_action(self) -> str:
        return NOMS_ACTIONS[self.action]
