import os
import sys
import io

# Force UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

# Ensure current directory is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tools.internet import web_search

def run_test():
    print("=== STARTING HUMAN-LIKE WEB SEARCH TEST ===")
    
    test_query = "latest space news 2026"
    print(f"Testing search query: '{test_query}'")
    
    results = web_search(test_query)
    
    print("\n--- RESULTS ---")
    print(results)
    print("----------------\n")
    
    # Check if screenshots were created
    screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "app", "debug_screenshots"))
    if os.path.exists(screenshots_dir):
        files = os.listdir(screenshots_dir)
        print(f"Screenshots in directory ({screenshots_dir}): {files}")
    else:
        print(f"Screenshots directory not found at: {screenshots_dir}")
        
    print("=== TEST COMPLETED ===")

if __name__ == "__main__":
    run_test()
