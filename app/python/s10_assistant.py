"""Seance 10 : la route POST /api/assistant, avec appel d'outil.

Objectif : repondre a une question sur une commande en laissant le modele
demander l'outil chercher_commande, que VOTRE serveur execute.
Le contrat exact est dans app/CONTRAT.md, section "Route 2".

Vous remplissez les TODO 6 a 8 de ce fichier, et rien d'autre.
Tant qu'un TODO n'est pas ecrit, la route repond 501 "a ecrire".

Verifier :
    make app                      # terminal 1
    make conformite SEANCE=10     # terminal 2
"""
import json  # noqa: F401  (utile pour le TODO 8)
import time

from fastapi import APIRouter, Request
from fourni.donnees import chercher_commande  # noqa: F401  (utile pour le TODO 7)
from fourni.modele import appeler, streamer  # noqa: F401  (utiles pour le TODO 8)
from fourni.transport import RequeteInvalide, fin, flux_ou_503, fragment, lire_corps  # noqa: F401

routeur = APIRouter()


# =====================================================================
# TODO 6 : declarer l'outil au format attendu par le modele
# =====================================================================
# Un objet {"type": "function", "function": {name, description, parameters}}.
# La description est LUE PAR LE MODELE : elle fait partie du prompt, et c'est
# elle qui decide s'il appelle l'outil ou s'il repond de memoire.
OUTILS = []


# =====================================================================
# TODO 7 : la table des outils executables
# =====================================================================
# Une table explicite, jamais une resolution dynamique du nom recu du modele.
# Les arguments viennent du modele : validez-les AVANT d'executer.
TABLE_DES_OUTILS = {}


@routeur.post("/api/assistant")
async def assistant(requete: Request):
    debut = time.perf_counter()
    corps = await lire_corps(requete)
    question = corps.get("question")
    if not isinstance(question, str) or not question.strip():
        raise RequeteInvalide("question invalide")

    async def flux():
        # =============================================================
        # TODO 8 : la boucle d'appel d'outil
        # =============================================================
        # 1. appeler(messages, outils=OUTILS) renvoie (message, usage)
        # 2. si message["tool_calls"] existe, pour chaque appel :
        #    valider les arguments, executer, puis ajouter au fil des messages
        #    {"role": "tool", "tool_call_id": ..., "content": json.dumps(resultat)}
        # 3. rappeler le modele en streaming pour qu'il redige la reponse
        # 4. cumuler l'usage des DEUX appels : le client doit voir le total
        raise NotImplementedError("TODO 8 : la boucle d'appel d'outil")
        yield fin({}, debut)

    return await flux_ou_503(flux())
