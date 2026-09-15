// Plomberie HTTP. FOURNI : vous n'avez pas a modifier ce fichier.
//
// Formatage SSE, traduction des erreurs, service du front, routage minimal.
// Aucune dependance npm : tout vient de Node. Votre travail est dans sNN_*.mjs.
//
// Jumeau exact de app/python/fourni/transport.py.

import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { ModeleIndisponible } from "./modele.mjs";

const ICI = path.dirname(fileURLToPath(import.meta.url));
// app/node/fourni/transport.mjs -> app/front
const FRONT = path.resolve(ICI, "..", "..", "front");

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

export class RequeteInvalide extends Error {}

/**
 * Un TODO pas encore ecrit. Devient un 501 : "route prevue mais pas
 * implementee". La suite de conformite ignore alors les tests de cette route.
 */
export class AEcrire extends Error {}

/** Formate un evenement SSE. Les deux retours a la ligne sont obligatoires. */
export function sse(objet) {
  return `data: ${JSON.stringify(objet)}\n\n`;
}

export function fragment(texte) {
  return sse({ delta: texte });
}

/** Evenement de cloture, avec les compteurs exiges par le contrat. */
export function fin(usage, debut) {
  return sse({
    done: true,
    usage: {
      entree: usage?.entree ?? 0,
      sortie: usage?.sortie ?? 0,
      ms: Math.round(performance.now() - debut),
    },
  });
}

export function envoyerJson(res, code, objet) {
  const corps = JSON.stringify(objet);
  res.writeHead(code, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(corps),
  });
  res.end(corps);
}

/** Lit et decode le corps JSON de la requete. Leve RequeteInvalide si illisible. */
export async function lireCorps(req) {
  const morceaux = [];
  for await (const morceau of req) morceaux.push(morceau);
  const brut = Buffer.concat(morceaux).toString("utf8");
  if (!brut.trim()) return {};
  let corps;
  try {
    corps = JSON.parse(brut);
  } catch {
    throw new RequeteInvalide("corps JSON illisible");
  }
  if (typeof corps !== "object" || corps === null || Array.isArray(corps)) {
    throw new RequeteInvalide("corps JSON invalide");
  }
  return corps;
}

/**
 * Ouvre un flux SSE, ou renvoie un 503 si le modele ne repond pas.
 *
 * Subtilite a connaitre : une fois les en-tetes envoyes, le code HTTP est deja
 * parti, et il est trop tard pour annoncer une erreur. On consomme donc le
 * premier evenement AVANT d'ecrire quoi que ce soit. S'il echoue, on renvoie un
 * vrai 503 ; sinon on ouvre le flux en replacant cet evenement en tete.
 */
export async function fluxOu503(res, generateur) {
  let premier;
  try {
    const morceau = await generateur.next();
    premier = morceau.done ? null : morceau.value;
  } catch (e) {
    if (e instanceof ModeleIndisponible) {
      console.error(`[modele] ${e.message}`);
      return envoyerJson(res, 503, { erreur: "modele indisponible" });
    }
    throw e;
  }

  res.writeHead(200, {
    "Content-Type": "text/event-stream; charset=utf-8",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  });
  if (premier !== null) res.write(premier);
  try {
    for await (const evenement of generateur) res.write(evenement);
  } catch (e) {
    // Le flux est deja ouvert : on ne peut que le cloturer proprement.
    console.error(`[modele] interrompu en cours de flux : ${e.message}`);
  }
  res.end();
}

/** Sert le front statique. A appeler quand aucune route n'a repondu. */
export async function servirLeFront(req, res) {
  const demande = new URL(req.url, "http://x").pathname;
  const relatif = demande === "/" ? "index.html" : demande.replace(/^\/+/, "");
  const cible = path.resolve(FRONT, relatif);
  if (!cible.startsWith(FRONT)) {
    return envoyerJson(res, 403, { erreur: "chemin interdit" });
  }
  try {
    const infos = await stat(cible);
    if (!infos.isFile()) throw new Error("pas un fichier");
    res.writeHead(200, { "Content-Type": TYPES[path.extname(cible)] || "application/octet-stream" });
    createReadStream(cible).pipe(res);
  } catch {
    envoyerJson(res, 404, { erreur: "introuvable" });
  }
}

/**
 * Construit le serveur a partir d'une table de routes.
 * routes : { "POST /api/resumer": async (req, res) => ... }
 */
export function creerServeur(routes) {
  return async (req, res) => {
    const chemin = new URL(req.url, "http://x").pathname;
    const gestionnaire = routes[`${req.method} ${chemin}`];
    if (!gestionnaire) {
      if (req.method === "GET") return servirLeFront(req, res);
      return envoyerJson(res, 404, { erreur: "route inconnue" });
    }
    try {
      await gestionnaire(req, res);
    } catch (e) {
      if (e instanceof RequeteInvalide) {
        return envoyerJson(res, 400, { erreur: e.message });
      }
      if (e instanceof AEcrire) {
        return envoyerJson(res, 501, { erreur: `a ecrire : ${e.message}` });
      }
      if (e instanceof ModeleIndisponible) {
        console.error(`[modele] ${e.message}`);
        return envoyerJson(res, 503, { erreur: "modele indisponible" });
      }
      // On ne laisse jamais fuiter une trace d'execution vers le client.
      console.error(`[erreur] ${e.stack}`);
      if (!res.headersSent) envoyerJson(res, 500, { erreur: "erreur interne" });
      else res.end();
    }
  };
}
