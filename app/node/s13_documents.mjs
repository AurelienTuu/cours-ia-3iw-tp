// Seance 13, seconde partie : la route POST /api/documents.
//
// Objectif : repondre a partir du corpus en citant les sources, et refuser
// quand le corpus ne contient pas la reponse.
// Le contrat exact est dans app/CONTRAT.md, section "Route 3".
//
// Prerequis : les TODO 9 a 11 de s13_index.mjs.
// Vous remplissez le TODO 12 de ce fichier, et rien d'autre.
//
// Verifier :
//     make app-node                 # terminal 1
//     make conformite SEANCE=13     # terminal 2

import { plonger, streamer } from "./fourni/modele.mjs"; // utiles pour le TODO 12
import {
  AEcrire, fin, fluxOu503, fragment, lireCorps, RequeteInvalide, sse,
} from "./fourni/transport.mjs";
import { chercher, indexer } from "./s13_index.mjs"; // utiles pour le TODO 12

async function documents(req, res) {
  const debut = performance.now();
  const corps = await lireCorps(req);
  const question = corps.question;
  if (typeof question !== "string" || !question.trim()) {
    throw new RequeteInvalide("question invalide");
  }

  async function* flux() {
    // =================================================================
    // TODO 12 : le pipeline RAG
    // =================================================================
    // 1. const vecteurs = await indexer()
    // 2. vectoriser la question avec plonger([question])
    // 3. chercher(...) pour les 3 morceaux les plus proches
    // 4. emettre sse({ sources: [{ titre, score }] }) AVANT tout fragment de
    //    reponse : le contrat l'exige
    // 5. injecter les extraits dans le prompt, et INTERDIRE au modele de
    //    repondre a partir d'autre chose que ces extraits
    // 6. streamer la reponse, puis cloturer avec l'usage
    throw new AEcrire("TODO 12 : le pipeline RAG");
    yield fin({}, debut);
  }

  await fluxOu503(res, flux());
}

export const routes = { "POST /api/documents": documents };
