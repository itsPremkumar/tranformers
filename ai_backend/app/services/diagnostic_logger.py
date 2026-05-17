import os
from datetime import datetime

# Absolute path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "data", "diagnostics.xlsx")

def log_diagnostic_event(category: str, event_text: str, status: str = "success"):
    """Saves diagnostic telemetry transaction details to Excel using Pandas."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": category,
        "event": event_text,
        "status": status
    }
    
    print(f"[DIAGNOSTICS] Logging transaction: Category={category} | Event='{event_text}' | Status={status}")
    
    try:
        import pandas as pd
        
        # Load or create dataframe
        if os.path.exists(LOG_FILE):
            try:
                df = pd.read_excel(LOG_FILE)
            except Exception:
                df = pd.DataFrame()
        else:
            df = pd.DataFrame()
            
        new_df = pd.DataFrame([new_entry])
        
        if not df.empty:
            df = pd.concat([df, new_df], ignore_index=True)
        else:
            df = new_df
            
        # Maintain rolling log limit of 1000 items
        df = df.tail(1000)
        df.to_excel(LOG_FILE, index=False)
    except ImportError:
        print("[DIAGNOSTICS WARNING] 'pandas' or 'openpyxl' libraries are not installed. Logging event to console only.")
        # Simulating saving by storing to a simple plain-text log backup
        backup_log = os.path.join(BASE_DIR, "data", "diagnostics.txt")
        try:
            with open(backup_log, "a", encoding="utf-8") as f:
                f.write(f"{new_entry['timestamp']} | {new_entry['category']} | {new_entry['event']} | {new_entry['status']}\n")
        except Exception as e:
            print(f"[DIAGNOSTICS ERROR] Text logger backup write failed: {e}")
    except Exception as e:
        print(f"[DIAGNOSTICS ERROR] Excel spreadsheet write transaction failed: {e}")
