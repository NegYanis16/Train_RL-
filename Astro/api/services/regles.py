"""Les règles qui interprètent une partie de LunarLander : situation, issue, carburant, réussite.

Ces règles ne jouent pas : elles disent seulement comment lire ce qui s'est passé.
"""

from typing import Literal

import gymnasium as gym

Situation = Literal["haute altitude", "approche", "près du sol", "au sol"]
Issue = Literal["posé", "crash", "sorti de l'écran", "temps écoulé"]

# Même critère que l'étape 2 (entrainement.resume) : une partie est réussie à partir de 200 points
SEUIL_REUSSITE = 200

# LunarLander n'a pas de réservoir : il retire 0,30 point par pas de moteur principal et 0,03 par pas de
# moteur latéral. On compte le carburant dans les mêmes proportions : 1 unité pour le principal, 0,1 pour un latéral.
CARBURANT_PAR_ACTION = {0: 0.0, 1: 0.1, 2: 1.0, 3: 0.1}

# Altitude y de l'état : 0 = hauteur de la zone d'atterrissage ; le module part vers y = 1,4
ALTITUDE_PRES_DU_SOL = 0.3
ALTITUDE_APPROCHE = 0.8


def situation(etat) -> Situation:
    """La phase de vol d'un état, pour savoir quelles décisions l'agent prend à chaque phase."""
    if etat[6] or etat[7]:  # un pied touche le sol
        return "au sol"
    if etat[1] < ALTITUDE_PRES_DU_SOL:
        return "près du sol"
    if etat[1] < ALTITUDE_APPROCHE:
        return "approche"
    return "haute altitude"


def issue(env: gym.Env, terminated: bool) -> Issue:
    """Pourquoi la partie s'est arrêtée, d'après les mêmes tests que LunarLander.step().

    À appeler à la fin de la partie, avant env.close(), tant que le module existe encore.
    """
    if not terminated:
        return "temps écoulé"  # tronquée par la limite de 1000 pas
    lunar_lander = env.unwrapped  # sous les wrappers ajoutés par gym.make (TimeLimit...), le vrai environnement
    if not lunar_lander.lander.awake:  # le module ne bouge plus : il est posé (+100)
        return "posé"
    if lunar_lander.game_over:  # le corps du module a touché le sol (-100)
        return "crash"
    return "sorti de l'écran"  # |x| >= 1 (-100)


def carburant(action: int) -> float:
    """Carburant consommé par une action pendant un pas."""
    return CARBURANT_PAR_ACTION[action]


def est_reussie(recompense_totale: float) -> bool:
    # bool() : si le score est un nombre numpy, la comparaison donne un np.bool_, que Pydantic et SQLAlchemy refusent
    return bool(recompense_totale >= SEUIL_REUSSITE)
