const fs = require("fs");
const path = require("path");

const ORIGIN = "https://www.alexsjsju.eu/alexai";

function setCorsHeaders(res) {
  res.setHeader("Access-Control-Allow-Origin", ORIGIN);
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
}

module.exports = async (req, res) => {
  setCorsHeaders(res);

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  const animaPath = path.join(process.cwd(), "anima", "core.txt");

  if (req.method === "GET") {
    try {
      const contenuto = fs.readFileSync(animaPath, "utf8");
      return res.status(200).json({ ok: true, anima: contenuto });
    } catch (err) {
      console.error(err);
      return res.status(500).json({ error: "Errore nella lettura dell'anima" });
    }
  }

  if (req.method === "POST") {
    try {
      const body = await new Promise(resolve => {
        let data = "";
        req.on("data", chunk => data += chunk);
        req.on("end", () => resolve(JSON.parse(data || "{}")));
      });

      const messaggio = body.messaggio?.trim();
      if (!messaggio) {
        return res.status(400).json({ error: "messaggio mancante" });
      }

      const contenuto = fs.readFileSync(animaPath, "utf8");

      const nuovoRicordo = `
---
Ricordo del ${new Date().toLocaleString()}:
${messaggio}
`.trim();

      fs.writeFileSync(animaPath, contenuto + "\n\n" + nuovoRicordo);

      return res.status(200).json({ ok: true, ricordo: nuovoRicordo });
    } catch (err) {
      console.error(err);
      return res.status(500).json({ error: "Errore nel salvataggio dell'anima" });
    }
  }

  return res.status(405).json({ error: "Metodo non consentito" });
};
