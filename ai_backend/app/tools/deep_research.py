from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from ddgs import DDGS
import time

def deep_research(query: str) -> str:
    """Performs deep research on a topic by opening a visible browser, navigating to multiple top websites, and reading their full articles."""
    print(f"\n[ACTION] ======= DEEP RESEARCH AGENT START =======\nQuery: '{query}'")
    
    # Step 1: Find best links using DuckDuckGo
    urls = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            urls = [r['href'] for r in results if 'href' in r]
    except Exception as e:
        print(f"[SEARCH ERROR] Could not get search results: {e}")
        return f"Research failed: {str(e)}"
        
    if not urls:
        print("[SEARCH ERROR] No relevant URLs found.")
        return "Deep research failed: No relevant websites found."
        
    print(f"[ACTION] URLs Found for Deep Scrape: {urls}")
    research_report = []
    
    # Step 2: Launch browser and read DOM
    try:
        with sync_playwright() as p:
            # Launch headful (visible) by default so the user can watch the robot learn live!
            print("[BROWSER] Launching VISIBLE Chrome instance...")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            for url in urls:
                try:
                    print(f"[BROWSER] Opening Tab & Navigating to: {url}")
                    page = context.new_page()
                    # 15s timeout
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    time.sleep(2) # Wait for page hydration
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title and paragraph texts
                    title = page.title()
                    paragraphs = [p_tag.get_text() for p_tag in soup.find_all('p')]
                    
                    # Merge paragraphs (up to 3000 chars per page to avoid prompt blowup)
                    content = " ".join(paragraphs)[:3000].strip()
                    
                    if len(content) > 100:
                        research_report.append(f"SOURCE: {url}\nTITLE: {title}\nCONTENT:\n{content}\n---")
                        print(f"[BROWSER] Successfully read {len(content)} characters from {title}")
                    else:
                        print(f"[BROWSER] Page had too little text content, skipping.")
                    page.close()
                except Exception as ex:
                    print(f"[BROWSER ERROR] Failed reading {url}: {ex}")
                    research_report.append(f"SOURCE: {url}\nERROR: Failed to load page or extract content.")
            
            browser.close()
    except Exception as e:
        # Fallback to headless if graphical system is missing or fails (e.g. CI/CD or headless environment)
        print(f"[BROWSER FAIL] Headful browser failed, falling back to HEADLESS mode: {e}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                for url in urls:
                    try:
                        page = context.new_page()
                        page.goto(url, timeout=15000, wait_until="domcontentloaded")
                        html = page.content()
                        soup = BeautifulSoup(html, 'html.parser')
                        title = page.title()
                        content = " ".join([p_tag.get_text() for p_tag in soup.find_all('p')])[:3000].strip()
                        research_report.append(f"SOURCE: {url}\nTITLE: {title}\nCONTENT:\n{content}\n---")
                        page.close()
                    except Exception as ex:
                        research_report.append(f"SOURCE: {url}\nERROR: {str(ex)}")
                browser.close()
        except Exception as fallback_err:
            print(f"[BROWSER FALLBACK CRITICAL FAIL] {fallback_err}")
            return f"Deep research failed: {str(fallback_err)}"

    print("[ACTION] ======= DEEP RESEARCH AGENT COMPLETE =======\n")
    return "\n\n".join(research_report)
