export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "https://www.alexsjsju.eu");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  
  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Use POST" });
  }

  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: "Missing message" });
    }

    const apiKey = process.env.API_KEY_AI_GEMINI;
    if (!apiKey) {
      return res.status(500).json({ error: "Missing API_KEY_AI_GEMINI" });
    }

    const response = await fetch(
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + apiKey,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [
            { role: "user", parts: [{ text: message }] }
          ]
        })
      }
    );

    const data = await response.json();

function extractGeminiReply(data) {
  if (!data?.candidates?.length) return null;

  const c = data.candidates[0];

  if (c.content?.parts?.[0]?.text) {
    return c.content.parts[0].text;
  }

  if (Array.isArray(c.content) && c.content[0]?.parts?.[0]?.text) {
    return c.content[0].parts[0].text;
  }

  return null;
}

const reply = extractGeminiReply(data) || "[no reply]";

return res.status(200).json({ reply });

  } catch (err) {
    return res.status(500).json({ error: "Server error", detail: err.message });
  }
}
