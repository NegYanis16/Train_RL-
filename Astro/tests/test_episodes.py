"""POST /episodes, GET /episodes, GET /episodes/{id}, GET /episodes/{id}/video."""

import pytest


@pytest.fixture
def partie(client):
    """Une partie jouée avec vidéo, graine 5000 (posée, 261,6 points, 215 pas)."""
    reponse = client.post("/episodes", json={"seed": 5000})
    assert reponse.status_code == 201
    return reponse.json()


def test_jouer_une_partie(partie, dossier_videos):
    assert partie["seed"] == 5000
    assert partie["issue"] == "posé"
    assert partie["recompense"] == pytest.approx(261.587, abs=1e-3)
    assert partie["duree"] == 215
    assert partie["video_url"] == f"/episodes/{partie['id']}/video"
    assert "video" not in partie  # le nom du fichier sur le disque reste interne
    assert len(list(dossier_videos.glob("*.mp4"))) == 1


def test_jouer_sans_graine(client):
    reponse = client.post("/episodes")
    assert reponse.status_code == 201
    assert reponse.json()["seed"] >= 0  # tirée au hasard et renvoyée


def test_jouer_refuse_une_graine_negative(client):
    assert client.post("/episodes", json={"seed": -1}).status_code == 422


def test_lister(client, partie):
    client.post("/evaluate", json={"n_parties": 2, "seed": 1})
    reponse = client.get("/episodes")
    assert reponse.status_code == 200
    parties = reponse.json()
    assert [p["id"] for p in parties] == [3, 2, 1]  # les plus récentes d'abord
    assert client.get("/episodes", params={"limite": 1, "decalage": 2}).json()[0]["id"] == partie["id"]


def test_detail(client, partie):
    reponse = client.get(f"/episodes/{partie['id']}")
    assert reponse.status_code == 200
    detail = reponse.json()
    assert len(detail["pas"]) == detail["duree"] == 215
    assert [p["numero"] for p in detail["pas"]] == list(range(215))
    premier = detail["pas"][0]
    assert len(premier["etat"]) == 8
    assert premier["situation"] == "haute altitude"
    # L'état d'un pas, renvoyé à /play, redonne l'action que l'agent avait choisie
    assert client.post("/play", json={"etat": premier["etat"]}).json()["action"] == premier["action"]


def test_detail_partie_inexistante(client):
    assert client.get("/episodes/999").status_code == 404


def test_video(client, partie):
    reponse = client.get(partie["video_url"])
    assert reponse.status_code == 200
    assert reponse.headers["content-type"] == "video/mp4"
    assert reponse.content[4:8] == b"ftyp"  # signature d'un fichier MP4


def test_video_par_morceaux(client, partie):
    # Le navigateur demande la vidéo par morceaux (Range) pour pouvoir avancer dedans
    reponse = client.get(partie["video_url"], headers={"Range": "bytes=0-99"})
    assert reponse.status_code == 206
    assert len(reponse.content) == 100


def test_video_introuvable(client):
    assert client.get("/episodes/999/video").status_code == 404
    sans_video = client.post("/evaluate", json={"n_parties": 1}).json()["lot"]
    partie_id = client.get("/episodes", params={"lot": sans_video}).json()[0]["id"]
    assert client.get(f"/episodes/{partie_id}/video").status_code == 404
