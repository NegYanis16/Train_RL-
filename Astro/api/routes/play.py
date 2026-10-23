"""POST /play : un état entre, une action sort. C'est l'endpoint demandé par l'énoncé."""

from fastapi import APIRouter

from api.dependencies import AgentDep
from api.schemas.play import ActionSortie, EtatEntree

router = APIRouter(tags=["Pilotage"])


@router.post("/play", response_model=ActionSortie, summary="Choisir l'action pour un état (8 valeurs)")
def play(entree: EtatEntree, agent: AgentDep):
    action, probabilites = agent.choisir_action(entree.etat)
    return ActionSortie(action=action, probabilites=probabilites)
