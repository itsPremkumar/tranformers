import sys
import os

# Add package directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.tools.deep_research import deep_research

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        result = deep_research(query)
        print(result)
    else:
        print("Error: No search query provided.")
