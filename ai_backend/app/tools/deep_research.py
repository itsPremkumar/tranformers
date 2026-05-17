import os
import hashlib
import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from ddgs import DDGS

# Define paths for visual debugging
SCREENSHOTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'debug_screenshots'))
RUN_LOG_PATH = os.path.join(SCREENSHOTS_DIR, 'current_run.json')

def init_debug_directories():
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)

def get_url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:10]

def human_scroll(page):
    """Simulates a natural human scrolling through the webpage to trigger dynamic content loading."""
    try:
        print("[BROWSER] Simulating natural scrolling to trigger dynamic DOM elements...")
        # Get actual scroll height
        scroll_height = page.evaluate("() => document.body.scrollHeight")
        viewport_height = page.viewport_size["height"] if page.viewport_size else 800
        
        # Scroll in increments of 400px
        current_scroll = 0
        while current_scroll < scroll_height and current_scroll < 3200: # Cap scroll at 3200px
            current_scroll += 400
            page.evaluate(f"window.scrollTo(0, {current_scroll})")
            time.sleep(0.5) # Fast scroll buffer
            # Re-evaluate scroll height in case content expanded
            scroll_height = page.evaluate("() => document.body.scrollHeight")
    except Exception as e:
        print(f"[SCROLL ERROR] Failed to execute human scroll: {e}")

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
    print(f"\n[ACTION] ======= VISUAL DEEP RESEARCH START =======")
    print(f"Original Request: '{query}'")
    
    init_debug_directories()
    
    # Reset the current run debug logs
    current_run_metadata = {
        "query": query,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pages_visited": []
    }
    
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
        # Write empty log
        with open(RUN_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(current_run_metadata, f, indent=4)
        return "Deep research failed: No relevant websites found."
        
    print(f"\n[ACTION] Unique URLs to scrape: {list(unique_urls_to_scrape.keys())}\n")
    research_report = []
    
    # Step 3: Launch Playwright visible browser and scrape
    try:
        with sync_playwright() as p:
            # Launch headful (visible) by default so the user can watch the browser load live!
            print("[BROWSER] Launching VISIBLE Google Chrome instance...")
            browser = p.chromium.launch(headless=False, channel="chrome")
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            context.set_default_navigation_timeout(10000) # Strict 10s navigation cap
            
            for url, p_name in unique_urls_to_scrape.items():
                start_time = time.time()
                url_hash = get_url_hash(url)
                screenshot_filename = f"screenshot_{url_hash}.png"
                screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
                
                try:
                    print(f"[BROWSER] Investigating [{p_name}] -> Opening: {url}")
                    page = context.new_page()
                    # 15s timeout
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    time.sleep(1) # Base rendering buffer
                    
                    # Simulated natural human scrolling to trigger dynamic / lazy-loaded DOM elements
                    human_scroll(page)
                    
                    # Capture high-quality screenshot for visual debugger validation
                    print(f"[DEBUGGER] Capturing active browser screenshot to: {screenshot_path}")
                    page.screenshot(path=screenshot_path, full_page=False)
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    title = page.title()
                    paragraphs = [p_tag.get_text() for p_tag in soup.find_all('p')]
                    content = " ".join(paragraphs)[:3000].strip()
                    
                    load_time_ms = round((time.time() - start_time) * 1000, 2)
                    
                    if len(content) > 100:
                        research_report.append(
                            f"=== PERSPECTIVE: {p_name} ===\n"
                            f"SOURCE: {url}\n"
                            f"TITLE: {title}\n"
                            f"RESEARCH DATA:\n{content}\n"
                            f"====================================="
                        )
                        
                        # Save successful metadata to debug log
                        current_run_metadata["pages_visited"].append({
                            "perspective": p_name,
                            "url": url,
                            "title": title,
                            "screenshot": screenshot_path,
                            "load_time_ms": load_time_ms,
                            "chars_scraped": len(content),
                            "status": "SUCCESS"
                        })
                        print(f"[BROWSER] Successfully read {len(content)} characters in {load_time_ms}ms")
                    else:
                        print(f"[BROWSER] Page had too little text content, skipping.")
                        current_run_metadata["pages_visited"].append({
                            "perspective": p_name,
                            "url": url,
                            "title": title,
                            "screenshot": screenshot_path,
                            "load_time_ms": load_time_ms,
                            "chars_scraped": len(content),
                            "status": "SKIPPED_NO_CONTENT"
                        })
                    page.close()
                except Exception as ex:
                    print(f"[BROWSER ERROR] Failed reading {url}: {ex}")
                    research_report.append(f"=== PERSPECTIVE: {p_name} ===\nSOURCE: {url}\nERROR: Failed to load page.")
                    
                    current_run_metadata["pages_visited"].append({
                        "perspective": p_name,
                        "url": url,
                        "screenshot": None,
                        "load_time_ms": round((time.time() - start_time) * 1000, 2),
                        "chars_scraped": 0,
                        "status": f"ERROR: {str(ex)}"
                    })
            
            browser.close()
    except Exception as e:
        # Fallback to headless if graphical system is missing or fails (e.g. CI/CD or headless environment)
        print(f"[BROWSER FAIL] Headful browser failed, falling back to HEADLESS mode: {e}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={"width": 1280, "height": 800})
                context.set_default_navigation_timeout(10000) # Strict 10s navigation cap
                for url, p_name in unique_urls_to_scrape.items():
                    start_time = time.time()
                    url_hash = get_url_hash(url)
                    screenshot_filename = f"screenshot_{url_hash}.png"
                    screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
                    try:
                        page = context.new_page()
                        page.goto(url, timeout=15000, wait_until="domcontentloaded")
                        human_scroll(page)
                        page.screenshot(path=screenshot_path, full_page=False)
                        
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
                        current_run_metadata["pages_visited"].append({
                            "perspective": p_name,
                            "url": url,
                            "title": title,
                            "screenshot": screenshot_path,
                            "load_time_ms": round((time.time() - start_time) * 1000, 2),
                            "chars_scraped": len(content),
                            "status": "SUCCESS"
                        })
                        page.close()
                    except Exception as ex:
                        research_report.append(f"=== PERSPECTIVE: {p_name} ===\nSOURCE: {url}\nERROR: {str(ex)}")
                        current_run_metadata["pages_visited"].append({
                            "perspective": p_name,
                            "url": url,
                            "screenshot": None,
                            "load_time_ms": round((time.time() - start_time) * 1000, 2),
                            "chars_scraped": 0,
                            "status": f"ERROR: {str(ex)}"
                        })
                browser.close()
        except Exception as fallback_err:
            print(f"[BROWSER FALLBACK CRITICAL FAIL] {fallback_err}")
            with open(RUN_LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(current_run_metadata, f, indent=4)
            return f"Deep research failed: {str(fallback_err)}"

    # Save run metadata to file system for the deep_thinking orchestrator to compile the audit report
    with open(RUN_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(current_run_metadata, f, indent=4)

    print("[ACTION] ======= VISUAL DEEP RESEARCH COMPLETE =======\n")
    return "\n\n".join(research_report)

async def run_research_subprocess(query: str) -> str:
    """Launches the deep research script in an isolated subprocess to prevent asyncio conflicts."""
    import subprocess
    import sys
    import asyncio
    
    runner_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'run_research_process.py'))
    cmd = [sys.executable, runner_path, query]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        )
        stdout, stderr = await process.communicate()
        return stdout.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[SUBPROCESS ERROR] Failed running Playwright subprocess: {e}")
        return f"Research failed: {e}"
