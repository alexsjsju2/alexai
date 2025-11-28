import google.generativeai as genai
import os
import requests
import json
import logging
from ddgs import DDGS
import re

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

def get_available_model(preferred_version='2.5-pro-exp', for_json=False):
    fallback_models = ['gemini-2.5-pro-exp', 'gemini-1.5-pro-latest', 'gemini-1.5-flash', 'gemini-pro']
    try:
        models = genai.list_models()
        available = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
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
        return fallback_models[0] if not for_json else fallback_models[1]

# ===============================
# FUNZIONE RICERCA WEB (con fallback DDGS)
# ===============================

def web_search(query):
    if serp_key:
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

# ===============================
# SELEZIONA MODELLI
# ===============================

ask_model_name = get_available_model('2.5-pro-exp')
ask_model = None
try:
    ask_model = genai.GenerativeModel(ask_model_name)
except Exception as e:
    logging.error(f"Errore creazione ask_model: {str(e)}. Provo fallback.")
    fallback_name = get_available_model('1.5-pro')
    try:
        ask_model = genai.GenerativeModel(fallback_name)
    except:
        logging.error("Fallback fallito. Uso default query.")

evolve_model_name = get_available_model('2.5-pro-exp', for_json=True)
evolve_model = None
try:
    evolve_model = genai.GenerativeModel(
        evolve_model_name,
        generation_config={
            "response_mime_type": "application/json"
        }
    )
except Exception as e:
    logging.error(f"Errore creazione evolve_model: {str(e)}. Provo fallback.")
    fallback_name = get_available_model('1.5-pro', for_json=True)
    try:
        evolve_model = genai.GenerativeModel(fallback_name, generation_config={"response_mime_type": "application/json"})
    except:
        logging.error("Fallback fallito. Uso default output.")

# ===============================
# 1) CHIEDI ALL'AI COSA CERCARE
# ===============================

ask_prompt = f"""
{system_prompt}

Memoria attuale: {memory[:2000]}... (troncata per brevità)

Decidi una query web utile per migliorare il sito.
Rispondi SOLO con la query, una frase breve.
"""

search_query = "latest ai developments"  # Default fallback
try:
    if ask_model is None:
        raise ValueError("Modello non disponibile.")
    search_query_response = ask_model.generate_content(ask_prompt)
    text = search_query_response.text.strip()
    text = re.sub(r'^```.*?\n|\n?```$', '', text)
    search_query = text
    logging.info(f"[Lorel] Query di ricerca: {search_query}")
except Exception as e:
    logging.error(f"Errore generazione query: {e}. Uso default.")

# ===============================
# 2) ESEGUI LA RICERCA
# ===============================

search_results = web_search(search_query)

# ===============================
# 3) PROMPT DI EVOLUZIONE
# ===============================

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

response_text = '{"new_memory": "' + memory.replace('"', '\\"') + '", "new_body": "' + current_body.replace('"', '\\"') + '", "reflection": "Evoluzione continuata nonostante errori."}'  # Default fallback robusto
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
    logging.error(f"Errore evoluzione: {e}. Uso fallback.")

# ===============================
# 4) PARSING JSON (più robusto con repair)
# ===============================

output = {
    "new_memory": memory,
    "new_body": current_body,
    "reflection": "Evoluzione continuata: mantengo stato attuale."
}  # Default robusto
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
except json.JSONDecodeError as je:
    logging.error(f"Errore parsing JSON: {je}. Provo repair.")
    # Repair con modello
    repair_model_name = get_available_model('2.5-pro-exp')
    repair_model = None
    try:
        repair_model = genai.GenerativeModel(repair_model_name)
        repair_prompt = f"""
        Il seguente testo è un JSON malformato: {response_text}
        
        Riparalo per renderlo un JSON valido conforme a questo schema: {json.dumps(schema)}
        Output SOLO il JSON riparato, senza extra.
        """
        repair_response = repair_model.generate_content(repair_prompt)
        repaired_text = repair_response.text.strip()
        repaired_text = re.sub(r'^```json\s*|\s*```$', '', repaired_text)
        output = json.loads(repaired_text)  # Prova parse dopo repair
    except Exception as re:
        logging.error(f"Errore repair JSON: {re}. Uso default robusto.")

# ===============================
# 5) SALVATAGGIO FILES
# ===============================

def write_file(path, content):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Aggiornato {path}")
    except Exception as e:
        logging.error(f"Errore salvataggio {path}: {str(e)}.")

if "new_memory" in output:
    write_file("core.txt", output["new_memory"])

if "new_body" in output:
    write_file("index.html", output["new_body"])

print("Evoluzione completata.")
print("Riflessione:", output.get("reflection", "Nessuna riflessione disponibile."))
