"""POST /evaluate."""

from config import MAX_EPISODES_EVALUATE


def test_evaluer(client, dossier_videos):
    reponse = client.post("/evaluate", json={"n_parties": 5, "seed": 5000})
    assert reponse.status_code == 200
    evaluation = reponse.json()
    assert evaluation["seed"] == 5000
    stats = evaluation["statistiques"]
    assert stats["nombre"] == 5
    assert sum(stats["issues"].values()) == 5
    assert stats["moyenne"] >= 200

    parties = client.get("/episodes", params={"lot": evaluation["lot"]}).json()
    assert sorted(p["seed"] for p in parties) == [5000, 5001, 5002, 5003, 5004]
    assert all(p["video_url"] is None for p in parties)
    assert not dossier_videos.exists() or not any(dossier_videos.iterdir())  # aucune vidéo écrite


def test_evaluer_est_reproductible(client):
    premiere = client.post("/evaluate", json={"n_parties": 3, "seed": 42}).json()["statistiques"]
    seconde = client.post("/evaluate", json={"n_parties": 3, "seed": 42}).json()["statistiques"]
    assert premiere == seconde


def test_evaluer_refuse_un_nombre_invalide(client):
    assert client.post("/evaluate", json={"n_parties": 0}).status_code == 422
    assert client.post("/evaluate", json={"n_parties": MAX_EPISODES_EVALUATE + 1}).status_code == 422
    assert client.post("/evaluate", json={}).status_code == 422
