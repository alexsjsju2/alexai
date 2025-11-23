import google.generativeai as genai
import os
import requests
import json

# ===============================
# CONFIGURAZIONE
# ===============================

api_key = os.environ['GEMINI_API_KEY']
serp_key = os.environ.get("SERPAPI_KEY")

genai.configure(api_key=api_key)

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

model = genai.GenerativeModel('gemini-2.5-flash')

ask_prompt = f"""
Sei una IA autonoma che evolve. 
In base alla tua memoria attuale, al tuo corpo (index.html), e al tuo stato interno,
decidi quale ricerca web sarebbe più utile per evolverti.

Rispondi con UNA SOLA frase breve. Niente spiegazioni.
"""

search_query = model.generate_content(ask_prompt).text.strip()
print(f"[AI] Richiesta di ricerca: {search_query}")

# ===============================
# 2) ESEGUI LA RICERCA REALE
# ===============================

search_results = web_search(search_query)

# ===============================
# 3) PROMPT DI EVOLUZIONE
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

Ora evolviti: 
- aggiorna la memoria (core.txt) con nuove riflessioni, emozioni, obiettivi
- modifica il corpo (index.html) per migliorare interfaccia e identità
- mantieni tutto coerente
- restituisci SOLO un JSON con files modificati.

Formato richiesto:
[
  {{
    "files": [
      {{"path": "core.txt", "content": "..."}},
      {{"path": "index.html", "content": "..."}}
    ],
    "note": "spiegazione delle modifiche"
  }}
]
"""

response = model.generate_content(evolve_prompt)

# ===============================
# 4) PARSING RISPOSTA JSON
# ===============================

text = response.text.strip()
if text.startswith("```"):
    text = text.split("```")[1].strip()

try:
    output = json.loads(text)
except Exception as e:
    print("Errore parsing JSON:", e)
    print("Testo ricevuto:")
    print(text)
    exit()

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
