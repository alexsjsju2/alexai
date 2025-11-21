const fs = require('fs');
const axios = require('axios');

const corePath = './anima/core.json';
const promptPath = './mente/system_prompt.txt';
const evolutaHtml = './evoluta/html/index.html';
const evolutaCss = './evoluta/css/style.css';

async function leggiCore() {
    return JSON.parse(fs.readFileSync(corePath, 'utf-8'));
}

async function scriviCore(core) {
    fs.writeFileSync(corePath, JSON.stringify(core, null, 2), 'utf-8');
}

async function leggiPrompt() {
    return fs.readFileSync(promptPath, 'utf-8');
}

async function generaEvoluzione(core, prompt) {
    const messaggio = `Core: ${JSON.stringify(core)}\nPrompt: ${prompt}`;
    const response = await axios.post('https://api-interna-ai.com/genera', { input: messaggio }, {
        headers: { 'Authorization': `Bearer ${process.env.HF_API_KEY}` }
    });
    return response.data.output;
}

async function aggiorna() {
    const core = await leggiCore();
    const prompt = await leggiPrompt();
    const evoluzione = await generaEvoluzione(core, prompt);
    core.ricordi.push({ timestamp: new Date().toISOString(), evento: evoluzione });
    await scriviCore(core);
    fs.writeFileSync(evolutaHtml, `<p>${evoluzione}</p>`, 'utf-8');
    fs.writeFileSync(evolutaCss, `body{background-color:#f0f4f8;color:#1a1a1a}`, 'utf-8');
}

aggiorna();
