"""POST /evaluate : jouer N parties sans vidéo, les enregistrer et renvoyer leurs statistiques (pour le tableau de bord)."""

import uuid

from fastapi import APIRouter

from api.dependencies import AgentDep, SessionDep
from api.repositories.parties import enregistrer_parties
from api.repositories.statistiques import statistiques
from api.schemas.evaluation import EvaluationDemande, EvaluationSortie
from api.services.simulation import jouer_parties

router = APIRouter(tags=["Évaluation"])


@router.post("/evaluate", response_model=EvaluationSortie, summary="Jouer N parties sans vidéo et les résumer")
def evaluate(demande: EvaluationDemande, agent: AgentDep, session: SessionDep):
    parties = jouer_parties(agent, demande.n_parties, seed=demande.seed)
    lot = uuid.uuid4().hex  # regroupe les parties de cette évaluation dans la base
    enregistrer_parties(session, parties, lot=lot)
    return EvaluationSortie(lot=lot, seed=parties[0]["seed"], statistiques=statistiques(session, lot))
