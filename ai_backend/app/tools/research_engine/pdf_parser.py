import os
import requests
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

def extract_pdf_content(url: str, max_pages: int = 5) -> str:
    """
    Feature 4: Academic PDF & Scientific Paper Extractor (arXiv / NASA ADS)
    Downloads and extracts text from scientific PDFs.
    """
    if not pdfplumber:
        print("[PDF EXTRACTOR ERROR] pdfplumber is not installed.")
        return ""
        
    print(f"[PDF EXTRACTOR] Downloading scientific paper from {url}...")
    temp_pdf_path = "temp_research_paper.pdf"
    
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        
        with open(temp_pdf_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        extracted_text = []
        with pdfplumber.open(temp_pdf_path) as pdf:
            pages_to_read = min(len(pdf.pages), max_pages)
            print(f"[PDF EXTRACTOR] Parsing first {pages_to_read} pages...")
            for i in range(pages_to_read):
                page = pdf.pages[i]
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
                    
        # Clean up
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            
        full_text = "\n".join(extracted_text)
        print(f"[PDF EXTRACTOR SUCCESS] Extracted {len(full_text)} characters from PDF.")
        return full_text
    except Exception as e:
        print(f"[PDF EXTRACTOR ERROR] Failed parsing {url}: {e}")
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        return ""
