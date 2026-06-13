"""
MCP Bridge v5 — Sends notifications/initialized correctly before executing.
"""
import json
import http.client
import os

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "build_production_transformer.py")

def main():
    print("=" * 60)
    print("PRODUCTION TRANSFORMER - Fusion 360 MCP Bridge v5")
    print("=" * 60)

    try:
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            script_code = f.read()
        print(f"Script loaded: {len(script_code)} chars")
    except Exception as e:
        print(f"Failed to read script: {e}")
        return

    conn = http.client.HTTPConnection("127.0.0.1", 27182, timeout=300)
    session_id = None
    req_id = 0

    def send(method, params=None, is_notification=False):
        nonlocal session_id, req_id
        payload = {"jsonrpc": "2.0", "method": method}
        if not is_notification:
            req_id += 1
            payload["id"] = req_id
            
        if params:
            payload["params"] = params
        
        headers = {"Content-Type": "application/json"}
        if session_id:
            headers["Mcp-Session-Id"] = session_id

        body = json.dumps(payload)
        conn.request("POST", "/mcp", body, headers)
        resp = conn.getresponse()
        
        # Capture session from response
        for h, v in resp.getheaders():
            if h.lower() == "mcp-session-id":
                session_id = v
        
        data = resp.read().decode("utf-8")
        if data and not is_notification:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                print(f"Invalid JSON response: {data[:100]}")
                return None
        return None

    # 1. Initialize
    print("\n[1] Initializing MCP session...")
    init_result = send("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "transformer_builder", "version": "5.0"}
    })
    
    if init_result and "result" in init_result:
        info = init_result["result"].get("serverInfo", {})
        print(f"  Server: {info.get('name', '?')} v{info.get('version', '?')}")
        print(f"  Session: {session_id}")
    else:
        print(f"  FAILED: {init_result}")
        conn.close()
        return

    # 2. Notification initialized
    print("\n[2] Sending 'notifications/initialized'...")
    send("notifications/initialized", is_notification=True)

    # 3. Execute script
    print("\n[3] Executing build script via 'fusion_mcp_execute' tool...")
    arguments = {
        "featureType": "script",
        "object": {
            "script": script_code
        }
    }
    
    result = send("tools/call", {
        "name": "fusion_mcp_execute",
        "arguments": arguments
    })
    
    if result and "result" in result:
        content = result["result"]
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    text = item["text"]
                    print(f"\n  Output:\n{text[:3000]}")
        elif isinstance(content, dict) and "content" in content:
            for item in content["content"]:
                if isinstance(item, dict) and "text" in item:
                    print(f"\n  Output:\n{item['text'][:3000]}")
        else:
            print(f"\n  Result:\n{json.dumps(content, indent=2)[:3000]}")
            
        print("\n  ✅ SUCCESS!")
    elif result and "error" in result:
        err = result["error"]
        msg = err.get("message", "") if isinstance(err, dict) else str(err)
        print(f"\n  ❌ ERROR: {msg}")
        if "data" in err:
            print(f"  Data: {err['data']}")
    else:
        print(f"\n  ❓ Unknown result: {result}")

    print("\n" + "=" * 60)
    print("Execution complete. Check Fusion 360 for the model.")
    print("=" * 60)
    conn.close()

if __name__ == "__main__":
    main()
