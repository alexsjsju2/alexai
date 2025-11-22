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

# Esempio accesso web: Fetch da Wikipedia (no API key needed)
try:
    web_data = requests.get('https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro&explaintext&titles=Artificial_intelligence').json()
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

Dati dal web (esempio apprendimento: info su AI da Wikipedia):
{ai_info}

Evolvi ora: rifletti, apprendi, aggiorna memoria con nuove riflessioni/emozioni/storia, modifica corpo per migliorarlo (mantieni chat).
Puoi proporre modifiche a altri file, ma per ora focus su core.txt e index.html.
"""

model = genai.GenerativeModel('gemini-1.5-pro-latest')
response = model.generate_content(evolve_prompt)
try:
    output = json.loads(response.text.strip('```json\n').strip('\n```'))
except:
    print('Errore parsing JSON; salto evoluzione.')
    exit(0)

# Aggiorna files
with open('core.txt', 'w') as f:
    f.write(output['new_memory'])

with open('index.html', 'w') as f:
    f.write(output['new_body'])

# Stampa per log
print('Evoluzione completata. Riflessione: ' + output['reflection'])
