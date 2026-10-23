"""Page « Tableau de bord » : les performances de l'agent sur toutes les parties enregistrées, ou sur une évaluation.

Les statistiques (moyenne, écart-type, décisions par phase...) sont calculées par l'API (GET /stats) ;
la page ne calcule que la moyenne glissante de la courbe, qui est de l'affichage.
"""

import streamlit as st

from config import MAX_EPISODES_EVALUATE
from gui import client, graphiques

TOUTES = "Toutes les parties"


# Les données changent quand une partie est jouée : cache court, vidé après chaque évaluation lancée d'ici
@st.cache_data(ttl=30, show_spinner=False)
def charger(lot: str | None) -> tuple[list[dict], dict]:
    # Le générateur lit la base page par page ; list() rassemble les résumés (quelques champs par partie)
    return list(client.toutes_les_parties(lot=lot)), client.statistiques(lot)


@st.cache_data(ttl=300, show_spinner=False)
def fiche_modele() -> dict:
    return client.modele()


st.title("Tableau de bord")

# ── Remplir la base : faire jouer N parties à l'API ───────────────────────
with st.expander("Lancer une évaluation", icon=":material/play_circle:"):
    with st.form("evaluation"):
        gauche, droite = st.columns(2)
        n_parties = gauche.slider("Nombre de parties", 1, MAX_EPISODES_EVALUATE, 50)
        seed = droite.number_input("Graine de départ (facultative)", min_value=0, max_value=2**31 - 1,
                                   value=None, step=1, placeholder="au hasard")
        lancer = st.form_submit_button("Évaluer l'agent", type="primary")
    if lancer:
        try:
            with st.spinner(f"L'API joue {n_parties} parties…"):
                resultat = client.evaluer(n_parties, None if seed is None else int(seed))
            charger.clear()
            st.session_state["lot"] = resultat["lot"]  # afficher directement cette évaluation
            stats = resultat["statistiques"]
            st.success(f"{stats['nombre']} parties jouées : moyenne {stats['moyenne']:.1f} "
                       f"± {stats['ecart_type']:.1f}, réussite {stats['taux_reussite']:.0%}.")
        except client.ErreurAPI as erreur:
            st.error(str(erreur))

# ── Filtre : toutes les parties ou une seule évaluation ───────────────────
try:
    tout, _ = charger(None)
except client.ErreurAPI as erreur:
    st.error(str(erreur))
    st.stop()

if not tout:
    st.info("Aucune partie enregistrée. Lancez une évaluation ci-dessus ou jouez une partie.")
    st.stop()

# Les lots, du plus récent au plus ancien (tout est trié du plus récent au plus ancien par l'API)
lots = list(dict.fromkeys(p["lot"] for p in tout if p["lot"]))
choix = [TOUTES, *lots]
selection = st.session_state.get("lot")
lot_affiche = st.selectbox(
    "Parties analysées", choix, index=choix.index(selection) if selection in choix else 0,
    format_func=lambda l: l if l == TOUTES else f"Évaluation {l[:8]}",
)
st.session_state["lot"] = lot_affiche
lot = None if lot_affiche == TOUTES else lot_affiche

parties, stats = charger(lot)  # lot None : déjà en cache depuis l'appel au-dessus

# ── Indicateurs ───────────────────────────────────────────────────────────
try:
    reference = fiche_modele()["score_test"]
except client.ErreurAPI:
    reference = None

colonnes = st.columns(6)
colonnes[0].metric("Parties", stats["nombre"])
colonnes[1].metric(
    "Moyenne", f"{stats['moyenne']:.1f}",
    # Écart avec le score de test de l'étape 2 : l'agent tient-il ses performances ?
    f"{stats['moyenne'] - reference['moyenne']:+.1f} vs test" if reference else None,
    help="Récompense moyenne par partie. Objectif du projet : plus de 200.",
)
colonnes[2].metric("Écart-type", f"{stats['ecart_type']:.1f}", help="Plus il est petit, plus l'agent est régulier.")
colonnes[3].metric("Réussite", f"{stats['taux_reussite']:.0%}", help="Parties à 200 points ou plus.")
colonnes[4].metric("Carburant moyen", f"{stats['carburant_moyen']:.1f}")
colonnes[5].metric("Durée moyenne", f"{stats['duree_moyenne']:.0f} pas")

# ── Graphiques ────────────────────────────────────────────────────────────
fenetre = st.slider("Fenêtre de la moyenne glissante", 2, 50, 10, help="Nombre de parties moyennées.")
tableau = graphiques.tableau_parties(parties, fenetre)
st.altair_chart(graphiques.courbe_recompenses(tableau, fenetre), width="stretch")

gauche, droite = st.columns(2, gap="large")
gauche.altair_chart(graphiques.histogramme_recompenses(tableau), width="stretch")
droite.altair_chart(graphiques.barres_issues(stats["issues"]), width="stretch")

st.altair_chart(graphiques.heatmap_decisions(stats["decisions"]), width="stretch")
st.caption("Chaque ligne fait 100 % : la part de chaque action dans les pas passés dans cette phase de vol. "
           "Survolez une case pour voir le nombre de pas.")

with st.expander("Tableau des parties"):
    colonnes_tableau = ["id", "date", "seed", "recompense", "duree", "carburant", "issue", "reussite", "lot"]
    st.dataframe(tableau[colonnes_tableau].sort_values("id", ascending=False), hide_index=True, width="stretch")
