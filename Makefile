.DEFAULT_GOAL := help

# Les Fondamentaux de l'IA : 3IW
# Makefile etudiant : installation du poste, puis travail sur l'application.

UV := uv
export UV_PROJECT_ENVIRONMENT := .venv

# Le socle impose a toute la classe. Surchargeable :
#   make ollama-pull MODEL_BASE=llama3.2:1b
# generation, ~1.9 Go, sait faire du tool calling
MODEL_BASE  ?= qwen2.5:3b
# secours pour les machines les plus justes
MODEL_TINY  ?= llama3.2:1b
# confort, a partir de 16 Go de RAM
MODEL_PLUS  ?= qwen2.5:7b
# embeddings multilingues, ~562 Mo
MODEL_EMBED ?= paraphrase-multilingual

OLLAMA_HOST ?= http://localhost:11434

# Port de VOTRE serveur, pas celui du modele.
PORT     ?= 3000
BASE_URL ?= http://localhost:$(PORT)

.PHONY: help uv-install ollama-install outils outils-check install \
	ollama-check ollama-pull ollama-pull-tiny ollama-pull-plus ollama-list ollama-run ollama-run-tiny ollama-run-plus ollama-run-verbose ollama-ps ollama-stop \
	setup-check setup-check-node prompt prompt-node banc banc-node \
	liberer-port app app-node front-streamlit conformite

help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ----- 1. Outils : uv et Ollama, pour les postes qui ne les ont pas -----

uv-install:  ## Installe uv s'il est absent (script officiel, macOS et Linux)
	@if command -v uv >/dev/null 2>&1; then \
		echo "uv deja installe : $$(uv --version)"; \
	else \
		echo "installation de uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh \
		&& echo "uv installe. Ouvrez un nouveau terminal (ou : source $$HOME/.local/bin/env)"; \
	fi

ollama-install:  ## Installe Ollama s'il est absent (script officiel, macOS et Linux)
	@if command -v ollama >/dev/null 2>&1; then \
		echo "Ollama deja installe : $$(ollama --version 2>/dev/null | tail -1)"; \
	else \
		echo "installation d'Ollama..."; \
		curl -fsSL https://ollama.com/install.sh | sh \
		&& echo "Ollama installe. Ensuite : ollama serve, puis make ollama-pull"; \
	fi

outils: uv-install ollama-install  ## Installe uv et Ollama si besoin

outils-check:  ## Verifie la presence de uv, Ollama et Node (Ollama obligatoire)
	@if command -v ollama >/dev/null 2>&1; then \
		echo "  ok      ollama  $$(ollama --version 2>/dev/null | tail -1)"; \
	else \
		echo "  ABSENT  ollama  -> make ollama-install"; exit 1; \
	fi
	@command -v uv >/dev/null 2>&1 \
		&& echo "  ok      uv      $$(uv --version)" \
		|| echo "  absent  uv      (voie Python) -> make uv-install"
	@command -v node >/dev/null 2>&1 \
		&& echo "  ok      node    $$(node --version)" \
		|| echo "  absent  node    (voie JavaScript) -> https://nodejs.org"

# ----- 2. Environnement Python : tests de conformite et voie Python -----

install: uv-install  ## Installe l'environnement Python (tests, et FastAPI pour la voie Python)
	$(UV) sync
	@echo "environnement pret : .venv"

# ----- 3. Modeles -----

ollama-check:  ## Verifie qu'Ollama repond et liste les modeles installes
	@curl -sf $(OLLAMA_HOST)/api/tags > /dev/null \
		&& echo "Ollama repond sur $(OLLAMA_HOST)" \
		|| (echo "Ollama ne repond pas. Lancez : ollama serve"; exit 1)
	@ollama list

ollama-pull:  ## Telecharge le socle du cours (generation + embeddings, ~2,5 Go)
	ollama pull $(MODEL_BASE)
	ollama pull $(MODEL_EMBED)
	@echo "Socle pret : $(MODEL_BASE) + $(MODEL_EMBED)"

ollama-pull-tiny:  ## Telecharge le modele de secours, pour les machines a 8 Go
	ollama pull $(MODEL_TINY)

ollama-pull-plus:  ## Telecharge le modele de confort (16 Go de RAM minimum)
	ollama pull $(MODEL_PLUS)

ollama-list:  ## Liste les modeles presents sur la machine
	ollama list

# Discuter avec un modele dans le terminal. /bye pour sortir.
#   make ollama-run MODEL=llama3.2:1b          autre modele
#   make ollama-run PROMPT="Explique un token"  une seule question, sans session
MODEL  ?= $(MODEL_BASE)
PROMPT ?=
ollama-run:  ## Discute avec le modele du socle (MODEL=..., PROMPT="..." pour une question)
	ollama run $(MODEL) $(if $(PROMPT),"$(PROMPT)")

ollama-run-tiny:  ## Discute avec le modele de secours (machines a 8 Go)
	ollama run $(MODEL_TINY) $(if $(PROMPT),"$(PROMPT)")

ollama-run-plus:  ## Discute avec le modele de confort (16 Go de RAM minimum)
	ollama run $(MODEL_PLUS) $(if $(PROMPT),"$(PROMPT)")

# --verbose affiche apres chaque reponse le debit (eval rate, en tokens/s) et le
# temps de chargement : c'est la mesure relevee a l'atelier de la seance 4.
ollama-run-verbose:  ## Discute en affichant le debit en tokens/s (MODEL=... pour changer)
	ollama run --verbose $(MODEL) $(if $(PROMPT),"$(PROMPT)")

ollama-ps:  ## Liste les modeles charges en memoire, et sur CPU ou GPU
	ollama ps

ollama-stop:  ## Decharge le modele de la memoire (MODEL=... pour un autre)
	ollama stop $(MODEL)

# ----- 4. Diagnostic du poste -----

setup-check: outils-check  ## Diagnostic complet du poste, voie Python
	@command -v uv >/dev/null 2>&1 \
		|| (echo "uv est requis pour la voie Python. Lancez : make uv-install"; exit 1)
	$(UV) run python tp/00_setup/check.py

setup-check-node: outils-check  ## Diagnostic complet du poste, voie JavaScript
	@command -v node >/dev/null 2>&1 \
		|| (echo "Node 20+ est requis pour la voie JavaScript : https://nodejs.org"; exit 1)
	node tp/00_setup/check.mjs

# ----- 5. Ateliers des seances 5 et 11 -----

# Atelier de la seance 5 : on ne modifie que CONSIGNE, en haut du fichier,
# et on relance apres chaque changement pour voir le score bouger.
prompt:  ## Atelier prompt de la seance 5, voie Python
	@MODEL_BASE=$(MODEL_BASE) OLLAMA_BASE_URL=$(OLLAMA_HOST) \
		$(UV) run python tp/05_prompt/evaluer.py

prompt-node:  ## Atelier prompt de la seance 5, voie JavaScript
	@MODEL_BASE=$(MODEL_BASE) OLLAMA_BASE_URL=$(OLLAMA_HOST) \
		node tp/05_prompt/evaluer.mjs

# Banc d'essai de la seance 11 : le prompt est fige, ce sont les modeles qui
# varient. Surchargeable : make banc MODELES="qwen2.5:3b llama3.2:1b"
MODELES ?= $(MODEL_BASE) $(MODEL_TINY)

banc:  ## Banc d'essai de la seance 11, voie Python
	@OLLAMA_BASE_URL=$(OLLAMA_HOST) $(UV) run python tp/11_banc/banc.py $(MODELES)

banc-node:  ## Banc d'essai de la seance 11, voie JavaScript
	@OLLAMA_BASE_URL=$(OLLAMA_HOST) node tp/11_banc/banc.mjs $(MODELES)

# ----- 6. Travailler sur l'application -----

# Tue ce qui ecoute sur $(PORT) : SIGTERM, puis SIGKILL si le port tient encore.
# Ne touche jamais au port d'Ollama. Autre port : make liberer-port PORT=4000
liberer-port:  ## Libere le port de l'app (3000 par defaut) si un ancien serveur l'occupe
	@if command -v lsof >/dev/null 2>&1; then \
		PIDS=$$(lsof -ti tcp:$(PORT) -sTCP:LISTEN 2>/dev/null); \
		[ -z "$$PIDS" ] && exit 0; \
		echo "port $(PORT) occupe (pid $$(echo $$PIDS)), arret..."; \
		kill $$PIDS 2>/dev/null; \
		for i in 1 2 3 4 5 6 7 8 9 10; do \
			lsof -ti tcp:$(PORT) -sTCP:LISTEN >/dev/null 2>&1 || break; sleep 0.3; \
		done; \
		PIDS=$$(lsof -ti tcp:$(PORT) -sTCP:LISTEN 2>/dev/null); \
		[ -n "$$PIDS" ] && kill -9 $$PIDS 2>/dev/null; \
		echo "port $(PORT) libere"; \
	elif command -v fuser >/dev/null 2>&1; then \
		fuser -k $(PORT)/tcp >/dev/null 2>&1 && echo "port $(PORT) libere" || true; \
	else \
		echo "ni lsof ni fuser : impossible de verifier le port $(PORT)"; \
	fi

app: liberer-port  ## Lance VOTRE serveur, voie Python (rechargement automatique)
	$(UV) run uvicorn --app-dir app/python main:app --reload --port $(PORT)

app-node: liberer-port  ## Lance VOTRE serveur, voie JavaScript (rechargement automatique)
	PORT=$(PORT) node --watch app/node/main.mjs

# Front d'exemple en Streamlit : il appelle le serveur deja lance sur $(PORT).
# Streamlit n'est pas une dependance du projet : uv le fournit a la volee.
front-streamlit:  ## Lance le front d'exemple Streamlit, devant un serveur DEJA lance
	@echo "front Streamlit sur http://localhost:8501, branche sur $(BASE_URL)"
	@API_URL=$(BASE_URL) $(UV) run --with streamlit --with httpx \
		streamlit run app/front_streamlit/app.py \
		--server.headless true --browser.gatherUsageStats false

# SEANCE=n ne lance que les tests de cette seance, et exige que la route soit
# ecrite : un TODO oublie fait echouer au lieu d'etre ignore.
conformite:  ## Verifie votre serveur deja lance ; SEANCE=9, 10 ou 13 pour cibler une seance
	@BASE_URL=$(BASE_URL) $(if $(SEANCE),EXIGER=1,EXIGER=$(EXIGER)) \
		$(UV) run pytest examen/conformite $(if $(SEANCE),-m s$(SEANCE))
