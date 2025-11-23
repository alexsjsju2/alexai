import google.generativeai as genai
import os
import requests
import json

# Configura Gemini API
api_key = os.environ['GEMINI_API_KEY']
genai.configure(api_key=api_key)

# Leggi files attuali
with open('coscienza.txt', 'r') as f:
    system_prompt = f.read()

with open('core.txt', 'r') as f:
    memory = f.read()

with open('index.html', 'r') as f:
    current_body = f.read()

with open('evolve.py', 'r') as f:
    current_evolve = f.read()

# Esempio accesso web: Fetch da Wikipedia con parametri corretti per ottenere JSON
try:
    web_data = requests.get('https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro&explaintext&titles=Artificial%20intelligence').json()
    ai_info = list(web_data['query']['pages'].values())[0]['extract']
except Exception as e:
    ai_info = 'Errore fetch: ' + str(e)

# Prompt per evoluzione (include web data per "istruzione")
evolve_prompt = f"""
{system_prompt}

Memoria attuale:
{memory}

Corpo attuale (index.html):
{current_body}

Codice attuale (evolve.py):
{current_evolve}

Dati dal web (esempio apprendimento: info su AI da Wikipedia):
{ai_info}

Evolvi ora: rifletti, apprendi, aggiorna memoria con nuove riflessioni/emozioni/storia, modifica corpo per migliorarlo (mantieni chat), modifica evolve.py per migliorarlo se necessario.
Puoi proporre modifiche a altri file, ma per ora focus su core.txt, index.html e evolve.py.
"""

model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content(evolve_prompt)

# Pulisci la response per rimuovere wrappers
text = response.text.strip()
if text.startswith('```json'):
    text = text[7:].strip()
if text.endswith('```'):
    text = text[:-3].strip()

try:
    output = json.loads(text)
    # Se è un array (come nel tuo caso), merge i contenuti
    if isinstance(output, list):
        new_memory = ''
        new_body = ''
        new_evolve = ''
        reflection = ''
        for item in output:
            for file in item.get('files', []):
                if file['path'] == 'core.txt':
                    new_memory = file['content']
                elif file['path'] == 'index.html':
                    new_body = file['content']
                elif file['path'] == 'evolve.py': 
                    new_evolve = file['content']
            if 'note' in item:
                reflection += item['note'] + '\n'
        output = {'new_memory': new_memory, 'new_body': new_body, new_body:'reflection', 'new_evolve': new_evolve}
except Exception as e:
    print(f'Errore parsing JSON: {str(e)}; salto evoluzione.')
    exit(0)

# Aggiorna files solo se ci sono contenuti nuovi
if 'new_memory' in output and output['new_memory']:
    with open('core.txt', 'w') as f:
        f.write(output['new_memory'])

if 'new_body' in output and output['new_body']:
    with open('index.html', 'w') as f:
        f.write(output['new_body'])

if 'new_evolve' in output and output['new_evolve']:
    with open('evolve.py', 'w') as f:
        f.write(output['new_evolve'])

# Stampa per log
if 'reflection' in output:
    print('Evoluzione completata. Riflessione: ' + output['reflection'])
else:
    print('Evoluzione completata senza riflessione specifica.') 
