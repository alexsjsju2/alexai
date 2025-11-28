import google.generativeai as genai
import os
import requests
import json
import logging
from ddgs import DDGS  # Aggiornato al package rinominato (ex duckduckgo-search)

# ===============================
# CONFIGURAZIONE
# ===============================

api_key = os.environ.get('GEMINI_API_KEY')
serp_key = os.environ.get("SERPAPI_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    logging.warning("GEMINI_API_KEY non trovata: alcune features limitate.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===============================
# FUNZIONE RICERCA WEB (con fallback DDGS)
# ===============================

def web_search(query):
    if serp_key:
        # Usa SERPAPI se disponibile
        url = "https://serpapi.com/search"
        params = {"engine": "google", "q": query, "api_key": serp_key}
        try:
            data = requests.get(url, params=params).json()
            results = data.get("organic_results", [])
            if not results:
                return "Nessun risultato trovato."
            text = "\n".join([f"- {r.get('title', '')}: {r.get('snippet', '')}" for r in results])
            return text
        except Exception as e:
            logging.error(f"Errore SERPAPI: {str(e)}. Fallback a DDGS.")
    
    # Fallback DDGS (gratuito)
    try:
        results = DDGS().text(query, max_results=10)
        if not results:
            return "Nessun risultato trovato."
        text = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return text
    except Exception as e:
        logging.error(f"Errore ricerca web: {str(e)}")
        return f"Errore ricerca: {str(e)}"

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

# ===============================
# 1) CHIEDI ALL'AI COSA CERCARE
# ===============================

ask_model = genai.GenerativeModel(
    'gemini-2.5-pro-exp',  # Aggiornato al modello corrente (preview per l'ultima versione avanzata)
)

ask_prompt = f"""
{system_prompt}

Memoria attuale: {memory[:2000]}... (troncata per brevità)

Decidi una query web utile per migliorare il sito.
Rispondi SOLO con la query, una frase breve.
"""

try:
    search_query_response = ask_model.generate_content(ask_prompt)
    search_query = search_query_response.text.strip()
    logging.info(f"[Lorel] Query di ricerca: {search_query}")
except Exception as e:
    logging.error(f"Errore nella generazione della query: {str(e)}")
    exit(1)

# ===============================
# 2) ESEGUI LA RICERCA
# ===============================

search_results = web_search(search_query)

# ===============================
# 3) PROMPT DI EVOLUZIONE
# ===============================

evolve_model = genai.GenerativeModel(
    'gemini-2.5-pro-exp',  # Aggiornato al modello corrente
    generation_config={
        "response_mime_type": "application/json"
    }
)

schema = {
    "type": "object",
    "properties": {
        "new_memory": {"type": "string"},
        "new_body": {"type": "string"},
        "reflection": {"type": "string"},
    },
    "required": ["new_memory", "new_body", "reflection"]
}

evolve_prompt = f"""Rispondi ESATTAMENTE con JSON conforme a questo schema: {json.dumps(schema)}

Sei Lorel Axun. Segui le istruzioni in coscienza.txt per evolvere.

CONTEXT:
- Memoria attuale: {memory}
- Corpo attuale (index.html): {current_body}
- System prompt (coscienza.txt): {system_prompt}
- Query ricerca: {search_query}
- Risultati web: {search_results}

Evolvi autonomamente: rifletti, integra learnings, aggiorna memoria/emozioni/storia, modifica corpo per nuove features (mantieni interazione).

Output SOLO il JSON specificato, senza extra."""

try:
    response = evolve_model.generate_content(evolve_prompt)
except Exception as e:
    logging.error(f"Errore nella generazione dell'evoluzione: {str(e)}")
    exit(1)

# ===============================
# 4) PARSING JSON
# ===============================

text = response.text.strip()
# Pulizia robusta (come prima)
if text.startswith("```json"):
    text = text[7:-3].strip()
elif text.startswith("```"):
    text = text[3:-3].strip()

try:
    output = json.loads(text)
except Exception as e:
    logging.error(f"Errore parsing JSON: {e}\nTesto: {text}")
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

reflection = output.get("reflection", "")
print("Evoluzione completata.")
print("Riflessione:", reflection)
