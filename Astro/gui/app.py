"""Point d'entrée du GUI Eagle-1 : la navigation entre les pages et l'état de l'API dans la barre latérale.

Lancement, depuis le dossier Astro, venv activé, l'API étant déjà lancée (uvicorn api.main:app) :
    streamlit run gui/app.py
"""

import sys
from pathlib import Path

# streamlit run ajoute au chemin d'import le dossier du script (gui/), pas la racine du projet :
# sans cette ligne, "import config" et "from gui import ..." échoueraient.
RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

import streamlit as st  # noqa: E402

from config import API_URL  # noqa: E402
from gui import client  # noqa: E402

st.set_page_config(page_title="Eagle-1", page_icon=":material/rocket:", layout="wide")

# st.navigation remplace la détection automatique du dossier pages/ : l'ordre et les titres sont choisis ici
navigation = st.navigation([
    st.Page(RACINE / "gui" / "pages" / "partie.py", title="Partie jouée", icon=":material/movie:", default=True),
    st.Page(RACINE / "gui" / "pages" / "tableau_de_bord.py", title="Tableau de bord", icon=":material/monitoring:"),
])

with st.sidebar:
    st.header("Eagle-1")
    try:
        sante = client.sante()
        if sante["modele_charge"]:
            infos = client.modele()
            st.success(f"API connectée — {infos['algo']} v{infos['version']}", icon=":material/check_circle:")
            st.caption(f"Score de test du modèle : {infos['score_test']['moyenne']:.1f} "
                       f"± {infos['score_test']['ecart_type']:.1f}")
        else:
            st.warning("API connectée, mais sans modèle : elle ne peut pas jouer.", icon=":material/warning:")
    except client.ErreurAPI as erreur:
        st.error(str(erreur), icon=":material/error:")
    st.caption(f"API : {API_URL} — [documentation]({API_URL}/docs)")

navigation.run()
