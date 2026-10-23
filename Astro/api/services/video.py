"""Écriture des vidéos MP4 des parties, image par image.

Chaque image est envoyée à ffmpeg dès qu'elle est calculée : seule l'image en cours est en mémoire,
quelle que soit la durée de la partie.
"""

import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import imageio
import numpy as np

from config import VIDEO_FPS, VIDEOS_PATH, logger


def nouveau_chemin_video(dossier: Path = VIDEOS_PATH) -> Path:
    """Un chemin de fichier unique pour la vidéo d'une partie qui va être jouée.

    Le nom est tiré au hasard (uuid) : la vidéo est écrite pendant la partie, avant que la base lui donne un id.
    """
    return Path(dossier) / f"{uuid.uuid4().hex}.mp4"


@contextmanager
def ecrire_video(chemin: Path, fps: int = VIDEO_FPS) -> Iterator[Callable[[np.ndarray], None]]:
    """Ouvre un fichier MP4 et donne une fonction pour lui ajouter une image.

        with ecrire_video(chemin) as ajouter_image:
            ajouter_image(env.render())

    À la sortie du bloc, le fichier est fermé. Si une erreur survient dans le bloc, la vidéo à moitié écrite
    est supprimée : elle serait illisible.
    """
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    # H.264 en yuv420p (le défaut d'imageio) : le format que tous les navigateurs savent lire.
    # Les images LunarLander font 600 x 400 ; 600 n'est pas un multiple de 16, le bloc par défaut, mais l'est de 8.
    writer = imageio.get_writer(chemin, fps=fps, codec="libx264", macro_block_size=8)
    try:
        yield writer.append_data
    except BaseException:
        writer.close()
        chemin.unlink(missing_ok=True)
        logger.warning(f"Vidéo interrompue, fichier supprimé : {chemin.name}")
        raise
    writer.close()
