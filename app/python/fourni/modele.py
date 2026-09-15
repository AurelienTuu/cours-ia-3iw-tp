"""Client du modele local. FOURNI : vous n'avez pas a modifier ce fichier.

Il parle l'API compatible OpenAI exposee par Ollama. Le meme code fonctionnerait
face a un fournisseur cloud : seules OLLAMA_BASE_URL et l'authentification
changeraient.
"""
import json
import os

import httpx

BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
MODELE = os.environ.get("MODEL_BASE", "qwen2.5:3b")
DELAI = float(os.environ.get("DELAI_MODELE", "60"))


class ModeleIndisponible(RuntimeError):
    """Le modele n'a pas repondu. La route doit traduire ca en 503."""


def _corps(messages, temperature, max_tokens, outils, flux):
    corps = {
        "model": MODELE,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": flux,
    }
    if flux:
        # Sans cette option, le dernier fragment n'apporte aucun compte de tokens.
        corps["stream_options"] = {"include_usage": True}
    if outils:
        corps["tools"] = outils
    return corps


async def streamer(messages, temperature=0.3, max_tokens=400, outils=None):
    """Appelle le modele en streaming.

    Produit des couples (genre, valeur) :
        ("delta", "un morceau de texte")
        ("usage", {"entree": 312, "sortie": 88})

    Leve ModeleIndisponible si le modele ne repond pas ou renvoie une erreur.
    """
    corps = _corps(messages, temperature, max_tokens, outils, flux=True)
    try:
        async with httpx.AsyncClient(timeout=DELAI) as client:
            async with client.stream("POST", f"{BASE}/v1/chat/completions",
                                     json=corps) as reponse:
                if reponse.status_code >= 400:
                    await reponse.aread()
                    raise ModeleIndisponible(f"le modele a repondu {reponse.status_code}")
                async for ligne in reponse.aiter_lines():
                    if not ligne.startswith("data: "):
                        continue
                    charge = ligne[6:].strip()
                    if not charge or charge == "[DONE]":
                        continue
                    bloc = json.loads(charge)
                    for choix in bloc.get("choices") or []:
                        morceau = (choix.get("delta") or {}).get("content")
                        if morceau:
                            yield "delta", morceau
                    if bloc.get("usage"):
                        yield "usage", {
                            "entree": bloc["usage"].get("prompt_tokens", 0),
                            "sortie": bloc["usage"].get("completion_tokens", 0),
                        }
    except httpx.HTTPError as e:
        raise ModeleIndisponible(str(e)) from e


async def appeler(messages, temperature=0.0, max_tokens=400, outils=None):
    """Appel classique, sans streaming. Utile pour la boucle d'appel d'outil.

    Renvoie le message brut du modele, tel que le fournisseur le rend.
    """
    corps = _corps(messages, temperature, max_tokens, outils, flux=False)
    try:
        async with httpx.AsyncClient(timeout=DELAI) as client:
            reponse = await client.post(f"{BASE}/v1/chat/completions", json=corps)
            reponse.raise_for_status()
    except httpx.HTTPError as e:
        raise ModeleIndisponible(str(e)) from e
    donnees = reponse.json()
    message = donnees["choices"][0]["message"]
    usage = donnees.get("usage") or {}
    return message, {
        "entree": usage.get("prompt_tokens", 0),
        "sortie": usage.get("completion_tokens", 0),
    }


async def plonger(textes):
    """Vectorise une liste de textes avec le modele d'embedding. Seance 12."""
    modele = os.environ.get("MODEL_EMBED", "paraphrase-multilingual")
    try:
        async with httpx.AsyncClient(timeout=DELAI) as client:
            reponse = await client.post(f"{BASE}/api/embed",
                                        json={"model": modele, "input": textes})
            reponse.raise_for_status()
    except httpx.HTTPError as e:
        raise ModeleIndisponible(str(e)) from e
    return reponse.json()["embeddings"]
