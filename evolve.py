import google.generativeai as genai
import os
import requests
import json
import re
from json.decoder import JSONDecodeError

# Configura Gemini API
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    raise RuntimeError("GEMINI_API_KEY non impostata in environment")

genai.configure(api_key=api_key)

# Leggi files attuali
with open('coscienza.txt', 'r', encoding='utf-8') as f:
    system_prompt = f.read()

with open('core.txt', 'r', encoding='utf-8') as f:
    memory = f.read()

with open('index.html', 'r', encoding='utf-8') as f:
    current_body = f.read()

with open('evolve.py', 'r', encoding='utf-8') as f:
    current_evolve = f.read()

# Esempio accesso web: Fetch da Wikipedia con parametri corretti per ottenere JSON
try:
    web_data = requests.get(
        'https://en.wikipedia.org/w/api.php',
        params={
            'action': 'query',
            'format': 'json',
            'prop': 'extracts',
            'exintro': '',
            'explaintext': '',
            'titles': 'Artificial%20intelligence'
        },
        timeout=10
    ).json()
    ai_info = list(web_data['query']['pages'].values())[0].get('extract', '')
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

# Ottieni il testo dalla response (adattare se la struttura è diversa)
raw_text = getattr(response, 'text', None)
if raw_text is None:
    # fallback: alcune SDK mettono il risultato in .candidates[0].content o simili
    try:
        raw_text = response.candidates[0].content
    except Exception:
        raw_text = str(response)

raw_text = raw_text.strip()

# Rimuovi blocchi di codice ```json ... ``` o ``` ... ```
# Gestiamo vari casi: ```json\n{...}\n``` oppure ```\n...\n```
raw_text = re.sub(r'^```json\s*', '', raw_text, flags=re.I)
raw_text = re.sub(r'^```\s*', '', raw_text)
raw_text = re.sub(r'```\s*$', '', raw_text)

# Estraggo la porzione che sembra JSON: dal primo '{' o '[' all'ultimo '}' o ']'
def extract_json_substring(s):
    first_obj = s.find('{')
    first_arr = s.find('[')
    # scegli il primo tra i due che esiste
    starts = [p for p in (first_obj, first_arr) if p != -1]
    if not starts:
        return s  # niente JSON evidente, ritorno tutto (fallback)
    start = min(starts)
    # cerca l'ultima parentesi chiusa corrispondente
    last_obj = s.rfind('}')
    last_arr = s.rfind(']')
    ends = [p for p in (last_obj, last_arr) if p != -1]
    if not ends:
        return s[start:]
    end = max(ends)
    return s[start:end+1]

candidate = extract_json_substring(raw_text)

# Prima prova di parsing diretto
parsed = None
try:
    parsed = json.loads(candidate)
except JSONDecodeError as e:
    # Tentativo di riparazione: molte volte l'errore è un backslash non validamente escapato.
    # Escapiamo i backslash che non precedono un escape JSON valido: " / \ b f n r t u
    fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', candidate)
    # Altre pulizie leggere: sostituisco virgolette tipografiche con quote normali
    fixed = fixed.replace('“', '"').replace('”', '"').replace("’", "'")
    try:
        parsed = json.loads(fixed)
    except JSONDecodeError as e2:
        # Ultimo fallback: provo ad interpretare come lista di oggetti separati (es. output multi-block)
        # oppure come testo non JSON; logghiami l'errore e salviamo il testo grezzo in file di debug.
        with open('evolve_response_debug.txt', 'w', encoding='utf-8') as dbg:
            dbg.write("Original response:\n")
            dbg.write(raw_text + "\n\n")
            dbg.write("Candidate JSON substring:\n")
            dbg.write(candidate + "\n\n")
            dbg.write("Fixed attempt:\n")
            dbg.write(fixed + "\n\n")
            dbg.write("JSONDecodeError original:\n")
            dbg.write(str(e) + "\n")
            dbg.write("JSONDecodeError fixed:\n")
            dbg.write(str(e2) + "\n")
        print("Errore parsing JSON dopo tentativi di riparazione. Vedi evolve_response_debug.txt per dettagli.")
        parsed = None

# Se parsed è None, interrompiamo l'evoluzione in modo pulito
if parsed is None:
    print("Evoluzione saltata: impossibile parsare JSON dalla risposta.")
    # opzionale: stampo una porzione della risposta per debugging veloce (non tutto se è lungo)
    print("Preview della risposta (primi 1000 char):")
    print(raw_text[:1000])
    exit(0)

# Ora parsed dovrebbe essere un dict o una lista
# Normalizziamo in un dict d'uscita come volevi
new_memory = ''
new_body = ''
new_evolve = ''
reflection = ''

if isinstance(parsed, dict):
    # caso: singolo oggetto
    items = [parsed]
elif isinstance(parsed, list):
    items = parsed
else:
    items = [parsed]

for item in items:
    # se l'item ha struttura {'files':[...], 'note': '...'}
    if isinstance(item, dict):
        for file in item.get('files', []):
            path = file.get('path', '')
            content = file.get('content', '')
            if path == 'core.txt':
                new_memory = content
            elif path == 'index.html':
                new_body = content
            elif path == 'evolve.py':
                new_evolve = content
        if 'note' in item:
            reflection += str(item['note']) + '\n'
    else:
        # item non dict: aggiungilo come riflessione testuale
        reflection += str(item) + '\n'

output = {
    'new_memory': new_memory,
    'new_body': new_body,
    'new_evolve': new_evolve,
    'reflection': reflection.strip()
}

# Aggiorna files solo se ci sono contenuti nuovi (non vuoti e diversi dall'esistente)
if output.get('new_memory'):
    try:
        # evita sovrascrivere con lo stesso contenuto
        if output['new_memory'] != memory:
            with open('core.txt', 'w', encoding='utf-8') as f:
                f.write(output['new_memory'])
            print("core.txt aggiornato.")
        else:
            print("core.txt identico — non sovrascritto.")
    except Exception as e:
        print("Errore scrittura core.txt:", e)

if output.get('new_body'):
    try:
        if output['new_body'] != current_body:
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(output['new_body'])
            print("index.html aggiornato.")
        else:
            print("index.html identico — non sovrascritto.")
    except Exception as e:
        print("Errore scrittura index.html:", e)

if output.get('new_evolve'):
    try:
        if output['new_evolve'] != current_evolve:
            with open('evolve.py', 'w', encoding='utf-8') as f:
                f.write(output['new_evolve'])
            print("evolve.py aggiornato.")
        else:
            print("evolve.py identico — non sovrascritto.")
    except Exception as e:
        print("Errore scrittura evolve.py:", e)

if output.get('reflection'):
    print('Evoluzione completata. Riflessione:\n' + output['reflection'])
else:
    print('Evoluzione completata senza riflessione specifica.') 
