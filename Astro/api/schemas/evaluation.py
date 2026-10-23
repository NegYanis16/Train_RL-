"""Format de POST /evaluate : jouer N parties sans vidéo et renvoyer leurs statistiques."""

from pydantic import BaseModel, Field

from api.schemas.statistiques import Statistiques
from config import MAX_EPISODES_EVALUATE


class EvaluationDemande(BaseModel):
    # La limite protège le serveur : 200 parties prennent déjà quelques secondes et ~40 000 lignes en base
    n_parties: int = Field(
        ge=1, le=MAX_EPISODES_EVALUATE,
        description=f"Nombre de parties à jouer (au maximum {MAX_EPISODES_EVALUATE})",
        examples=[100],
    )
    seed: int | None = Field(
        default=None, ge=0, lt=2**31,
        description="Graine de la première partie ; les suivantes prennent seed + 1, seed + 2... Vide : tirée au hasard",
        examples=[5000],
    )


class EvaluationSortie(BaseModel):
    lot: str = Field(description="Identifiant de cette évaluation : GET /episodes?lot=... et GET /stats?lot=... la retrouvent")
    seed: int = Field(description="Graine de la première partie : la même graine rejoue la même série")
    statistiques: Statistiques
