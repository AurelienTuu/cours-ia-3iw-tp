#!/usr/bin/env node
// Banc d'essai de la seance 11 : comparer des modeles sur VOS cas.
//
// Un seul parametre varie : le modele. Le prompt est une constante du script.
// Le faire varier en meme temps rendrait la comparaison inexploitable.
//
//     node tp/11_banc/banc.mjs qwen2.5:3b llama3.2:1b
//     node tp/11_banc/banc.mjs            # utilise la liste par defaut
//
// Jumeau exact de banc.py.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ICI = path.dirname(fileURLToPath(import.meta.url));
const BASE = (process.env.OLLAMA_BASE_URL || "http://localhost:11434").replace(/\/$/, "");
const CAS = JSON.parse(readFileSync(path.join(ICI, "..", "05_prompt", "cas.json"), "utf8"));
const MODELES_PAR_DEFAUT = ["qwen2.5:3b", "llama3.2:1b"];

// Constante du banc : le meme prompt pour tous les modeles, sans exception.
// =====================================================================
// COLLEZ ICI votre meilleure consigne de l'atelier de la seance 5.
// C'est elle qu'on compare d'un modele a l'autre, sans la retoucher.
// =====================================================================
const CONSIGNE = `A REMPLACER`;

/** Un appel en streaming. Renvoie { sortie, ttft, debit }. */
async function mesurer(modele, texte) {
  const depart = performance.now();
  const reponse = await fetch(`${BASE}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: modele,
      temperature: 0,
      max_tokens: 80,
      stream: true,
      stream_options: { include_usage: true },
      messages: [
        { role: "system", content: CONSIGNE },
        { role: "user", content: texte },
      ],
    }),
    signal: AbortSignal.timeout(120000),
  });

  const lecteur = reponse.body.getReader();
  const decodeur = new TextDecoder();
  let tampon = "", sortie = "", ttft = null, tokensSortie = 0;
  for (;;) {
    const { done, value } = await lecteur.read();
    if (done) break;
    tampon += decodeur.decode(value, { stream: true });
    const lignes = tampon.split("\n");
    tampon = lignes.pop();
    for (const ligne of lignes) {
      if (!ligne.startsWith("data: ")) continue;
      const charge = ligne.slice(6).trim();
      if (!charge || charge === "[DONE]") continue;
      const bloc = JSON.parse(charge);
      for (const choix of bloc.choices || []) {
        const morceau = choix.delta?.content;
        if (morceau) {
          if (ttft === null) ttft = performance.now() - depart;
          sortie += morceau;
        }
      }
      if (bloc.usage) tokensSortie = bloc.usage.completion_tokens ?? 0;
    }
  }
  const duree = (performance.now() - depart) / 1000;
  return { sortie, ttft: ttft ?? 0, debit: duree && tokensSortie ? tokensSortie / duree : 0 };
}

function extraireJson(brut) {
  const debut = brut.indexOf("{");
  const fin = brut.lastIndexOf("}");
  if (debut === -1 || fin === -1) return null;
  try {
    return JSON.parse(brut.slice(debut, fin + 1));
  } catch {
    return null;
  }
}

const mediane = (xs) => {
  if (!xs.length) return 0;
  const tries = [...xs].sort((a, b) => a - b);
  const m = Math.floor(tries.length / 2);
  return tries.length % 2 ? tries[m] : (tries[m - 1] + tries[m]) / 2;
};

async function evaluer(modele) {
  const cas = CAS.cas;
  let formes = 0, exacts = 0;
  const ttfts = [], debits = [];
  // Le premier appel inclut le chargement du modele en memoire : on le jette.
  process.stdout.write(`  ${modele} : chauffe...\r`);
  await mesurer(modele, cas[0].texte);

  for (const [index, c] of cas.entries()) {
    process.stdout.write(`  ${modele} : cas ${index + 1}/${cas.length}   \r`);
    let resultat;
    try {
      resultat = await mesurer(modele, c.texte);
    } catch (e) {
      console.log(`\n  ${modele} : echec sur le cas ${index + 1} (${e.message})`);
      continue;
    }
    ttfts.push(resultat.ttft);
    debits.push(resultat.debit);
    const obtenu = extraireJson(resultat.sortie);
    if (obtenu === null) continue;
    formes += 1;
    if (obtenu.categorie === c.categorie && obtenu.urgence === c.urgence) exacts += 1;
  }
  process.stdout.write(" ".repeat(50) + "\r");
  return {
    modele,
    json: Math.floor((100 * formes) / cas.length),
    exact: Math.floor((100 * exacts) / cas.length),
    ttft: mediane(ttfts),
    debit: mediane(debits),
  };
}

if (CONSIGNE.trim() === "A REMPLACER") {
  console.log("Collez d'abord votre meilleure consigne de la seance 5 dans CONSIGNE,");
  console.log("en haut de tp/11_banc/banc.mjs, puis relancez.");
  process.exit(1);
}

const modeles = process.argv.slice(2).length ? process.argv.slice(2) : MODELES_PAR_DEFAUT;
console.log(`Banc d'essai : ${CAS.cas.length} cas, prompt constant, temperature 0\n`);
const resultats = [];
for (const m of modeles) resultats.push(await evaluer(m));

console.log(`  ${"Modele".padEnd(22)} ${"JSON".padStart(6)} ${"Exact".padStart(7)}`
  + ` ${"1er frag.".padStart(11)} ${"Debit".padStart(10)}`);
console.log("  " + "-".repeat(60));
for (const r of resultats) {
  console.log(`  ${r.modele.padEnd(22)} ${String(r.json).padStart(5)}%`
    + ` ${String(r.exact).padStart(6)}% ${r.ttft.toFixed(0).padStart(9)}ms`
    + ` ${r.debit.toFixed(1).padStart(8)}/s`);
}
console.log("\n  Retenez le plus petit modele qui passe vos seuils, pas le meilleur.");
