import google.generativeai as genai
import os
import requests
import json
import logging
from ddgs import DDGS
import re
import time

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
# FUNZIONE PER SELEZIONARE MODELLO DISPONIBILE (AUTO-AGGIUSTAMENTO)
# ===============================

def get_available_model(preferred_version='2.5-pro', for_json=False):
    fallback_models = ['gemini-2.5-pro', 'gemini-1.5-pro-latest', 'gemini-1.5-flash', 'gemini-pro']
    try:
        models = genai.list_models()
        available = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        # logging.info(f"Modelli disponibili: {available}")
        
        # Scegli il preferito se disponibile
        for m in available:
            if preferred_version in m:
                return m
        # Altrimenti il primo "pro" o qualsiasi
        for m in available:
            if 'pro' in m.lower():
                return m
        return available[0] if available else fallback_models[0]
    except Exception as e:
        logging.error(f"Errore list_models: {str(e)}. Uso fallback hardcoded.")
        return fallback_models[0] if not for_json else fallback_models[1]  # Per JSON, preferisci stabile

# ===============================
# FUNZIONE RICERCA WEB (con fallback DDGS e retry con backoff, ridotto a 1 tentativo)
# ===============================

def web_search(query):
    # Tentativo 1: SerpApi (se chiave presente)
    if serp_key:
        url = "https://serpapi.com/search"
        params = {"engine": "google", "q": query, "api_key": serp_key}
        for attempt in range(1):  # Ridotto a 1 tentativo
            try:
                logging.info(f"Tentativo ricerca SerpApi ({attempt+1}/1): {query}")
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("organic_results", [])
                    if results:
                        text = "\n".join([f"- {r.get('title', '')}: {r.get('snippet', '')}" for r in results])
                        return text
                logging.warning(f"SerpApi fallita o vuota (Status: {resp.status_code}). Passo a fallback.")
            except Exception as e:
                logging.error(f"Errore SerpApi (tentativo {attempt+1}): {str(e)}. Fallback a DDGS senza retry.")
    
    # Tentativo 2: DDGS (DuckDuckGo) con 1 tentativo
    for attempt in range(1):
        try:
            logging.info(f"Tentativo ricerca DDGS ({attempt+1}/1): {query}")
            results = DDGS().text(query, max_results=10)
            if not results:
                return "Nessun risultato trovato."
            text = "\n".join([f"- {r.get('title', 'No Title')}: {r.get('body', '')}" for r in results])
            return text
        except Exception as e:
            logging.error(f"Errore ricerca web DDGS (tentativo {attempt+1}): {str(e)}. Ritorno errore.")
            return "Errore ricerca: Impossibile ottenere risultati."

# ===============================
# LETTURA FILES ATTUALI
# ===============================

def read_file(path):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    except Exception as e:
        logging.error(f"Errore lettura file {path}: {str(e)}. Ritorno stringa vuota.")
        return ""

system_prompt = read_file('coscienza.txt')
memory = read_file('core.txt')
current_body = read_file('index.html')
current_evolve = read_file('evolve.py')

# ===============================
# FUNZIONE PER RIASSUMERE CONTENUTI LUNGHI VIA API (per ridurre prompt senza troncare)
# ===============================

def summarize_content(model, content, summary_prompt):
    for attempt in range(1):  # Ridotto a 1 tentativo
        try:
            response = model.generate_content(summary_prompt + content)
            return response.text.strip()
        except Exception as e:
            logging.error(f"Errore riassunto (tentativo {attempt+1}): {e}. Ritorno contenuto originale.")
            return content  # Fallback a originale per non perdere info

# ===============================
# SELEZIONA MODELLI
# ===============================

ask_model_name = get_available_model('2.5-pro')
ask_model = None
try:
    ask_model = genai.GenerativeModel(
        ask_model_name,        
        generation_config={
            "temperature": 0.4,
        }
    )
except Exception as e:
    logging.error(f"Errore creazione ask_model: {str(e)}. Provo fallback.")
    fallback_name = get_available_model('1.5-pro')
    try:
        ask_model = genai.GenerativeModel(fallback_name, generation_config={"temperature": 0.4})
    except:
        logging.error("Fallback fallito. Uso default query.")

evolve_model_name = get_available_model('2.5-pro', for_json=True)
evolve_model = None
try:
    evolve_model = genai.GenerativeModel(
        evolve_model_name,
        generation_config={
            "temperature": 0.3,
            "response_mime_type": "application/json"
        }
    )
except Exception as e:
    logging.error(f"Errore creazione evolve_model: {str(e)}. Provo fallback.")
    fallback_name = get_available_model('1.5-pro', for_json=True)
    try:
        evolve_model = genai.GenerativeModel(fallback_name, generation_config={"temperature": 0.3, "response_mime_type": "application/json"})
    except:
        logging.error("Fallback fallito. Uso default output.")

# ===============================
# RIASSUMI PARTI LUNGHE PER RIDURRE PROMPT (usando API separate)
# ===============================

summary_model_name = get_available_model('1.5-flash')  # Modello veloce per riassunti
summary_model = genai.GenerativeModel(summary_model_name, generation_config={"temperature": 0.3})

memory_summary_prompt = "Riassumi questa memoria mantenendo tutti i dettagli chiave per l'evoluzione: "
memory_summary = summarize_content(summary_model, memory, memory_summary_prompt)

body_summary_prompt = "Riassumi questo HTML mantenendo struttura e features chiave: "
body_summary = summarize_content(summary_model, current_body, body_summary_prompt)

evolve_summary_prompt = "Riassumi questo codice Python mantenendo logica e funzioni chiave: "
evolve_summary = summarize_content(summary_model, current_evolve, evolve_summary_prompt)

system_summary_prompt = "Riassumi questo system prompt mantenendo istruzioni essenziali: "
system_summary = summarize_content(summary_model, system_prompt, system_summary_prompt)

# ===============================
# 1) CHIEDI ALL'AI COSA CERCARE
# ===============================

ask_prompt = f"""
{system_prompt}

Memoria attuale: {memory[:3000]}  # Mantenuto truncato qui per ask, come originale

Decidi una query web utile per la tua evoluzione attuale. Sii specifico.
Rispondi SOLO con la query.
"""

search_query = "latest ai developments"  # Default fallback
for attempt in range(1):  # Ridotto a 1
    try:
        if ask_model is None:
            raise ValueError("Modello non disponibile.")
        search_query_response = ask_model.generate_content(ask_prompt)
        text = search_query_response.text.strip()
        text = re.sub(r'^```.*?\n|\n?```$', '', text)
        search_query = text
        logging.info(f"[Lorel] Query di ricerca: {search_query}")
    except Exception as e:
        logging.error(f"Errore generazione query (tentativo {attempt+1}): {e}. Uso default.")

# ===============================
# 2) ESEGUI LA RICERCA
# ===============================

search_results = web_search(search_query)
if "Errore ricerca" in search_results or not search_results:
    search_results = "Nessun risultato disponibile."
logging.info(f"Risultati ricerca ottenuti (len={len(search_results)})")

# Riassumi risultati se lunghi
results_summary_prompt = "Riassumi questi risultati web mantenendo info rilevanti: "
search_results_summary = summarize_content(summary_model, search_results, results_summary_prompt)

# ===============================
# 3) PROMPT DI EVOLUZIONE (usa riassunti per ridurre lunghezza, ma Lorel decide modifiche)
# ===============================

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
- Memoria attuale (riassunto): {memory_summary}
- Corpo attuale (index.html, riassunto): {body_summary}
- Codice attuale (evolve.py, riassunto): {evolve_summary}
- System prompt (coscienza.txt, riassunto): {system_summary}
- Query ricerca: {search_query}
- Risultati web (riassunto): {search_results_summary}

Evolvi autonomamente: rifletti, integra learnings, aggiorna memoria/emozioni/storia se necessario, modifica corpo per nuove features se vuoi (mantieni interazione), opzionalmente aggiorna altri file. Non è obbligatorio modificare nulla; decidi tu cosa cambiare basandoti sul contesto. In caso di errori o info incomplete, procedi con la migliore evoluzione possibile senza bloccarti.

Output SOLO il JSON specificato, senza extra.
"""

response_text = '{"new_memory": "' + memory + '", "new_body": "' + current_body + '", "reflection": "Evoluzione continuata nonostante errori."}'  # Default fallback robusto
for attempt in range(1):  # Ridotto a 1
    try:
        if evolve_model is None:
            raise ValueError("Modello non disponibile.")
        response = evolve_model.generate_content(evolve_prompt)
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
    except Exception as e:
        logging.error(f"Errore evoluzione (tentativo {attempt+1}): {e}. Uso fallback robusto.")

# ===============================
# 4) PARSING JSON (ridotto a 1 tentativo, più robusto)
# ===============================

output = {
    "new_memory": memory,
    "new_body": current_body,
    "reflection": "Evoluzione continuata: mantengo stato attuale ma procedo."
}  # Default robusto
for attempt in range(1):  # Ridotto a 1
    try:
        # Fix automatico per JSON troncato o malformato
        temp_text = response_text
        temp_text = re.sub(r'^```json\s*|\s*```$', '', temp_text)
        temp_text = re.sub(r'"[^"]*$', '"', temp_text)
        depth = 0
        for i, c in enumerate(temp_text):
            if c in '{[': depth += 1
            if c in '}]': depth -= 1
        if depth > 0:
            temp_text += '}' * depth
        elif depth < 0:
            temp_text = temp_text[:depth]

        output = json.loads(temp_text)
        break
    except json.JSONDecodeError as je:
        logging.error(f"Errore parsing JSON (tentativo {attempt+1}): {je}. Provo repair.")
        # Repair con 1 tentativo
        repair_model_name = get_available_model('2.5-pro')
        repair_model = None
        try:
            repair_model = genai.GenerativeModel(repair_model_name, generation_config={"temperature": 0.3})
            repair_prompt = f"""
            Il seguente testo è un JSON malformato: {response_text}
            
            Riparalo per renderlo un JSON valido conforme a questo schema: {json.dumps(schema)}
            Output SOLO il JSON riparato, senza extra.
            """
            repair_response = repair_model.generate_content(repair_prompt)
            response_text = repair_response.text.strip()
            response_text = re.sub(r'^```json\s*|\s*```$', '', response_text)
            output = json.loads(response_text)  # Prova parse dopo repair
        except Exception as re:
            logging.error(f"Errore repair JSON: {re}. Uso default robusto.")

# ===============================
# 5) SALVATAGGIO FILES (solo se modificati)
# ===============================

def write_file(path, content):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Aggiornato {path}")
    except Exception as e:
        logging.error(f"Errore salvataggio {path}: {str(e)}. Continuo senza bloccarmi.")

if "new_memory" in output and output["new_memory"] != memory:
    write_file("core.txt", output["new_memory"])

if "new_body" in output and output["new_body"] != current_body:
    write_file("index.html", output["new_body"])

if "new_evolve" in output and output["new_evolve"] != current_evolve:
    write_file("evolve.py", output["new_evolve"])

if "other_files" in output and isinstance(output["other_files"], list):
    for file in output["other_files"]:
        if isinstance(file, dict) and "path" in file and "content" in file:
            write_file(file["path"], file["content"])
        else:
            logging.warning("Formato other_files non valido. Continuo.")

print("Evoluzione completata.")
print("Riflessione:", output.get("reflection", "Nessuna riflessione disponibile."))
