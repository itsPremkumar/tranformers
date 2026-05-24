import os
import time
import random
from duckduckgo_search import DDGS
import wikipedia
import pywhatkit
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def stealth_override(page):
    """Applies high-level anti-bot evasion and browser signature masking (Stealth mode)."""
    try:
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        # Mock WebGL vendor to hide swiftshader/headless signatures
        page.add_init_script("""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter.apply(this, arguments);
            };
        """)
    except Exception as e:
        print(f"[STEALTH ERROR] Failed applying overrides: {e}")

def human_like_web_search(query: str) -> str:
    """
    Performs a human-like web search by opening a browser, navigating to a search engine,
    focusing the search bar, typing the query character-by-character with random delays,
    pressing Enter, waiting for results, and extracting the snippets.
    """
    print(f"[HUMAN SEARCH] Initiating visual web search for query: '{query}'")
    
    # We will try Google first, and fall back to DuckDuckGo if Google blocks us or fails.
    engines = ["google", "duckduckgo"]
    results_text = []
    
    # Base directory relative to app
    current_dir = os.path.dirname(os.path.abspath(__file__))
    screenshots_dir = os.path.abspath(os.path.join(current_dir, "..", "debug_screenshots"))
    try:
        os.makedirs(screenshots_dir, exist_ok=True)
    except Exception as e:
        print(f"[HUMAN SEARCH WARNING] Could not create screenshots directory: {e}")

    for engine in engines:
        try:
            with sync_playwright() as p:
                print(f"[HUMAN SEARCH] Launching browser for {engine} search...")
                # Launch headful chromium (visible on screen). Fallback to headless if it fails.
                try:
                    browser = p.chromium.launch(headless=False)
                except Exception as launch_err:
                    print(f"[HUMAN SEARCH WARNING] Headful launch failed, trying headless: {launch_err}")
                    browser = p.chromium.launch(headless=True)
                
                context = browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                context.set_default_navigation_timeout(15000)
                
                page = context.new_page()
                stealth_override(page)
                
                if engine == "google":
                    print("[HUMAN SEARCH] Navigating to Google homepage...")
                    page.goto("https://www.google.com", wait_until="domcontentloaded")
                    time.sleep(random.uniform(1.0, 2.0))
                    
                    # Detect if Google blocked us immediately (e.g. CAPTCHA)
                    html = page.content()
                    if "captcha" in html.lower() or "unusual traffic" in html.lower():
                        print("[HUMAN SEARCH WARNING] Google CAPTCHA wall detected! Switching to DuckDuckGo...")
                        browser.close()
                        continue
                    
                    # Google search input element can be textarea[name="q"] or input[name="q"]
                    search_input_selector = 'textarea[name="q"], input[name="q"]'
                    try:
                        page.wait_for_selector(search_input_selector, timeout=5000)
                    except Exception:
                        print("[HUMAN SEARCH WARNING] Google search bar not found. Switching to DuckDuckGo...")
                        browser.close()
                        continue
                        
                    # Simulating human focus & click
                    page.click(search_input_selector)
                    time.sleep(random.uniform(0.2, 0.5))
                    
                    # Simulate human typing
                    print(f"[HUMAN SEARCH] Simulating human typing on Google for: '{query}'")
                    page.type(search_input_selector, query, delay=random.randint(60, 150))
                    time.sleep(random.uniform(0.5, 1.0))
                    
                    # Press Enter
                    page.press(search_input_selector, "Enter")
                    
                    # Wait for results to load
                    try:
                        page.wait_for_selector("#rso, div#search", timeout=8000)
                    except Exception:
                        # Check again for captcha
                        if "captcha" in page.content().lower():
                            print("[HUMAN SEARCH WARNING] Google CAPTCHA triggered on search submit. Switching to DuckDuckGo...")
                            browser.close()
                            continue
                        raise Exception("Google results failed to load in time.")
                    
                    # Extract search results
                    soup = BeautifulSoup(page.content(), "html.parser")
                    # Capture screenshot for visual audit
                    try:
                        screenshot_path = os.path.join(screenshots_dir, f"human_search_google_{int(time.time())}.png")
                        page.screenshot(path=screenshot_path)
                        print(f"[HUMAN SEARCH] Screenshot saved to {screenshot_path}")
                    except Exception as se:
                        print(f"[HUMAN SEARCH WARNING] Failed to capture Google screenshot: {se}")
                    
                    search_results = soup.select("#rso div.g")
                    for res in search_results[:3]:
                        # Try finding title & link
                        title_el = res.select_one("h3")
                        link_el = res.select_one("a[href]")
                        snippet_el = res.select_one("div[style*='-webkit-line-clamp'], .VwiC3b, .yGrid")
                        
                        if title_el and link_el:
                            title = title_el.get_text().strip()
                            url = link_el["href"]
                            snippet = snippet_el.get_text().strip() if snippet_el else ""
                            results_text.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}")
                            
                elif engine == "duckduckgo":
                    print("[HUMAN SEARCH] Navigating to DuckDuckGo homepage...")
                    page.goto("https://duckduckgo.com", wait_until="domcontentloaded")
                    time.sleep(random.uniform(1.0, 2.0))
                    
                    search_input_selector = 'input[name="q"], input#searchbox_input'
                    try:
                        page.wait_for_selector(search_input_selector, timeout=5000)
                    except Exception:
                        print("[HUMAN SEARCH WARNING] DuckDuckGo search bar not found.")
                        browser.close()
                        continue
                        
                    # Simulating human focus & click
                    page.click(search_input_selector)
                    time.sleep(random.uniform(0.2, 0.5))
                    
                    # Simulate human typing
                    print(f"[HUMAN SEARCH] Simulating human typing on DuckDuckGo for: '{query}'")
                    page.type(search_input_selector, query, delay=random.randint(60, 150))
                    time.sleep(random.uniform(0.5, 1.0))
                    
                    # Press Enter
                    page.press(search_input_selector, "Enter")
                    
                    # Wait for results to load
                    try:
                        page.wait_for_selector('article[data-testid="result"], .result__body', timeout=8000)
                    except Exception:
                        raise Exception("DuckDuckGo results failed to load in time.")
                    
                    # Extract search results
                    soup = BeautifulSoup(page.content(), "html.parser")
                    try:
                        screenshot_path = os.path.join(screenshots_dir, f"human_search_ddg_{int(time.time())}.png")
                        page.screenshot(path=screenshot_path)
                        print(f"[HUMAN SEARCH] Screenshot saved to {screenshot_path}")
                    except Exception as se:
                        print(f"[HUMAN SEARCH WARNING] Failed to capture DDG screenshot: {se}")
                    
                    # DuckDuckGo visual search selectors
                    search_results = soup.select('article[data-testid="result"]') or soup.select(".result__body")
                    for res in search_results[:3]:
                        title_el = res.select_one('h2 a, a[data-testid="result-title-a"]')
                        snippet_el = res.select_one('div[data-testid="result-snippet"], .result__snippet')
                        
                        if title_el:
                            title = title_el.get_text().strip()
                            url = title_el.get("href", "")
                            snippet = snippet_el.get_text().strip() if snippet_el else ""
                            results_text.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}")
                
                browser.close()
                if results_text:
                    print(f"[HUMAN SEARCH SUCCESS] Extracted {len(results_text)} results from {engine}.")
                    return "\n\n".join(results_text)
                    
        except Exception as e:
            print(f"[HUMAN SEARCH ERROR] Engine {engine} search failed: {e}")
            
    # Fallback to standard DDGS API Search if all automated visual searches fail
    print("[HUMAN SEARCH] Visual browser search failed or was blocked. Falling back to DuckDuckGo API search...")
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results)
    except Exception as e:
        return f"Search error: {str(e)}"

def web_search(query: str):
    """Searches the live internet with human-like visual browsing simulation."""
    print(f"[ACTION] Web Search: {query}")
    try:
        return human_like_web_search(query)
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
