"""Seance 9 : la route POST /api/resumer.

Chaque test correspond a une ligne de app/CONTRAT.md.
"""
import pytest
from conftest import appeler, appeler_sse, exiger_route

pytestmark = pytest.mark.s9


@pytest.fixture(autouse=True)
def _route_presente():
    exiger_route("/api/resumer", {"texte": "Mon colis n'est jamais arrive."})

TEXTE = (
    "Bonjour, j'ai commande un casque le 3 mars et je n'ai toujours rien recu. "
    "Le suivi indique une livraison le 7 mars mais rien n'est arrive. "
    "Je souhaite savoir ou en est ma commande, ou etre rembourse."
)


# --- cas nominal ---------------------------------------------------------

def test_la_route_repond_en_sse():
    f = appeler_sse("/api/resumer", {"texte": TEXTE})
    assert f.code == 200, f"attendu 200, recu {f.code}"
    assert "text/event-stream" in f.type_contenu, (
        f"attendu text/event-stream, recu {f.type_contenu!r}")


def test_le_flux_contient_des_fragments():
    f = appeler_sse("/api/resumer", {"texte": TEXTE})
    assert f.fragments, "aucun evenement portant une cle 'delta'"
    assert f.texte.strip(), "les fragments sont vides"


def test_le_format_sse_est_respecte():
    f = appeler_sse("/api/resumer", {"texte": TEXTE})
    assert "data: " in f.brut, "aucune ligne 'data: ' dans la reponse"
    assert "\n\n" in f.brut, (
        "chaque evenement doit etre suivi de deux retours a la ligne")


def test_l_evenement_final_porte_l_usage():
    f = appeler_sse("/api/resumer", {"texte": TEXTE})
    assert f.final is not None, "aucun evenement avec done: true"
    usage = f.final.get("usage")
    assert isinstance(usage, dict), "l'evenement final doit porter un objet 'usage'"
    for cle in ("entree", "sortie", "ms"):
        assert cle in usage, f"usage.{cle} manquant"
        assert isinstance(usage[cle], (int, float)), f"usage.{cle} doit etre un nombre"
    assert usage["entree"] > 0, "usage.entree doit compter les tokens envoyes"


def test_l_evenement_final_est_le_dernier():
    f = appeler_sse("/api/resumer", {"texte": TEXTE})
    assert f.evenements, "aucun evenement recu"
    assert f.evenements[-1].get("done") is True, (
        "l'evenement done doit cloturer le flux")


def test_le_ton_direct_est_accepte():
    f = appeler_sse("/api/resumer", {"texte": TEXTE, "ton": "direct"})
    assert f.code == 200
    assert f.fragments, "le ton 'direct' doit produire un flux comme le ton neutre"


def test_le_ton_est_optionnel():
    f = appeler_sse("/api/resumer", {"texte": TEXTE})
    assert f.code == 200, "l'absence de 'ton' doit valoir 'neutre', pas une erreur"


# --- cas invalides -------------------------------------------------------

@pytest.mark.parametrize("charge, raison", [
    ({}, "texte absent"),
    ({"texte": ""}, "texte vide"),
    ({"texte": "   "}, "texte compose d'espaces"),
    ({"texte": None}, "texte nul"),
    ({"texte": "x" * 20_001}, "texte trop long"),
    ({"texte": TEXTE, "ton": "sarcastique"}, "ton inconnu"),
])
def test_les_entrees_invalides_donnent_400(charge, raison):
    r = appeler("/api/resumer", charge)
    assert r.status_code == 400, f"{raison} : attendu 400, recu {r.status_code}"


def test_l_erreur_est_du_json_pas_du_sse():
    r = appeler("/api/resumer", {"texte": ""})
    assert "application/json" in r.headers.get("content-type", ""), (
        "une erreur doit etre du JSON classique, jamais un flux SSE")
    corps = r.json()
    assert "erreur" in corps, "le corps d'erreur doit porter une cle 'erreur'"
    assert isinstance(corps["erreur"], str) and corps["erreur"].strip()


def test_le_serveur_ne_renvoie_jamais_500():
    """Une entree hostile est une entree invalide, pas un plantage."""
    for charge in ({"texte": {"objet": "au lieu d une chaine"}},
                   {"texte": ["une", "liste"]},
                   {"texte": 42}):
        r = appeler("/api/resumer", charge)
        assert r.status_code == 400, (
            f"{charge} : attendu 400, recu {r.status_code}")
