# Contrat de route : l'application fil rouge

Ce fichier fait foi. En cas de divergence entre un squelette, une slide et ce
document, c'est ce document qui a raison.

Il décrit **le seul point de contact** entre le front fourni et votre serveur.
Ce que vous écrivez derrière, et dans quelle langue, ne regarde que vous.

## Principe

```
Navigateur  ---->  Votre serveur  ---->  Modèle (Ollama)
 (fourni)          (votre travail)       (localhost:11434)
```

Le navigateur n'appelle jamais le modèle directement. Il n'appelle que vos
routes. Toute requête partant du front vers le port 11434 est une non-conformité.

## Route 1 : résumer un texte (séance 9)

### Requête

```
POST /api/resumer
Content-Type: application/json

{ "texte": "le contenu a resumer", "ton": "neutre" }
```

| Champ | Type | Obligatoire | Valeurs |
| --- | --- | --- | --- |
| `texte` | chaîne | oui | non vide, 20 000 caractères maximum |
| `ton` | chaîne | non | `neutre` (défaut) ou `direct` |

### Réponse nominale

Code `200`, en-tête `Content-Type: text/event-stream`.

Un événement SSE par fragment produit par le modèle :

```
data: {"delta":"Le client"}

data: {"delta":" ne parvient pas"}

data: {"done":true,"usage":{"entree":312,"sortie":88,"ms":2140}}

```

- Chaque événement est une ligne `data: ` suivie de **deux** retours à la ligne.
- Le dernier événement porte `done: true` et l'objet `usage`.
- `usage.entree` et `usage.sortie` sont des nombres de tokens, `usage.ms` la
  durée totale en millisecondes.

### Réponses d'erreur

| Situation | Code | Corps |
| --- | --- | --- |
| `texte` absent, vide ou trop long | `400` | `{ "erreur": "texte invalide" }` |
| `ton` inconnu | `400` | `{ "erreur": "ton invalide" }` |
| Modèle injoignable ou en timeout | `503` | `{ "erreur": "modele indisponible" }` |

Les erreurs sont du JSON classique, **pas** du SSE. Elles doivent arriver avant
le début du flux.

## Route 2 : rechercher une commande (séance 10)

Ajoutée lors de la séance sur l'appel d'outils. Même principe, même gestion
d'erreurs.

```
POST /api/assistant
{ "question": "ou en est la commande CMD-2024-118 ?" }
```

La réponse est un flux SSE de même forme. Le serveur a le droit d'appeler le
modèle plusieurs fois (boucle d'appel d'outil) avant de commencer à streamer.

## Route 3 : interroger le corpus (séance 13)

```
POST /api/documents
{ "question": "comment demander un remboursement ?" }
```

Réponse SSE de même forme, avec un événement supplémentaire **avant** les
fragments, listant les sources retenues :

```
data: {"sources":[{"titre":"Remboursements","score":0.81}]}

```

## Règles communes à toutes les routes

1. Le prompt est assemblé **côté serveur**. Le client n'envoie jamais de prompt.
2. Toute entrée est validée avant d'atteindre le modèle.
3. Tout appel au modèle a un timeout explicite, et un repli en cas d'échec.
4. Chaque appel est journalisé : modèle, tokens d'entrée et de sortie, durée, issue.
5. Aucun secret, aucune URL de modèle, aucune configuration serveur n'est
   exposée au client.

## Comment votre rendu est vérifié

```bash
# depuis la racine du depot, votre serveur devant tourner sur le port 3000
make conformite SEANCE=9     # une seance, qui doit etre ecrite
make conformite              # tout ; les routes pas encore ecrites sont ignorees
```

La suite est écrite en Python et n'interroge que le HTTP. Elle donne le même
verdict que votre serveur soit en FastAPI, en Express, en Symfony ou en Go.

Une route prévue mais pas encore écrite doit répondre **`501`** : la suite
ignore alors ses tests, ce qui permet de la lancer dès la séance 9. Les deux
squelettes fournis le font déjà. Pour la correction du CC2, toutes les routes
sont exigées : une route en `501` y compte comme un échec.

## Voies fournies

| Dossier | Pile | État |
| --- | --- | --- |
| `app/front/` | HTML et JavaScript statiques | **fourni, gelé, ne pas modifier** |
| `app/python/` | FastAPI | un fichier par séance, TODO à remplir |
| `app/node/` | Node, sans dépendance | un fichier par séance, TODO à remplir |

Dans les deux voies, les fichiers de séance sont identiques d'une langue à
l'autre : `s09_resumer`, `s10_assistant`, `s13_index`, `s13_documents`. Le point
d'entrée `main` et le dossier `fourni/` ne se modifient pas.

Déclarez votre voie au début du projet et tenez-vous-y. Une autre pile est
acceptée si vous l'assumez : le contrat est le même, mais le squelette est à
votre charge.
