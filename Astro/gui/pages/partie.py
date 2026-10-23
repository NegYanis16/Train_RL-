"""Page « Partie jouée » : faire jouer une partie à l'agent et la regarder, vidéo et courbes pas à pas.

La page ne joue rien elle-même : elle demande la partie à l'API (POST /episodes) puis affiche ce qu'elle renvoie.
"""

import streamlit as st

from gui import client, graphiques


# Une partie enregistrée ne change plus : son détail et sa vidéo peuvent être gardés en cache par id.
# max_entries limite la RAM : seules les 20 dernières parties regardées restent en mémoire.
@st.cache_data(max_entries=20, show_spinner=False)
def detail(partie_id: int) -> dict:
    return client.detail_partie(partie_id)


@st.cache_data(max_entries=20, show_spinner=False)
def video(partie_id: int) -> bytes:
    return client.video_partie(partie_id)


def libelle(partie: dict) -> str:
    """Texte d'une partie dans la liste déroulante."""
    date = partie["date"][:16].replace("T", " ")
    return f"#{partie['id']} — {partie['recompense']:.0f} pts, {partie['issue']} ({date})"


st.title("Partie jouée")
st.caption("L'agent PPO pilote le module Eagle-1 dans LunarLander-v3. Toute la décision est prise par l'API.")

# ── Choisir la partie : en jouer une nouvelle ou en revoir une ────────────
nouvelle, ancienne = st.columns(2, gap="large")

with nouvelle:
    st.subheader("Nouvelle partie")
    seed = st.number_input(
        "Graine (facultative)", min_value=0, max_value=2**31 - 1, value=None, step=1,
        placeholder="au hasard",
        help="La même graine rejoue exactement la même situation de départ.",
    )
    if st.button("Lancer l'atterrissage", type="primary", icon=":material/rocket_launch:"):
        try:
            with st.spinner("L'agent pilote le module…"):
                partie = client.jouer_partie(None if seed is None else int(seed))
            st.session_state["partie_id"] = partie["id"]
        except client.ErreurAPI as erreur:
            st.error(str(erreur))

with ancienne:
    st.subheader("Revoir une partie")
    try:
        # Seules les parties jouées par POST /episodes ont une vidéo ; celles de /evaluate n'en ont pas
        avec_video = [p for p in client.lister_parties(limite=200) if p["video_url"]]
    except client.ErreurAPI as erreur:
        st.error(str(erreur))
        st.stop()
    if avec_video:
        ids = [p["id"] for p in avec_video]
        par_id = {p["id"]: p for p in avec_video}
        courante = st.session_state.get("partie_id")
        choisie = st.selectbox(
            "Parties avec vidéo, les plus récentes d'abord", ids,
            index=ids.index(courante) if courante in ids else 0,
            format_func=lambda i: libelle(par_id[i]),
        )
        st.session_state["partie_id"] = choisie
    else:
        st.info("Aucune partie avec vidéo pour l'instant : lancez-en une.")

partie_id = st.session_state.get("partie_id")
if partie_id is None:
    st.stop()

# ── Afficher la partie ────────────────────────────────────────────────────
try:
    partie = detail(partie_id)
    film = video(partie_id)
except client.ErreurAPI as erreur:
    st.error(str(erreur))
    st.stop()

st.divider()
st.subheader(f"Partie #{partie['id']} — graine {partie['seed']}")

colonnes = st.columns(4)
colonnes[0].metric("Récompense", f"{partie['recompense']:.1f}")
colonnes[1].metric("Issue", partie["issue"], "réussie" if partie["reussite"] else "ratée",
                   delta_color="normal" if partie["reussite"] else "inverse")
colonnes[2].metric("Durée", f"{partie['duree']} pas")
colonnes[3].metric("Carburant", f"{partie['carburant']:.1f}")

pas = graphiques.tableau_pas(partie)

gauche, droite = st.columns([3, 2], gap="large")
with gauche:
    st.video(film, format="video/mp4")
with droite:
    st.altair_chart(graphiques.heatmap_decisions(graphiques.decisions_de_la_partie(pas)), width="stretch")

haut_gauche, haut_droite = st.columns(2, gap="large")
haut_gauche.altair_chart(graphiques.courbe_altitude(pas), width="stretch")
haut_droite.altair_chart(graphiques.courbe_score(pas), width="stretch")
st.altair_chart(graphiques.chronologie_actions(pas), width="stretch")

with st.expander("Tableau pas à pas"):
    st.dataframe(pas, hide_index=True, width="stretch")
