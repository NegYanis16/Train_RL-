"""Format de GET /health et GET /model : l'état de l'API et la fiche du modèle chargé."""

from typing import Literal

from pydantic import BaseModel, Field


class Sante(BaseModel):
    statut: Literal["ok", "dégradé"] = Field(description="dégradé : l'API répond, mais sans modèle elle ne peut pas jouer")
    modele_charge: bool


class ScoreTest(BaseModel):
    """Le score obtenu par le modèle sur les épisodes de test de l'étape 2 (models/eagle1_final.json)."""

    moyenne: float
    ecart_type: float
    minimum: float
    taux_reussite: float
    duree_moyenne: float


class InfosModele(BaseModel):
    algo: str = Field(description="PPO ou DQN")
    version: str
    fichier: str
    experience: str = Field(description="Nom de l'expérience de l'étape 2 dont vient ce modèle")
    score_test: ScoreTest
