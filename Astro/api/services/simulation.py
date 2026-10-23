"""La boucle de jeu : fait jouer l'agent dans LunarLander et garde le détail de chaque pas."""

import random
from contextlib import nullcontext
from pathlib import Path

import gymnasium as gym

from api.services import regles
from api.services.agent import Agent
from api.services.video import ecrire_video
from config import ENV_ID, logger


def _graine_au_hasard() -> int:
    return random.randrange(2**31)


def jouer_partie(agent: Agent, seed: int | None = None, chemin_video: Path | None = None) -> dict:
    """Joue une partie complète et renvoie son résumé et la liste de ses pas.

    seed         : situation de départ. Sans graine, on en tire une et on la renvoie, pour pouvoir rejouer la partie.
    chemin_video : fichier MP4 à écrire. Sans chemin, aucune image n'est calculée (bien plus rapide).
    """
    if seed is None:
        seed = _graine_au_hasard()

    env = gym.make(ENV_ID, render_mode="rgb_array" if chemin_video else None)
    # Sans vidéo, nullcontext() remplace ecrire_video() : le bloc with est le même, ajouter_image vaut None
    video = ecrire_video(chemin_video) if chemin_video else nullcontext()

    try:
        with video as ajouter_image:
            etat, _ = env.reset(seed=seed)
            if ajouter_image:
                ajouter_image(env.render())

            pas, recompense_totale, carburant = [], 0.0, 0.0
            terminated = truncated = False

            # La boucle RL : l'agent observe l'état, choisit une action, l'environnement renvoie
            # le nouvel état et la récompense, jusqu'à la fin de la partie
            while not (terminated or truncated):
                etat_decision = etat  # l'état vu au moment de la décision : c'est lui qui explique l'action
                action, _ = agent.choisir_action(etat_decision)
                etat, recompense, terminated, truncated, _ = env.step(action)

                recompense_totale += float(recompense)
                carburant += regles.carburant(action)
                pas.append({
                    "numero": len(pas),
                    "etat": [float(v) for v in etat_decision],
                    "action": action,
                    "recompense": float(recompense),
                    "carburant": round(carburant, 2),  # cumulé ; arrondi car 0,1 + 0,1 + ... n'est pas exact en float
                    "situation": regles.situation(etat_decision),
                })
                if ajouter_image:
                    ajouter_image(env.render())

            issue = regles.issue(env, terminated)  # avant env.close(), tant que le module existe encore
    finally:
        env.close()

    logger.debug(f"Partie jouée (graine {seed}) : {issue}, {recompense_totale:.1f} points, {len(pas)} pas")
    return {
        "seed": seed,
        "recompense": recompense_totale,
        "duree": len(pas),
        "carburant": round(carburant, 2),
        "issue": issue,
        "reussite": regles.est_reussie(recompense_totale),
        "pas": pas,
    }


def jouer_parties(agent: Agent, n_parties: int, seed: int | None = None) -> list[dict]:
    """Joue n_parties sans vidéo, avec les graines seed, seed + 1, seed + 2...

    Des graines qui se suivent : la même graine de départ rejoue exactement la même série de parties.
    """
    if seed is None:
        seed = _graine_au_hasard()
    parties = [jouer_partie(agent, seed=seed + i) for i in range(n_parties)]
    logger.info(f"{n_parties} parties jouées (graines {seed} à {seed + n_parties - 1})")
    return parties
