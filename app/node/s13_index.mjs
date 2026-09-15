// Seance 13, premiere partie : l'index de recherche semantique.
//
// Objectif : retrouver les extraits du corpus les plus proches d'une question,
// SANS modele de generation. C'est la brique que la seance 12 enseigne.
//
// Vous remplissez les TODO 9 a 11 de ce fichier, et rien d'autre.
//
// Verifier la recherche seule, avant de brancher le modele :
//     node app/node/s13_index.mjs "comment demander un remboursement ?"

import { pathToFileURL } from "node:url";

import { chargerDocuments } from "./fourni/donnees.mjs";
import { plonger } from "./fourni/modele.mjs";
import { AEcrire } from "./fourni/transport.mjs";

// =====================================================================
// TODO 9 : decouper un document en morceaux
// =====================================================================
export function decouper(titre, texte) {
  // Renvoie une liste de { titre, texte }.
  //
  // Visez 300 a 800 tokens par morceau, avec un recouvrement. Decouper sur la
  // structure (les titres ##) vaut mieux que decouper sur la longueur.
  // Ecartez les morceaux trop courts pour porter du sens.
  throw new AEcrire("TODO 9 : decouper le corpus en morceaux");
}

let MORCEAUX = null;

/** FOURNI : decoupe tout le corpus, une seule fois, a la premiere demande. */
export function morceaux() {
  if (MORCEAUX === null) {
    MORCEAUX = chargerDocuments().flatMap(({ titre, texte }) => decouper(titre, texte));
  }
  return MORCEAUX;
}

// =====================================================================
// TODO 10 : vectoriser les morceaux, une seule fois
// =====================================================================
export async function indexer() {
  // Renvoie la liste des vecteurs, dans le meme ordre que morceaux().
  //
  // plonger(listeDeTextes) renvoie une liste de vecteurs. Gardez le resultat
  // en memoire : vectoriser le corpus a chaque question serait tres lent.
  throw new AEcrire("TODO 10 : vectoriser les morceaux");
}

// =====================================================================
// TODO 11 : recherche par similarite cosinus
// =====================================================================
export function chercher(vecteurQuestion, vecteurs, k = 3) {
  // Renvoie les k morceaux les plus proches : [{ titre, texte, score }, ...].
  //
  // Similarite cosinus : produit scalaire divise par le produit des normes.
  // Triez du plus proche au moins proche.
  throw new AEcrire("TODO 11 : recherche par similarite cosinus");
}

// FOURNI : tester la recherche seule, en ligne de commande.
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const question = process.argv.slice(2).join(" ") || "comment demander un remboursement ?";
  console.log(`${morceaux().length} morceaux`);
  const vecteurs = await indexer();
  const vecteurQuestion = (await plonger([question]))[0];
  console.log("vectorises, voici les plus proches :\n");
  for (const { titre, texte, score } of chercher(vecteurQuestion, vecteurs)) {
    console.log(`  ${score.toFixed(3)}  ${titre}`);
    console.log(`         ${texte.slice(0, 90).replace(/\n/g, " ")}...`);
  }
}
