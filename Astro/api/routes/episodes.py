"""Les parties jouées : en jouer une avec vidéo, les lister, voir le détail et la vidéo d'une partie."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse

from api.dependencies import AgentDep, DossierVideosDep, SessionDep
from api.repositories.parties import enregistrer_parties, lister_parties, trouver_partie
from api.schemas.episodes import PartieDemande, PartieDetail, PartieResume
from api.services.simulation import jouer_partie
from api.services.video import nouveau_chemin_video

router = APIRouter(prefix="/episodes", tags=["Parties"])


def _partie_introuvable(partie_id: int) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"Partie {partie_id} introuvable")


@router.post("", response_model=PartieResume, status_code=status.HTTP_201_CREATED,
             summary="Jouer une partie avec vidéo et l'enregistrer (pour le GUI)")
def jouer(agent: AgentDep, session: SessionDep, dossier_videos: DossierVideosDep,
          demande: PartieDemande = PartieDemande()):  # corps facultatif : sans corps, graine au hasard
    chemin_video = nouveau_chemin_video(dossier_videos)
    partie = jouer_partie(agent, seed=demande.seed, chemin_video=chemin_video)
    partie["video"] = chemin_video.name
    [enregistree] = enregistrer_parties(session, [partie])
    return enregistree


@router.get("", response_model=list[PartieResume], summary="La liste des parties jouées, les plus récentes d'abord")
def lister(
    session: SessionDep,
    limite: Annotated[int, Query(ge=1, le=500, description="Nombre de parties par page")] = 100,
    decalage: Annotated[int, Query(ge=0, description="Nombre de parties à sauter (page suivante)")] = 0,
    lot: Annotated[str | None, Query(description="Seulement les parties de ce /evaluate")] = None,
):
    return lister_parties(session, limite=limite, decalage=decalage, lot=lot)


@router.get("/{partie_id}", response_model=PartieDetail, summary="Le détail pas à pas d'une partie")
def detail(partie_id: int, session: SessionDep):
    partie = trouver_partie(session, partie_id, avec_pas=True)
    if partie is None:
        raise _partie_introuvable(partie_id)
    return partie


@router.get("/{partie_id}/video", response_class=FileResponse, summary="La vidéo MP4 de l'atterrissage",
            responses={200: {"content": {"video/mp4": {}}}, 404: {"description": "Partie ou vidéo introuvable"}})
def video(partie_id: int, session: SessionDep, dossier_videos: DossierVideosDep):
    partie = trouver_partie(session, partie_id)
    if partie is None:
        raise _partie_introuvable(partie_id)
    chemin = dossier_videos / partie.video if partie.video else None
    if chemin is None or not chemin.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"La partie {partie_id} n'a pas de vidéo")
    # FileResponse lit le fichier par morceaux et gère les requêtes Range : le navigateur peut avancer dans la vidéo
    return FileResponse(chemin, media_type="video/mp4")
