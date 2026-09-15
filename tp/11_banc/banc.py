#!/usr/bin/env python3
"""Banc d'essai de la seance 11 : comparer des modeles sur VOS cas.

Un seul parametre varie : le modele. Le prompt est une constante du script.
Le faire varier en meme temps rendrait la comparaison inexploitable.

    python3 tp/11_banc/banc.py qwen2.5:3b llama3.2:1b
    python3 tp/11_banc/banc.py            # utilise la liste par defaut

Jumeau exact de banc.mjs.
"""
import json
import os
import pathlib
import statistics
import sys
import time
import urllib.request

BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
CAS = json.loads(
    (pathlib.Path(__file__).parents[1] / "05_prompt" / "cas.json").read_text(encoding="utf-8"))
MODELES_PAR_DEFAUT = ["qwen2.5:3b", "llama3.2:1b"]

# Constante du banc : le meme prompt pour tous les modeles, sans exception.
# =====================================================================
# COLLEZ ICI votre meilleure consigne de l'atelier de la seance 5.
# C'est elle qu'on compare d'un modele a l'autre, sans la retoucher.
# =====================================================================
CONSIGNE = """A REMPLACER"""


def mesurer(modele, texte):
    """Un appel en streaming. Renvoie (sortie, ttft_ms, tokens_par_seconde)."""
    charge = json.dumps({
        "model": modele,
        "temperature": 0,
        "max_tokens": 80,
        "stream": True,
        "stream_options": {"include_usage": True},
        "messages": [{"role": "system", "content": CONSIGNE},
                     {"role": "user", "content": texte}],
    }).encode()
    requete = urllib.request.Request(
        f"{BASE}/v1/chat/completions", data=charge,
        headers={"Content-Type": "application/json"}, method="POST")

    depart = time.perf_counter()
    ttft, sortie, tokens_sortie = None, "", 0
    with urllib.request.urlopen(requete, timeout=120) as reponse:
        for ligne in reponse:
            ligne = ligne.decode().strip()
            if not ligne.startswith("data: "):
                continue
            charge_utile = ligne[6:]
            if charge_utile == "[DONE]":
                break
            bloc = json.loads(charge_utile)
            for choix in bloc.get("choices") or []:
                morceau = (choix.get("delta") or {}).get("content")
                if morceau:
                    if ttft is None:
                        ttft = (time.perf_counter() - depart) * 1000
                    sortie += morceau
            if bloc.get("usage"):
                tokens_sortie = bloc["usage"].get("completion_tokens", 0)
    duree = time.perf_counter() - depart
    debit = tokens_sortie / duree if duree and tokens_sortie else 0
    return sortie, ttft or 0, debit


def extraire_json(brut):
    debut, fin = brut.find("{"), brut.rfind("}")
    if debut == -1 or fin == -1:
        return None
    try:
        return json.loads(brut[debut:fin + 1])
    except json.JSONDecodeError:
        return None


def evaluer(modele):
    cas = CAS["cas"]
    formes = exacts = 0
    ttfts, debits = [], []
    # Le premier appel inclut le chargement du modele en memoire : on le jette.
    print(f"  {modele} : chauffe...", end="", flush=True)
    mesurer(modele, cas[0]["texte"])
    print("\r" + " " * 40, end="\r")

    for i, c in enumerate(cas, 1):
        print(f"  {modele} : cas {i}/{len(cas)}", end="\r", flush=True)
        try:
            brut, ttft, debit = mesurer(modele, c["texte"])
        except Exception as e:
            print(f"\n  {modele} : echec sur le cas {i} ({e})")
            continue
        ttfts.append(ttft)
        debits.append(debit)
        obtenu = extraire_json(brut)
        if obtenu is None:
            continue
        formes += 1
        if obtenu.get("categorie") == c["categorie"] and obtenu.get("urgence") == c["urgence"]:
            exacts += 1
    print(" " * 50, end="\r")
    return {
        "modele": modele,
        "json": 100 * formes // len(cas),
        "exact": 100 * exacts // len(cas),
        "ttft": statistics.median(ttfts) if ttfts else 0,
        "debit": statistics.median(debits) if debits else 0,
    }


def main():
    if CONSIGNE.strip() == "A REMPLACER":
        print("Collez d'abord votre meilleure consigne de la seance 5 dans CONSIGNE,")
        print("en haut de tp/11_banc/banc.py, puis relancez.")
        return 1
    modeles = sys.argv[1:] or MODELES_PAR_DEFAUT
    print(f"Banc d'essai : {len(CAS['cas'])} cas, prompt constant, temperature 0\n")
    resultats = [evaluer(m) for m in modeles]

    print(f"  {'Modele':22s} {'JSON':>6s} {'Exact':>7s} {'1er frag.':>11s} {'Debit':>10s}")
    print("  " + "-" * 60)
    for r in resultats:
        print(f"  {r['modele']:22s} {r['json']:5d}% {r['exact']:6d}% "
              f"{r['ttft']:9.0f}ms {r['debit']:8.1f}/s")
    print("\n  Retenez le plus petit modele qui passe vos seuils, pas le meilleur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
