// Point d'entree du serveur, voie JavaScript. FOURNI : ne le modifiez pas.
//
// Il assemble les routes des trois seances et sert le front. Votre travail est
// dans les fichiers de seance :
//
//     s09_resumer.mjs      seance 9   TODO 1 a 5
//     s10_assistant.mjs    seance 10  TODO 6 a 8
//     s13_index.mjs        seance 13  TODO 9 a 11
//     s13_documents.mjs    seance 13  TODO 12
//
// Lancement, depuis la racine du depot :
//     make app-node

import { createServer } from "node:http";

import { creerServeur } from "./fourni/transport.mjs";
import { routes as resumer } from "./s09_resumer.mjs";
import { routes as assistant } from "./s10_assistant.mjs";
import { routes as documents } from "./s13_documents.mjs";

const PORT = Number(process.env.PORT || 3000);

createServer(creerServeur({ ...resumer, ...assistant, ...documents }))
  .listen(PORT, () => console.log(`serveur pret sur http://localhost:${PORT}`));
