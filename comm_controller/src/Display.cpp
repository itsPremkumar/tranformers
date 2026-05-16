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
    int rnd = random(0, 100);
    if (rnd < 5) randomBlink();
}
