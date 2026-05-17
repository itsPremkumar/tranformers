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

def stealth_override(page):
    """Injects client evasive mocks into the page context to bypass Cloudflare/anti-bot challenge screens."""
    try:
        print("[STEALTH] Applying automation signature evasion overrides...")
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

def harvest_seo_geo_metadata(soup) -> dict:
    """Extracts high-density meta schemas, OpenGraph descriptions, and JSON-LD structural data optimized for SEO/GEO/AEO."""
    meta_data = {
        "description": "",
        "og_description": "",
        "json_ld_summary": ""
    }
    try:
        # Extract Standard Meta Description (SEO/AEO card)
        desc_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'name': 'Description'})
        if desc_tag and desc_tag.get('content'):
            meta_data["description"] = desc_tag.get('content').strip()
            
        # Extract OpenGraph Description (GEO card)
        og_tag = soup.find('meta', attrs={'property': 'og:description'})
        if og_tag and og_tag.get('content'):
            meta_data["og_description"] = og_tag.get('content').strip()
            
        # Extract JSON-LD Struct Data (Dense Technical schemas)
        json_ld_tags = soup.find_all('script', type='application/ld+json')
        ld_summaries = []
        for tag in json_ld_tags:
            try:
                js_data = json.loads(tag.string)
                if isinstance(js_data, dict):
                    for field in ["description", "articleBody", "abstract", "headline"]:
                        if js_data.get(field):
                            ld_summaries.append(str(js_data.get(field)))
                elif isinstance(js_data, list):
                    for item in js_data:
                        if isinstance(item, dict):
                            for field in ["description", "articleBody", "abstract", "headline"]:
                                if item.get(field):
                                    ld_summaries.append(str(item.get(field)))
            except:
                pass
        if ld_summaries:
            meta_data["json_ld_summary"] = " | ".join(ld_summaries)[:1500]
    except Exception as e:
        print(f"[METADATA HARVEST ERROR] {e}")
    return meta_data

def grade_research_content(html: str, content: str, title: str) -> tuple[int, str]:
    """Scores the quality of the scraped research page from 0 to 100 and returns a detailed quality rationale.
    Detects Cloudflare connection challenges, bot block pages, and low text density.
    """
    score = 100
    reasons = []
    
    # 1. Detect anti-bot blockers (Immediate Low Quality Grade)
    blocked_keywords = [
        "checking your connection", 
        "checking your browser", 
        "cloudflare", 
        "enable javascript", 
        "access denied", 
        "attention required",
        "just a moment..."
    ]
    
    html_lower = html.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    if any(kw in html_lower or kw in title_lower or kw in content_lower for kw in blocked_keywords):
        return 0, "BLOCKED: Anti-bot / Cloudflare connection check challenge page detected."
        
    # 2. Grade text length
    content_len = len(content)
    if content_len < 100:
        score -= 60
        reasons.append(f"Severely low content length ({content_len} chars)")
    elif content_len < 500:
        score -= 30
        reasons.append(f"Low content length ({content_len} chars)")
    elif content_len > 2500:
        score += 10 # Rich text density bonus
        reasons.append("Rich high-density content")
        
    # 3. Grade title context
    if not title or len(title) < 5 or "attention required" in title_lower:
        score -= 20
        reasons.append("Missing or generic webpage title")
        
    score = max(0, min(100, score))
    rationale = ", ".join(reasons) if reasons else "High quality research page"
    return score, rationale

def human_scroll(page):
    """Simulates a natural human scrolling through the webpage to trigger dynamic content loading."""
    try:
        print("[BROWSER] Simulating natural scrolling to trigger dynamic DOM elements...")
        # Get actual scroll height
        scroll_height = page.evaluate("() => document.body.scrollHeight")
        
        # Scroll in increments of 500px
        current_scroll = 0
        while current_scroll < scroll_height and current_scroll < 4000: # Cap scroll at 4000px
            current_scroll += 500
            page.evaluate(f"window.scrollTo(0, {current_scroll})")
            time.sleep(0.4) # Human scroll render buffer
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
    """Performs advanced, multi-perspective deep research by launching a visible browser with anti-bot overrides."""
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
    url_snippets = {} # Cache DuckDuckGo search snippets to act as SEO fallback if browser gets Cloudflare-blocked!
    
    # Step 2: Gather unique URLs and snippets
    with DDGS() as ddgs:
        for p_name, p_query in perspectives.items():
            try:
                print(f"[SEARCH] Searching for perspective '{p_name}'...")
                results = list(ddgs.text(p_query, max_results=2))
                urls = []
                for r in results:
                    if 'href' in r:
                        urls.append(r['href'])
                        url_snippets[r['href']] = r.get('body', '')
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
        with open(RUN_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(current_run_metadata, f, indent=4)
        return "Deep research failed: No relevant websites found."
        
    print(f"\n[ACTION] Unique URLs to scrape: {list(unique_urls_to_scrape.keys())}\n")
    research_report = []
    
    # Step 3: Launch Playwright browser and scrape
    try:
        with sync_playwright() as p:
            print("[BROWSER] Launching VISIBLE Google Chrome instance with Stealth Evasion...")
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
                    stealth_override(page) # Inject anti-bot signature overrides
                    
                    page.goto(url, timeout=12000, wait_until="domcontentloaded")
                    time.sleep(1.5) # Base rendering buffer
                    
                    # Human scroll
                    human_scroll(page)
                    
                    # Capture FULL PAGE visual debugger screenshot
                    print(f"[DEBUGGER] Capturing FULL PAGE visual screenshot to: {screenshot_path}")
                    page.screenshot(path=screenshot_path, full_page=True)
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    title = page.title()
                    
                    # Scrape DOM content
                    paragraphs = [p_tag.get_text() for p_tag in soup.find_all('p')]
                    content = " ".join(paragraphs)[:3000].strip()
                    
                    # Harvest SEO/GEO/AEO Structured schemas
                    metadata = harvest_seo_geo_metadata(soup)
                    
                    # Run Content Grader
                    grade, rationale = grade_research_content(html, content, title)
                    load_time_ms = round((time.time() - start_time) * 1000, 2)
                    
                    # Content check
                    if grade >= 40:
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
                            "load_time_ms": load_time_ms,
                            "chars_scraped": len(content),
                            "status": f"SUCCESS (Grade: {grade}/100)",
                            "seo_metadata": metadata,
                            "scraped_content": content
                        })
                        print(f"[BROWSER] Successfully scraped high quality page (Grade: {grade}) in {load_time_ms}ms")
                    else:
                        # FALLBACK ROUTE: Low grade or Cloudflare block detected! Activate search snippets
                        fallback_text = url_snippets.get(url, "Alternative rich content snippet.")
                        seo_desc = metadata["description"] or metadata["og_description"] or "AEO Optimized Web Result"
                        print(f"[GRADER ALERT] Low quality or Cloudflare block detected (Grade: {grade}). Activating clean search-snippet fallback...")
                        
                        research_report.append(
                            f"=== PERSPECTIVE: {p_name} ===\n"
                            f"SOURCE: {url} (Clean SEO Fallback)\n"
                            f"TITLE: {title or 'SEO Scraped Page'}\n"
                            f"METADATA SUMMARY: {seo_desc}\n"
                            f"RESEARCH DATA:\n{fallback_text}\n"
                            f"====================================="
                        )
                        current_run_metadata["pages_visited"].append({
                            "perspective": p_name,
                            "url": url,
                            "title": title or "Blocked/Protected Webpage",
                            "screenshot": screenshot_path,
                            "load_time_ms": load_time_ms,
                            "chars_scraped": len(fallback_text),
                            "status": f"FALLBACK_AEO (Browser Grade: {grade}/100)",
                            "seo_metadata": metadata,
                            "scraped_content": fallback_text
                        })
                    page.close()
                except Exception as ex:
                    print(f"[BROWSER ERROR] Scraper thread failed reading {url}: {ex}")
                    fallback_text = url_snippets.get(url, "Alternative fallback context.")
                    research_report.append(
                        f"=== PERSPECTIVE: {p_name} ===\n"
                        f"SOURCE: {url} (Clean Scrape Fallback)\n"
                        f"RESEARCH DATA:\n{fallback_text}\n"
                        f"====================================="
                    )
                    current_run_metadata["pages_visited"].append({
                        "perspective": p_name,
                        "url": url,
                        "screenshot": None,
                        "load_time_ms": round((time.time() - start_time) * 1000, 2),
                        "chars_scraped": len(fallback_text),
                        "status": f"FALLBACK_ERROR: {str(ex)}",
                        "scraped_content": fallback_text
                    })
            browser.close()
    except Exception as e:
        # Fallback to headless if graphical system is missing or fails (e.g. CI/CD or headless environment)
        print(f"[BROWSER FAIL] Headful browser failed, falling back to HEADLESS mode: {e}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={"width": 1280, "height": 800})
                context.set_default_navigation_timeout(10000)
                
                for url, p_name in unique_urls_to_scrape.items():
                    start_time = time.time()
                    url_hash = get_url_hash(url)
                    screenshot_filename = f"screenshot_{url_hash}.png"
                    screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
                    
                    try:
                        page = context.new_page()
                        stealth_override(page)
                        
                        page.goto(url, timeout=12000, wait_until="domcontentloaded")
                        human_scroll(page)
                        
                        page.screenshot(path=screenshot_path, full_page=True)
                        
                        html = page.content()
                        soup = BeautifulSoup(html, 'html.parser')
                        title = page.title()
                        paragraphs = [p_tag.get_text() for p_tag in soup.find_all('p')]
                        content = " ".join(paragraphs)[:3000].strip()
                        
                        metadata = harvest_seo_geo_metadata(soup)
                        grade, rationale = grade_research_content(html, content, title)
                        load_time_ms = round((time.time() - start_time) * 1000, 2)
                        
                        if grade >= 40:
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
                                "load_time_ms": load_time_ms,
                                "chars_scraped": len(content),
                                "status": f"SUCCESS (Grade: {grade}/100)",
                                "seo_metadata": metadata,
                                "scraped_content": content
                            })
                        else:
                            fallback_text = url_snippets.get(url, "Alternative rich content snippet.")
                            seo_desc = metadata["description"] or metadata["og_description"] or "AEO Optimized Web Result"
                            research_report.append(
                                f"=== PERSPECTIVE: {p_name} ===\n"
                                f"SOURCE: {url} (Clean SEO Fallback)\n"
                                f"TITLE: {title or 'SEO Scraped Page'}\n"
                                f"METADATA SUMMARY: {seo_desc}\n"
                                f"RESEARCH DATA:\n{fallback_text}\n"
                                f"====================================="
                            )
                            current_run_metadata["pages_visited"].append({
                                "perspective": p_name,
                                "url": url,
                                "title": title or "Blocked/Protected Webpage",
                                "screenshot": screenshot_path,
                                "load_time_ms": load_time_ms,
                                "chars_scraped": len(fallback_text),
                                "status": f"FALLBACK_AEO (Browser Grade: {grade}/100)",
                                "seo_metadata": metadata,
                                "scraped_content": fallback_text
                            })
                        page.close()
                    except Exception as ex:
                        fallback_text = url_snippets.get(url, "Alternative fallback context.")
                        research_report.append(
                            f"=== PERSPECTIVE: {p_name} ===\n"
                            f"SOURCE: {url} (Clean Scrape Fallback)\n"
                            f"RESEARCH DATA:\n{fallback_text}\n"
                            f"====================================="
                        )
                        current_run_metadata["pages_visited"].append({
                            "perspective": p_name,
                            "url": url,
                            "screenshot": None,
                            "load_time_ms": round((time.time() - start_time) * 1000, 2),
                            "chars_scraped": len(fallback_text),
                            "status": f"FALLBACK_ERROR: {str(ex)}",
                            "scraped_content": fallback_text
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
