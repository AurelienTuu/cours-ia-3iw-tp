"""Seance 10 : la route POST /api/assistant, avec appel d'outil.

Ces tests se passent d'eux-memes tant que la route n'existe pas.
"""
import pytest
from conftest import appeler, appeler_sse, exiger_route

pytestmark = pytest.mark.s10

CHEMIN = "/api/assistant"


@pytest.fixture(autouse=True)
def _route_presente():
    exiger_route(CHEMIN, {"question": "Ou en est la commande CMD-2024-118 ?"})


def test_la_route_repond_en_sse():
    f = appeler_sse(CHEMIN, {"question": "Ou en est la commande CMD-2024-118 ?"})
    assert f.code == 200
    assert "text/event-stream" in f.type_contenu


def test_l_outil_est_reellement_appele():
    """La reponse doit contenir une information qui ne peut venir que du fichier."""
    f = appeler_sse(CHEMIN, {"question": "Ou en est la commande CMD-2024-118 ?"})
    reponse = f.texte.lower()
    assert reponse.strip(), "aucun texte produit"
    assert any(mot in reponse for mot in ("expedi", "livr", "prepar", "annul")), (
        "la reponse ne reprend aucun statut du fichier de commandes : "
        "l'outil n'a probablement pas ete appele")


def test_une_commande_inconnue_ne_fait_pas_planter():
    f = appeler_sse(CHEMIN, {"question": "Ou en est la commande CMD-0000-000 ?"})
    assert f.code == 200, "une commande introuvable est un cas normal, pas une erreur"
    assert f.final is not None, "le flux doit se terminer proprement"


def test_l_evenement_final_porte_l_usage():
    f = appeler_sse(CHEMIN, {"question": "Ou en est la commande CMD-2024-118 ?"})
    assert f.final is not None
    assert isinstance(f.final.get("usage"), dict)


@pytest.mark.parametrize("charge", [{}, {"question": ""}, {"question": "   "}])
def test_les_entrees_invalides_donnent_400(charge):
    assert appeler(CHEMIN, charge).status_code == 400
