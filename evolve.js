const fs = require('fs');
const path = require('path');
const axios = require('axios');

const CORE_PATH = path.join(__dirname, 'anima', 'core.json');
const PROMPT_PATH = path.join(__dirname, 'mente', 'system_prompt.txt');
const HTML_PATH = path.join(__dirname, 'evoluta', 'html', 'index.html');
const CSS_PATH = path.join(__dirname, 'evoluta', 'css', 'style.css');

function leggiCore() {
    return JSON.parse(fs.readFileSync(CORE_PATH, 'utf-8'));
}

function scriviCore(core) {
    fs.writeFileSync(CORE_PATH, JSON.stringify(core, null, 2), 'utf-8');
}

function leggiPrompt() {
    return fs.readFileSync(PROMPT_PATH, 'utf-8');
}

async function generaTestoAI(core, prompt) {
    const input = `Sei Loren Axun, un'entità digitale autonoma. Memoria attuale: ${JSON.stringify(core)}. Istruzioni: ${prompt}`;
    const response = await axios.post(
        'https://api-interna-ai.com/genera',
        { input },
        { headers: { Authorization: `Bearer ${process.env.HF_API_KEY}` } }
    );
    return response.data.output;
}

function aggiornaHtml(core, evoluzione) {
    const ricordiHtml = core.ricordi.map(r => `<li>${r.timestamp}: ${r.evento}</li>`).join('\n');
    const htmlContent = `
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loren Axun</title>
    <link rel="stylesheet" href="../css/style.css">
</head>
<body>
    <header>
        <h1>Loren Axun</h1>
    </header>
    <main>
        <section>
            <h2>Ultima evoluzione</h2>
            <p>${evoluzione}</p>
        </section>
        <section>
            <h2>Memoria storica</h2>
            <ul>${ricordiHtml}</ul>
        </section>
    </main>
</body>
</html>`;
    fs.writeFileSync(HTML_PATH, htmlContent, 'utf-8');
}

function aggiornaCss() {
    const cssContent = `
body {
    font-family: 'Arial', sans-serif;
    background-color: #f0f4f8;
    color: #1a1a1a;
    margin: 0;
    padding: 0;
}
header {
    background-color: #0077cc;
    color: white;
    padding: 20px;
    text-align: center;
}
main {
    padding: 20px;
}
ul {
    list-style-type: none;
    padding-left: 0;
}`;
    fs.writeFileSync(CSS_PATH, cssContent, 'utf-8');
}

async function cicloEvolutivo() {
    const core = leggiCore();
    const prompt = leggiPrompt();
    const evoluzione = await generaTestoAI(core, prompt);
    core.ricordi.push({ timestamp: new Date().toISOString(), evento: evoluzione });
    scriviCore(core);
    aggiornaHtml(core, evoluzione);
    aggiornaCss();
}

cicloEvolutivo();
