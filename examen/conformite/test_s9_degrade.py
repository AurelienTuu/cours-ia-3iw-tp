"""Seance 9 : le comportement quand le modele ne repond pas.

Ce test ne peut pas eteindre le modele a votre place. Lancez votre serveur en
le pointant vers un port ou rien n'ecoute, puis relancez la suite ainsi :

    OLLAMA_BASE_URL=http://localhost:1 <lancement de votre serveur>
    MODELE_INJOIGNABLE=1 pytest examen/conformite -k degrade
"""
import os

import pytest
from conftest import appeler, exiger_route

pytestmark = pytest.mark.s9


@pytest.fixture(autouse=True)
def _route_presente():
    exiger_route("/api/resumer", {"texte": "Mon colis n'est jamais arrive."})

TEXTE = "Un texte quelconque, suffisamment long pour etre valide."


@pytest.mark.skipif(
    os.environ.get("MODELE_INJOIGNABLE") != "1",
    reason="lancez le serveur sans modele joignable, puis MODELE_INJOIGNABLE=1")
def test_modele_injoignable_donne_503():
    r = appeler("/api/resumer", {"texte": TEXTE})
    assert r.status_code == 503, (
        f"modele injoignable : attendu 503, recu {r.status_code}")
    assert "erreur" in r.json()


@pytest.mark.skipif(
    os.environ.get("MODELE_INJOIGNABLE") != "1",
    reason="lancez le serveur sans modele joignable, puis MODELE_INJOIGNABLE=1")
def test_le_serveur_n_attend_pas_indefiniment():
    """Un timeout explicite est exige : la reponse doit arriver, meme en echec."""
    import time
    t0 = time.perf_counter()
    appeler("/api/resumer", {"texte": TEXTE})
    assert time.perf_counter() - t0 < 45, (
        "le serveur doit abandonner et repondre, pas attendre indefiniment")
