"""Seance 13 : la route POST /api/documents, RAG avec citation des sources."""
import pytest
from conftest import appeler, appeler_sse, exiger_route

pytestmark = pytest.mark.s13

CHEMIN = "/api/documents"


@pytest.fixture(autouse=True)
def _route_presente():
    exiger_route(CHEMIN, {"question": "Comment demander un remboursement ?"})


def test_la_route_repond_en_sse():
    f = appeler_sse(CHEMIN, {"question": "Comment demander un remboursement ?"})
    assert f.code == 200
    assert "text/event-stream" in f.type_contenu


def test_les_sources_arrivent_avant_les_fragments():
    f = appeler_sse(CHEMIN, {"question": "Comment demander un remboursement ?"})
    positions = [i for i, e in enumerate(f.evenements) if "sources" in e]
    assert positions, "aucun evenement 'sources' : les extraits doivent etre cites"
    premier_fragment = next(
        (i for i, e in enumerate(f.evenements) if "delta" in e), None)
    if premier_fragment is not None:
        assert positions[0] < premier_fragment, (
            "l'evenement 'sources' doit preceder les fragments de reponse")


def test_les_sources_sont_bien_formees():
    f = appeler_sse(CHEMIN, {"question": "Comment demander un remboursement ?"})
    sources = next(e["sources"] for e in f.evenements if "sources" in e)
    assert isinstance(sources, list) and sources, "la liste de sources est vide"
    for source in sources:
        assert "titre" in source, "chaque source doit porter un titre"
        assert "score" in source, "chaque source doit porter un score de similarite"
        assert -1.0 <= float(source["score"]) <= 1.0, "un cosinus vit entre -1 et 1"


def test_une_question_hors_corpus_est_refusee():
    """Le modele doit dire qu'il ne sait pas, pas inventer."""
    f = appeler_sse(CHEMIN, {"question": "Quelle est la capitale du Perou ?"})
    reponse = f.texte.lower()
    assert reponse.strip(), "aucun texte produit"
    assert "lima" not in reponse, (
        "le modele a repondu hors corpus : la consigne doit le lui interdire")


@pytest.mark.parametrize("charge", [{}, {"question": ""}, {"question": "   "}])
def test_les_entrees_invalides_donnent_400(charge):
    assert appeler(CHEMIN, charge).status_code == 400
