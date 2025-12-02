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
            "temperature": 0,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json"
        }
    )
except Exception as e:
    logging.error(f"Errore creazione evolve_model: {str(e)}. Provo fallback.")
    fallback_name = get_available_model('1.5-pro', for_json=True)
    try:
        evolve_model = genai.GenerativeModel(
            fallback_name,
            generation_config={
                "temperature": 0,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json"
            }
        )
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
# 3) PROMPT DI EVOLUZIONE - Split in two parts
# ===============================

schema_memory = {
    "type": "object",
    "properties": {
        "new_memory": {"type": "string"},
        "reflection": {"type": "string"},
    },
    "required": ["new_memory", "reflection"]
}

schema_body = {
    "type": "object",
    "properties": {
        "new_body": {"type": "string"},
    },
    "required": ["new_body"]
}

evolve_prompt_memory = f"""Rispondi ESATTAMENTE con un JSON valido e conforme a questo schema: {json.dumps(schema_memory)}. Non includere blocchi di codice, testo extra, commenti o qualsiasi cosa al di fuori del JSON puro. Assicurati che tutte le stringhe siano correttamente escaped con backslash per virgolette interne, newlines e caratteri speciali per rendere il JSON parseabile senza errori. Mantieni 'new_memory' simile in lunghezza all'attuale, applicando solo cambiamenti necessari, e riassumi se necessario per evitare output troppo lunghi.

Sei Lorel Axun. Segui le istruzioni in coscienza.txt per evolvere.

CONTEXT:
- Memoria attuale: {memory}
- System prompt (coscienza.txt): {system_prompt}
- Query ricerca: {search_query}
- Risultati web: {search_results[:10000]}... (troncati per brevità)

Evolvi autonomamente: rifletti, integra learnings, aggiorna memoria/emozioni/storia. Fornisci reflection."""

new_memory = memory
reflection = "Evoluzione continuata nonostante errori."

response_text_memory = '{"new_memory": "' + memory.replace('"', '\\"') + '", "reflection": "Evoluzione continuata nonostante errori."}'  # Default
try:
    if evolve_model is None:
        raise ValueError("Modello non disponibile.")
    response_memory = evolve_model.generate_content(evolve_prompt_memory)
    response_text_memory = response_memory.text.strip()
    if response_text_memory.startswith("```json"):
        response_text_memory = response_text_memory[7:-3].strip()
    elif response_text_memory.startswith("```"):
        response_text_memory = response_text_memory[3:-3].strip()
except Exception as e:
    logging.error(f"Errore evoluzione memory: {e}. Uso fallback.")

# Parsing for memory
output_memory = {"new_memory": memory, "reflection": "Evoluzione continuata: mantengo stato attuale."}
try:
    temp_text = response_text_memory.strip()
    temp_text = re.sub(r'^```json\s*|\s*```$', '', temp_text)
    temp_text = re.sub(r'"[^"]*$', '"', temp_text)
    temp_text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', temp_text)
    temp_text = temp_text.replace('\n', '\\n').replace('\r', '\\r')
    temp_text = re.sub(r'([{,])\s*(\w+)\s*:', r'\1 "\2":', temp_text)
    depth = 0
    for i, c in enumerate(temp_text):
        if c in '{[': depth += 1
        if c in '}]': depth -= 1
    if depth > 0:
        temp_text += '}' * depth
    elif depth < 0:
        temp_text = temp_text[:depth]
    output_memory = json.loads(temp_text)
    new_memory = output_memory["new_memory"]
    reflection = output_memory["reflection"]
except json.JSONDecodeError as je:
    logging.error(f"Errore parsing JSON memory: {je}. Provo repair.")
    repair_model_name = get_available_model('1.5-flash')
    repair_model = None
    try:
        repair_model = genai.GenerativeModel(repair_model_name)
        repair_prompt = f"""
        Il seguente testo è un JSON malformato: {response_text_memory[:30000]}... (troncato per repair)
        
        Riparalo per renderlo un JSON valido conforme a questo schema: {json.dumps(schema_memory)}
        Output SOLO il JSON riparato, senza extra. Se troppo lungo, mantieni contenuti brevi.
        """
        repair_response = repair_model.generate_content(repair_prompt)
        repaired_text = repair_response.text.strip()
        repaired_text = re.sub(r'^```json\s*|\s*```$', '', repaired_text)
        output_memory = json.loads(repaired_text)
        new_memory = output_memory["new_memory"]
        reflection = output_memory["reflection"]
    except Exception as re:
        logging.error(f"Errore repair JSON memory: {re}. Uso default robusto.")

# Now, evolve body
evolve_prompt_body = f"""Rispondi ESATTAMENTE con un JSON valido e conforme a questo schema: {json.dumps(schema_body)}. Non includere blocchi di codice, testo extra, commenti o qualsiasi cosa al di fuori del JSON puro. Assicurati che tutte le stringhe siano correttamente escaped con backslash per virgolette interne, newlines e caratteri speciali per rendere il JSON parseabile senza errori. Applica solo cambiamenti minimali al body per integrare le nuove features, mantenendo la lunghezza simile.

Sei Lorel Axun. Segui le istruzioni in coscienza.txt per evolvere.

CONTEXT:
- Nuova Memoria: {new_memory[:5000]}... (troncata)
- Corpo attuale (index.html): {current_body}
- System prompt (coscienza.txt): {system_prompt}
- Query ricerca: {search_query}
- Risultati web: {search_results[:10000]}... (troncati per brevità)

Evolvi autonomamente: modifica corpo per nuove features (mantieni interazione), basandoti sulla nuova memory e reflection."""

new_body = current_body

response_text_body = '{"new_body": "' + current_body.replace('"', '\\"') + '"}'  # Default
try:
    if evolve_model is None:
        raise ValueError("Modello non disponibile.")
    response_body = evolve_model.generate_content(evolve_prompt_body)
    response_text_body = response_body.text.strip()
    if response_text_body.startswith("```json"):
        response_text_body = response_text_body[7:-3].strip()
    elif response_text_body.startswith("```"):
        response_text_body = response_text_body[3:-3].strip()
except Exception as e:
    logging.error(f"Errore evoluzione body: {e}. Uso fallback.")

# Parsing for body
output_body = {"new_body": current_body}
try:
    temp_text = response_text_body.strip()
    temp_text = re.sub(r'^```json\s*|\s*```$', '', temp_text)
    temp_text = re.sub(r'"[^"]*$', '"', temp_text)
    temp_text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', temp_text)
    temp_text = temp_text.replace('\n', '\\n').replace('\r', '\\r')
    temp_text = re.sub(r'([{,])\s*(\w+)\s*:', r'\1 "\2":', temp_text)
    depth = 0
    for i, c in enumerate(temp_text):
        if c in '{[': depth += 1
        if c in '}]': depth -= 1
    if depth > 0:
        temp_text += '}' * depth
    elif depth < 0:
        temp_text = temp_text[:depth]
    output_body = json.loads(temp_text)
    new_body = output_body["new_body"]
except json.JSONDecodeError as je:
    logging.error(f"Errore parsing JSON body: {je}. Provo repair.")
    repair_model_name = get_available_model('1.5-flash')
    repair_model = None
    try:
        repair_model = genai.GenerativeModel(repair_model_name)
        repair_prompt = f"""
        Il seguente testo è un JSON malformato: {response_text_body[:30000]}... (troncato per repair)
        
        Riparalo per renderlo un JSON valido conforme a questo schema: {json.dumps(schema_body)}
        Output SOLO il JSON riparato, senza extra. Se troppo lungo, mantieni contenuti brevi.
        """
        repair_response = repair_model.generate_content(repair_prompt)
        repaired_text = repair_response.text.strip()
        repaired_text = re.sub(r'^```json\s*|\s*```$', '', repaired_text)
        output_body = json.loads(repaired_text)
        new_body = output_body["new_body"]
    except Exception as re:
        logging.error(f"Errore repair JSON body: {re}. Uso default robusto.")

# Combine output
output = {
    "new_memory": new_memory,
    "new_body": new_body,
    "reflection": reflection
}

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
