"""Plan des expériences de l'étape 2.

Chaque ligne change UN seul paramètre par rapport à la meilleure configuration trouvée avant elle.
Usage en ligne de commande (pour lancer une série en arrière-plan) : python experiences.py DQN
"""

import sys

# --- Série DQN : on corrige un à un les réglages par défaut mis en cause à l'étape 1 ---
BUDGET_DQN = 300_000
SERIE_DQN = [
    ("D0_defaut", {}),                                              # référence au nouveau budget
    ("D1_target_update", {"target_update_interval": 250}),          # 10 000 -> 250
    ("D2_learning_rate", {"learning_rate": 6e-4}),                  # 1e-4 -> 6e-4
    ("D3_buffer_size", {"buffer_size": 50_000}),                    # 1 000 000 -> 50 000
    ("D4_batch_size", {"batch_size": 128}),                         # 32 -> 128
    ("D5_reseau", {"policy_kwargs": {"net_arch": [256, 256]}}),     # [64, 64] -> [256, 256]
    ("D6_gamma", {"gamma": 0.999}),                                 # 0.99 -> 0.999
]

# --- Série PPO : PPO a besoin de plus de pas que DQN, d'où un budget plus grand ---
BUDGET_PPO = 1_000_000
SERIE_PPO = [
    ("P0_defaut", {}),                                              # PPO par défaut, 1 environnement
    ("P1_n_steps", {"n_steps": 1024}),                              # 2048 -> 1024
    ("P2_n_envs", {"n_envs": 16}),                                  # 1 -> 16 environnements en parallèle
    ("P3_gamma", {"gamma": 0.999}),                                 # 0.99 -> 0.999
    ("P4_ent_coef", {"ent_coef": 0.01}),                            # 0 -> 0.01
]

SERIES = {"DQN": (SERIE_DQN, BUDGET_DQN), "PPO": (SERIE_PPO, BUDGET_PPO)}


if __name__ == "__main__":
    import torch

    from entrainement import lancer_serie

    torch.set_num_threads(2)  # deux séries tournent en même temps : on partage les cœurs du processeur
    algo = sys.argv[1]
    serie, budget = SERIES[algo]
    journal, config, nom = lancer_serie(algo, serie, budget)
    print("Meilleure expérience :", nom, config)
