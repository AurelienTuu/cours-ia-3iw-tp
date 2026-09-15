"""Seance 13, premiere partie : l'index de recherche semantique.

Objectif : retrouver les extraits du corpus les plus proches d'une question,
SANS modele de generation. C'est la brique que la seance 12 enseigne.

Vous remplissez les TODO 9 a 11 de ce fichier, et rien d'autre.

Verifier la recherche seule, avant de brancher le modele :
    uv run python app/python/s13_index.py "comment demander un remboursement ?"
"""
from fourni.donnees import charger_documents
from fourni.modele import plonger


# =====================================================================
# TODO 9 : decouper un document en morceaux
# =====================================================================
def decouper(titre, texte):
    """Renvoie une liste de (titre_du_morceau, texte_du_morceau).

    Visez 300 a 800 tokens par morceau, avec un recouvrement. Decouper sur la
    structure (les titres ##) vaut mieux que decouper sur la longueur.
    Ecartez les morceaux trop courts pour porter du sens.
    """
    raise NotImplementedError("TODO 9 : decouper le corpus en morceaux")


_MORCEAUX = None


def morceaux():
    """FOURNI : decoupe tout le corpus, une seule fois, a la premiere demande."""
    global _MORCEAUX
    if _MORCEAUX is None:
        _MORCEAUX = [m for titre, texte in charger_documents()
                     for m in decouper(titre, texte)]
    return _MORCEAUX


# =====================================================================
# TODO 10 : vectoriser les morceaux, une seule fois
# =====================================================================
async def indexer():
    """Renvoie la liste des vecteurs, dans le meme ordre que morceaux().

    plonger(liste_de_textes) renvoie une liste de vecteurs. Gardez le resultat
    en memoire : vectoriser le corpus a chaque question serait tres lent.
    """
    raise NotImplementedError("TODO 10 : vectoriser les morceaux")


# =====================================================================
# TODO 11 : recherche par similarite cosinus
# =====================================================================
def chercher(vecteur_question, vecteurs, k=3):
    """Renvoie les k morceaux les plus proches : [(titre, texte, score), ...].

    Similarite cosinus : produit scalaire divise par le produit des normes.
    Triez du plus proche au moins proche.
    """
    raise NotImplementedError("TODO 11 : recherche par similarite cosinus")


if __name__ == "__main__":
    # FOURNI : tester la recherche seule, en ligne de commande.
    import asyncio
    import sys

    async def _essai(question):
        print(f"{len(morceaux())} morceaux")
        vecteurs = await indexer()
        vecteur_question = (await plonger([question]))[0]
        print("vectorises, voici les plus proches :\n")
        for titre, texte, score in chercher(vecteur_question, vecteurs):
            print(f"  {score:.3f}  {titre}")
            print(f"         {texte[:90].replace(chr(10), ' ')}...")

    asyncio.run(_essai(" ".join(sys.argv[1:]) or "comment demander un remboursement ?"))
