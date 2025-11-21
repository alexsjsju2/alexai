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
  const response = await axios.get(`https://api.example.com/search?q=${encodeURIComponent(query)}`, {
    headers: { 'Authorization': process.env.LLM_API_KEY }
  });
  return response.data.results.slice(0, 3).map(r => r.snippet).join('\n');  
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
  Output JSON: { nuovaAnima: "...", modificheEvoluta: [{file: "stile.css", content: "..."}, ...] }
  Limiti: Modifica solo /evoluta/, mantieni integrità, non codice malevolo.
  `;

  const response = await axios.post('https://api.groq.com/openai/v1/chat/completions', {  
    model: 'mixtral-8x7b-32768', 
    messages: [{ role: 'system', content: prompt }]
  }, {
    headers: { 'Authorization': `Bearer ${process.env.LLM_API_KEY}` }
  });

  return JSON.parse(response.data.choices[0].message.content);
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
