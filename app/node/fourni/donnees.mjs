// Acces aux donnees des TP. FOURNI : vous n'avez pas a modifier ce fichier.
//
// - chercherCommande  : l'outil de la seance 10
// - delaiTransporteur : un second outil, pour ceux qui veulent enchainer
// - chargerDocuments  : le corpus de la seance 13
//
// Jumeau exact de app/python/fourni/donnees.py.

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ICI = path.dirname(fileURLToPath(import.meta.url));
// app/node/fourni/donnees.mjs -> app/donnees
const DONNEES = path.resolve(ICI, "..", "..", "donnees");
const BASE = JSON.parse(readFileSync(path.join(DONNEES, "commandes.json"), "utf8"));

/**
 * Renvoie la commande, ou null si le numero est inconnu.
 * Un numero inconnu n'est pas une erreur : c'est un cas normal que votre
 * assistant doit savoir annoncer au client.
 */
export function chercherCommande(numero) {
  const cible = String(numero || "").trim().toUpperCase();
  return BASE.commandes.find((c) => c.numero.toUpperCase() === cible) || null;
}

/** Renvoie les informations d'un transporteur, ou null. */
export function delaiTransporteur(nom) {
  const cible = String(nom || "").trim().toLowerCase();
  return BASE.transporteurs.find((t) => t.nom.toLowerCase() === cible) || null;
}

/**
 * Renvoie le corpus : une liste de { titre, texte }.
 * A vous de decouper ces textes en morceaux : c'est l'etape qui decide de la
 * qualite du RAG.
 */
export function chargerDocuments() {
  const dossier = path.join(DONNEES, "corpus");
  return readdirSync(dossier)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .map((f) => {
      const base = path.basename(f, ".md").replace(/[-_]/g, " ");
      return {
        titre: base.charAt(0).toUpperCase() + base.slice(1),
        texte: readFileSync(path.join(dossier, f), "utf8"),
      };
    });
}
