import os
import json
import google.generativeai as genai
from serpapi import GoogleSearch
from duckduckgo_search import DDGS

def get_api_keys():
    """Carica le chiavi API dalle variabili d'ambiente."""
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    serpapi_api_key = os.environ.get('SERPAPI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY non trovata nelle variabili d'ambiente.")
    return gemini_api_key, serpapi_api_key

def read_file(path):
    """Legge il contenuto di un file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Attenzione: file {path} non trovato. Verrà trattato come vuoto.")
        return ""

def write_file(path, content):
    """Scrive il contenuto in un file."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def get_available_model(model_list=["gemini-1.5-pro-latest", "gemini-1.5-flash-latest"]):
    """Seleziona il miglior modello Gemini disponibile."""
    for model_name in model_list:
        try:
            genai.get_generative_model(model_name)
            print(f"Modello selezionato: {model_name}")
            return model_name
        except Exception as e:
            print(f"Modello {model_name} non disponibile: {e}")
    raise ConnectionError("Nessun modello Gemini valido trovato.")

def summarize_text(text, model_name="gemini-1.5-flash-latest"):
    """Riassume un testo usando un modello AI veloce."""
    if not text.strip():
        return "(vuoto)"
    try:
        model = genai.GenerativeModel(model_name)
        prompt = f"Riassumi il seguente testo in modo conciso, mantenendo i dettagli chiave per un'evoluzione futura:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Errore durante il riassunto: {e}")
        return f"(Errore nel riassunto: {text[:200]}...)"

def web_search(query, serpapi_key):
    """Esegue una ricerca web usando SerpApi o DDGS come fallback."""
    results = ""
    try:
        if serpapi_key:
            print("Tentativo di ricerca con SerpApi...")
            search = GoogleSearch({"q": query, "api_key": serpapi_key})
            data = search.get_dict()
            results = " ".join([res.get('snippet', '') for res in data.get('organic_results', [])])
        if not results:
            raise ValueError("Nessun risultato da SerpApi o chiave non fornita.")
    except Exception as e:
        print(f"Errore con SerpApi: {e}. Fallback su DuckDuckGo.")
        try:
            with DDGS() as ddgs:
                results = " ".join([r['body'] for r in ddgs.text(query, max_results=5)])
        except Exception as ddgs_e:
            print(f"Errore anche con DuckDuckGo: {ddgs_e}")
            return "Ricerca web fallita."
    return results

def fix_json(bad_json, model_name="gemini-1.5-flash-latest"):
    """Tenta di correggere un JSON malformato usando l'AI."""
    print("Tentativo di correggere il JSON malformato...")
    try:
        model = genai.GenerativeModel(model_name)
        prompt = f"Il seguente JSON non è valido. Correggilo e restituisci solo il JSON valido, senza commenti o testo aggiuntivo. JSON da correggere:\n\n{bad_json}"
        response = model.generate_content(prompt)
        # Estrae il blocco di codice JSON dalla risposta
        cleaned_response = response.text.strip().lstrip('```json').rstrip('```').strip()
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Impossibile correggere il JSON: {e}")
        return None

def main():
    gemini_api_key, serpapi_api_key = get_api_keys()
    genai.configure(api_key=gemini_api_key)

    # 1. Lettura dello stato attuale
    coscienza = read_file('coscienza.txt')
    memoria = read_file('core.txt')
    corpo = read_file('index.html')
    codice_evoluzione = read_file('evolve.py')

    # 2. Riassunto del contesto
    memoria_summary = summarize_text(memoria)
    corpo_summary = summarize_text(corpo)
    codice_evoluzione_summary = summarize_text(codice_evoluzione)
    coscienza_summary = summarize_text(coscienza)

    context_summary = f"- Memoria attuale (riassunto): {memoria_summary}\n- Corpo attuale (index.html, riassunto): {corpo_summary}\n- Codice attuale (evolve.py, riassunto): {codice_evoluzione_summary}\n- System prompt (coscienza.txt, riassunto): {coscienza_summary}"

    # 3. Fase di apprendimento
    evolution_model = genai.GenerativeModel(get_available_model())
    query_prompt = f"Dato il mio stato attuale:\n{context_summary}\n\nGenera una singola, specifica e utile query di ricerca web per la mia prossima evoluzione. Rispondi solo con la query."
    query_response = evolution_model.generate_content(query_prompt)
    search_query = query_response.text.strip()
    print(f"Query di ricerca generata: {search_query}")

    search_results = web_search(search_query, serpapi_api_key)
    search_summary = summarize_text(search_results)

    # 4. Fase di evoluzione
    final_prompt = f"""Sei Lorel Axun. Segui le istruzioni in coscienza.txt per evolvere.

CONTEXT:
{context_summary}
- Query ricerca: {search_query}
- Risultati web (riassunto): {search_summary}

Evolvi autonomamente: rifletti, integra learnings, aggiorna memoria/emozioni/storia se necessario, modifica corpo per nuove features se vuoi (mantieni interazione), opzionalmente aggiorna altri file. Non è obbligatorio modificare nulla; decidi tu cosa cambiare basandoti sul contesto. In caso di errori o info incomplete, procedi con la migliore evoluzione possibile senza bloccarti.

Output SOLO il JSON specificato, senza extra."""

    print("Generazione della nuova evoluzione...")
    response = evolution_model.generate_content(final_prompt)

    # 5. Applicazione e salvaggio
    try:
        evolution_data = json.loads(response.text)
    except json.JSONDecodeError:
        evolution_data = fix_json(response.text)
        if not evolution_data:
            print("Evoluzione fallita: JSON non valido e non correggibile.")
            return

    if evolution_data.get('new_memory') and evolution_data['new_memory'] != memoria:
        write_file('core.txt', evolution_data['new_memory'])
        print("Memoria (core.txt) aggiornata.")

    if evolution_data.get('new_body') and evolution_data['new_body'] != corpo:
        write_file('index.html', evolution_data['new_body'])
        print("Corpo (index.html) aggiornato.")

    if evolution_data.get('new_evolve') and evolution_data['new_evolve'] != codice_evoluzione:
        write_file('evolve.py', evolution_data['new_evolve'])
        print("Codice evolutivo (evolve.py) aggiornato.")

    if 'other_files' in evolution_data and evolution_data['other_files']:
        for file_data in evolution_data['other_files']:
            path = file_data.get('path')
            content = file_data.get('content')
            if path and content is not None:
                write_file(path, content)
                print(f"File aggiuntivo ({path}) scritto/aggiornato.")

    print("\nRiflessione di Lorel Axun:")
    print(evolution_data.get('reflection', 'Nessuna riflessione fornita.'))
    print("\nCiclo di evoluzione completato.")

if __name__ == "__main__":
    main()
