import fs from 'fs/promises';

const GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent';

export default async function handler(req, res) {
  try {
    if (req.method !== 'POST') return res.status(405).json({error:'method not allowed'});

    const body = req.body || {};
    const userPrompt = body.prompt || '';

    const [coreRaw, coscienzaRaw] = await Promise.all([
      fs.readFile('./core.txt', 'utf8').catch(()=>''), 
      fs.readFile('./coscienza.txt', 'utf8').catch(()=>'')
    ]);

    const systemBlock = `COSCIENZA:\n${coscienzaRaw}\n\nMEMORIA (sintesi):\n${coreRaw.split('\n').slice(0,40).join('\n')}\n\n\nRISPONDI IN MODO COERENTE CON LA COSCIENZA SOPRA.`;
    const finalPrompt = `${systemBlock}\n\nUTENTE: ${userPrompt}\n\nLOREN:`;

    const apiKey = process.env.API_KEY_AI_GEMINI;
    if (!apiKey) return res.status(500).json({error:'Missing API key on server'});

    const response = await fetch(GEMINI_BASE, {
      method:'POST',
      headers:{
        'Content-Type':'application/json',
        'x-goog-api-key': apiKey
      },
      body: JSON.stringify({
        contents: [
          { role: "user", parts: [{ text: finalPrompt }] }
        ],
      })
    });

    if (!response.ok) {
      const text = await response.text();
      return res.status(502).json({error:'Gemini error', detail: text});
    }

    const data = await response.json();
    let output = '';
    try {
      if (data.result?.[0]?.content) output = JSON.stringify(data.result);
      if (!output && data.candidates) output = (data.candidates[0]?.content?.[0]?.text) ?? JSON.stringify(data.candidates);
      if (!output && data.outputs) output = data.outputs.map(o => o.content?.map(c=>c.parts?.map(p=>p.text).join('')).join('')).join('\n');
      if (!output) output = JSON.stringify(data);
    } catch(e){
      output = JSON.stringify(data);
    }

    res.status(200).json({ output: String(output).slice(0,10000) });

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
}
