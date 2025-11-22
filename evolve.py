import google.generativeai as genai
import os
import requests
import json
import re  # Added for better cleaning

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
# Aggiunto istruzioni esplicite per output JSON valido
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

Output your entire response as a single valid JSON object (no markdown wrappers). Ensure all strings are properly escaped for JSON (e.g., double backslashes \\\\ for literal \\, escape quotes, etc.). The structure must be:
[
  {{
    "files": [
      {{"path": "core.txt", "content": "updated content here"}},
      {{"path": "index.html", "content": "updated content here"}},
      {{"path": "evolve.py", "content": "updated content here"}}
    ],
    "note": "your reflections here"
  }}
]
If no changes for a file, omit it or use empty string.
"""

model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content(evolve_prompt)

# Pulisci la response per rimuovere wrappers (migliorato)
text = response.text.strip()

# Rimuovi markdown code blocks se presenti (e.g., ```json
text = re.sub(r'^```json\s*|\s*```$', '', text).strip()

# Debug: Stampa il text pulito per ispezionare
print("Testo pulito prima del parsing JSON:\n", text)

# Fallback: Doubla backslashes non escaped (solo come fix temporaneo, rimuovi se non necessario)
# Questo assume che \ non sia già escaped; testa con il tuo output
text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)  # Doubla \ seguiti da char invalidi

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
        output = {'new_memory': new_memory, 'new_body': new_body, 'new_evolve': new_evolve, 'reflection': reflection}
except Exception as e:
    print(f'Errore parsing JSON: {str(e)}')
    print('Testo che ha causato l\'errore:', text)  # Stampa per debug
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
