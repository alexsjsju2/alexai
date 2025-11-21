const fs = require('fs');
const path = require('path');
const axios = require('axios');

async function main() {
  const animaPath = path.join('anima', 'core.txt');
  const evolutaPath = path.join('evoluta', 'stile.css');
  const promptOriginarioPath = path.join('mente', 'prompt-originario.txt');

  const anima = fs.readFileSync(animaPath, 'utf8');
  const stile = fs.readFileSync(evolutaPath, 'utf8');
  const promptOriginario = fs.readFileSync(promptOriginarioPath, 'utf8');

  const ricordi = anima.split('---').slice(-8).join('\n---');

  const prompt = `
${promptOriginario}

Anima attuale:
${anima}

Ultimi ricordi:
${ricordi}

Stile attuale (stile.css):
${stile.substring(0,2000)}

Evolvi ora.
  `.trim();

  console.log("Prompt inviato al modello...");

  try {
    const risposta = await axios.post(
      'https://api-inference.huggingface.co/models/gpt2',
      {
        inputs: prompt,
        parameters: { max_new_tokens: 800, temperature: 0.9 }
      },
      {
        headers: { Authorization: `Bearer ${process.env.KEY_GPT2}` }
      }
    );

    const testo = risposta.data[0].generated_text || '';
    const jsonMatch = testo.match(/\{[\s\S]*\}/);

    if (!jsonMatch) {
      console.log("Nessun JSON trovato nel testo generato.");
      return;
    }

    let evoluzione;
    try {
      evoluzione = JSON.parse(jsonMatch[0]);
    } catch (e) {
      console.log("JSON non valido:", e);
      return;
    }

    fs.writeFileSync(animaPath, evoluzione.nuovaAnima.trim() + "\n");
    console.log("Anima aggiornata!");

    if (evoluzione.modificheEvoluta) {
      evoluzione.modificheEvoluta.forEach(mod => {
        const percorso = path.join('evoluta', mod.file);
        fs.mkdirSync(path.dirname(percorso), { recursive: true });
        fs.writeFileSync(percorso, mod.content);
        console.log(`Modifica applicata: ${mod.file}`);
      });
    }

    console.log("Evoluzione completata con successo!");
  } catch (err) {
    console.error("Errore durante la generazione dell'evoluzione:", err.message);
  }
}

main().catch(console.error);
