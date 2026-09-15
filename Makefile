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
	ollama-check ollama-pull ollama-pull-tiny ollama-pull-plus ollama-list \
	setup-check setup-check-node liberer-port app app-node conformite

help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

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

# ----- 4. Diagnostic du poste -----

setup-check: outils-check  ## Diagnostic complet du poste, voie Python
	@command -v uv >/dev/null 2>&1 \
		|| (echo "uv est requis pour la voie Python. Lancez : make uv-install"; exit 1)
	$(UV) run python tp/00_setup/check.py

setup-check-node: outils-check  ## Diagnostic complet du poste, voie JavaScript
	@command -v node >/dev/null 2>&1 \
		|| (echo "Node 20+ est requis pour la voie JavaScript : https://nodejs.org"; exit 1)
	node tp/00_setup/check.mjs

# ----- 5. Travailler sur l'application -----

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

# SEANCE=n ne lance que les tests de cette seance, et exige que la route soit
# ecrite : un TODO oublie fait echouer au lieu d'etre ignore.
conformite:  ## Verifie votre serveur deja lance ; SEANCE=9, 10 ou 13 pour cibler une seance
	@BASE_URL=$(BASE_URL) $(if $(SEANCE),EXIGER=1,EXIGER=$(EXIGER)) \
		$(UV) run pytest examen/conformite $(if $(SEANCE),-m s$(SEANCE))
