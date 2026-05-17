#include "Display.h"
#include "expressionbitmap.h"

void DisplayController::drawBitmapFace(int index) {
    if (index < 0 || index >= 10) return;
    clearFace();
    _display.drawBitmap(0, 0, (const unsigned char*)pgm_read_ptr(&(allBitmaps[index])), 128, 64, WHITE);
    showFace();
}

DisplayController::DisplayController(uint8_t address, int width, int height) 
    : _display(width, height, &Wire, -1), _address(address) {
}

void DisplayController::begin() {
    if (!_display.begin(SSD1306_SWITCHCAPVCC, _address)) {
        Serial.println("OLED not found");
        return;
    }
    _display.clearDisplay();
    _display.display();
    randomSeed(analogRead(0));
}

void DisplayController::clearFace() {
    _display.clearDisplay();
    drawTopStatusBar(_wifiPercent, _batteryPercent, _isMuted);
}

void DisplayController::showFace() {
    _display.display();
}

void DisplayController::drawNormalEyes(int leftX, int rightX, int y) {
    _display.drawCircle(40, y, 14, WHITE);
    _display.drawCircle(88, y, 14, WHITE);
    _display.fillCircle(leftX, y, 5, WHITE);
    _display.fillCircle(rightX, y, 5, WHITE);
}

void DisplayController::drawClosedEyes() {
    _display.drawLine(28, 24, 52, 24, WHITE);
    _display.drawLine(76, 24, 100, 24, WHITE);
}

void DisplayController::drawSmile() {
    _display.drawLine(48, 46, 80, 46, WHITE);
    _display.drawLine(48, 46, 43, 41, WHITE);
    _display.drawLine(80, 46, 85, 41, WHITE);
}

void DisplayController::drawSadMouth() {
    _display.drawLine(48, 52, 80, 52, WHITE);
    _display.drawLine(48, 52, 43, 57, WHITE);
    _display.drawLine(80, 52, 85, 57, WHITE);
}

void DisplayController::drawStraightMouth() {
    _display.drawLine(48, 50, 80, 50, WHITE);
}

void DisplayController::drawHeart(int x, int y) {
    _display.fillCircle(x - 3, y - 2, 3, WHITE);
    _display.fillCircle(x + 3, y - 2, 3, WHITE);
    _display.fillTriangle(x - 6, y, x + 6, y, x, y + 8, WHITE);
}

void DisplayController::randomBlink() {
    clearFace();
    drawClosedEyes();
    showFace();
    delay(200);

    clearFace();
    drawNormalEyes(40, 88);
    showFace();
    delay(200);
}

void DisplayController::happyFace() {
    clearFace();
    drawNormalEyes(40, 88);
    drawSmile();
    showFace();
}

void DisplayController::sadFace() {
    clearFace();
    drawNormalEyes(40, 88);
    drawSadMouth();
    showFace();
}

void DisplayController::peaceFace() {
    clearFace();
    drawNormalEyes(40, 88);
    drawSmile();
    _display.fillCircle(64, 56, 3, WHITE); // peace dot
    showFace();
}

void DisplayController::heroFace() {
    clearFace();
    _display.drawLine(28, 14, 50, 24, WHITE);
    _display.drawLine(78, 24, 100, 14, WHITE);
    drawNormalEyes(40, 88);
    drawSmile();
    showFace();
}

void DisplayController::loveFace() {
    clearFace();
    drawHeart(40, 26);
    drawHeart(88, 26);
    drawSmile();
    showFace();
}

void DisplayController::fearFace() {
    clearFace();
    // Large open terrified eyes with tiny pupils
    _display.drawCircle(40, 26, 12, WHITE);
    _display.drawCircle(88, 26, 12, WHITE);
    _display.fillCircle(40, 26, 2, WHITE);
    _display.fillCircle(88, 26, 2, WHITE);
    // Trembling circular mouth
    _display.drawCircle(64, 48, 5, WHITE);
    showFace();
}

void DisplayController::disgustFace() {
    clearFace();
    // Squinting disgusted eyes
    // Left eye: >
    _display.drawLine(30, 20, 46, 26, WHITE);
    _display.drawLine(30, 32, 46, 26, WHITE);
    // Right eye: <
    _display.drawLine(98, 20, 82, 26, WHITE);
    _display.drawLine(98, 32, 82, 26, WHITE);
    // Wavy horizontal mouth
    _display.drawLine(48, 48, 56, 52, WHITE);
    _display.drawLine(56, 52, 64, 48, WHITE);
    _display.drawLine(64, 48, 72, 52, WHITE);
    _display.drawLine(72, 52, 80, 48, WHITE);
    showFace();
}

void DisplayController::wonderFace() {
    clearFace();
    // Standard wide open eyes
    drawNormalEyes(40, 88);
    // Arched highly raised eyebrows
    _display.drawLine(28, 10, 40, 6, WHITE);
    _display.drawLine(40, 6, 52, 10, WHITE);
    _display.drawLine(76, 10, 88, 6, WHITE);
    _display.drawLine(88, 6, 100, 10, WHITE);
    // Wide open gasp/surprise mouth
    _display.drawCircle(64, 48, 7, WHITE);
    showFace();
}

void DisplayController::angryFace() {
    clearFace();
    _display.drawLine(28, 14, 50, 24, WHITE);
    _display.drawLine(78, 24, 100, 14, WHITE);
    _display.drawCircle(40, 28, 10, WHITE);
    _display.drawCircle(88, 28, 10, WHITE);
    _display.fillCircle(40, 28, 4, WHITE);
    _display.fillCircle(88, 28, 4, WHITE);
    drawStraightMouth();
    showFace();
}

void DisplayController::sleepMode() {
    clearFace();
    drawClosedEyes();
    _display.setTextSize(1);
    _display.setTextColor(WHITE);
    _display.setCursor(90, 8);
    _display.print("Z Z");
    showFace();
}

void DisplayController::warningFace() {
    clearFace();
    drawNormalEyes(40, 88);
    _display.drawLine(64, 38, 64, 50, WHITE);
    _display.fillCircle(64, 56, 2, WHITE);
    showFace();
}

void DisplayController::showProgress(String label, int percent) {
    clearFace();
    _display.setTextSize(1);
    _display.setTextColor(WHITE);
    _display.setCursor(20, 10);
    _display.print(label);
    
    // Draw Progress Bar Frame
    _display.drawRect(14, 30, 100, 10, WHITE);
    // Draw Progress Fill
    _display.fillRect(14, 30, percent, 10, WHITE);
    
    _display.setCursor(55, 45);
    _display.print(String(percent) + "%");
    showFace();
}

void DisplayController::talkingAnimation() {
    for (int i = 0; i < 3; i++) {
        clearFace();
        drawNormalEyes(40, 88);
        _display.fillRect(54, 42, 20, 10, WHITE); // open
        showFace();
        delay(250);

        clearFace();
        drawNormalEyes(40, 88);
        _display.drawRect(56, 44, 16, 6, WHITE); // half open
        showFace();
        delay(250);
    }
}

void DisplayController::drawVisualizerFace(float low, float mid, float high) {
    clearFace();
    
    // 1. Eyes react to High Frequencies (Pitch/Tone)
    // Map high energy to eye radius (10-18)
    int eyeR = 14 + (high * 4);
    _display.drawCircle(40, 24, eyeR, WHITE);
    _display.drawCircle(88, 24, eyeR, WHITE);
    _display.fillCircle(40, 24, 5, WHITE);
    _display.fillCircle(88, 24, 5, WHITE);

    // 2. Mouth reacts to Low/Mid Frequencies (Beat/Volume)
    int mouthH = 4 + (low * 15) + (mid * 10);
    int mouthW = 20 + (mid * 20);
    _display.fillRect(64 - (mouthW / 2), 52 - (mouthH / 2), mouthW, mouthH, WHITE);
    
    showFace();
}

void DisplayController::updateRandom() {
    // If running under a custom State, process dynamic organic face updates
    if (_state != FaceState::Idle || random(0, 10) < 4) {
        updateFaceEngine();
    } else {
        int rnd = random(0, 100);
        if (rnd < 5) randomBlink();
    }
}

void DisplayController::SetState(FaceState state) {
    _state = state;
}

void DisplayController::IdleBehavior(int eyeHeight) {
    // 1. Drifting looking around logic from new engine
    if (random(0, 40) == 0) {
        _idleOffsetX = random(-3, 4); // Drift -3 to 3
        _idleOffsetY = random(-2, 3); // Drift -2 to 2
    }

    clearFace();

    // 2. Render normal eyes with drift offsets
    int leftEyeX = 40 + _idleOffsetX;
    int rightEyeX = 88 + _idleOffsetX;
    int eyeY = 24 + _idleOffsetY;

    if (eyeHeight <= 2) {
        drawClosedEyes();
    } else {
        // Draw open eyes with scaled height (blink size)
        _display.drawCircle(40, eyeY, eyeHeight, WHITE);
        _display.drawCircle(88, eyeY, eyeHeight, WHITE);
        _display.fillCircle(leftEyeX, eyeY, 5, WHITE);
        _display.fillCircle(rightEyeX, eyeY, 5, WHITE);
    }

    // 3. Render idle mouth with offsets
    _display.drawLine(48 + _idleOffsetX, 46 + _idleOffsetY, 80 + _idleOffsetX, 46 + _idleOffsetY, WHITE);
    
    showFace();
}

void DisplayController::ListeningBehavior(int eyeHeight) {
    clearFace();

    // 1. Asymmetric listening eyes from new engine (left eye smaller than right)
    int leftEyeR = eyeHeight - 3;
    if (leftEyeR < 2) leftEyeR = 2;
    int rightEyeR = eyeHeight;
    int eyeY = 24;

    if (eyeHeight <= 2) {
        drawClosedEyes();
    } else {
        _display.drawCircle(40, eyeY, leftEyeR, WHITE);
        _display.drawCircle(88, eyeY, rightEyeR, WHITE);
        _display.fillCircle(40, eyeY, 4, WHITE);
        _display.fillCircle(88, eyeY, 5, WHITE);
    }

    // 2. Listening mouth (thinking flat shifted left mouth)
    _display.drawLine(44, 46, 64, 46, WHITE);

    showFace();
}

void DisplayController::SpeakingBehavior(int eyeHeight) {
    unsigned long now = millis();

    // 1. Update random speak mouth target size (from new speaking engine)
    if (now - _lastSpeakUpdate > 120) {
        _lastSpeakUpdate = now;
        int r = random(0, 100);
        if (r < 20) _speakMouthTarget = 2;
        else if (r < 50) _speakMouthTarget = 8;
        else if (r < 80) _speakMouthTarget = 14;
        else _speakMouthTarget = 20;
    }

    // 2. Smoothly step towards speaking mouth height target (lerping)
    if (_speakMouthCurrent < _speakMouthTarget) _speakMouthCurrent += 2;
    else if (_speakMouthCurrent > _speakMouthTarget) _speakMouthCurrent -= 2;

    clearFace();

    // 3. Render normal eyes
    if (eyeHeight <= 2) {
        drawClosedEyes();
    } else {
        _display.drawCircle(40, 24, eyeHeight, WHITE);
        _display.drawCircle(88, 24, eyeHeight, WHITE);
        _display.fillCircle(40, 24, 5, WHITE);
        _display.fillCircle(88, 24, 5, WHITE);
    }

    // 4. Render smooth speaking mouth
    int mouthH = _speakMouthCurrent;
    int mouthW = 20;
    _display.fillRect(64 - (mouthW / 2), 48 - (mouthH / 2), mouthW, mouthH, WHITE);

    showFace();
}

void DisplayController::updateFaceEngine() {
    unsigned long now = millis();
    int eyeHeight = 14; // Base eye radius for 128x64 face

    // 1. Organic 3-Phase Blink Machine from new engine
    if (_blinkPhase == 0) {
        if (random(0, 150) == 0) {
            _blinkPhase = 1;
            _lastBlinkUpdate = now;
        }
    }

    if (_blinkPhase > 0 && now - _lastBlinkUpdate > 50) {
        _lastBlinkUpdate = now;
        _blinkPhase++;
        if (_blinkPhase > 3) _blinkPhase = 0; // Blink completed
    }

    switch (_blinkPhase) {
        case 1: eyeHeight = 6; break;
        case 2: eyeHeight = 1; break; // Fully closed
        case 3: eyeHeight = 8; break;
        default: eyeHeight = 14; break; // Fully open
    }

    // 2. Render state-based behaviors
    switch (_state) {
        case FaceState::Idle:
            IdleBehavior(eyeHeight);
            break;
        case FaceState::Listening:
            ListeningBehavior(eyeHeight);
            break;
        case FaceState::Speaking:
            SpeakingBehavior(eyeHeight);
            break;
        case FaceState::DebugHUD:
            drawDebugHUD();
            break;
    }
}

void DisplayController::updateSystemStatus(int wifi, int battery, bool muted) {
    _wifiPercent = wifi;
    _batteryPercent = battery;
    _isMuted = muted;
}

void DisplayController::drawTopStatusBar(int wifiPercent, int batteryPercent, bool isMuted) {
    // 1. Wi-Fi Icon (simple cell signal-style bars)
    int wifiX = 4;
    int wifiY = 8;
    if (wifiPercent > 0) {
        _display.fillRect(wifiX, wifiY - 2, 2, 2, WHITE);
        if (wifiPercent > 30) _display.fillRect(wifiX + 3, wifiY - 4, 2, 4, WHITE);
        if (wifiPercent > 60) _display.fillRect(wifiX + 6, wifiY - 6, 2, 6, WHITE);
        if (wifiPercent > 80) _display.fillRect(wifiX + 9, wifiY - 8, 2, 8, WHITE);
    } else {
        // Draw a small warning cross if Wi-Fi is disconnected
        _display.drawLine(wifiX, wifiY - 6, wifiX + 6, wifiY, WHITE);
        _display.drawLine(wifiX + 6, wifiY - 6, wifiX, wifiY, WHITE);
    }

    // 2. Battery Shape on the top-right
    int batX = 110;
    int batY = 1;
    _display.drawRect(batX, batY, 14, 7, WHITE); // Battery body frame
    _display.fillRect(batX + 14, batY + 2, 2, 3, WHITE); // Battery nipple
    
    // Draw battery level fill inside bat frame
    int fillW = map(batteryPercent, 0, 100, 0, 10);
    if (fillW > 10) fillW = 10;
    if (fillW > 0) {
        _display.fillRect(batX + 2, batY + 2, fillW, 3, WHITE);
    }

    // 3. Microphone Mute / Slash slash icon next to battery
    if (isMuted) {
        int micX = 98;
        int micY = 1;
        _display.drawCircle(micX + 3, micY + 3, 2, WHITE);
        _display.drawLine(micX, micY, micX + 6, micY + 6, WHITE);
    }

    // 4. Horizontal Separator Line below the top bar
    _display.drawLine(0, 10, 128, 10, WHITE);
}

void DisplayController::drawDebugHUD() {
    // Clear screen and draw Status Bar
    clearFace();

    _display.setTextSize(1);
    _display.setTextColor(WHITE);
    
    // 1. Diagnostics Title Header
    _display.setCursor(4, 12);
    _display.print("--- SYS DIAGNOSTICS ---");
    
    // 2. System Uptime (seconds)
    _display.setCursor(4, 24);
    _display.print("Uptime:   ");
    _display.print(millis() / 1000);
    _display.print("s");

    // 3. Dynamic Wi-Fi Strength
    _display.setCursor(4, 34);
    _display.print("Signal:   ");
    _display.print(_wifiPercent);
    _display.print("%");

    // 4. Free Heap Memory (RAM monitor)
    _display.setCursor(4, 44);
    _display.print("Free RAM: ");
    _display.print(ESP.getFreeHeap() / 1024);
    _display.print(" KB");

    // 5. Min Free Heap (Lowest recorded RAM stability monitor)
    _display.setCursor(4, 54);
    _display.print("Min RAM:  ");
    _display.print(ESP.getMinFreeHeap() / 1024);
    _display.print(" KB");

    showFace();
}
