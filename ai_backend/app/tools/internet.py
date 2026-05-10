from duckduckgo_search import DDGS
import wikipedia
import pywhatkit

def web_search(query: str):
    """Searches the live internet."""
    print(f"[ACTION] Web Search: {query}")
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results)
    except Exception as e:
        return f"Search error: {str(e)}"

def wiki_lookup(topic: str):
    """Wikipedia summary lookup."""
    try:
        return wikipedia.summary(topic, sentences=2)
    except:
        return "Topic not found on Wikipedia."

def play_youtube(song_name: str):
    """Plays media on YouTube."""
    try:
        pywhatkit.playonyt(song_name)
        return f"Playing '{song_name}' on YouTube."
    except:
        return "Failed to play YouTube media."
