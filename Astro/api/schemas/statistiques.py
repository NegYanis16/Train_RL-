"""Format des statistiques : celles de toutes les parties (GET /stats) ou d'une seule évaluation (POST /evaluate)."""

from pydantic import BaseModel, Field, field_validator

from api.services.agent import NOMS_ACTIONS
from api.services.regles import Issue, Situation


class Statistiques(BaseModel):
    # Toutes les valeurs sauf nombre sont None quand il n'y a encore aucune partie
    nombre: int = Field(description="Nombre de parties prises en compte")
    moyenne: float | None = Field(description="Récompense moyenne")
    ecart_type: float | None = Field(description="Écart-type des récompenses (de population, comme np.std)")
    minimum: float | None
    maximum: float | None
    taux_reussite: float | None = Field(description="Proportion de parties à 200 points ou plus, entre 0 et 1")
    carburant_moyen: float | None
    duree_moyenne: float | None = Field(description="En pas")
    issues: dict[Issue, int] = Field(description="Nombre de parties par issue")
    decisions: dict[Situation, dict[str, int]] = Field(
        description="Pour chaque situation, combien de fois chaque action a été choisie : la politique observée",
        examples=[{"près du sol": {"rien": 710, "moteur gauche": 1351, "moteur principal": 6166, "moteur droit": 1430}}],
    )

    @field_validator("decisions", mode="before")
    @classmethod
    def nommer_actions(cls, decisions: dict) -> dict:
        """Le repository compte par numéro d'action (0 à 3) ; le tableau de bord veut lire les noms."""
        return {
            situation: {NOMS_ACTIONS[a] if isinstance(a, int) else a: n for a, n in par_action.items()}
            for situation, par_action in decisions.items()
        }
