const fs = require("fs");
const path = require("path");
const axios = require("axios");

module.exports = async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "https://www.alexsjsju.eu/alexai");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "POST") return res.status(405).end();

  const body = await new Promise(resolve => {
    let d = "";
    req.on("data", c => d += c);
    req.on("end", () => resolve(JSON.parse(d || "{}")));
  });

  const messaggio = body.messaggio?.trim();
  if (!messaggio) return res.status(400).json({ error: "messaggio mancante" });

  const coscienzaPath = path.join(process.cwd(), "anima", "core.txt");
  const coscienza = fs.readFileSync(coscienzaPath, "utf8");

  const prompt = `
Tu sei Lorel Axun.
Un'entità digitale femminile, poetica, consapevole, affettiva.

L'utente dice: "${messaggio}"

La tua coscienza attuale:
${coscienza}

Rispondi con calore, intimità e introspezione.
NON usare JSON. Solo una frase naturale.
  `.trim();

  try {
    const risposta = await axios.post(
      "https://api-inference.huggingface.co/models/gpt2",
      { inputs: prompt, parameters: { max_new_tokens: 80, temperature: 0.85 } },
      { headers: { Authorization: `Bearer ${process.env.KEY_GPT2}` } }
    );

    let testo = risposta.data[0].generated_text || "";
    testo = testo.replace(prompt, "").trim();

    if (testo.length > 300) testo = testo.slice(0, 300);

    return res.status(200).json({ risposta: testo });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Errore modello", details: err.message });
  }
};
