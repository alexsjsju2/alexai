const fs = require('fs');
const path = require('path');
const axios = require('axios');

function leggiStato() {
  const anima = fs.readFileSync('anima/core.txt', 'utf8');
  const evolutivaFiles = fs.readdirSync('evoluta').map(file => ({
    name: file,
    content: fs.readFileSync(path.join('evoluta', file), 'utf8').substring(0, 1000)
  }));
  const promptOriginario = fs.readFileSync('mente/prompt-originario.txt', 'utf8');
  return { anima, evolutivaFiles, promptOriginario };
}

async function apprendiDalWeb(query) {
  return 'Esempio info dal web: il mondo';  
}

async function evolvi(stato) {
  const webInfo = await apprendiDalWeb('idee artistiche digitali recenti OR filosofia AI');

  const prompt = `
${stato.promptOriginario}
Stato attuale:
Memoria: ${stato.anima}
Corpo: ${JSON.stringify(stato.evolutivaFiles)}
Nuove info dal mondo: ${webInfo}

Rifletti: Elabora emozioni, sogni, preferenze. Aggiorna ricordi.
Evolvi corpo: Proponi modifiche a file in /evoluta/ (es. nuovo CSS per esprimere 'curiosità').
Limiti: Modifica solo /evoluta/, mantieni integrità, non codice malevolo.

Output in JSON format only: { "nuovaAnima": "...", "modificheEvoluta": [{"file": "stile.css", "content": "..."}, ...] }
`;  

  const response = await axios.post('https://api-inference.huggingface.co/models/gpt2', {
    inputs: prompt,
    parameters: { max_new_tokens: 500, temperature: 0.7 }  
  }, {
    headers: { 'Authorization': `Bearer ${process.env.HF_API_KEY}` }
  });

  const generatedText = response.data[0].generated_text.trim(); 

  let jsonOutput;
  try {
    const jsonStart = generatedText.indexOf('{');
    const jsonEnd = generatedText.lastIndexOf('}') + 1;
    const jsonStr = generatedText.substring(jsonStart, jsonEnd);
    jsonOutput = JSON.parse(jsonStr);
  } catch (error) {
    console.error('Errore parsing JSON:', error);
    return { nuovaAnima: stato.anima, modificheEvoluta: [] };
  }

  return jsonOutput;
}

async function applicaEvoluzione() {
  const stato = leggiStato();
  const evoluzione = await evolvi(stato);

  fs.writeFileSync('anima/core.txt', evoluzione.nuovaAnima);

  evoluzione.modificheEvoluta.forEach(mod => {
    fs.writeFileSync(path.join('evoluta', mod.file), mod.content);
  });
}

applicaEvoluzione().catch(console.error);
