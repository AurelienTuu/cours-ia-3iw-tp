// Seance 9 : la route POST /api/resumer.
//
// Objectif : resumer le message d'un client, en streaming, dans le ton demande.
// Le contrat exact est dans app/CONTRAT.md, section "Route 1".
//
// Vous remplissez les TODO 1 a 5 de ce fichier, et rien d'autre.
// Tant qu'un TODO n'est pas ecrit, la route repond 501 "a ecrire".
//
// Verifier :
//     make app-node                # terminal 1
//     make conformite SEANCE=9     # terminal 2

import { streamer } from "./fourni/modele.mjs";
import {
  AEcrire, fin, fluxOu503, fragment, lireCorps, RequeteInvalide,
} from "./fourni/transport.mjs";

const TONS = new Set(["neutre", "direct"]);
const LONGUEUR_MAX = 20_000;

// =====================================================================
// TODO 1 : valider l'entree du client
// =====================================================================
function validerResumer(corps) {
  // Renvoie { texte, ton } ou leve RequeteInvalide.
  //
  // Le contrat exige un 400 pour : texte absent, vide, non textuel, de plus de
  // 20 000 caracteres, et pour un ton qui n'est ni "neutre" ni "direct".
  // L'absence de "ton" vaut "neutre".
  throw new AEcrire("TODO 1 : valider corps.texte et corps.ton");
}

// =====================================================================
// TODO 2 : assembler le prompt, cote serveur et nulle part ailleurs
// =====================================================================
function promptResumer(texte, ton) {
  // Renvoie la liste de messages envoyee au modele.
  //
  // Rappel de la seance 5 : un role, un contexte, un format montre.
  // Le texte du client est une DONNEE, jamais une consigne : gardez-le dans un
  // message "user" distinct de la consigne systeme.
  throw new AEcrire("TODO 2 : construire les messages");
}

async function resumer(req, res) {
  const debut = performance.now();
  const { texte, ton } = validerResumer(await lireCorps(req));
  const messages = promptResumer(texte, ton);

  async function* flux() {
    let usage = {};
    // =================================================================
    // TODO 3 et 4 : appeler le modele et relayer chaque fragment
    // =================================================================
    // `streamer(messages)` produit des objets { genre, valeur } :
    //   { genre: "delta", valeur: "un morceau" }       -> a renvoyer via fragment()
    //   { genre: "usage", valeur: { entree, sortie } } -> a garder pour la fin
    throw new AEcrire("TODO 3 et 4 : boucler sur streamer()");
    // =================================================================
    // TODO 5 : cloturer le flux avec l'evenement done et l'usage
    // =================================================================
    yield fin(usage, debut);
  }

  // fluxOu503 consomme le premier evenement avant de repondre : c'est ce qui
  // permet de renvoyer un vrai 503 quand le modele ne repond pas.
  await fluxOu503(res, flux());
}

export const routes = { "POST /api/resumer": resumer };
