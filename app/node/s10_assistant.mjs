// Seance 10 : la route POST /api/assistant, avec appel d'outil.
//
// Objectif : repondre a une question sur une commande en laissant le modele
// demander l'outil chercher_commande, que VOTRE serveur execute.
// Le contrat exact est dans app/CONTRAT.md, section "Route 2".
//
// Vous remplissez les TODO 6 a 8 de ce fichier, et rien d'autre.
// Tant qu'un TODO n'est pas ecrit, la route repond 501 "a ecrire".
//
// Verifier :
//     make app-node                 # terminal 1
//     make conformite SEANCE=10     # terminal 2

import { chercherCommande } from "./fourni/donnees.mjs"; // utile pour le TODO 7
import { appeler, streamer } from "./fourni/modele.mjs"; // utiles pour le TODO 8
import {
  AEcrire, fin, fluxOu503, fragment, lireCorps, RequeteInvalide,
} from "./fourni/transport.mjs";

// =====================================================================
// TODO 6 : declarer l'outil au format attendu par le modele
// =====================================================================
// Un objet { type: "function", function: { name, description, parameters } }.
// La description est LUE PAR LE MODELE : elle fait partie du prompt, et c'est
// elle qui decide s'il appelle l'outil ou s'il repond de memoire.
const OUTILS = [];

// =====================================================================
// TODO 7 : la table des outils executables
// =====================================================================
// Une table explicite, jamais une resolution dynamique du nom recu du modele.
// Les arguments viennent du modele : validez-les AVANT d'executer.
const TABLE_DES_OUTILS = {};

async function assistant(req, res) {
  const debut = performance.now();
  const corps = await lireCorps(req);
  const question = corps.question;
  if (typeof question !== "string" || !question.trim()) {
    throw new RequeteInvalide("question invalide");
  }

  async function* flux() {
    // =================================================================
    // TODO 8 : la boucle d'appel d'outil
    // =================================================================
    // 1. appeler(messages, { outils: OUTILS }) renvoie { message, usage }
    // 2. si message.tool_calls existe, pour chaque appel :
    //    valider les arguments, executer, puis ajouter au fil des messages
    //    { role: "tool", tool_call_id: ..., content: JSON.stringify(resultat) }
    // 3. rappeler le modele en streaming pour qu'il redige la reponse
    // 4. cumuler l'usage des DEUX appels : le client doit voir le total
    throw new AEcrire("TODO 8 : la boucle d'appel d'outil");
    yield fin({}, debut);
  }

  await fluxOu503(res, flux());
}

export const routes = { "POST /api/assistant": assistant };
