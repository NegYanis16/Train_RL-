"""GET /stats."""

import pytest


def test_stats_base_vide(client):
    reponse = client.get("/stats")
    assert reponse.status_code == 200
    stats = reponse.json()
    assert stats["nombre"] == 0
    assert stats["moyenne"] is None and stats["ecart_type"] is None
    assert stats["issues"] == {} and stats["decisions"] == {}


def test_stats(client):
    seule = client.post("/episodes", json={"seed": 5000}).json()
    evaluation = client.post("/evaluate", json={"n_parties": 2, "seed": 5001}).json()
    recompenses = [seule["recompense"]] + [p["recompense"] for p in client.get(
        "/episodes", params={"lot": evaluation["lot"]}).json()]

    stats = client.get("/stats").json()
    assert stats["nombre"] == 3
    assert stats["moyenne"] == pytest.approx(sum(recompenses) / 3)
    moyenne = sum(recompenses) / 3
    assert stats["ecart_type"] == pytest.approx((sum((r - moyenne) ** 2 for r in recompenses) / 3) ** 0.5)
    assert stats["taux_reussite"] == pytest.approx(sum(r >= 200 for r in recompenses) / 3)

    # Une décision par pas, rangée par situation et par nom d'action
    total_pas = sum(client.get(f"/episodes/{i}").json()["duree"] for i in (1, 2, 3))
    assert sum(n for par_action in stats["decisions"].values() for n in par_action.values()) == total_pas
    assert set(stats["decisions"]) <= {"haute altitude", "approche", "près du sol", "au sol"}
    assert all(set(par_action) <= {"rien", "moteur gauche", "moteur principal", "moteur droit"}
               for par_action in stats["decisions"].values())


def test_stats_d_un_lot(client):
    client.post("/episodes", json={"seed": 5000})
    evaluation = client.post("/evaluate", json={"n_parties": 2, "seed": 5001}).json()
    stats = client.get("/stats", params={"lot": evaluation["lot"]}).json()
    assert stats == evaluation["statistiques"]  # mêmes chiffres que ceux renvoyés par /evaluate
    assert stats["nombre"] == 2
