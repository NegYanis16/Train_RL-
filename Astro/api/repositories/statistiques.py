"""Statistiques des parties enregistrées, calculées par la base en SQL.

Chaque fonction peut se limiter à un lot (les parties d'un même /evaluate) ; sans lot, elle porte sur toutes les parties.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.db.models import Partie, Pas


def _filtre_lot(lot: str | None) -> list:
    """La condition WHERE à ajouter : aucune sans lot, sinon « lot = ... »."""
    return [] if lot is None else [Partie.lot == lot]


def resume_scores(session: Session, lot: str | None = None) -> dict:
    """Nombre de parties, moyenne, écart-type, min, max, taux de réussite, carburant et durée moyens.

    Sans partie, toutes les valeurs sauf le nombre valent None.
    """
    r = Partie.recompense
    # SQLite n'a pas de fonction écart-type : on utilise sqrt(moyenne(r²) - moyenne(r)²).
    # C'est l'écart-type « de population », le même que np.std à l'étape 2.
    # max(0, ...) évite la racine d'un nombre très légèrement négatif à cause des arrondis.
    ecart_type = func.sqrt(func.max(0, func.avg(r * r) - func.avg(r) * func.avg(r)))

    requete = select(
        func.count().label("nombre"),
        func.avg(r).label("moyenne"),
        ecart_type.label("ecart_type"),
        func.min(r).label("minimum"),
        func.max(r).label("maximum"),
        func.avg(Partie.reussite).label("taux_reussite"),  # moyenne de 0 et de 1 = proportion de réussites
        func.avg(Partie.carburant).label("carburant_moyen"),
        func.avg(Partie.duree).label("duree_moyenne"),
    ).where(*_filtre_lot(lot))

    resume = dict(session.execute(requete).mappings().one())
    if resume["nombre"] == 0:
        # max(0, NULL) vaut 0 en SQLite, l'écart-type sortirait à 0 au lieu de None
        resume["ecart_type"] = None
    return resume


def repartition_issues(session: Session, lot: str | None = None) -> dict[str, int]:
    """Nombre de parties par issue, de la plus fréquente à la plus rare : {"posé": 98, "crash": 2}."""
    n = func.count().label("n")
    requete = select(Partie.issue, n).where(*_filtre_lot(lot)).group_by(Partie.issue).order_by(n.desc())
    return {issue: nombre for issue, nombre in session.execute(requete)}


def decisions_par_situation(session: Session, lot: str | None = None) -> dict[str, dict[int, int]]:
    """Combien de fois chaque action a été choisie dans chaque situation : la politique observée de l'agent.

    Renvoie {situation: {action: nombre}}, par exemple {"près du sol": {0: 120, 2: 340}}.
    """
    requete = (
        select(Pas.situation, Pas.action, func.count())
        .join(Pas.partie)  # pour pouvoir filtrer sur le lot, qui est une colonne de la partie
        .where(*_filtre_lot(lot))
        .group_by(Pas.situation, Pas.action)
        .order_by(Pas.situation, Pas.action)
    )
    decisions: dict[str, dict[int, int]] = {}
    for situation, action, nombre in session.execute(requete):
        decisions.setdefault(situation, {})[action] = nombre
    return decisions


def statistiques(session: Session, lot: str | None = None) -> dict:
    """Les trois statistiques réunies, au format du schéma Statistiques."""
    return {
        **resume_scores(session, lot),
        "issues": repartition_issues(session, lot),
        "decisions": decisions_par_situation(session, lot),
    }
