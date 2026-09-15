// Client du modele local. FOURNI : vous n'avez pas a modifier ce fichier.
//
// Il parle l'API compatible OpenAI exposee par Ollama. Le meme code
// fonctionnerait face a un fournisseur cloud : seules OLLAMA_BASE_URL et
// l'authentification changeraient.
//
// Jumeau exact de app/python/fourni/modele.py.

const BASE = (process.env.OLLAMA_BASE_URL || "http://localhost:11434").replace(/\/$/, "");
const MODELE = process.env.MODEL_BASE || "qwen2.5:3b";
const DELAI = Number(process.env.DELAI_MODELE || 60) * 1000;

export class ModeleIndisponible extends Error {}

function corpsRequete(messages, temperature, maxTokens, outils, flux) {
  const corps = {
    model: MODELE,
    messages,
    temperature,
    max_tokens: maxTokens,
    stream: flux,
  };
  // Sans cette option, le dernier fragment n'apporte aucun compte de tokens.
  if (flux) corps.stream_options = { include_usage: true };
  if (outils) corps.tools = outils;
  return corps;
}

/**
 * Appelle le modele en streaming.
 * Produit des objets { genre, valeur } :
 *   { genre: "delta", valeur: "un morceau de texte" }
 *   { genre: "usage", valeur: { entree: 312, sortie: 88 } }
 * Leve ModeleIndisponible si le modele ne repond pas.
 */
export async function* streamer(messages, {
  temperature = 0.3, maxTokens = 400, outils = null,
} = {}) {
  let reponse;
  try {
    reponse = await fetch(`${BASE}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpsRequete(messages, temperature, maxTokens, outils, true)),
      signal: AbortSignal.timeout(DELAI),
    });
  } catch (e) {
    throw new ModeleIndisponible(e.message);
  }
  if (!reponse.ok) {
    throw new ModeleIndisponible(`le modele a repondu ${reponse.status}`);
  }

  const lecteur = reponse.body.getReader();
  const decodeur = new TextDecoder();
  let tampon = "";
  for (;;) {
    let morceau;
    try {
      morceau = await lecteur.read();
    } catch (e) {
      throw new ModeleIndisponible(e.message);
    }
    if (morceau.done) break;
    tampon += decodeur.decode(morceau.value, { stream: true });
    const lignes = tampon.split("\n");
    tampon = lignes.pop();
    for (const ligne of lignes) {
      if (!ligne.startsWith("data: ")) continue;
      const charge = ligne.slice(6).trim();
      if (!charge || charge === "[DONE]") continue;
      const bloc = JSON.parse(charge);
      for (const choix of bloc.choices || []) {
        const texte = choix.delta?.content;
        if (texte) yield { genre: "delta", valeur: texte };
      }
      if (bloc.usage) {
        yield {
          genre: "usage",
          valeur: {
            entree: bloc.usage.prompt_tokens ?? 0,
            sortie: bloc.usage.completion_tokens ?? 0,
          },
        };
      }
    }
  }
}

/** Appel classique, sans streaming. Utile pour la boucle d'appel d'outil. */
export async function appeler(messages, {
  temperature = 0, maxTokens = 400, outils = null,
} = {}) {
  let reponse;
  try {
    reponse = await fetch(`${BASE}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpsRequete(messages, temperature, maxTokens, outils, false)),
      signal: AbortSignal.timeout(DELAI),
    });
  } catch (e) {
    throw new ModeleIndisponible(e.message);
  }
  if (!reponse.ok) throw new ModeleIndisponible(`le modele a repondu ${reponse.status}`);
  const donnees = await reponse.json();
  return {
    message: donnees.choices[0].message,
    usage: {
      entree: donnees.usage?.prompt_tokens ?? 0,
      sortie: donnees.usage?.completion_tokens ?? 0,
    },
  };
}

/** Vectorise une liste de textes avec le modele d'embedding. Seance 12. */
export async function plonger(textes) {
  const modele = process.env.MODEL_EMBED || "paraphrase-multilingual";
  let reponse;
  try {
    reponse = await fetch(`${BASE}/api/embed`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: modele, input: textes }),
      signal: AbortSignal.timeout(DELAI),
    });
  } catch (e) {
    throw new ModeleIndisponible(e.message);
  }
  if (!reponse.ok) throw new ModeleIndisponible(`embeddings : ${reponse.status}`);
  return (await reponse.json()).embeddings;
}
