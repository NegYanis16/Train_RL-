"""GET /health et GET /model."""

import api.dependencies
import api.routes.systeme


def _modele_absent():
    raise FileNotFoundError("models/eagle1_final.zip")


def test_health(client):
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok", "modele_charge": True}


def test_health_sans_modele(client, monkeypatch):
    monkeypatch.setattr(api.routes.systeme, "get_agent", _modele_absent)
    reponse = client.get("/health")
    assert reponse.status_code == 200  # l'API répond quand même : c'est tout l'intérêt de /health
    assert reponse.json() == {"statut": "dégradé", "modele_charge": False}


def test_model(client):
    reponse = client.get("/model")
    assert reponse.status_code == 200
    infos = reponse.json()
    assert infos["algo"] == "PPO"
    assert infos["fichier"] == "eagle1_final.zip"
    assert infos["score_test"]["moyenne"] >= 200  # l'objectif de la mission


def test_routes_sans_modele_repondent_503(client, monkeypatch):
    monkeypatch.setattr(api.dependencies, "get_agent", _modele_absent)
    assert client.get("/model").status_code == 503
    assert client.post("/play", json={"etat": [0, 1.4, 0, -0.1, 0, 0, 0, 0]}).status_code == 503
