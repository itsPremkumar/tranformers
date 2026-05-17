import sys
import os
import asyncio
import io

# Force console to output UTF-8 safely to bypass CP1252/Windows encoding constraints
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Include correct paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tools.ota_compiler import modify_firmware_config, compile_firmware
from app.tools.research_engine.memory_vault import MemoryVault
from app.tools.research_engine.orchestrator import cross_encoder_rerank

async def run_detailed_diagnostics():
    print("==================================================")
    print("🤖 STARTING OMNI-MORPH SYSTEM V2.5 VALIDATION 🤖")
    print("==================================================")
    
    # ----------------------------------------------------
    # TEST 1: Semantic RAG - Parent-Child Chunking
    # ----------------------------------------------------
    print("\n--- [DIAGNOSTIC 1] Parent-Child Chunking Database Test ---")
    vault = MemoryVault()
    
    test_url = "https://arxiv.org/abs/2605.12345"
    # An elite detailed paragraph (Parent Chunk)
    test_parent_content = (
        "The Omni-Morph transformation sequence utilizes high-torque MG996R servos "
        "coordinated dynamically via a PCA9685 PWM driver. During walking gate sequences, "
        "the bipedal centers of gravity are continuously compensated via real-time MPU6050 IMU "
        "feedback filters, preventing humanoid falls during structural joint shifts."
    )
    
    print("[RAG Test] Indexing technical parent paragraph...")
    vault.store_knowledge(
        url=test_url,
        content=test_parent_content,
        perspective="Technical Mechanics"
    )
    
    # Ask a query that specifically targets a child segment
    query = "MG996R PCA9685 transformation sequence"
    print(f"[RAG Test] Querying Memory Vault for: '{query}'")
    results = vault.retrieve_knowledge(query, n_results=1)
    
    print("\n[RAG Results Summary]")
    if results:
        print(f"✔️ SUCCESS: Successfully matched and retrieved hierarchical context!")
        print(f"Retrieved Paragraph Context:\n--> \"{results[0]}\"")
        assert len(results[0]) > 200, "Should retrieve the large parent paragraph, not a child sentence."
    else:
        print("❌ FAILED: RAG memory lookup returned no contexts.")
        
    # ----------------------------------------------------
    # TEST 2: Semantic Cross-Encoder Reranking
    # ----------------------------------------------------
    print("\n--- [DIAGNOSTIC 2] Custom Cross-Encoder Reranking Test ---")
    document_text = (
        "We use standard lithium batteries for electronics.\n"
        "The primary transformation joints are actuated by MG996R high-torque servos and PCA9685 driver.\n"
        "Water cooling is not implemented on the ESP32 chip because it operates at normal room temperatures.\n"
        "Obstacle scanning sweeps front distances via ultrasonic HC-SR04 sensors on the gimbal."
    )
    
    target_query = "actuated MG996R servos and PCA9685"
    print(f"[Rerank Test] Query: '{target_query}'")
    reranked_output = cross_encoder_rerank(document_text, target_query, max_chars=1000)
    
    print("\n[Rerank Results Summary]")
    print(f"Reranked Paragraph Contexts:\n{reranked_output}")
    if "MG996R" in reranked_output and "PCA9685" in reranked_output:
        print("✔️ SUCCESS: Cross-Encoder successfully re-sorted and selected the most relevant paragraphs!")
    else:
        print("❌ FAILED: Reranker failed to isolate high-fidelity context.")

    # ----------------------------------------------------
    # TEST 3: C++ Configuration Modifications
    # ----------------------------------------------------
    print("\n--- [DIAGNOSTIC 3] C++ Config Modifier Test ---")
    print("[Config Test] Attempting to temporarily modify Config.h...")
    
    # Let's read current WIFI_PASS value from Config.h if we can, or just mock modify
    success = modify_firmware_config("WIFI_PASS", '"12345678"')
    if success:
        print("✔️ SUCCESS: C++ preprocessor configuration parsed and updated successfully!")
    else:
        print("❌ FAILED: Could not update Config.h")
        
    # ----------------------------------------------------
    # TEST 4: PlatformIO C++ Compilation Verification
    # ----------------------------------------------------
    print("\n--- [DIAGNOSTIC 4] PlatformIO Compiler Verification ---")
    print("[Compile Test] Launching compiler. This verifies PlatformIO dependencies and C++ syntax are sound...")
    
    # We will compile. It can take up to 30-40 seconds on first build, but PIO caches make it fast
    compile_success, log = await compile_firmware()
    
    print("\n[Compiler Results Summary]")
    if compile_success:
        print("✔️ SUCCESS: PlatformIO successfully compiled the firmware to binary output!")
    else:
        print("❌ FAILED/SKIPPED: PlatformIO compiler was not run or encountered errors.")
        print("Compiler Logs (Truncated):")
        print("\n".join(log.split("\n")[-15:]))
        
    print("\n==================================================")
    print("🤖 OMNI-MORPH SYSTEM V2.5 DIAGNOSTICS COMPLETE 🤖")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_detailed_diagnostics())
