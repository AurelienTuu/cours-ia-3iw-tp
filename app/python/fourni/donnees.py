"""Acces aux donnees des TP. FOURNI : vous n'avez pas a modifier ce fichier.

- chercher_commande  : l'outil de la seance 10
- delai_transporteur : un second outil, pour ceux qui veulent enchainer
- charger_documents  : le corpus de la seance 13
"""
import json
import pathlib

# app/python/fourni/donnees.py -> app/donnees
DONNEES = pathlib.Path(__file__).resolve().parents[2] / "donnees"
_BASE = json.loads((DONNEES / "commandes.json").read_text(encoding="utf-8"))


def chercher_commande(numero):
    """Renvoie la commande, ou None si le numero est inconnu.

    Un numero inconnu n'est pas une erreur : c'est un cas normal que votre
    assistant doit savoir annoncer au client.
    """
    numero = (numero or "").strip().upper()
    for commande in _BASE["commandes"]:
        if commande["numero"].upper() == numero:
            return commande
    return None


def delai_transporteur(nom):
    """Renvoie les informations d'un transporteur, ou None."""
    nom = (nom or "").strip().lower()
    for transporteur in _BASE["transporteurs"]:
        if transporteur["nom"].lower() == nom:
            return transporteur
    return None


def charger_documents():
    """Renvoie le corpus : une liste de (titre, texte).

    Le titre est celui du fichier, sans extension ni tiret. A vous de decouper
    ces textes en morceaux : c'est l'etape qui decide de la qualite du RAG.
    """
    documents = []
    for fichier in sorted((DONNEES / "corpus").glob("*.md")):
        titre = fichier.stem.replace("-", " ").replace("_", " ").capitalize()
        documents.append((titre, fichier.read_text(encoding="utf-8")))
    return documents
