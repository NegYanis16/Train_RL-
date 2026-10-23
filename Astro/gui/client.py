"""Le client de l'API Eagle-1 : le seul fichier du GUI qui fait des appels HTTP.

Les pages ne connaissent ni les URL ni httpx : elles appellent ces fonctions et reçoivent le JSON de l'API
(des dict et des list). Aucune logique RL ici : l'API joue, enregistre et calcule ; le GUI affiche.
"""

import httpx

from config import API_URL, logger

# Jouer une partie avec vidéo ou évaluer 200 parties prend plusieurs secondes : le délai par défaut de httpx (5 s)
# couperait ces appels. 10 s suffisent pour se connecter ; on attend la réponse jusqu'à 5 minutes.
DELAI = httpx.Timeout(300.0, connect=10.0)

# Un seul client pour toute la session : il garde la connexion ouverte entre deux appels.
# Streamlit relance le script des pages à chaque clic, mais un module importé n'est chargé qu'une fois.
_client = httpx.Client(base_url=API_URL, timeout=DELAI)


class ErreurAPI(Exception):
    """L'API est injoignable ou a refusé la demande ; le message est prêt à être affiché dans la page."""


def _appeler(methode: str, chemin: str, **options) -> httpx.Response:
    """Envoie la requête et transforme toute erreur réseau ou HTTP en ErreurAPI lisible."""
    try:
        reponse = _client.request(methode, chemin, **options)
    except httpx.HTTPError as erreur:
        logger.warning(f"GUI : API injoignable sur {API_URL} ({erreur})")
        raise ErreurAPI(f"L'API ne répond pas sur {API_URL}. Est-elle lancée (uvicorn api.main:app) ?") from erreur
    if reponse.is_error:
        # FastAPI met la raison du refus dans "detail" (texte pour un 404 ou un 503, liste pour un 422)
        try:
            detail = reponse.json().get("detail", reponse.text)
        except ValueError:
            detail = reponse.text
        logger.warning(f"GUI : {methode} {chemin} -> {reponse.status_code} {detail}")
        raise ErreurAPI(f"L'API a répondu {reponse.status_code} : {detail}")
    return reponse


# ── Système ───────────────────────────────────────────────────────────────

def sante() -> dict:
    """GET /health : {"statut": "ok" | "dégradé", "modele_charge": bool}."""
    return _appeler("GET", "/health").json()


def modele() -> dict:
    """GET /model : algorithme, version et score de test du modèle chargé."""
    return _appeler("GET", "/model").json()


# ── Parties ───────────────────────────────────────────────────────────────

def jouer_partie(seed: int | None = None) -> dict:
    """POST /episodes : l'API joue une partie avec vidéo, l'enregistre et renvoie son résumé."""
    return _appeler("POST", "/episodes", json={"seed": seed}).json()


def lister_parties(limite: int = 100, decalage: int = 0, lot: str | None = None) -> list[dict]:
    """GET /episodes : les résumés des parties, les plus récentes d'abord."""
    params = {"limite": limite, "decalage": decalage}
    if lot is not None:  # httpx enverrait sinon "lot=" et l'API filtrerait sur un lot vide
        params["lot"] = lot
    return _appeler("GET", "/episodes", params=params).json()


def toutes_les_parties(lot: str | None = None, taille_page: int = 500):
    """Toutes les parties enregistrées, page par page.

    Un générateur : il demande une page de 500 résumés à la fois au lieu de tout charger d'un coup,
    ce qui protège la RAM de l'API et du GUI quand la base grossit.
    """
    decalage = 0
    while True:
        page = lister_parties(limite=taille_page, decalage=decalage, lot=lot)
        yield from page
        if len(page) < taille_page:  # page incomplète : c'était la dernière
            return
        decalage += taille_page


def detail_partie(partie_id: int) -> dict:
    """GET /episodes/{id} : le résumé plus la liste "pas" (état, action, récompense, carburant, situation)."""
    return _appeler("GET", f"/episodes/{partie_id}").json()


def video_partie(partie_id: int) -> bytes:
    """GET /episodes/{id}/video : le fichier MP4, que st.video affiche directement."""
    return _appeler("GET", f"/episodes/{partie_id}/video").content


# ── Évaluation et statistiques ────────────────────────────────────────────

def evaluer(n_parties: int, seed: int | None = None) -> dict:
    """POST /evaluate : l'API joue n parties sans vidéo ; renvoie le lot, la graine et leurs statistiques."""
    return _appeler("POST", "/evaluate", json={"n_parties": n_parties, "seed": seed}).json()


def statistiques(lot: str | None = None) -> dict:
    """GET /stats : moyenne, écart-type, réussite, carburant, issues et décisions par situation."""
    params = {"lot": lot} if lot is not None else None
    return _appeler("GET", "/stats", params=params).json()
