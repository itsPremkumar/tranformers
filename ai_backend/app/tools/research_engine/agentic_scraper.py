import time
import os
from bs4 import BeautifulSoup

def agentic_follow_links(page, html, soup, current_url: str) -> str:
    """
    Feature 2: Multi-Step Iterative Scraper Loop (Claude-inspired)
    Detects if the page lacks deep content and autonomously follows references/links
    to find the ground-truth moving data source.
    """
    print(f"[AGENTIC LOOP] Evaluating {current_url} for deep context...")
    
    # Simple heuristic: if the page text is extremely short or contains 'Moved', we iterate.
    text_density = len(soup.get_text(strip=True))
    if text_density < 500:
        print("[AGENTIC ALERT] Page content is very sparse. Searching for redirection or citation links to follow...")
        
        # Look for "Read more", "Full article", or the first major outbound link
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True).lower()
            if any(k in text for k in ["read more", "continue", "full article", "source", "here"]):
                # Construct full URL if relative
                if href.startswith('/'):
                    from urllib.parse import urlparse
                    parsed_uri = urlparse(current_url)
                    href = f"{parsed_uri.scheme}://{parsed_uri.netloc}{href}"
                
                if href.startswith("http"):
                    print(f"[AGENTIC LOOP] Autonomously following reference link -> {href}")
                    try:
                        page.goto(href, timeout=10000, wait_until="domcontentloaded")
                        time.sleep(1.5)
                        new_html = page.content()
                        new_soup = BeautifulSoup(new_html, 'html.parser')
                        print("[AGENTIC LOOP SUCCESS] Successfully navigated to deeper context source.")
                        return new_soup
                    except Exception as e:
                        print(f"[AGENTIC LOOP ERROR] Failed following link: {e}")
                        return soup
    return soup
