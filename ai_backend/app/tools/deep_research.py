from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from ddgs import DDGS
import time

def generate_perspectives(query: str) -> dict:
    """Generates 3 distinct search queries/perspectives based on the topic type for exhaustive research."""
    q_low = query.lower()
    
    # 1. Scientific & Technical Problems
    if any(k in q_low for k in ["science", "physics", "solve", "how to", "mechanism", "why does", "explain", "chemical", "quantum", "theory", "robot", "battery"]):
        return {
            "Technical/Core Mechanism": query,
            "Scientific Challenges & Critiques": f"{query} scientific challenges critique limitations",
            "Latest Research & Solutions 2026": f"{query} latest research papers breakthroughs 2026"
        }
    # 2. News, Weather & Live Events
    elif any(k in q_low for k in ["news", "latest", "current", "weather", "today", "recent", "event", "happened", "president", "election"]):
        return {
            "Current Status & Live Updates": f"{query} latest live updates",
            "Background Context & History": f"{query} history context background timeline",
            "Public Response & Future Outlook": f"{query} reaction analysis future outlook"
        }
    # 3. Default / General Concepts
    else:
        return {
            "General Overview": query,
            "Latest Technological Advancements": f"{query} latest news technology advancements 2026",
            "Alternative Perspectives & Applications": f"{query} alternative viewpoints applications use cases"
        }

def deep_research(query: str) -> str:
    """Performs advanced, multi-perspective deep research by launching a visible browser and investigating different angles."""
    print(f"\n[ACTION] ======= MULTI-PERSPECTIVE DEEP RESEARCH START =======")
    print(f"Original Request: '{query}'")
    
    # Step 1: Generate 3 research perspectives
    perspectives = generate_perspectives(query)
    print("\n[RESEARCH PLAN] Generated 3 Exhaustive Research Perspectives:")
    for name, q in perspectives.items():
        print(f"  - {name}: '{q}'")
    print("")
    
    all_sources = {}
    
    # Step 2: Gather unique URLs for each perspective
    with DDGS() as ddgs:
        for p_name, p_query in perspectives.items():
            try:
                print(f"[SEARCH] Searching for perspective '{p_name}'...")
                results = list(ddgs.text(p_query, max_results=2))
                urls = [r['href'] for r in results if 'href' in r]
                all_sources[p_name] = urls
            except Exception as e:
                print(f"[SEARCH ERROR] Could not fetch results for '{p_name}': {e}")
                all_sources[p_name] = []
                
    # Flatten unique URLs to avoid scraping the same site twice
    unique_urls_to_scrape = {}
    for p_name, urls in all_sources.items():
        for url in urls:
            if url not in unique_urls_to_scrape:
                unique_urls_to_scrape[url] = p_name

    if not unique_urls_to_scrape:
        print("[SEARCH ERROR] No URLs found across any perspectives.")
        return "Deep research failed: No relevant websites found."
        
    print(f"\n[ACTION] Unique URLs to scrape: {list(unique_urls_to_scrape.keys())}\n")
    research_report = []
    
    # Step 3: Launch Playwright visible browser and scrape
    try:
        with sync_playwright() as p:
            # Launch headful (visible) by default so the user can watch the robot learn live!
            print("[BROWSER] Launching VISIBLE Chrome instance...")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            for url, p_name in unique_urls_to_scrape.items():
                try:
                    print(f"[BROWSER] Investigating [{p_name}] -> Opening: {url}")
                    page = context.new_page()
                    # 15s timeout
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    time.sleep(2) # Wait for page hydration
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    title = page.title()
                    paragraphs = [p_tag.get_text() for p_tag in soup.find_all('p')]
                    content = " ".join(paragraphs)[:3000].strip()
                    
                    if len(content) > 100:
                        research_report.append(
                            f"=== PERSPECTIVE: {p_name} ===\n"
                            f"SOURCE: {url}\n"
                            f"TITLE: {title}\n"
                            f"RESEARCH DATA:\n{content}\n"
                            f"====================================="
                        )
                        print(f"[BROWSER] Successfully read {len(content)} characters for perspective: {p_name}")
                    else:
                        print(f"[BROWSER] Page had too little text content, skipping.")
                    page.close()
                except Exception as ex:
                    print(f"[BROWSER ERROR] Failed reading {url}: {ex}")
                    research_report.append(f"=== PERSPECTIVE: {p_name} ===\nSOURCE: {url}\nERROR: Failed to load page.")
            
            browser.close()
    except Exception as e:
        # Fallback to headless if graphical system is missing or fails (e.g. CI/CD or headless environment)
        print(f"[BROWSER FAIL] Headful browser failed, falling back to HEADLESS mode: {e}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                for url, p_name in unique_urls_to_scrape.items():
                    try:
                        page = context.new_page()
                        page.goto(url, timeout=15000, wait_until="domcontentloaded")
                        html = page.content()
                        soup = BeautifulSoup(html, 'html.parser')
                        title = page.title()
                        content = " ".join([p_tag.get_text() for p_tag in soup.find_all('p')])[:3000].strip()
                        research_report.append(
                            f"=== PERSPECTIVE: {p_name} ===\n"
                            f"SOURCE: {url}\n"
                            f"TITLE: {title}\n"
                            f"RESEARCH DATA:\n{content}\n"
                            f"====================================="
                        )
                        page.close()
                    except Exception as ex:
                        research_report.append(f"=== PERSPECTIVE: {p_name} ===\nSOURCE: {url}\nERROR: {str(ex)}")
                browser.close()
        except Exception as fallback_err:
            print(f"[BROWSER FALLBACK CRITICAL FAIL] {fallback_err}")
            return f"Deep research failed: {str(fallback_err)}"

    print("[ACTION] ======= MULTI-PERSPECTIVE DEEP RESEARCH COMPLETE =======\n")
    return "\n\n".join(research_report)
