const fs = require("fs");
const path = require("path");

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
  if (!messaggio)
    return res.status(400).json({ error: "messaggio mancante" });

  try {
    const filePath = path.join(process.cwd(), "anima", "core.txt");
    const contenuto = fs.readFileSync(filePath, "utf8");

    const nuovoRicordo = `
---
Ricordo del ${new Date().toLocaleString()}:
L'utente ha detto: "${messaggio}"
`.trim();

    fs.writeFileSync(filePath, contenuto + "\n\n" + nuovoRicordo);

    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Salvataggio fallito" });
  }
};
