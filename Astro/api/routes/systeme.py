"""GET /health et GET /model."""

from fastapi import APIRouter

from api.dependencies import AgentDep
from api.schemas.systeme import InfosModele, Sante
from api.services.agent import get_agent

router = APIRouter(tags=["Système"])


@router.get("/health", response_model=Sante, summary="L'API tourne-t-elle, le modèle est-il chargé ?")
def health():
    # Pas de AgentDep ici : /health doit répondre même sans modèle, c'est justement ce qu'il signale
    try:
        get_agent()
        modele_charge = True
    except Exception:
        modele_charge = False
    return Sante(statut="ok" if modele_charge else "dégradé", modele_charge=modele_charge)


@router.get("/model", response_model=InfosModele, summary="Algorithme, version et score de test du modèle")
def model(agent: AgentDep):
    return InfosModele(
        algo=agent.algo,
        version=agent.version,
        fichier=agent.fichier,
        experience=agent.fiche["experience"],
        score_test=agent.fiche["test"],
    )
