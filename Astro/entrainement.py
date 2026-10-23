"""Outils d'entraînement et d'évaluation des agents Eagle-1 sur LunarLander-v3.

Chaque expérience entraîne un agent, garde le meilleur modèle vu pendant l'entraînement,
l'évalue sur 100 épisodes et enregistre le résultat dans resultats/<nom>.json.
Si l'expérience a déjà été faite, le résultat est relu au lieu de réentraîner.
"""

import json
import time
from pathlib import Path

import gymnasium as gym
import numpy as np
from stable_baselines3 import DQN, PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.monitor import Monitor

ENV_ID = "LunarLander-v3"
ALGOS = {"DQN": DQN, "PPO": PPO}

# Trois jeux de graines séparés, pour ne jamais évaluer l'agent sur des situations déjà vues :
SEED_VALIDATION_CALLBACK = 500  # choix du meilleur modèle pendant l'entraînement
SEED_VALIDATION = 1000          # comparaison des expériences entre elles
SEED_TEST = 5000                # évaluation finale du modèle retenu, utilisée une seule fois

DOSSIER = Path(__file__).parent
DOSSIER_MODELES = DOSSIER / "models"
DOSSIER_LOGS = DOSSIER / "logs"
DOSSIER_RESULTATS = DOSSIER / "resultats"


def evaluer(model, n_episodes=100, seed=SEED_VALIDATION):
    """Évalue un modèle sans exploration et renvoie les récompenses et durées de chaque épisode."""
    env = Monitor(gym.make(ENV_ID))
    env.reset(seed=seed)  # fixe la suite des situations de départ : même graine = mêmes épisodes
    recompenses, durees = evaluate_policy(
        model, env, n_eval_episodes=n_episodes, deterministic=True, return_episode_rewards=True
    )
    env.close()
    return np.array(recompenses), np.array(durees)


def resume(recompenses, durees):
    """Résume une évaluation en quelques chiffres."""
    return {
        "moyenne": float(np.mean(recompenses)),
        "ecart_type": float(np.std(recompenses)),
        "minimum": float(np.min(recompenses)),
        "taux_reussite": float(np.mean(recompenses >= 200)),
        "duree_moyenne": float(np.mean(durees)),
    }


def charger_resultats():
    """Relit le résultat de toutes les expériences déjà faites : {nom: résultat}."""
    return {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(DOSSIER_RESULTATS.glob("*.json"))}


def _enregistrer_resultat(nom, resultat):
    # Un fichier par expérience : deux entraînements lancés en parallèle n'écrivent jamais le même fichier
    DOSSIER_RESULTATS.mkdir(parents=True, exist_ok=True)
    (DOSSIER_RESULTATS / f"{nom}.json").write_text(json.dumps(resultat, indent=2, ensure_ascii=False), encoding="utf-8")


def lancer_experience(nom, algo, parametres, total_timesteps, n_envs=1, seed=0):
    """Entraîne un agent, sauvegarde le meilleur modèle et l'évalue sur 100 épisodes.

    nom             : identifiant de l'expérience (dossier du modèle, courbe TensorBoard)
    algo            : "DQN" ou "PPO"
    parametres      : hyperparamètres passés à l'algorithme (dictionnaire)
    total_timesteps : budget d'entraînement, en pas
    n_envs          : nombre d'environnements joués en parallèle
    seed            : graine de l'entraînement
    """
    resultats = charger_resultats()
    if nom in resultats:
        print(f"[{nom}] déjà entraîné : résultat relu depuis resultats/{nom}.json")
        return resultats[nom]

    dossier_modele = DOSSIER_MODELES / nom
    debut = time.time()

    train_env = make_vec_env(ENV_ID, n_envs=n_envs, seed=seed)
    callback_env = make_vec_env(ENV_ID, n_envs=1, seed=SEED_VALIDATION_CALLBACK)

    # Toutes les 25 000 pas, on joue 20 épisodes sans exploration
    # et on sauvegarde le modèle s'il bat son meilleur score.
    callback = EvalCallback(
        callback_env,
        n_eval_episodes=20,
        eval_freq=max(25_000 // n_envs, 1),  # eval_freq se compte en appels à step() de chaque environnement
        best_model_save_path=str(dossier_modele),
        log_path=str(dossier_modele),
        deterministic=True,
        verbose=0,
    )

    model = ALGOS[algo]("MlpPolicy", train_env, seed=seed, verbose=0,
                        tensorboard_log=str(DOSSIER_LOGS), **parametres)
    model.learn(total_timesteps=total_timesteps, callback=callback, tb_log_name=nom)
    model.save(dossier_modele / "final_model")
    train_env.close()
    callback_env.close()

    # On évalue le meilleur modèle sauvegardé, sur des graines différentes de celles qui ont servi à le choisir
    meilleur = ALGOS[algo].load(dossier_modele / "best_model")
    recompenses, durees = evaluer(meilleur, n_episodes=100, seed=SEED_VALIDATION)

    resultat = {
        "algo": algo,
        "parametres": parametres,
        "total_timesteps": total_timesteps,
        "n_envs": n_envs,
        "seed": seed,
        "meilleur_score_callback": float(callback.best_mean_reward),
        "evaluation": resume(recompenses, durees),
        "duree_minutes": round((time.time() - debut) / 60, 1),
    }
    _enregistrer_resultat(nom, resultat)
    return resultat


def lancer_serie(algo, serie, total_timesteps, seed=0):
    """Enchaîne des expériences en ne changeant qu'un paramètre à la fois.

    serie : liste de (nom, changement). Chaque changement est appliqué à la meilleure configuration
    trouvée jusque-là. On le garde si la moyenne d'évaluation progresse, sinon on l'annule.
    La clé "n_envs" d'un changement règle le nombre d'environnements au lieu d'un hyperparamètre.

    Renvoie le journal de la série et la meilleure configuration.
    """
    meilleure_config, meilleur_score, meilleur_nom = {"n_envs": 1}, -np.inf, None
    journal = []

    for nom, changement in serie:
        config = {**meilleure_config, **changement}
        parametres = {k: v for k, v in config.items() if k != "n_envs"}
        resultat = lancer_experience(nom, algo, parametres, total_timesteps, n_envs=config["n_envs"], seed=seed)
        afficher(nom, resultat)

        score = resultat["evaluation"]["moyenne"]
        garde = score > meilleur_score
        if garde:
            meilleure_config, meilleur_score, meilleur_nom = config, score, nom

        journal.append({"nom": nom, "changement": changement, "garde": garde, **resultat["evaluation"]})

    return journal, meilleure_config, meilleur_nom


def afficher(nom, resultat):
    """Affiche le résultat d'une expérience sur une ligne."""
    e = resultat["evaluation"]
    print(f"{nom:<22} | moyenne {e['moyenne']:>7.1f} +/- {e['ecart_type']:>5.1f} | "
          f"min {e['minimum']:>7.1f} | réussite {e['taux_reussite']:>4.0%} | "
          f"durée {e['duree_moyenne']:>4.0f} pas | {resultat['duree_minutes']} min")
