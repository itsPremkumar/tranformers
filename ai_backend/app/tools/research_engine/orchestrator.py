import os
import json
import time
import re
from duckduckgo_search import DDGS
from playwright.sync_api import sync_playwright

from app.tools.research_engine.query_expansion import expand_research_queries
from app.tools.research_engine.agentic_scraper import agentic_follow_links
from app.tools.research_engine.memory_vault import MemoryVault
from app.tools.research_engine.pdf_parser import extract_pdf_content
from app.tools.research_engine.telemetry_analytics import analyze_hardware_telemetry

# Initialize Persistent Vault
vault = MemoryVault()

import app.tools.deep_research as legacy_dr

def cross_encoder_rerank(text: str, query: str, max_chars: int = 3000) -> str:
    """
    Highly advanced Semantic Term-Frequency Cross-Encoder.
    Splits text into paragraphs, scores them using query-token density,
    unique keyword overlaps, and semantic matching, then returns the highest-scoring blocks.
    """
    if not text or not query:
        return ""
        
    # Split text into clean paragraphs
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 40]
    if not paragraphs:
        # Fallback to sentence splitting if no clean paragraphs
        paragraphs = [s.strip() for s in text.split(". ") if len(s.strip()) > 30]
        
    query_tokens = set(re.findall(r"\w+", query.lower()))
    if not query_tokens:
        return text[:max_chars]
        
    scored_paragraphs = []
    for p in paragraphs:
        p_tokens = re.findall(r"\w+", p.lower())
        if not p_tokens:
            continue
            
        p_token_set = set(p_tokens)
        
        # 1. Direct Term Match Overlap
        overlap = query_tokens.intersection(p_token_set)
        
        # 2. Match Density (how clustered query words are in this paragraph)
        density_score = len(overlap) / len(query_tokens)
        
        # 3. Frequency Score (if key terms appear multiple times)
        freq_score = sum(1 for token in p_tokens if token in query_tokens)
        
        # 4. Length Penalty Mitigation (don't over-penalize complete detailed paragraphs)
        len_factor = min(1.0, len(p) / 400.0)
        
        # Combined semantic cross-score
        cross_score = (density_score * 5.0) + (freq_score * 0.5) * len_factor
        
        scored_paragraphs.append((cross_score, p))
        
    # Sort by cross-score descending
    scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
    
    # Select top scoring paragraphs up to max_chars limit
    selected = []
    current_len = 0
    for score, p in scored_paragraphs:
        if score <= 0.1:  # Reject low semantic overlap noise
            continue
        if current_len + len(p) <= max_chars:
            selected.append(p)
            current_len += len(p) + 1
        else:
            # If we have space, take a snippet
            remaining = max_chars - current_len
            if remaining > 100:
                selected.append(p[:remaining] + "...")
            break
            
    # Fallback to plain truncated text if nothing matched well
    if not selected:
        return text[:max_chars]
        
    return "\n\n".join(selected)

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
                        clean_pdf = cross_encoder_rerank(pdf_text, query, 3000)
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
                    
                    clean_text = cross_encoder_rerank(raw_text, query, 3000)
                    
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

