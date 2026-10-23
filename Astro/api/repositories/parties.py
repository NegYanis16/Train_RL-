"""Enregistrer, lister et relire les parties jouées."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from api.db.models import COLONNES_ETAT, Partie, Pas
from config import logger


def _vers_modele(partie: dict, lot: str | None) -> Partie:
    """Transforme une partie renvoyée par la simulation (un dict) en objets Partie et Pas."""
    return Partie(
        lot=lot,
        seed=partie["seed"],
        recompense=partie["recompense"],
        duree=partie["duree"],
        carburant=partie["carburant"],
        issue=partie["issue"],
        reussite=partie["reussite"],
        video=partie.get("video"),
        pas=[
            Pas(
                numero=pas["numero"],
                **dict(zip(COLONNES_ETAT, pas["etat"])),  # [x, y, ...] -> x=..., y=..., ...
                action=pas["action"],
                recompense=pas["recompense"],
                carburant=pas["carburant"],
                situation=pas["situation"],
            )
            for pas in partie["pas"]
        ],
    )


def enregistrer_parties(session: Session, parties: list[dict], lot: str | None = None) -> list[Partie]:
    """Enregistre des parties et leurs pas, dans une seule transaction : toutes ou aucune.

    lot : identifiant commun aux parties d'un même /evaluate.
    """
    modeles = [_vers_modele(partie, lot) for partie in parties]
    session.add_all(modeles)  # les pas suivent leur partie grâce à la relation (cascade)
    session.commit()  # c'est ici que SQLite attribue les id
    logger.info(f"{len(modeles)} partie(s) enregistrée(s)" + (f" (lot {lot})" if lot else ""))
    return modeles


def lister_parties(session: Session, limite: int = 100, decalage: int = 0, lot: str | None = None) -> list[Partie]:
    """Les parties, les plus récentes d'abord, sans leurs pas. Avec un lot, seulement les parties de ce lot.

    limite / decalage : la pagination (les parties 0 à 99, puis 100 à 199...), pour ne pas tout renvoyer d'un coup.
    """
    requete = select(Partie).order_by(Partie.id.desc()).limit(limite).offset(decalage)
    if lot is not None:
        requete = requete.where(Partie.lot == lot)
    return list(session.scalars(requete))


def trouver_partie(session: Session, partie_id: int, avec_pas: bool = False) -> Partie | None:
    """Une partie par son id, ou None si elle n'existe pas.

    avec_pas : charge aussi tous ses pas, en une seule requête supplémentaire (selectinload).
    Sans ça, ils seraient lus plus tard, un par un ou après la fermeture de la session.
    """
    requete = select(Partie).where(Partie.id == partie_id)
    if avec_pas:
        requete = requete.options(selectinload(Partie.pas))
    return session.scalars(requete).first()
