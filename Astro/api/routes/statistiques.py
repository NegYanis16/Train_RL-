"""GET /stats : les statistiques de toutes les parties enregistrées, ou d'une seule évaluation."""

from typing import Annotated

from fastapi import APIRouter, Query

from api.dependencies import SessionDep
from api.repositories.statistiques import statistiques
from api.schemas.statistiques import Statistiques

router = APIRouter(tags=["Statistiques"])


@router.get("/stats", response_model=Statistiques,
            summary="Moyenne, écart-type, réussite, carburant, issues et décisions par situation")
def stats(session: SessionDep, lot: Annotated[str | None, Query(description="Seulement ce /evaluate")] = None):
    return statistiques(session, lot)
