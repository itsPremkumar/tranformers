#ifndef ROBOT_SERVER_H
#define ROBOT_SERVER_H

#include <Arduino.h>
#include <WebServer.h>
#include <WebSocketsServer.h>
#include <WebSocketsClient.h>
#include <WiFi.h>
#include "Audio.h"
#include "Config.h"
#include "SurroundControl.h"
#include "Network.h"

class WebInterface {
public:
    WebInterface(AudioSystem* audio, SurroundControl* surround, Network* net, int port = 80);
    void begin();
    void handleClient();
    void broadcast(String msg);
    void sendToAi(String msg);

    
    // Commands received from Web UI that need to be forwarded to Motion Controller
    String getLastCommand();
    bool hasNewCommand();
    void clearCommand();

private:
    WebServer _server;
    WebSocketsServer _webSocket = WebSocketsServer(81);
    WebSocketsClient _aiClient;
    
    String _lastCommand;
    bool _hasNewCommand;
    AudioSystem* _audio;
    SurroundControl* _surround;
    Network* _net;
    
    // HTML page
    String getHTML();
    
    // WebSocket Event Handlers
    void onWebSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length);
    void onAiEvent(WStype_t type, uint8_t * payload, size_t length);


    // Request handlers
    void handleRoot();
    void handleForward();
    void handleBackward();
    void handleLeft();
    void handleRight();
    void handleLeftPivot();
    void handleRightPivot();
    void handleStop();
    void handleStatus();
    void handleTransform();
    void handleWalk();
    void handleAuto();
    void handleTest();
    void handlePan();
    void handleTilt();
    void handleExpression();
    void handleVoice();
    void handleScan();
    void handleTakeover();
    void handleStealth();
    void handleDeauth();
    void handleHoneypot();
};

#endif
