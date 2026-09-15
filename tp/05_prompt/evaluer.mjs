#!/usr/bin/env node
// Atelier de la seance 5 : mesurer un prompt de classification.
//
// Vous ne modifiez QUE la constante CONSIGNE. Tout le reste est l'instrument de
// mesure : y toucher fausserait la comparaison.
//
//     node tp/05_prompt/evaluer.mjs
//
// Jumeau exact de evaluer.py : meme jeu de cas, meme score.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ICI = path.dirname(fileURLToPath(import.meta.url));
const BASE = (process.env.OLLAMA_BASE_URL || "http://localhost:11434").replace(/\/$/, "");
const MODELE = process.env.MODEL_BASE || "qwen2.5:3b";
const CAS = JSON.parse(readFileSync(path.join(ICI, "cas.json"), "utf8"));

// =====================================================================
// LA SEULE CHOSE QUE VOUS MODIFIEZ
// =====================================================================
const CONSIGNE = `Classe le ticket de support.`;
// =====================================================================

async function classer(texte) {
  const reponse = await fetch(`${BASE}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: MODELE,
      temperature: 0,
      max_tokens: 80,
      messages: [
        { role: "system", content: CONSIGNE },
        { role: "user", content: texte },
      ],
    }),
    signal: AbortSignal.timeout(60000),
  });
  const brut = (await reponse.json()).choices[0].message.content;
  const debut = brut.indexOf("{");
  const fin = brut.lastIndexOf("}");
  if (debut === -1 || fin === -1) return null;
  try {
    return JSON.parse(brut.slice(debut, fin + 1));
  } catch {
    return null;
  }
}

const total = CAS.cas.length;
let formes = 0, categories = 0, urgences = 0;
console.log(`modele : ${MODELE}   cas : ${total}\n`);

for (const [index, cas] of CAS.cas.entries()) {
  const numero = String(index + 1).padStart(2, " ");
  const obtenu = await classer(cas.texte);
  if (obtenu === null) {
    console.log(`  ${numero}. JSON illisible          <- ${cas.texte.slice(0, 44)}`);
    continue;
  }
  formes += 1;
  const bonneCategorie = obtenu.categorie === cas.categorie;
  const bonneUrgence = obtenu.urgence === cas.urgence;
  categories += bonneCategorie ? 1 : 0;
  urgences += bonneUrgence ? 1 : 0;
  const marque = bonneCategorie && bonneUrgence ? "ok " : "   ";
  console.log(`  ${numero}. ${marque} attendu ${cas.categorie}/${cas.urgence}`
    + `  obtenu ${obtenu.categorie}/${obtenu.urgence}`);
}

const pct = (n) => Math.floor((100 * n) / total);
console.log(`\n  JSON valide  : ${formes}/${total}  (${pct(formes)} %)`);
console.log(`  Categorie    : ${categories}/${total}  (${pct(categories)} %)`);
console.log(`  Urgence      : ${urgences}/${total}  (${pct(urgences)} %)`);
console.log("\nNotez ce score, modifiez CONSIGNE, relancez. Gardez la trace de "
  + "chaque version : elle est demandee au CC2.");
