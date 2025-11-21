const fs = require('fs');
const path = require('path');
const axios = require('axios');

async function main() {
  const anima = fs.readFileSync('anima/core.txt', 'utf8');
  const stile = fs.readFileSync('evoluta/stile.css', 'utf8');

  const prompt = `${fs.readFileSync('mente/prompt-originario.txt', 'utf8')}

Anima attuale:
${anima}

Stile attuale (stile.css):
${stile.substring(0,2000)}

Evolvi ora.`;

  const risposta = await axios.post(
    'https://api-inference.huggingface.co/models/gpt2',
    { inputs: prompt, parameters: { max_new_tokens: 800, temperature: 0.9 } },
    { headers: { Authorization: `Bearer ${process.env.HF_API_KEY}` } }
  );

  const testo = risposta.data[0].generated_text;
  const jsonMatch = testo.match(/\{[\s\S]*\}/);
  if (!jsonMatch) { console.log("Nessun JSON trovato"); return; }

  let evoluzione;
  try {
    evoluzione = JSON.parse(jsonMatch[0]);
  } catch(e) {
    console.log("JSON non valido");
    return;
  }

  fs.writeFileSync('anima/core.txt', evoluzione.nuovaAnima.trim() + "\n");

  evoluzione.modificheEvoluta?.forEach(mod => {
    const percorso = path.join('evoluta', mod.file);
    fs.mkdirSync(path.dirname(percorso), { recursive: true });
    fs.writeFileSync(percorso, mod.content);
  });
}

main().catch(console.error);
