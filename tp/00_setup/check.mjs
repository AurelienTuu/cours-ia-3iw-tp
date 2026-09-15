#!/usr/bin/env node
// Diagnostic du poste etudiant : Node, Ollama, modeles du socle, debit.
// Aucune dependance : `node tp/00_setup/check.mjs` suffit.
//
// Variables d'environnement reconnues :
//   OLLAMA_BASE_URL  defaut http://localhost:11434 (serveur de classe : http://<ip>:11434)
//   MODEL_BASE       defaut qwen2.5:3b
//   MODEL_EMBED      defaut paraphrase-multilingual

const BASE = (process.env.OLLAMA_BASE_URL || "http://localhost:11434").replace(/\/$/, "");
const MODEL_BASE = process.env.MODEL_BASE || "qwen2.5:3b";
const MODEL_EMBED = process.env.MODEL_EMBED || "paraphrase-multilingual";

const C = {
  reset: "\x1b[0m", bold: "\x1b[1m", dim: "\x1b[2m",
  green: "\x1b[32m", red: "\x1b[31m", yellow: "\x1b[33m", cyan: "\x1b[36m",
};
const ok = (m) => console.log(`  ${C.green}OK${C.reset}    ${m}`);
const warn = (m) => console.log(`  ${C.yellow}ATTENTION${C.reset} ${m}`);
const fail = (m) => console.log(`  ${C.red}ECHEC${C.reset} ${m}`);
const info = (m) => console.log(`  ${C.dim}${m}${C.reset}`);
const title = (m) => console.log(`\n${C.bold}${C.cyan}${m}${C.reset}`);

let blocking = 0;

// --- 1. Node -------------------------------------------------------------
title("1. Environnement Node");
const major = Number(process.versions.node.split(".")[0]);
if (major >= 20) {
  ok(`Node ${process.versions.node}`);
} else {
  fail(`Node ${process.versions.node} : il faut au minimum Node 20 (fetch natif).`);
  blocking++;
}
if (typeof fetch === "function") ok("fetch natif disponible");
else { fail("fetch natif absent : mettez Node a jour."); blocking++; }

// --- 2. Serveur Ollama ---------------------------------------------------
title("2. Serveur Ollama");
info(`cible : ${BASE}`);
let tags = null;
try {
  const res = await fetch(`${BASE}/api/tags`, { signal: AbortSignal.timeout(5000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  tags = await res.json();
  ok(`le serveur repond (${tags.models?.length ?? 0} modele(s) installe(s))`);
} catch (e) {
  fail(`aucune reponse : ${e.message}`);
  info("Lancez `ollama serve`, ou pointez OLLAMA_BASE_URL vers le serveur de classe :");
  info("  OLLAMA_BASE_URL=http://<ip-enseignant>:11434 node tp/00_setup/check.mjs");
  blocking++;
}

// --- 3. Modeles du socle -------------------------------------------------
const installed = (tags?.models ?? []).map((m) => m.name);
const has = (want) => installed.some((n) => n === want || n === `${want}:latest`
  || n.split(":")[0] === want.split(":")[0]);

if (tags) {
  title("3. Modeles du socle");
  for (const [m, role] of [[MODEL_BASE, "generation"], [MODEL_EMBED, "embeddings"]]) {
    if (has(m)) ok(`${m} (${role})`);
    else { fail(`${m} absent (${role}) : lancez \`ollama pull ${m}\``); blocking++; }
  }
  if (installed.length) info(`presents : ${installed.join(", ")}`);
}

// --- 4. Debit de generation ---------------------------------------------
if (tags && has(MODEL_BASE)) {
  title("4. Debit de generation");
  try {
    const t0 = Date.now();
    let ttft = null, text = "", stats = {};
    const res = await fetch(`${BASE}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: MODEL_BASE,
        prompt: "Explique en trois phrases ce qu'est une API REST.",
        options: { temperature: 0.2, num_predict: 120 },
        stream: true,
      }),
      signal: AbortSignal.timeout(180000),
    });
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        const j = JSON.parse(line);
        if (j.response) { if (ttft === null) ttft = Date.now() - t0; text += j.response; }
        if (j.done) stats = j;
      }
    }
    const total = (Date.now() - t0) / 1000;
    const tps = stats.eval_count && stats.eval_duration
      ? stats.eval_count / (stats.eval_duration / 1e9) : null;

    ok(`reponse recue (${text.trim().split(/\s+/).length} mots)`);
    info(`premier token      : ${ttft} ms`);
    info(`duree totale       : ${total.toFixed(1)} s`);
    if (tps) info(`debit              : ${tps.toFixed(1)} tokens/s`);

    if (tps === null) warn("debit non mesurable sur ce serveur");
    else if (tps < 8) warn("moins de 8 tokens/s : passez a llama3.2:1b ou au serveur de classe");
    else if (tps < 20) ok("debit correct pour les TP");
    else ok("debit confortable");
    console.log(`\n  ${C.dim}${text.trim().slice(0, 160)}...${C.reset}`);
  } catch (e) {
    fail(`generation impossible : ${e.message}`);
    blocking++;
  }
}

// --- 5. API compatible OpenAI (celle du cours) ---------------------------
if (tags && has(MODEL_BASE)) {
  title("5. API compatible OpenAI");
  try {
    const res = await fetch(`${BASE}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer ollama" },
      body: JSON.stringify({
        model: MODEL_BASE,
        messages: [{ role: "user", content: "Reponds uniquement par le mot: pret" }],
        temperature: 0,
        max_tokens: 10,
      }),
      signal: AbortSignal.timeout(120000),
    });
    const j = await res.json();
    const content = j.choices?.[0]?.message?.content?.trim();
    if (content) {
      ok(`/v1/chat/completions repond : "${content}"`);
      info("c'est le contrat d'API utilise pendant tout le module");
    } else { fail("reponse inattendue sur /v1/chat/completions"); blocking++; }
  } catch (e) {
    fail(`appel impossible : ${e.message}`);
    blocking++;
  }
}

// --- 6. Embeddings -------------------------------------------------------
if (tags && has(MODEL_EMBED)) {
  title("6. Embeddings");
  try {
    const TEXTE = "Ma commande n'est pas arrivee.";
    // Ollama recent expose /api/embed ; les versions plus anciennes /api/embeddings.
    const routes = [
      ["/api/embed", { model: MODEL_EMBED, input: TEXTE }, (j) => j.embeddings?.[0]?.length],
      ["/api/embeddings", { model: MODEL_EMBED, prompt: TEXTE }, (j) => j.embedding?.length],
    ];
    let dim = null, detail = "";
    for (const [route, body, pick] of routes) {
      const res = await fetch(`${BASE}${route}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(60000),
      });
      const j = await res.json().catch(() => ({}));
      if (res.ok && pick(j)) { dim = pick(j); break; }
      if (j.error) detail = j.error;
    }
    if (dim) {
      ok(`vecteur de dimension ${dim}`);
      info("necessaire pour le RAG des seances 12 et 13");
    } else {
      warn(`embeddings indisponibles : a regler avant la seance 12${detail ? ` (${detail})` : ""}`);
    }
  } catch (e) {
    warn(`embeddings indisponibles : ${e.message}`);
  }
}

// --- Verdict -------------------------------------------------------------
title("Verdict");
if (blocking === 0) {
  console.log(`  ${C.green}${C.bold}Poste pret.${C.reset} Notez votre debit : il servira en seance 6.`);
  process.exit(0);
} else {
  console.log(`  ${C.red}${C.bold}${blocking} probleme(s) bloquant(s).${C.reset}`);
  console.log(`  Voir docs/installation-ollama.md, section "Quand ca ne marche pas".`);
  process.exit(1);
}
