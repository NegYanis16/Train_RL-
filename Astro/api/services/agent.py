"""Le pilote Eagle-1 : charge le modèle entraîné une seule fois et choisit les actions.

Le reste de l'API ne touche jamais à Stable-Baselines3 directement : il passe par get_agent().
"""

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch

from config import MODEL_PATH, MODEL_VERSION, logger
from entrainement import ALGOS

NOMS_ACTIONS = ["rien", "moteur gauche", "moteur principal", "moteur droit"]


class Agent:
    """Un modèle entraîné et sa fiche (algorithme, scores de test)."""

    def __init__(self, chemin_modele: Path = MODEL_PATH):
        # La fiche .json, à côté du .zip, dit si c'est un PPO ou un DQN : il faut le savoir pour recharger le modèle
        self.fiche = json.loads(chemin_modele.with_suffix(".json").read_text(encoding="utf-8"))
        self.algo = self.fiche["algo"]
        self.version = MODEL_VERSION
        self.fichier = chemin_modele.name
        # Un petit réseau MLP va aussi vite sur le CPU, et on évite d'en dépendre d'une carte graphique
        self.model = ALGOS[self.algo].load(chemin_modele, device="cpu")
        logger.info(f"Modèle chargé : {chemin_modele.name} ({self.algo}, version {self.version})")

    def choisir_action(self, etat) -> tuple[int, list[float] | None]:
        """Renvoie l'action choisie pour un état (8 valeurs) et, pour PPO, la probabilité de chaque action.

        L'agent n'explore pas : il joue toujours l'action qu'il juge la meilleure (comme deterministic=True).
        """
        obs = np.asarray(etat, dtype=np.float32)

        if self.algo == "PPO":
            # PPO apprend une politique : pour un état, une probabilité par action.
            # L'action la plus probable est exactement celle que predict(deterministic=True) renverrait,
            # on la prend donc directement, sans repasser une deuxième fois dans le réseau.
            obs_tensor, _ = self.model.policy.obs_to_tensor(obs)
            with torch.no_grad():  # pas d'apprentissage ici : inutile de garder de quoi calculer des gradients
                probas = self.model.policy.get_distribution(obs_tensor).distribution.probs[0].numpy()
            return int(probas.argmax()), probas.tolist()

        # DQN apprend une valeur par action, pas une probabilité : on ne renvoie que l'action
        action, _ = self.model.predict(obs, deterministic=True)
        return int(action), None


@lru_cache(maxsize=1)
def get_agent() -> Agent:
    """Charge le modèle au premier appel, puis renvoie toujours le même agent."""
    return Agent()
