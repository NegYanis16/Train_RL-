"""POST /play."""

import pytest

from api.services.agent import get_agent

ETAT = [0.0, 1.4, 0.0, -0.1, 0.0, 0.0, 0.0, 0.0]


def test_play(client):
    reponse = client.post("/play", json={"etat": ETAT})
    assert reponse.status_code == 200
    sortie = reponse.json()
    assert sortie["action"] in (0, 1, 2, 3)
    assert sortie["probabilites"] == pytest.approx(get_agent().choisir_action(ETAT)[1])
    assert sum(sortie["probabilites"]) == pytest.approx(1, abs=1e-5)
    # Sans exploration, l'agent joue l'action la plus probable
    assert sortie["action"] == max(range(4), key=lambda a: sortie["probabilites"][a])
    assert isinstance(sortie["nom_action"], str)


@pytest.mark.parametrize("etat", [
    ETAT[:7],                          # 7 valeurs
    ETAT + [0.0],                      # 9 valeurs
    [0, "haut", 0, -0.1, 0, 0, 0, 0],  # pas un nombre
    [0, 1.4, 0, -50, 0, 0, 0, 0],      # vy hors des bornes du jeu
])
def test_play_refuse_un_etat_invalide(client, etat):
    assert client.post("/play", json={"etat": etat}).status_code == 422
