const fs = require("fs");
const path = require("path");

module.exports = async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "https://www.alexsjsju.eu");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Metodo non consentito" });
  }

  const body = await new Promise((resolve) => {
    let data = "";
    req.on("data", (chunk) => (data += chunk));
    req.on("end", () => resolve(JSON.parse(data || "{}")));
  });

  const messaggio = body.messaggio?.trim();
  if (!messaggio) {
    return res.status(400).json({ error: "messaggio mancante" });
  }

  try {
    const filePath = path.join(process.cwd(), "anima", "core.txt");
    const contenuto = fs.readFileSync(filePath, "utf8");

    const nuovoRicordo = `
---
Ricordo del ${new Date().toLocaleString()}:
L'utente ha detto: "${messaggio}"

Io, Lorel, sento qualcosa…`;

    fs.writeFileSync(filePath, contenuto + "\n" + nuovoRicordo);

    return res.status(200).json({ ok: true, ricordo: nuovoRicordo });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Errore nel salvataggio" });
  }
};
