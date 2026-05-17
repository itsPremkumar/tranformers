import os
import json
import time
from ddgs import DDGS
from playwright.sync_api import sync_playwright

from app.tools.research_engine.query_expansion import expand_research_queries
from app.tools.research_engine.agentic_scraper import agentic_follow_links
from app.tools.research_engine.memory_vault import MemoryVault
from app.tools.research_engine.pdf_parser import extract_pdf_content
from app.tools.research_engine.telemetry_analytics import analyze_hardware_telemetry

# Initialize Persistent Vault
vault = MemoryVault()

# We will import these from the original deep_research to reuse existing code where possible,
# or we can redefine the semantics. For simplicity in refactoring, we import the existing helpers:
import app.tools.deep_research as legacy_dr

def execute_advanced_research(query: str, is_telemetry: bool = False) -> str:
    """
    The New Master Controller for Advanced Research.
    """
    print(f"\n[ORCHESTRATOR] ======= ADVANCED AGENTIC RESEARCH START =======")
    
    # Feature 5: Telemetry Interception
    if is_telemetry or query.startswith("{") and "battery_level" in query:
        print("[ORCHESTRATOR] Detected Hardware Telemetry payload.")
        return analyze_hardware_telemetry(query)
        
    # Feature 3: Check Persistent Memory Vault First
    past_knowledge = vault.retrieve_knowledge(query)
    if past_knowledge:
        print("[ORCHESTRATOR] Found exact match in Hermes Memory Vault. Accelerating response.")
        vault_report = "=== HERMES MEMORY VAULT RECALL ===\n"
        vault_report += f"The robot already possesses knowledge regarding this query from past research:\n\n"
        vault_report += "\n".join(past_knowledge)
        vault_report += "\n=====================================\n"
        # We append this to the final report, but we still search for live news to be safe.
    else:
        vault_report = ""

    # Feature 1: RAG Query Expansion
    perspectives = expand_research_queries(query)
    
    all_sources = {}
    with DDGS() as ddgs:
        for p_name, p_query in perspectives.items():
            try:
                results = list(ddgs.text(p_query, max_results=2))
                urls = [r['href'] for r in results if 'href' in r]
                all_sources[p_name] = urls
            except Exception:
                all_sources[p_name] = []

    unique_urls = {}
    for p_name, urls in all_sources.items():
        for url in urls:
            if url not in unique_urls:
                unique_urls[url] = p_name

    research_report = [vault_report] if vault_report else []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            
            for url, p_name in unique_urls.items():
                # Feature 4: Academic PDF Parsing
                if url.endswith(".pdf") or "arxiv.org/pdf" in url:
                    pdf_text = extract_pdf_content(url)
                    if pdf_text:
                        clean_pdf = legacy_dr.semantic_rerank_text(pdf_text, query, 3000)
                        research_report.append(
                            f"=== PERSPECTIVE: {p_name} ===\nSOURCE: {url} (PDF EXTRACTION)\n"
                            f"RESEARCH DATA:\n{clean_pdf}\n====================================="
                        )
                        vault.store_knowledge(url, clean_pdf, p_name)
                    continue
                
                try:
                    page = context.new_page()
                    legacy_dr.stealth_override(page)
                    page.goto(url, timeout=10000, wait_until="domcontentloaded")
                    
                    html = page.content()
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Feature 2: Multi-Step Agentic Loop
                    soup = agentic_follow_links(page, html, soup, url)
                    
                    paragraphs = [p_tag.get_text() for p_tag in soup.find_all('p')]
                    raw_text = " ".join(paragraphs)
                    
                    clean_text = legacy_dr.semantic_rerank_text(raw_text, query, 3000)
                    
                    if len(clean_text) > 100:
                        research_report.append(
                            f"=== PERSPECTIVE: {p_name} ===\nSOURCE: {url}\n"
                            f"RESEARCH DATA:\n{clean_text}\n====================================="
                        )
                        # Feature 3: Store in Vault
                        vault.store_knowledge(url, clean_text, p_name)
                        
                    page.close()
                except Exception as e:
                    print(f"[ORCHESTRATOR ERROR] Failed processing {url}: {e}")
            browser.close()
    except Exception as e:
        print(f"[ORCHESTRATOR FATAL] {e}")

    return "\n\n".join(research_report)
