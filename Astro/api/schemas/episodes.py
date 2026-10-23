"""Format des parties : la demande de POST /episodes, le résumé d'une partie et son détail pas à pas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from api.services.agent import NOMS_ACTIONS
from api.services.regles import Issue, Situation


class PartieDemande(BaseModel):
    # Gymnasium n'accepte que des graines positives ; 2**31 est la limite des graines tirées au hasard par la simulation
    seed: int | None = Field(
        default=None, ge=0, lt=2**31,
        description="Situation de départ. Vide : tirée au hasard (et renvoyée dans la réponse pour rejouer la partie)",
        examples=[5021],
    )


class PasSortie(BaseModel):
    # from_attributes : le schéma se remplit en lisant les attributs d'un objet Pas de SQLAlchemy (pas.numero...)
    model_config = ConfigDict(from_attributes=True)

    numero: int
    etat: list[float] = Field(description="Les 8 valeurs vues au moment de la décision, dans l'ordre de /play")
    action: int
    recompense: float = Field(description="Récompense de ce pas seulement")
    carburant: float = Field(description="Carburant consommé depuis le début de la partie")
    situation: Situation

    @computed_field
    @property
    def nom_action(self) -> str:
        return NOMS_ACTIONS[self.action]


class PartieResume(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime
    lot: str | None = Field(description="Identifiant du /evaluate qui a joué cette partie ; vide pour une partie seule")
    seed: int
    recompense: float
    duree: int = Field(description="En pas")
    carburant: float
    issue: Issue
    reussite: bool
    # Le nom du fichier sur le disque est un détail interne : il sert à calculer video_url mais n'est pas renvoyé
    video: str | None = Field(exclude=True)

    @computed_field
    @property
    def video_url(self) -> str | None:
        """Adresse où regarder la vidéo, ou None si la partie a été jouée sans vidéo."""
        return f"/episodes/{self.id}/video" if self.video else None


class PartieDetail(PartieResume):
    """Le résumé, plus tous les pas : hérite de PartieResume pour ne pas répéter ses champs."""

    pas: list[PasSortie]
