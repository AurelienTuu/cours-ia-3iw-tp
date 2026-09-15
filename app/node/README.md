# Voie JavaScript : squelette Node

**Aucune dépendance npm.** Node 20 ou plus suffit, et il n'y a rien à installer.
C'est délibéré : ce squelette ne peut pas casser à l'installation.

## Lancer

Depuis la racine du dépôt :

```bash
make app-node    # votre serveur, relancé à chaque sauvegarde
```

Ouvrez ensuite <http://localhost:3000>. Le front s'affiche, mais chaque action
répond « à écrire » : c'est normal, les TODO ne sont pas encore remplis.

## Un fichier par séance

| Fichier | Séance | Ce que vous écrivez |
| --- | --- | --- |
| `s09_resumer.mjs` | 9 | TODO 1 à 5 : la route « résumer », en streaming |
| `s10_assistant.mjs` | 10 | TODO 6 à 8 : l'outil et la boucle d'appel d'outil |
| `s13_index.mjs` | 13 | TODO 9 à 11 : découper, vectoriser, chercher |
| `s13_documents.mjs` | 13 | TODO 12 : le pipeline RAG complet |

Vous n'ouvrez que le fichier de la séance du jour. Chacun commence par son
objectif et la commande qui le vérifie.

## Ce que vous ne modifiez pas

| Fichier | Rôle |
| --- | --- |
| `main.mjs` | assemble les routes des trois séances et sert le front |
| `fourni/modele.mjs` | client du modèle local : streaming, appel d'outil, embeddings |
| `fourni/transport.mjs` | SSE, lecture du corps, erreurs, routage, service du front |
| `fourni/donnees.mjs` | fichier des commandes et corpus documentaire |

Un TODO non écrit lève `AEcrire`, que le transport traduit en réponse `501`.

## Vérifier

Serveur lancé dans un premier terminal, puis dans un second :

```bash
make conformite SEANCE=9     # seulement la séance 9, et elle doit être écrite
make conformite              # tout ; les routes pas encore écrites sont ignorées
```

La suite de conformité est écrite en Python, mais elle n'interroge que du HTTP :
elle vous juge exactement comme elle juge un rendu Python.

Pour la séance 13, vérifiez la recherche seule avant de brancher le modèle :

```bash
node app/node/s13_index.mjs "comment demander un remboursement ?"
```

## Express, Fastify, Next.js

Ce squelette utilise le module `node:http` pour éviter toute installation. Si
vous préférez Express ou Fastify, vous en avez le droit : le contrat est le
même, et `fourni/modele.mjs` fonctionnera tel quel. Vous reprenez alors à votre
charge le routage et le service du front, en respectant
[../CONTRAT.md](../CONTRAT.md).

## Réglages

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | où joindre le modèle |
| `MODEL_BASE` | `qwen2.5:3b` | modèle de génération |
| `MODEL_EMBED` | `paraphrase-multilingual` | modèle d'embedding, séance 13 |
| `DELAI_MODELE` | `60` | timeout en secondes |
| `PORT` | `3000` | port d'écoute |
