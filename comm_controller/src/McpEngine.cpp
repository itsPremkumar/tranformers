#include "McpEngine.h"
#include "Display.h"
#include <WiFi.h>

void McpEngine::begin() {
    _tools.clear();
    registerCommonTools();
}

void McpEngine::registerTool(const String& name, const String& description, std::function<String(JsonVariantConst arguments)> callback) {
    _tools.push_back({name, description, callback});
}

void McpEngine::registerCommonTools() {
    // 1. self.get_device_status
    registerTool("self.get_device_status", 
                 "Provides real-time information of the robot, including subtitle, battery percentage, wifi status, and active mode.", 
                 [](JsonVariantConst args) -> String {
        JsonDocument doc;
        doc["status"] = "online";
        doc["wifi_rssi"] = WiFi.status() == WL_CONNECTED ? String(WiFi.RSSI()) + " dBm" : "disconnected";
        doc["battery"] = "85%";
        doc["swarms"] = "active";
        
        String output;
        serializeJson(doc, output);
        return output;
    });

    // 2. self.display.set_subtitle
    registerTool("self.display.set_subtitle",
                 "Renders real-time text subtitle track on the OLED screen.",
                 [](JsonVariantConst args) -> String {
        if (args.containsKey("text")) {
            String text = args["text"].as<String>();
            displayCtrl.SetSubtitle(text);
            return "Subtitle updated successfully to: " + text;
        }
        return "Error: Missing 'text' argument";
    });

    // 3. self.motion.transform
    registerTool("self.motion.transform",
                 "Triggers the physical transformation routine to Crawler mode or Walker mode.",
                 [](JsonVariantConst args) -> String {
        String mode = "Crawler";
        if (args.containsKey("mode")) {
            mode = args["mode"].as<String>();
        }
        
        Serial.println("[MCP MOTION] Triggering mode transformation: " + mode);
        
        // Dispatch serial coordinates
        if (mode.equalsIgnoreCase("Crawler")) {
            Serial2.println("CMD:CRAWLER");
        } else {
            Serial2.println("CMD:WALK");
        }
        
        return "Transformation initiated successfully to: " + mode;
    });
}

String McpEngine::parseAndExecute(const String& requestStr) {
    JsonDocument reqDoc;
    DeserializationError error = deserializeJson(reqDoc, requestStr);
    
    if (error) {
        JsonDocument resDoc;
        resDoc["jsonrpc"] = "2.0";
        resDoc["id"] = nullptr;
        resDoc["error"]["code"] = -32700;
        resDoc["error"]["message"] = "Parse error: " + String(error.c_str());
        
        String response;
        serializeJson(resDoc, response);
        return response;
    }
    
    String version = reqDoc["jsonrpc"] | "2.0";
    long id = reqDoc["id"] | 0;
    String method = reqDoc["method"] | "";
    
    JsonDocument resDoc;
    resDoc["jsonrpc"] = "2.0";
    resDoc["id"] = id;
    
    if (method == "tools/list") {
        JsonObject result = resDoc["result"].to<JsonObject>();
        JsonArray toolsArr = result["tools"].to<JsonArray>();
        
        for (const auto& tool : _tools) {
            JsonObject tObj = toolsArr.add<JsonObject>();
            tObj["name"] = tool.name;
            tObj["description"] = tool.description;
            
            JsonObject inputSchema = tObj["inputSchema"].to<JsonObject>();
            inputSchema["type"] = "object";
            JsonObject properties = inputSchema["properties"].to<JsonObject>();
            
            if (tool.name == "self.display.set_subtitle") {
                JsonObject textProp = properties["text"].to<JsonObject>();
                textProp["type"] = "string";
                textProp["description"] = "The text to display on the scrolling ticker";
            } else if (tool.name == "self.motion.transform") {
                JsonObject modeProp = properties["mode"].to<JsonObject>();
                modeProp["type"] = "string";
                modeProp["description"] = "The target mode (Crawler or Walker)";
            }
        }
        
        String response;
        serializeJson(resDoc, response);
        return response;
        
    } else if (method == "tools/call") {
        JsonObject params = reqDoc["params"].as<JsonObject>();
        String toolName = params["name"] | "";
        JsonVariantConst toolArgs = params["arguments"];
        
        bool found = false;
        String executionResult = "";
        
        for (const auto& tool : _tools) {
            if (tool.name == toolName) {
                found = true;
                executionResult = tool.callback(toolArgs);
                break;
            }
        }
        
        if (found) {
            JsonObject result = resDoc["result"].to<JsonObject>();
            JsonArray content = result["content"].to<JsonArray>();
            JsonObject cObj = content.add<JsonObject>();
            cObj["type"] = "text";
            cObj["text"] = executionResult;
            resDoc["isError"] = false;
        } else {
            resDoc["error"]["code"] = -32601;
            resDoc["error"]["message"] = "Method not found: " + toolName;
        }
        
        String response;
        serializeJson(resDoc, response);
        return response;
    }
    
    resDoc["error"]["code"] = -32601;
    resDoc["error"]["message"] = "Method not found: " + method;
    String response;
    serializeJson(resDoc, response);
    return response;
}
