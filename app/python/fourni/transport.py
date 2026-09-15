"""Plomberie HTTP. FOURNI : vous n'avez pas a modifier ce fichier.

Tout ce qui suit est du transport : formatage SSE, lecture du corps, traduction
des erreurs, service du front. Votre travail est dans les fichiers sNN_*.py.
"""
import json
import pathlib
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .modele import ModeleIndisponible

# app/python/fourni/transport.py -> app/front
FRONT = pathlib.Path(__file__).resolve().parents[2] / "front"


class RequeteInvalide(ValueError):
    """Entree du client refusee. Devient un 400 avec un corps JSON."""


async def lire_corps(requete):
    """Decode le corps JSON de la requete. Leve RequeteInvalide s'il est illisible."""
    try:
        corps = await requete.json()
    except ValueError as e:
        raise RequeteInvalide("corps JSON illisible") from e
    if not isinstance(corps, dict):
        raise RequeteInvalide("corps JSON invalide")
    return corps


def sse(objet):
    """Formate un evenement SSE. Les deux retours a la ligne sont obligatoires."""
    return f"data: {json.dumps(objet, ensure_ascii=False)}\n\n"


def fragment(texte):
    return sse({"delta": texte})


def fin(usage, debut):
    """Evenement de cloture, avec les compteurs exiges par le contrat."""
    return sse({
        "done": True,
        "usage": {
            "entree": usage.get("entree", 0),
            "sortie": usage.get("sortie", 0),
            "ms": int((time.perf_counter() - debut) * 1000),
        },
    })


async def flux_ou_503(generateur):
    """Ouvre un flux SSE, ou renvoie un 503 si le modele ne repond pas.

    Subtilite a connaitre : une fois le flux ouvert, le code HTTP est deja
    parti, et il est trop tard pour annoncer une erreur. On consomme donc le
    premier evenement AVANT de repondre. S'il echoue, on renvoie un vrai 503 ;
    sinon on ouvre le flux en replacant cet evenement en tete.
    """
    premier = None
    try:
        premier = await generateur.__anext__()
    except StopAsyncIteration:
        pass
    except ModeleIndisponible as e:
        print(f"[modele] {e}")
        return JSONResponse({"erreur": "modele indisponible"}, status_code=503)

    async def suite():
        if premier is not None:
            yield premier
        try:
            async for evenement in generateur:
                yield evenement
        except ModeleIndisponible as e:
            # Le flux est deja ouvert : on ne peut que le cloturer proprement.
            print(f"[modele] interrompu en cours de flux : {e}")

    return StreamingResponse(suite(), media_type="text/event-stream")


def creer_application():
    app = FastAPI(title="Assistant support", docs_url=None, redoc_url=None)

    @app.exception_handler(RequeteInvalide)
    async def _invalide(_requete: Request, exc: RequeteInvalide):
        return JSONResponse({"erreur": str(exc)}, status_code=400)

    @app.exception_handler(NotImplementedError)
    async def _a_ecrire(_requete: Request, exc: NotImplementedError):
        # Un TODO pas encore ecrit. 501 dit "route prevue mais pas implementee" :
        # la suite de conformite ignore alors les tests de cette route.
        return JSONResponse({"erreur": f"a ecrire : {exc}"}, status_code=501)

    @app.exception_handler(ModeleIndisponible)
    async def _modele_indisponible(_requete: Request, exc: ModeleIndisponible):
        print(f"[modele] {exc}")
        return JSONResponse({"erreur": "modele indisponible"}, status_code=503)

    @app.exception_handler(Exception)
    async def _imprevu(_requete: Request, exc: Exception):
        # On ne laisse jamais fuiter une trace d'execution vers le client.
        print(f"[erreur] {type(exc).__name__}: {exc}")
        return JSONResponse({"erreur": "erreur interne"}, status_code=500)

    return app


def servir_le_front(app):
    """A appeler en dernier : la racine attrape tout ce qui n'est pas une route."""
    app.mount("/", StaticFiles(directory=FRONT, html=True), name="front")
