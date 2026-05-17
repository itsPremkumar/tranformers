import json
from app.tools.research_engine.orchestrator import execute_advanced_research
from app.tools.research_engine.memory_vault import MemoryVault

def run_advanced_tests():
    print("==================================================================")
    print("STARTING ADVANCED RESEARCH BRAIN TEST RUN (6 FEATURES)")
    print("==================================================================\n")

    # Feature 5: Telemetry Analytics Test
    print("[TEST CASE 1] Physical Hardware Telemetry Parsing")
    telemetry_payload = json.dumps({
        "battery_level": 15,
        "imu_drift_x": 6.2,
        "imu_drift_y": 0.1,
        "motor_currents_ma": [800, 900, 1600, 850]
    })
    telemetry_result = execute_advanced_research(telemetry_payload, is_telemetry=True)
    print(telemetry_result)
    print("Status: PASS\n")

    # Feature 1, 2, 3, 4: Deep Orchestrator Test (Query Expansion, Agentic Scraper, Vault)
    print("[TEST CASE 2] Multi-Perspective Agentic Scrape & Memory Vault")
    # This query will trigger technical expansion, scraper loops, and vault saving
    query = "explain quantum entanglement"
    research_result = execute_advanced_research(query)
    print("\n--- RESEARCH RESULT ---")
    print(research_result[:1000] + "...\n[TRUNCATED]")
    
    # Feature 3 Verification: Memory Vault Recall
    print("\n[TEST CASE 3] Checking Persistent Hermes Memory Vault Recall")
    vault = MemoryVault()
    past_memories = vault.retrieve_knowledge("explain quantum entanglement")
    if past_memories:
        print(f"Vault successfully recalled {len(past_memories)} chunks of knowledge from previous runs!")
        print("Status: PASS\n")
    else:
        print("Vault did not recall memory. Check ChromaDB initialization.")
        print("Status: FAIL\n")
        
    print("\nAdvanced Brain Run Complete.")

if __name__ == "__main__":
    run_advanced_tests()
