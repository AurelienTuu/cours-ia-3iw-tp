"""Seance 13, seconde partie : la route POST /api/documents.

Objectif : repondre a partir du corpus en citant les sources, et refuser
quand le corpus ne contient pas la reponse.
Le contrat exact est dans app/CONTRAT.md, section "Route 3".

Prerequis : les TODO 9 a 11 de s13_index.py.
Vous remplissez le TODO 12 de ce fichier, et rien d'autre.

Verifier :
    make app                      # terminal 1
    make conformite SEANCE=13     # terminal 2
"""
import time

import s13_index  # noqa: F401  (utile pour le TODO 12)
from fastapi import APIRouter, Request
from fourni.modele import plonger, streamer  # noqa: F401  (utiles pour le TODO 12)
from fourni.transport import (  # noqa: F401
    RequeteInvalide,
    fin,
    flux_ou_503,
    fragment,
    lire_corps,
    sse,
)

routeur = APIRouter()


@routeur.post("/api/documents")
async def documents(requete: Request):
    debut = time.perf_counter()
    corps = await lire_corps(requete)
    question = corps.get("question")
    if not isinstance(question, str) or not question.strip():
        raise RequeteInvalide("question invalide")

    async def flux():
        # =============================================================
        # TODO 12 : le pipeline RAG
        # =============================================================
        # 1. vecteurs = await s13_index.indexer()
        # 2. vectoriser la question avec plonger([question])
        # 3. s13_index.chercher(...) pour les 3 morceaux les plus proches
        # 4. emettre sse({"sources": [{"titre": ..., "score": ...}]}) AVANT tout
        #    fragment de reponse : le contrat l'exige
        # 5. injecter les extraits dans le prompt, et INTERDIRE au modele de
        #    repondre a partir d'autre chose que ces extraits
        # 6. streamer la reponse, puis cloturer avec l'usage
        raise NotImplementedError("TODO 12 : le pipeline RAG")
        yield fin({}, debut)

    return await flux_ou_503(flux())
