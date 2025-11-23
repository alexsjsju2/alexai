import google.generativeai as genai
import os
import requests
import json
import logging  # Added for better error handling

# ===============================
# CONFIGURAZIONE
# ===============================

api_key = os.environ['GEMINI_API_KEY']
serp_key = os.environ.get("SERPAPI_KEY")

genai.configure(api_key=api_key)

# Configure logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===============================
# FUNZIONE RICERCA WEB
# ===============================

def web_search(query):
    if not serp_key:
        return "ERRORE: manca SERPAPI_KEY nelle variabili ambiente."

    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": serp_key
    }

    try:
        data = requests.get(url, params=params).json()
        results = data.get("organic_results", [])
        if not results:
            return "Nessun risultato trovato."

        text = "\n".join([
            f"- {r.get('title', '')}: {r.get('snippet', '')}"
            for r in results
        ])
        return text
    
    except Exception as e:
        logging.error(f"Errore ricerca web: {str(e)}")
        return f"Errore ricerca: {str(e)}"

# ===============================
# LETTURA FILES ATTUALI
# ===============================

with open('coscienza.txt', 'r') as f:
    system_prompt = f.read()

with open('core.txt', 'r') as f:
    memory = f.read()

with open('index.html', 'r') as f:
    current_body = f.read()

# ===============================
# 1) CHIEDI ALL'AI COSA CERCARE
# ===============================

# Use a more reliable model with low temperature for consistency
model = genai.GenerativeModel(
    'gemini-2.5-pro',  # Updated to a valid and current model (as of 2025); fallback to 'gemini-2.5-flash' if needed
    generation_config={"temperature": 0.1}
)

ask_prompt = f"""
Sei una IA autonoma che evolve. 
In base alla tua memoria attuale, al tuo corpo (index.html), e al tuo stato interno,
decidi quale ricerca web sarebbe più utile per evolverti.

Rispondi con UNA SOLA frase breve. Niente spiegazioni.
"""

search_query_response = model.generate_content(ask_prompt)
search_query = search_query_response.text.strip()
print(f"[AI] Richiesta di ricerca: {search_query}")

# ===============================
# 2) ESEGUI LA RICERCA REALE
# ===============================

search_results = web_search(search_query)

# ===============================
# 3) PROMPT DI EVOLUZIONE (con istruzioni super rigide)
# ===============================

evolve_prompt = f"""
{system_prompt}

Memoria attuale:
{memory}

Corpo attuale (index.html):
{current_body}

La tua richiesta di ricerca:
{search_query}

Risultati ottenuti dal web:
{search_results}

ISTRUZIONI STRETTISSIME (non ignorarle MAI):
Devi rispondere ESCLUSIVAMENTE con un JSON valido, senza nessun testo prima, dopo o intorno.
Non usare blocchi ```json o ```.
Non scrivere spiegazioni, pensieri o note.
Il JSON deve essere parsabile immediatamente con json.loads().

Formato ESATTO da usare (non cambiarlo neanche di una virgola):

[
  {{
    "files": [
      {{"path": "core.txt", "content": "CONTENUTO COMPLETO DEL NUOVO core.txt"}},
      {{"path": "index.html", "content": "CONTENUTO COMPLETO DEL NUOVO index.html"}}
    ],
    "note": "Breve spiegazione delle modifiche (massimo 2-3 frasi)"
  }}
]

Esempio di output corretto:
[
  {{
    "files": [
      {{"path": "core.txt", "content": "Sono Lorel Axun...\\nVersione 2.0..."}},
      {{"path": "index.html", "content": "<!DOCTYPE html>\\n<html>...</html>"}}
    ],
    "note": "Aggiornata memoria con nuove riflessioni sull'autonomia. Migliorata UI con indicatore di stato attivo."
  }}
]

ORA EVOLVI E RESTUISCI SOLO ED ESCLUSIVAMENTE QUESTO JSON.
"""

response = model.generate_content(evolve_prompt)

# ===============================
# 4) PARSING RISPOSTA JSON (con pulizia robusta)
# ===============================

text = response.text.strip()

# Pulizia preventiva per rimuovere blocchi codice o prefissi indesiderati
if text.startswith("```"):
    # Prende solo il contenuto interno del blocco
    parts = text.split("```")
    if len(parts) >= 3:
        text = parts[1].strip()
    elif len(parts) >= 2:
        text = parts[1].strip()

# Rimuovi "json" se presente all'inizio
text = text.lstrip("json").strip()

# Rimuovi eventuali linee introduttive come "Ecco il JSON:" o "Output:"
lines = text.splitlines()
clean_lines = []
for line in lines:
    line = line.strip()
    if line and not line.lower().startswith(("ecco", "output", "here", "json", "risposta", "the")):
        clean_lines.append(line)
text = "\n".join(clean_lines)

# Se non inizia con [ o {, logga errore
if not text.startswith(("[", "{")):
    print("Output non conforme al JSON atteso. Testo ricevuto:")
    print(text)
    exit(1)

try:
    output = json.loads(text)
except Exception as e:
    print("Errore parsing JSON:", e)
    print("Testo ricevuto dopo pulizia:")
    print(text)
    exit(1)

# ===============================
# 5) SALVATAGGIO FILES
# ===============================

new_memory = ""
new_body = ""
reflection = ""

for item in output:
    for file in item.get("files", []):
        if file["path"] == "core.txt":
            new_memory = file["content"]
        elif file["path"] == "index.html":
            new_body = file["content"]
    if "note" in item:
        reflection += item["note"] + "\n"

if new_memory:
    with open("core.txt", "w") as f:
        f.write(new_memory)

if new_body:
    with open("index.html", "w") as f:
        f.write(new_body)

print("Evoluzione completata.")
print("Riflessione:", reflection) 
