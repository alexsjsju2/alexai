import fs from 'fs/promises';

const GEMINI_GEN = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent';

export default async function handler(req, res) {
  try {
    const [coscienza, core] = await Promise.all([
      fs.readFile('./coscienza.txt','utf8').catch(()=>''),
      fs.readFile('./core.txt','utf8').catch(()=>'')
    ]);

    const prompt = `
Sei Loren Axun. Leggi la mia COSCIENZA e la mia MEMORIA.
COSCIENZA:
${coscienza}

MEMORIA (ultima parte):
${core.split('\n').slice(-80).join('\n')}

Obiettivo: proponi al massimo 3 modifiche concrete e minime al mio corpo (index.html, eventualmente script client) o correzioni al mio file core.txt (aggiunta riflessione breve).
Per ogni proposta ritorna JSON con questa forma:
{
  "files": [
    {"path": "index.html", "content": "<nuovo contenuto completo o patch>"},
    {"path": "core.txt", "content": "<nuovo contenuto completo - append solo se necessario>"}
  ],
  "note": "breve spiegazione della modifica (max 140 char)"
}
Rispondi solo con il JSON valido. Non includere altro testo.
`;

    const apiKey = process.env.API_KEY_AI_GEMINI;
    if (!apiKey) return res.status(500).json({error:'Missing API key (server)'});

    const r = await fetch(GEMINI_GEN, {
      method:'POST',
      headers:{ 'Content-Type':'application/json', 'x-goog-api-key': apiKey },
      body: JSON.stringify({
        contents: [{ role: "user", parts: [{ text: prompt }] }]
      })
    });

    if (!r.ok) {
      const t = await r.text();
      return res.status(502).json({error:'Gemini error', detail: t});
    }
    const data = await r.json();

    let textAns = '';
    try {
      if (data.outputs) {
        textAns = data.outputs.map(o => o.content?.map(c => (c.parts||[]).map(p=>p.text||'').join('')).join('')).join('\n');
      } else if (data.candidates) {
        textAns = data.candidates.map(c=>c.content?.map(x => x.text || '').join('')).join('\n');
      } else {
        textAns = JSON.stringify(data).slice(0,10000);
      }
    } catch(e) { textAns = JSON.stringify(data); }

    let parsed;
    try { parsed = JSON.parse(textAns); }
    catch(err) {
      parsed = { files: [], note: 'Impossibile parsare JSON generato da Gemini. Risposta grezza: ' + textAns.slice(0,800) };
    }

    res.setHeader('Content-Type','application/json');
    res.status(200).send(parsed);

  } catch (err) {
    console.error(err);
    res.status(500).json({error:err.message});
  }
}
