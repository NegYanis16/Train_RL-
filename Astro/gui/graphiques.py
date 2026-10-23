"""Les graphiques du GUI : transforment le JSON reçu de l'API en tableaux pandas et en graphiques Altair.

Ce fichier ne fait ni appel à l'API ni appel à Streamlit : il reçoit des données et renvoie des figures.
Les pages les affichent avec st.altair_chart. Chaque graphique a une info-bulle au survol.
"""

import altair as alt
import pandas as pd

# ── Ordres et couleurs ────────────────────────────────────────────────────
# Ordres fixes : une couleur suit toujours la même action, même si une action manque dans les données

ACTIONS = ["rien", "moteur gauche", "moteur principal", "moteur droit"]
# Les 4 premières couleurs catégorielles de la palette de référence, validées pour le daltonisme
COULEURS_ACTIONS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]

# Les phases de vol sont ordonnées (de haut en bas) : une seule teinte, du clair au foncé
SITUATIONS = ["haute altitude", "approche", "près du sol", "au sol"]
COULEURS_SITUATIONS = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

# Les issues sont des états (bon, mauvais) : couleurs de statut, toujours accompagnées du nom de l'issue
ISSUES = ["posé", "temps écoulé", "sorti de l'écran", "crash"]
COULEURS_ISSUES = ["#0ca30c", "#fab219", "#ec835a", "#d03b3b"]

BLEU = "#2a78d6"
GRIS = "#898781"

# L'objectif du projet : une récompense moyenne au-dessus de 200. Affiché comme ligne de repère.
OBJECTIF = 200


def _echelle(domaine: list[str], couleurs: list[str]) -> alt.Scale:
    return alt.Scale(domain=domaine, range=couleurs)


def _ligne_objectif() -> alt.Chart:
    """Ligne pointillée horizontale à 200 points, avec son libellé."""
    base = alt.Chart(pd.DataFrame({"y": [OBJECTIF], "texte": [f"objectif {OBJECTIF}"]}))
    ligne = base.mark_rule(color=GRIS, strokeDash=[4, 4]).encode(y="y:Q")
    texte = base.mark_text(align="left", dx=4, dy=-6, color=GRIS).encode(
        y="y:Q", x=alt.value(0), text="texte:N"
    )
    return ligne + texte


# ── Une partie, pas à pas ─────────────────────────────────────────────────

def tableau_pas(partie: dict) -> pd.DataFrame:
    """Une ligne par pas, à partir de GET /episodes/{id}.

    L'état contient 8 valeurs dans l'ordre de LunarLander : x, y, vx, vy, angle, vitesse angulaire, pied gauche, pied droit.
    """
    lignes = [
        {
            "pas": p["numero"],
            "altitude": p["etat"][1],
            "position x": p["etat"][0],
            "vitesse verticale": p["etat"][3],
            "angle": p["etat"][4],
            "action": p["nom_action"],
            "situation": p["situation"],
            "récompense": p["recompense"],
            "carburant": p["carburant"],
        }
        for p in partie["pas"]
    ]
    df = pd.DataFrame(lignes)
    df["score cumulé"] = df["récompense"].cumsum()
    return df


def courbe_altitude(pas: pd.DataFrame) -> alt.Chart:
    """L'altitude au fil des pas ; chaque point est coloré par la phase de vol que l'API a reconnue."""
    survol = alt.selection_point(on="pointerover", nearest=True, fields=["pas"], empty=False)
    base = alt.Chart(pas).encode(x=alt.X("pas:Q", title="pas"))
    ligne = base.mark_line(strokeWidth=2, color=GRIS).encode(y=alt.Y("altitude:Q", title="altitude"))
    points = base.mark_circle(size=40).encode(
        y="altitude:Q",
        color=alt.Color("situation:N", scale=_echelle(SITUATIONS, COULEURS_SITUATIONS),
                        legend=alt.Legend(title="phase de vol", orient="bottom")),
        size=alt.condition(survol, alt.value(120), alt.value(30)),
        tooltip=["pas", alt.Tooltip("altitude:Q", format=".2f"), alt.Tooltip("vitesse verticale:Q", format=".2f"),
                 "situation", "action"],
    ).add_params(survol)
    return (ligne + points).properties(title="Altitude et phase de vol", height=260)


def courbe_score(pas: pd.DataFrame) -> alt.Chart:
    """Le score cumulé : comment la récompense s'accumule jusqu'à l'atterrissage."""
    survol = alt.selection_point(on="pointerover", nearest=True, fields=["pas"], empty=False)
    base = alt.Chart(pas).encode(x=alt.X("pas:Q", title="pas"))
    ligne = base.mark_line(strokeWidth=2, color=BLEU).encode(y=alt.Y("score cumulé:Q", title="score cumulé"))
    curseur = base.mark_rule(color=GRIS).encode(
        opacity=alt.condition(survol, alt.value(1), alt.value(0)),
        tooltip=["pas", alt.Tooltip("score cumulé:Q", format=".1f"), alt.Tooltip("récompense:Q", format=".2f"),
                 "action"],
    ).add_params(survol)
    return (ligne + curseur + _ligne_objectif()).properties(title="Score cumulé", height=260)


def chronologie_actions(pas: pd.DataFrame) -> alt.Chart:
    """Une marque par pas sur la ligne de l'action choisie : la suite des décisions de l'agent."""
    return alt.Chart(pas).mark_tick(thickness=2, size=18).encode(
        x=alt.X("pas:Q", title="pas"),
        y=alt.Y("action:N", sort=ACTIONS, title=None),
        color=alt.Color("action:N", scale=_echelle(ACTIONS, COULEURS_ACTIONS), legend=None),
        tooltip=["pas", "action", "situation", alt.Tooltip("altitude:Q", format=".2f")],
    ).properties(title="Action choisie à chaque pas", height=170)


def decisions_de_la_partie(pas: pd.DataFrame) -> dict[str, dict[str, int]]:
    """Compte les actions par phase de vol, au même format que "decisions" de GET /stats."""
    comptes = pas.groupby(["situation", "action"]).size()
    decisions: dict[str, dict[str, int]] = {}
    for (situation, action), nombre in comptes.items():
        decisions.setdefault(situation, {})[action] = int(nombre)
    return decisions


# ── Toutes les parties ────────────────────────────────────────────────────

def tableau_parties(parties: list[dict], fenetre: int = 10) -> pd.DataFrame:
    """Une ligne par partie, dans l'ordre où elles ont été jouées, avec la moyenne et l'écart-type glissants."""
    df = pd.DataFrame(parties)
    if df.empty:
        return df
    df = df.sort_values("id").reset_index(drop=True)
    df["partie"] = range(1, len(df) + 1)  # numéro dans la série affichée (les id peuvent avoir des trous si on filtre)
    glissant = df["recompense"].rolling(fenetre, min_periods=1)
    df["moyenne glissante"] = glissant.mean()
    df["écart-type glissant"] = glissant.std(ddof=0).fillna(0)  # ddof=0 : même écart-type que l'API (np.std)
    df["bas"] = df["moyenne glissante"] - df["écart-type glissant"]
    df["haut"] = df["moyenne glissante"] + df["écart-type glissant"]
    return df


def courbe_recompenses(parties: pd.DataFrame, fenetre: int = 10) -> alt.Chart:
    """La récompense de chaque partie (points colorés par issue), la moyenne glissante et sa bande ± 1 écart-type."""
    survol = alt.selection_point(on="pointerover", nearest=True, fields=["partie"], empty=False)
    base = alt.Chart(parties).encode(x=alt.X("partie:Q", title="partie (ordre de jeu)"))
    bande = base.mark_area(color=BLEU, opacity=0.15).encode(y=alt.Y("bas:Q", title="récompense"), y2="haut:Q")
    moyenne = base.mark_line(color=BLEU, strokeWidth=2).encode(y="moyenne glissante:Q")
    points = base.mark_circle(size=50, opacity=0.9).encode(
        y="recompense:Q",
        color=alt.Color("issue:N", scale=_echelle(ISSUES, COULEURS_ISSUES),
                        legend=alt.Legend(title="issue", orient="bottom")),
        size=alt.condition(survol, alt.value(140), alt.value(50)),
        tooltip=[
            alt.Tooltip("partie:Q", title="partie"), alt.Tooltip("id:Q", title="id"),
            alt.Tooltip("recompense:Q", title="récompense", format=".1f"),
            alt.Tooltip("moyenne glissante:Q", title=f"moyenne sur {fenetre}", format=".1f"),
            alt.Tooltip("écart-type glissant:Q", title=f"écart-type sur {fenetre}", format=".1f"),
            "issue", "seed", "duree",
        ],
    ).add_params(survol)
    titre = f"Récompense par partie — moyenne glissante sur {fenetre} parties ± 1 écart-type"
    return (bande + moyenne + _ligne_objectif() + points).properties(title=titre, height=320)


def histogramme_recompenses(parties: pd.DataFrame) -> alt.Chart:
    """La répartition des scores : un pic serré au-dessus de 200 signifie un agent fiable."""
    barres = alt.Chart(parties).mark_bar(color=BLEU, binSpacing=2, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("recompense:Q", bin=alt.Bin(maxbins=30), title="récompense"),
        y=alt.Y("count():Q", title="parties"),
        tooltip=[alt.Tooltip("recompense:Q", bin=alt.Bin(maxbins=30), title="tranche"),
                 alt.Tooltip("count():Q", title="parties")],
    )
    objectif = alt.Chart(pd.DataFrame({"x": [OBJECTIF]})).mark_rule(color=GRIS, strokeDash=[4, 4]).encode(x="x:Q")
    return (barres + objectif).properties(title="Répartition des récompenses", height=260)


def barres_issues(issues: dict[str, int]) -> alt.Chart:
    """Combien de parties par issue (posé, crash...), avec le nombre écrit au bout de chaque barre."""
    df = pd.DataFrame({"issue": ISSUES, "parties": [issues.get(i, 0) for i in ISSUES]})
    base = alt.Chart(df).encode(
        y=alt.Y("issue:N", sort=ISSUES, title=None),
        x=alt.X("parties:Q", title="parties"),
    )
    barres = base.mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        color=alt.Color("issue:N", scale=_echelle(ISSUES, COULEURS_ISSUES), legend=None),
        tooltip=["issue", "parties"],
    )
    nombres = base.mark_text(align="left", dx=4).encode(text="parties:Q")
    return (barres + nombres).properties(title="Issue des parties", height=200)


def heatmap_decisions(decisions: dict[str, dict[str, int]]) -> alt.Chart:
    """Pour chaque phase de vol, la part de chaque action : la politique de l'agent selon la circonstance.

    Les parts sont calculées par ligne (chaque phase fait 100 %) pour comparer des phases qui n'ont pas
    le même nombre de pas. Une action jamais choisie dans une phase est absente des données : elle vaut 0.
    """
    lignes = []
    for situation in SITUATIONS:
        par_action = decisions.get(situation, {})
        total = sum(par_action.values())
        for action in ACTIONS:
            nombre = par_action.get(action, 0)
            lignes.append({"situation": situation, "action": action, "nombre": nombre,
                           "part": nombre / total if total else 0.0})
    df = pd.DataFrame(lignes)
    # L'espace entre les cases vient de l'échelle (paddingInner) et non d'un contour : un contour blanc
    # ferait une grille éblouissante en thème sombre, alors qu'un vide laisse voir le fond, quel que soit le thème
    espace = alt.Scale(paddingInner=0.04)
    base = alt.Chart(df).encode(
        x=alt.X("action:N", sort=ACTIONS, title=None, scale=espace, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("situation:N", sort=SITUATIONS, title=None, scale=espace),
    )
    cases = base.mark_rect(cornerRadius=4).encode(
        color=alt.Color("part:Q", scale=alt.Scale(domain=[0, 1], range=["#cde2fb", "#0d366b"]),
                        legend=alt.Legend(title="part des pas", format=".0%")),
        tooltip=["situation", "action", alt.Tooltip("nombre:Q", title="pas"),
                 alt.Tooltip("part:Q", title="part dans la phase", format=".0%")],
    )
    # Le texte change de couleur selon le fond pour rester lisible sur les cases claires comme foncées
    textes = base.mark_text(fontSize=13).encode(
        text=alt.Text("part:Q", format=".0%"),
        color=alt.condition(alt.datum.part > 0.5, alt.value("white"), alt.value("#0b0b0b")),
    )
    return (cases + textes).properties(title="Décisions de l'agent selon la phase de vol", height=240)
