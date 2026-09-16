"""Seance 9 : la route POST /api/resumer.

Objectif : resumer le message d'un client, en streaming, dans le ton demande.
Le contrat exact est dans app/CONTRAT.md, section "Route 1".

Vous remplissez les TODO 1 a 5 de ce fichier, et rien d'autre.
Tant qu'un TODO n'est pas ecrit, la route repond 501 "a ecrire".

Verifier :
    make app                     # terminal 1
    make conformite SEANCE=9     # terminal 2
"""
import time

from fastapi import APIRouter, Request
from fourni.modele import streamer
from fourni.transport import RequeteInvalide, fin, flux_ou_503, fragment, lire_corps

routeur = APIRouter()

TONS = {"neutre", "direct"}
LONGUEUR_MAX = 20_000


# =====================================================================
# TODO 1 : valider l'entree du client
# =====================================================================
def valider_resumer(corps):
    """Renvoie (texte, ton) ou leve RequeteInvalide.

    Le contrat exige un 400 pour : texte absent, vide, non textuel, de plus de
    20 000 caracteres, et pour un ton qui n'est ni 'neutre' ni 'direct'.
    L'absence de 'ton' vaut 'neutre'.
    """
    if not isinstance(corps, dict):
        raise RequeteInvalide("Le corps de la requête doit être un dictionnaire.")

    if "texte" not in corps:
        raise RequeteInvalide("Le champ 'texte' est absent.")
    
    texte = corps["texte"]

    if not isinstance(texte, str) or not texte.strip():
        raise RequeteInvalide("Le champ 'texte' doit être une chaîne de caractères non vide.")
        
    if len(texte) > 20000:
        raise RequeteInvalide("Le champ 'texte' dépasse la limite de 20 000 caractères.")

    ton = corps.get("ton", "neutre")
    
    if ton not in ("neutre", "direct"):
        raise RequeteInvalide("Le champ 'ton' doit être soit 'neutre', soit 'direct'.")

    return texte, ton

# =====================================================================
# TODO 2 : assembler le prompt, cote serveur et nulle part ailleurs
# =====================================================================
def prompt_resumer(texte, ton):
    """Renvoie la liste de messages envoyee au modele.

    Rappel de la seance 5 : un role, un contexte, un format montre.
    Le texte du client est une DONNEE, jamais une consigne : gardez-le dans un
    message 'user' distinct de la consigne systeme.
    """
    if ton == "direct":
        consigne_ton = "Allez droit au but."
    else:
        consigne_ton = "Adoptez un ton neutre, objectif et professionnel."

    system_prompt = (
        "Vous êtes un assistant expert en synthèse de documents.\n"
        "Votre rôle est de résumer le texte fourni par l'utilisateur.\n"
        f"Consigne de ton : {consigne_ton}\n\n"
        "Format attendu :\n"
        "- Restez concis.\n"
        "- Restez fidèle au contenu d'origine sans ajouter d'informations extérieures."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": texte}
    ]


@routeur.post("/api/resumer")
async def resumer(requete: Request):
    debut = time.perf_counter()
    texte, ton = valider_resumer(await lire_corps(requete))
    messages = prompt_resumer(texte, ton)

    async def flux():
        usage = {}
        # =============================================================
        # TODO 3 et 4 : appeler le modele et relayer chaque fragment
        # =============================================================
        async for genre, valeur in streamer(messages):
            if genre == "delta":
                yield fragment(valeur)
            elif genre == "usage":
                usage = valeur
        # =============================================================
        # TODO 5 : cloturer le flux avec l'evenement done et l'usage
        # =============================================================
        yield fin(usage, debut)

    # flux_ou_503 consomme le premier evenement avant de repondre : c'est ce qui
    # permet de renvoyer un vrai 503 quand le modele ne repond pas.
    return await flux_ou_503(flux())
