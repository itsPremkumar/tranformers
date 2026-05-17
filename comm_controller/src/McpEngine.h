#ifndef MCP_ENGINE_H
#define MCP_ENGINE_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include <vector>
#include <functional>
#include <map>

// Forward declarations
class DisplayController;
extern DisplayController displayCtrl;

struct McpTool {
    String name;
    String description;
    std::function<String(JsonVariantConst arguments)> callback;
};

class McpEngine {
public:
    static McpEngine& getInstance() {
        static McpEngine instance;
        return instance;
    }

    void begin();
    
    // Register custom tool callback
    void registerTool(const String& name, const String& description, std::function<String(JsonVariantConst arguments)> callback);
    
    // Core JSONRPC processor
    String parseAndExecute(const String& requestStr);

private:
    McpEngine() = default;
    ~McpEngine() = default;
    McpEngine(const McpEngine&) = delete;
    McpEngine& operator=(const McpEngine&) = delete;

    std::vector<McpTool> _tools;

    void registerCommonTools();
};

#endif // MCP_ENGINE_H
