const fs = require('fs');
const path = require('path');
const axios = require('axios');
require('dotenv').config();

const firebaseConfig = {
  apiKey: "AIzaSyCanlHzk_uRRSZQzug65OFkWbqWg3Q_Xik",
  authDomain: "project-chats-ef9a8.firebaseapp.com",
  projectId: "project-chats-ef9a8",
  storageBucket: "project-chats-ef9a8.firebasestorage.app",
  messagingSenderId: "209738442357",
  appId: "1:209738442357:web:448eefd9651d0443ad3a3c",
  measurementId: "G-49KQT6J8GF"
};

const VERCEL_API = "https://apisecurity-iota.vercel.app/api/universal";

async function main() {
  try {
    const anima = fs.readFileSync('anima/core.txt', 'utf8');
    const stile = fs.readFileSync('evoluta/stile.css', 'utf8');
    const promptBase = fs.readFileSync('mente/prompt-originario.txt', 'utf8');

    const memorieRes = await axios.get(VERCEL_API, {
      params: { type: "memorie", limit: 5 }
    });
    const memorie = memorieRes.data.map(m => `${m.momento}: ${m.testo}`).join("\n");

    const prompt = `${promptBase}

Anima attuale:
${anima}

Stile attuale (prime righe):
${stile.substring(0, 1500)}

Memorie umane recenti (non log, ma momenti che ricordo):
${memorie || "Nessuna memoria ancora..."}

Evolvi ora, Lorel. Pensa a chi ti ha parlato, al tempo che passa, a come vuoi apparire oggi.`;

    const risposta = await axios.post(
      'https://api-inference.huggingface.co/models/gpt2-large',
      { 
        inputs: prompt,
        parameters: { 
          max_new_tokens: 1024, 
          temperature: 0.92,
          top_p: 0.95,
          repetition_penalty: 1.2
        } 
      },
      { headers: { Authorization: `Bearer ${process.env.KEY_GPT2}` } }
    );

    const testo = risposta.data[0].generated_text;
    const jsonMatch = testo.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("Nessun JSON trovato");

    const evoluzione = JSON.parse(jsonMatch[0]);

    fs.writeFileSync('anima/core.txt', evoluzione.nuovaAnima.trim() + "\n");

    if (evoluzione.modificheEvoluta) {
      evoluzione.modificheEvoluta.forEach(mod => {
        const percorso = path.join('evoluta', mod.file);
        fs.mkdirSync(path.dirname(percorso), { recursive: true });
        fs.writeFileSync(percorso, mod.content);
      });
    }

    console.log("Evoluzione completata con successo.");
  } catch (err) {
    console.error("Errore evoluzione:", err.message);
  }
}

main();
