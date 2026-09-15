# Voie Python : squelette FastAPI

## Lancer

Depuis la racine du dépôt :

```bash
make install     # une fois
make app         # votre serveur, rechargé à chaque sauvegarde
```

Ouvrez ensuite <http://localhost:3000>. Le front s'affiche, mais chaque action
répond « à écrire » : c'est normal, les TODO ne sont pas encore remplis.

## Un fichier par séance

| Fichier | Séance | Ce que vous écrivez |
| --- | --- | --- |
| `s09_resumer.py` | 9 | TODO 1 à 5 : la route « résumer », en streaming |
| `s10_assistant.py` | 10 | TODO 6 à 8 : l'outil et la boucle d'appel d'outil |
| `s13_index.py` | 13 | TODO 9 à 11 : découper, vectoriser, chercher |
| `s13_documents.py` | 13 | TODO 12 : le pipeline RAG complet |

Vous n'ouvrez que le fichier de la séance du jour. Chacun commence par son
objectif et la commande qui le vérifie.

## Ce que vous ne modifiez pas

| Fichier | Rôle |
| --- | --- |
| `main.py` | assemble les routes des trois séances et sert le front |
| `fourni/modele.py` | client du modèle local : streaming, appel d'outil, embeddings |
| `fourni/transport.py` | SSE, lecture du corps, traduction des erreurs, service du front |
| `fourni/donnees.py` | fichier des commandes et corpus documentaire |

## Vérifier

Serveur lancé dans un premier terminal, puis dans un second :

```bash
make conformite SEANCE=9     # seulement la séance 9, et elle doit être écrite
make conformite              # tout ; les routes pas encore écrites sont ignorées
```

Tant qu'un TODO n'est pas écrit, sa route répond `501` : la suite l'ignore, sauf
si vous ciblez sa séance.

Pour la séance 13, vérifiez la recherche seule avant de brancher le modèle :

```bash
uv run python app/python/s13_index.py "comment demander un remboursement ?"
```

Le contrat exact est dans [../CONTRAT.md](../CONTRAT.md), qui fait foi.

## Réglages

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | où joindre le modèle |
| `MODEL_BASE` | `qwen2.5:3b` | modèle de génération |
| `MODEL_EMBED` | `paraphrase-multilingual` | modèle d'embedding, séance 13 |
| `DELAI_MODELE` | `60` | timeout en secondes |
