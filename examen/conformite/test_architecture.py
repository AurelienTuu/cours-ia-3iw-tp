"""Verifications d'architecture, independantes du langage de rendu.

Elles portent sur la frontiere de confiance : le navigateur ne parle qu'a votre
serveur, jamais au modele.
"""
import pathlib

from conftest import BASE_URL, appeler

RACINE = pathlib.Path(__file__).resolve().parents[2]

# Extensions susceptibles d'etre servies au navigateur.
EXTENSIONS = (".html", ".htm", ".js", ".mjs", ".jsx", ".ts", ".tsx", ".vue", ".svelte")
# Dossiers dont le contenu part effectivement chez le client. Un fichier de
# serveur porte souvent la meme extension : on ne peut pas se fier a elle seule,
# sous peine d'accuser a tort un serveur Express nomme serveur.js.
# "src" est volontairement absent : il abrite aussi souvent du code serveur.
DOSSIERS_CLIENT = {"front", "public", "static", "client", "assets", "www"}
IGNORES = {"node_modules", ".git", ".venv", "__pycache__", "dist", "build",
           ".next", ".nuxt", "examen", "td", "coverage"}


def _fichiers_client():
    """Les fichiers reellement servis au navigateur.

    Deux familles : tout HTML ou qu'il soit, et le contenu des dossiers dont le
    nom annonce du code client. Le code serveur n'est jamais inspecte : il a le
    droit, et le devoir, de connaitre l'adresse du modele.
    """
    for chemin in RACINE.rglob("*"):
        if not chemin.is_file() or chemin.suffix.lower() not in EXTENSIONS:
            continue
        parties = set(chemin.relative_to(RACINE).parts)
        if IGNORES & parties:
            continue
        if chemin.suffix.lower() in (".html", ".htm") or DOSSIERS_CLIENT & parties:
            yield chemin


def test_le_front_n_appelle_pas_le_modele():
    """Le port du modele ne doit apparaitre dans aucun fichier servi au navigateur."""
    coupables = []
    for chemin in _fichiers_client():
        texte = chemin.read_text(encoding="utf-8", errors="ignore")
        if "11434" in texte or "api/chat/completions" in texte:
            coupables.append(str(chemin.relative_to(RACINE)))
    assert not coupables, (
        "ces fichiers cotes client joignent le modele directement : "
        + ", ".join(coupables))


def test_aucun_secret_dans_le_front():
    # "_API_KEY" couvre toutes les variables de cle, quel que soit le fournisseur.
    motifs = ("sk-", "Bearer ", "_API_KEY")
    coupables = []
    for chemin in _fichiers_client():
        texte = chemin.read_text(encoding="utf-8", errors="ignore")
        for motif in motifs:
            if motif in texte:
                coupables.append(f"{chemin.relative_to(RACINE)} ({motif})")
    assert not coupables, "secret potentiel expose au navigateur : " + ", ".join(coupables)


def test_le_serveur_n_expose_pas_sa_configuration():
    """Une erreur ne doit pas fuiter l'URL du modele ni une trace d'execution."""
    r = appeler("/api/resumer", {"texte": ""})
    corps = r.text.lower()
    for fuite in ("11434", "traceback", "at object.", "ollama_base_url"):
        assert fuite not in corps, (
            f"le corps d'erreur laisse fuiter {fuite!r} : renvoyez un message neutre")


def test_le_serveur_de_l_etudiant_n_est_pas_le_modele():
    """Erreur classique : donner l'URL d'Ollama au lieu de celle de son serveur."""
    assert "11434" not in BASE_URL, (
        "BASE_URL pointe sur le modele, pas sur votre serveur")
