#!/usr/bin/env python3
"""Diagnostic du poste : Node ou Python, Ollama, modeles du socle, debit.

Jumeau exact de check.mjs. Meme sortie, memes verdicts, meme code de retour :
c'est la premiere demonstration du principe du module, un contrat HTTP unique
et deux implementations.

Aucune dependance : `python3 tp/00_setup/check.py` suffit.

Variables d'environnement reconnues :
  OLLAMA_BASE_URL  defaut http://localhost:11434
  MODEL_BASE       defaut qwen2.5:3b
  MODEL_EMBED      defaut paraphrase-multilingual
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
MODEL_BASE = os.environ.get("MODEL_BASE", "qwen2.5:3b")
MODEL_EMBED = os.environ.get("MODEL_EMBED", "paraphrase-multilingual")

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
GREEN, RED, YELLOW, CYAN = "\033[32m", "\033[31m", "\033[33m", "\033[36m"

blocking = 0


def ok(m):
    print(f"  {GREEN}OK{RESET}    {m}")


def warn(m):
    print(f"  {YELLOW}ATTENTION{RESET} {m}")


def fail(m):
    global blocking
    blocking += 1
    print(f"  {RED}ECHEC{RESET} {m}")


def info(m):
    print(f"  {DIM}{m}{RESET}")


def titre(m):
    print(f"\n{BOLD}{CYAN}{m}{RESET}")


def poster(route, charge, timeout=180, flux=False):
    """POST JSON. Renvoie la reponse brute (flux) ou le JSON decode."""
    req = urllib.request.Request(
        f"{BASE}{route}",
        data=json.dumps(charge).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer ollama"},
        method="POST",
    )
    reponse = urllib.request.urlopen(req, timeout=timeout)
    return reponse if flux else json.loads(reponse.read())


# --- 1. Python -----------------------------------------------------------
titre("1. Environnement Python")
if sys.version_info >= (3, 11):
    ok(f"Python {sys.version.split()[0]}")
else:
    fail(f"Python {sys.version.split()[0]} : il faut au minimum Python 3.11.")

# --- 2. Serveur Ollama ---------------------------------------------------
titre("2. Serveur Ollama")
info(f"cible : {BASE}")
tags = None
try:
    with urllib.request.urlopen(f"{BASE}/api/tags", timeout=5) as r:
        tags = json.loads(r.read())
    ok(f"le serveur repond ({len(tags.get('models', []))} modele(s) installe(s))")
except (urllib.error.URLError, OSError) as e:
    fail(f"aucune reponse : {e}")
    info("Lancez `ollama serve`, ou pointez OLLAMA_BASE_URL vers le serveur de classe :")
    info("  OLLAMA_BASE_URL=http://<ip-enseignant>:11434 python3 tp/00_setup/check.py")

installes = [m["name"] for m in (tags or {}).get("models", [])]


def present(voulu):
    return any(n == voulu or n == f"{voulu}:latest"
               or n.split(":")[0] == voulu.split(":")[0] for n in installes)


# --- 3. Modeles du socle -------------------------------------------------
if tags:
    titre("3. Modeles du socle")
    for modele, role in ((MODEL_BASE, "generation"), (MODEL_EMBED, "embeddings")):
        if present(modele):
            ok(f"{modele} ({role})")
        else:
            fail(f"{modele} absent ({role}) : lancez `ollama pull {modele}`")
    if installes:
        info("presents : " + ", ".join(installes))

# --- 4. Debit de generation ---------------------------------------------
if tags and present(MODEL_BASE):
    titre("4. Debit de generation")
    try:
        t0 = time.perf_counter()
        ttft, texte, stats = None, "", {}
        flux = poster("/api/generate", {
            "model": MODEL_BASE,
            "prompt": "Explique en trois phrases ce qu'est une API REST.",
            "options": {"temperature": 0.2, "num_predict": 120},
            "stream": True,
        }, flux=True)
        for ligne in flux:
            if not ligne.strip():
                continue
            bloc = json.loads(ligne)
            if bloc.get("response"):
                if ttft is None:
                    ttft = time.perf_counter() - t0
                texte += bloc["response"]
            if bloc.get("done"):
                stats = bloc
        total = time.perf_counter() - t0
        tps = (stats["eval_count"] / (stats["eval_duration"] / 1e9)
               if stats.get("eval_count") and stats.get("eval_duration") else None)

        ok(f"reponse recue ({len(texte.split())} mots)")
        info(f"premier token      : {int(ttft * 1000)} ms")
        info(f"duree totale       : {total:.1f} s")
        if tps:
            info(f"debit              : {tps:.1f} tokens/s")

        if tps is None:
            warn("debit non mesurable sur ce serveur")
        elif tps < 8:
            warn("moins de 8 tokens/s : passez a llama3.2:1b ou au serveur de classe")
        elif tps < 20:
            ok("debit correct pour les TP")
        else:
            ok("debit confortable")
        print(f"\n  {DIM}{texte.strip()[:160]}...{RESET}")
    except Exception as e:
        fail(f"generation impossible : {e}")

# --- 5. API compatible OpenAI (celle du cours) ---------------------------
if tags and present(MODEL_BASE):
    titre("5. API compatible OpenAI")
    try:
        d = poster("/v1/chat/completions", {
            "model": MODEL_BASE,
            "messages": [{"role": "user", "content": "Reponds uniquement par le mot: pret"}],
            "temperature": 0,
            "max_tokens": 10,
        }, timeout=120)
        contenu = (d.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        if contenu:
            ok(f'/v1/chat/completions repond : "{contenu}"')
            info("c'est le contrat d'API utilise pendant tout le module")
        else:
            fail("reponse inattendue sur /v1/chat/completions")
    except Exception as e:
        fail(f"appel impossible : {e}")

# --- 6. Embeddings -------------------------------------------------------
if tags and present(MODEL_EMBED):
    titre("6. Embeddings")
    TEXTE = "Ma commande n'est pas arrivee."
    dimension, detail = None, ""
    # Ollama recent expose /api/embed ; les versions plus anciennes /api/embeddings.
    routes = (
        ("/api/embed", {"model": MODEL_EMBED, "input": TEXTE},
         lambda d: len(d["embeddings"][0])),
        ("/api/embeddings", {"model": MODEL_EMBED, "prompt": TEXTE},
         lambda d: len(d["embedding"])),
    )
    for route, charge, extraire in routes:
        try:
            dimension = extraire(poster(route, charge, timeout=60))
            break
        except urllib.error.HTTPError as e:
            try:
                detail = json.loads(e.read()).get("error", "")
            except Exception:
                detail = str(e)
        except Exception:
            continue
    if dimension:
        ok(f"vecteur de dimension {dimension}")
        info("necessaire pour le RAG des seances 12 et 13")
    else:
        warn("embeddings indisponibles : a regler avant la seance 12"
             + (f" ({detail})" if detail else ""))

# --- Verdict -------------------------------------------------------------
titre("Verdict")
if blocking == 0:
    print(f"  {GREEN}{BOLD}Poste pret.{RESET} Notez votre debit : il servira en seance 6.")
    sys.exit(0)
print(f"  {RED}{BOLD}{blocking} probleme(s) bloquant(s).{RESET}")
print('  Voir docs/installation-ollama.md, section "Quand ca ne marche pas".')
sys.exit(1)
