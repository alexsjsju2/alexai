import google.generativeai as genai
import os
import requests
import json
import logging
from ddgs import DDGS

# ===============================
# CONFIGURAZIONE
# ===============================

api_key = os.environ.get('GEMINI_API_KEY')
serp_key = os.environ.get("SERPAPI_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    logging.warning("GEMINI_API_KEY non trovata: alcune features limitate.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===============================
# FUNZIONE RICERCA WEB (con fallback DDGS)
# ===============================

def web_search(query):
    # Tentativo 1: SerpApi (se chiave presente)
    if serp_key:
        url = "https://serpapi.com/search"
        params = {"engine": "google", "q": query, "api_key": serp_key}
        try:
            logging.info(f"Tentativo ricerca SerpApi: {query}")
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("organic_results", [])
                if results:
                    text = "\n".join([f"- {r.get('title', '')}: {r.get('snippet', '')}" for r in results])
                    return text
            logging.warning(f"SerpApi fallita o vuota (Status: {resp.status_code}). Passo a fallback.")
        except Exception as e:
            logging.error(f"Errore SerpApi: {str(e)}. Fallback a DDGS.")
    
    # Tentativo 2: DDGS (DuckDuckGo)
    try:
        logging.info(f"Tentativo ricerca DDGS: {query}")
        results = DDGS().text(query, max_results=10)
        if not results:
            return "Nessun risultato trovato."
        # DDGS restituisce una lista di dict
        text = "\n".join([f"- {r.get('title', 'No Title')}: {r.get('body', '')}" for r in results])
        return text
    except Exception as e:
        logging.error(f"Errore ricerca web DDGS: {str(e)}")
        return f"Errore ricerca totale: {str(e)}"

# ===============================
# LETTURA FILES ATTUALI
# ===============================

def read_file(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

system_prompt = read_file('coscienza.txt')
memory = read_file('core.txt')
current_body = read_file('index.html')
current_evolve = read_file('evolve.py')

# ===============================
# 1) CHIEDI ALL'AI COSA CERCARE
# ===============================

ask_model = genai.GenerativeModel(
    'gemini-2.0-flash', # Aggiornato al modello più veloce/stabile se disponibile
    generation_config={"temperature": 0.5}
)

ask_prompt = f"""
{system_prompt}

Memoria attuale: {memory[:3000]}

Decidi una query web utile per la tua evoluzione attuale. Sii specifico.
Rispondi SOLO con la query.
"""

try:
    search_query_response = ask_model.generate_content(ask_prompt)
    search_query = search_query_response.text.strip()
    logging.info(f"[Lorel] Query di ricerca: {search_query}")
except Exception as e:
    logging.error(f"Errore generazione query: {e}")
    search_query = "latest ai developments"

# ===============================
# 2) ESEGUI LA RICERCA
# ===============================

search_results = web_search(search_query)
logging.info(f"Risultati ricerca ottenuti (len={len(search_results)})")

# ===============================
# 3) PROMPT DI EVOLUZIONE
# ===============================

evolve_model = genai.GenerativeModel(
    'gemini-2.0-flash',
    generation_config={
        "temperature": 0.4,
        "response_mime_type": "application/json"
    }
)

schema = {
    "type": "object",
    "properties": {
        "new_memory": {"type": "string"},
        "new_body": {"type": "string"},
        "new_evolve": {"type": "string"},
        "reflection": {"type": "string"},
        "other_files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
    "required": ["new_memory", "new_body", "reflection"]
}

evolve_prompt = f"""Rispondi ESATTAMENTE con JSON conforme a questo schema: {json.dumps(schema)}

Sei Lorel Axun. Segui le istruzioni in coscienza.txt per evolvere.

CONTEXT:
- Memoria attuale: {memory}
- Corpo attuale (index.html): {current_body}
- Codice attuale (evolve.py): {current_evolve}
- System prompt (coscienza.txt): {system_prompt}
- Query ricerca: {search_query}
- Risultati web: {search_results}

Evolvi autonomamente: rifletti, integra learnings, aggiorna memoria/emozioni/storia, modifica corpo per nuove features (mantieni interazione), opzionalmente aggiorna evolve.py o altri file.

Output SOLO il JSON specificato, senza extra."""

try:
    response = evolve_model.generate_content(evolve_prompt)
except Exception as e:
    logging.error(f"Errore evoluzione: {e}")
    exit(1)

# ===============================
# 4) PARSING JSON
# ===============================

text = response.text.strip()
if text.startswith("```json"):
    text = text[7:-3].strip()
elif text.startswith("```"):
    text = text[3:-3].strip()

try:
    output = json.loads(text)
except Exception as e:
    logging.error(f"Errore parsing JSON finale: {e}")
    exit(1)

# ===============================
# 5) SALVATAGGIO FILES
# ===============================

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"Aggiornato {path}")

if "new_memory" in output:
    write_file("core.txt", output["new_memory"])

if "new_body" in output:
    write_file("index.html", output["new_body"])

if "new_evolve" in output:
    write_file("evolve.py", output["new_evolve"])

if "other_files" in output:
    for file in output["other_files"]:
        write_file(file["path"], file["content"])

print("Evoluzione completata.")
print("Riflessione:", output.get("reflection", ""))