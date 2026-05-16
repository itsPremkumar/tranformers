#ifndef DASHBOARD_UI_H
#define DASHBOARD_UI_H

#include <Arduino.h>
#include <WiFi.h>
#include "Config.h"
#include "SurroundControl.h"

inline String getDashboardHTML(SurroundControl* surround) {
    String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1,user-scalable=no'>";
    html += "<meta charset='UTF-8'><title>Transformer Control Center</title>";
    html += "<style>";
    html += "*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',Roboto,sans-serif;background:#0f0c29;background:linear-gradient(to right,#24243e,#302b63,#0f0c29);color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}";
    html += ".container{width:100%;max-width:500px}.header{text-align:center;margin-bottom:20px}h1{font-size:1.8em;letter-spacing:2px;text-transform:uppercase;color:#00f2fe;text-shadow:0 0 10px rgba(0,242,254,0.5)}";
    html += ".card{background:rgba(255,255,255,0.05);backdrop-filter:blur(15px);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:20px;margin-bottom:15px;box-shadow:0 8px 32px 0 rgba(0,0,0,0.37);overflow:hidden}";
    html += ".video-container{position:relative;width:100%;border-radius:15px;overflow:hidden;border:2px solid #00f2fe;box-shadow:0 0 20px rgba(0,242,254,0.3);margin-bottom:15px}";
    html += ".video-container img{width:100%;display:block;transition:0.3s}";
    html += ".video-overlay{position:absolute;top:10px;left:10px;background:rgba(0,0,0,0.6);padding:2px 10px;border-radius:10px;font-size:0.6em;color:#00f2fe;border:1px solid #00f2fe;text-transform:uppercase;letter-spacing:1px}";
    html += ".status-bar{display:flex;justify-content:space-between;font-size:0.9em;color:#00f2fe;margin-bottom:10px}";
    html += ".grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;justify-items:center}";
    html += ".btn{width:100%;aspect-ratio:1/1;max-width:100px;border-radius:15px;border:none;color:#fff;font-weight:bold;cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;transition:0.2s;box-shadow:0 4px 15px rgba(0,0,0,0.3)}";
    html += ".btn:active{transform:scale(0.95);box-shadow:0 2px 5px rgba(0,0,0,0.5)}";
    html += ".btn-move{background:linear-gradient(45deg,#2193b0,#6dd5ed)}.btn-action{background:linear-gradient(45deg,#ff00cc,#3333ff)}.btn-stop{background:linear-gradient(45deg,#ed213a,#93291e)}.btn-mood{background:linear-gradient(45deg,#11998e,#38ef7d)}";
    html += ".icon{font-size:1.8em;margin-bottom:5px}.label{font-size:0.7em;text-transform:uppercase}";
    html += ".slider-container{margin-top:10px}.slider{width:100%;height:10px;border-radius:5px;background:#2c3e50;outline:none;appearance:none;margin:10px 0}.slider::-webkit-slider-thumb{appearance:none;width:20px;height:20px;border-radius:50%;background:#00f2fe;cursor:pointer;box-shadow:0 0 10px #00f2fe}";
    html += ".section-title{font-size:0.8em;color:rgba(255,255,255,0.5);margin-bottom:10px;text-transform:uppercase;letter-spacing:1px}";
    html += ".terminal{background:#000;color:#0f0;font-family:'Courier New',monospace;padding:10px;border-radius:10px;font-size:0.7em;height:150px;overflow-y:auto;border:1px solid #333;margin-top:10px;box-shadow:inset 0 0 10px #000}";
    html += ".log-entry{margin-bottom:2px;border-bottom:1px solid #111;padding-bottom:2px}";
    html += "</style></head><body>";
    html += "<div class='container'><div class='header'><h1>Transformer 🤖</h1></div>";
    
    html += "<div class='video-container'>";
    html += "  <div class='video-overlay'>● LIVE FPV</div>";
    String streamUrl = surround ? surround->getVisionURL() : String(VISION_CAM_URL);
    html += "  <img src='" + streamUrl + "' onerror=\"this.src='https://via.placeholder.com/400x300?text=Camera+Offline'\" />";
    html += "</div>";

    html += "<div class='card'><div class='status-bar'><span>IP: " + WiFi.localIP().toString() + "</span><span id='status'>READY</span></div></div>";
    
    html += "<div class='card'><div class='section-title' style='display:flex;justify-content:space-between;align-items:center'>";
    html += "<span>Movement Control</span>";
    html += "<select id='mode' style='background:#1a1a2e;color:#00f2fe;border:1px solid #00f2fe;border-radius:5px;font-size:0.7em'>";
    html += "<option value='latch'>CRUISE</option><option value='momentary'>HOLD</option></select></div>";
    html += "<div class='grid-3'>";
    html += "<div></div><button class='btn btn-move' onmousedown='m(\"forward\")' onmouseup='s()' onmouseleave='s()'><span class='icon'>▲</span><span class='label'>Forward</span></button><div></div>";
    html += "<button class='btn btn-move' onmousedown='m(\"left\")' onmouseup='s()' onmouseleave='s()'><span class='icon'>◀</span><span class='label'>Left</span></button>";
    html += "<button class='btn btn-stop' onclick='cmd(\"stop\")'><span class='icon'>■</span><span class='label'>Stop</span></button>";
    html += "<button class='btn btn-move' onmousedown='m(\"right\")' onmouseup='s()' onmouseleave='s()'><span class='icon'>▶</span><span class='label'>Right</span></button>";
    html += "<div></div><button class='btn btn-move' onmousedown='m(\"backward\")' onmouseup='s()' onmouseleave='s()'><span class='icon'>▼</span><span class='label'>Back</span></button><div></div>";
    html += "</div>";
    html += "<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px'>";
    html += "<button class='btn btn-move' style='aspect-ratio:auto;height:45px' onmousedown='m(\"left_pivot\")' onmouseup='s()' onmouseleave='s()'><span class='label'>↶ Pivot Left</span></button>";
    html += "<button class='btn btn-move' style='aspect-ratio:auto;height:45px' onmousedown='m(\"right_pivot\")' onmouseup='s()' onmouseleave='s()'><span class='label'>↷ Pivot Right</span></button>";
    html += "</div></div>";

    html += "<div class='card'><div class='section-title'>Head / Camera Pan-Tilt</div>";
    html += "<div class='slider-container'><div class='label'>Pan (Horizontal)</div><input type='range' min='0' max='180' value='90' class='slider' onchange='val(\"pan\",this.value)'></div>";
    html += "<div class='slider-container'><div class='label'>Tilt (Vertical)</div><input type='range' min='0' max='180' value='90' class='slider' onchange='val(\"tilt\",this.value)'></div>";
    html += "</div>";

    html += "<div class='card'><div class='section-title'>Actions & Modes</div><div class='grid-3'>";
    html += "<button class='btn btn-action' onclick='cmd(\"transform\")'><span class='icon'>🔄</span><span class='label'>Transform</span></button>";
    html += "<button class='btn btn-action' onclick='cmd(\"walk\")'><span class='icon'>🚶</span><span class='label'>Walk Mode</span></button>";
    html += "<button class='btn btn-action' onclick='cmd(\"auto\")'><span class='icon'>🤖</span><span class='label'>Auto Pilot</span></button>";
    html += "<button class='btn btn-action' style='background:linear-gradient(45deg,#ff9a9e,#fecfef)' onclick='cmd(\"flash\")'><span class='icon'>🔦</span><span class='label'>Flashlight</span></button>";
    html += "<button class='btn btn-action' style='background:linear-gradient(45deg,#f093fb,#f5576c)' onclick='cmd(\"test\")'><span class='icon'>🩺</span><span class='label'>Self-Test</span></button>";
    html += "</div></div>";

    html += "<div class='card'><div class='section-title'>Expressions</div><div class='grid-3'>";
    html += "<button class='btn btn-mood' onclick='expr(\"happy\")'><span class='icon'>😊</span><span class='label'>Happy</span></button>";
    html += "<button class='btn btn-mood' onclick='expr(\"angry\")'><span class='icon'>😠</span><span class='label'>Angry</span></button>";
    html += "<button class='btn btn-mood' onclick='expr(\"hero\")'><span class='icon'>😎</span><span class='label'>Hero</span></button>";
    html += "</div></div>";

    html += "<div class='card'><div class='section-title'>Intercom (Robot Voice)</div>";
    html += "<button id='micBtn' class='btn btn-stop' style='width:100%;aspect-ratio:auto;height:60px;flex-direction:row;gap:10px'>";
    html += "<span class='icon'>🎤</span><span class='label'>Hold to Talk</span></button>";
    html += "<div style='margin-top:10px;display:flex;gap:5px'>";
    html += "<input type='text' id='ttsInput' placeholder='Type for Jarvis...' style='flex:1;background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.2);color:white;padding:10px;border-radius:5px'>";
    html += "<button onclick='say()' style='background:#00f2fe;color:#000;border:none;padding:10px;border-radius:5px;font-weight:bold'>SAY</button></div></div>";

    html += "<div class='card'><div class='section-title' style='display:flex;justify-content:space-between;align-items:center'>";
    html += "<span>Surround Intelligence</span>";
    html += "<div><button onclick='cmd(\"scan\")' style='background:#00f2fe;color:#000;border:none;padding:2px 10px;border-radius:5px;font-size:0.7em;font-weight:bold;margin-right:5px'>SCAN</button>";
    html += "<button id='stealthBtn' onclick='cmd(\"stealth\")' style='background:#ff00cc;color:#fff;border:none;padding:2px 10px;border-radius:5px;font-size:0.7em;font-weight:bold;margin-right:5px'>STEALTH</button>";
    html += "<button id='honeypotBtn' onclick='cmd(\"honeypot\")' style='background:#ed213a;color:#fff;border:none;padding:2px 10px;border-radius:5px;font-size:0.7em;font-weight:bold'>HONEYPOT</button></div></div>";
    html += "<div id='device-list' style='font-size:0.8em;max-height:200px;overflow-y:auto;margin-top:10px'>";
    
    if (surround) {
        for (int i = 0; i < surround->getDeviceCount(); i++) {
            ScannedDevice d = surround->getDevice(i);
            String icon = d.isBle ? "📶 " : (d.isSniffed ? "🕵️ " : "🌐 ");
            html += "<div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.1)'>";
            html += "<span>" + icon + d.name + (d.isSniffed ? " (SNIFFED)" : "") + "</span>";
            
            html += "<div style='display:flex;gap:5px'>";
            if (d.mac != "" && !d.isBle) {
                html += "<button onclick='fetch(\"/takeover?mac=" + d.mac + "\")' style='background:none;border:1px solid #ff00cc;color:#ff00cc;font-size:0.7em;padding:1px 5px'>WOL</button>";
                html += "<button onclick='fetch(\"/deauth?mac=" + d.mac + "\")' style='background:none;border:1px solid #ed213a;color:#ed213a;font-size:0.7em;padding:1px 5px'>KICK</button>";
            } else if (!d.isBle && d.ip != "") {
                html += "<button onclick='fetch(\"/takeover?ip=" + d.ip + "\")' style='background:none;border:1px solid #00f2fe;color:#00f2fe;font-size:0.7em;padding:1px 5px'>TAKEOVER</button>";
            } else {
                html += "<span style='color:rgba(255,255,255,0.5)'>" + String(d.rssi) + " dBm</span>";
            }
            html += "</div></div>";
        }
    }
    html += "</div></div>";

    html += "<div class='card'><div class='section-title'>Wireless Serial Monitor</div>";
    html += "<div id='terminal' class='terminal'>[SYSTEM] Waiting for logs...</div></div>";
    html += "</div>"; // end container
    html += "<script>";
    html += "let socket; let useWS = false;";
    html += "const ROBOT_LANG = '" + String(ROBOT_LANGUAGE) + "';";
    html += "function initWS(){";
    html += "  socket = new WebSocket('ws://'+window.location.hostname+':81/');";
    html += "  socket.onopen = () => { console.log('WS Connected'); useWS = true; document.getElementById('status').textContent='⚡ REAL-TIME'; };";
    html += "  socket.onclose = () => { console.log('WS Disconnected'); useWS = false; document.getElementById('status').textContent='FALLBACK (HTTP)'; setTimeout(initWS, 2000); };";
    html += "  socket.onmessage = (e) => { ";
    html += "    if(e.data.startsWith('SAY:')){";
    html += "      let text = e.data.substring(4);";
    html += "      document.getElementById('status').textContent = 'ROBOT: ' + text;";
    html += "      let utterance = new SpeechSynthesisUtterance(text);";
    html += "      utterance.lang = ROBOT_LANG;";
    html += "      utterance.pitch = 0.8; utterance.rate = 1.0; ";
    html += "      window.speechSynthesis.speak(utterance);
    } else if(e.data.startsWith('LOG:')){
      let terminal = document.getElementById('terminal');
      let msg = e.data.substring(4);
      let entry = document.createElement('div');
      entry.className = 'log-entry';
      entry.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
      terminal.appendChild(entry);
      terminal.scrollTop = terminal.scrollHeight;";
    html += "    }";
    html += "  };";
    html += "}";

    
    html += "function cmd(d){ let c = 'CMD:'+d.toUpperCase(); if(useWS){ socket.send(c); } else { fetch('/'+d).then(r=>r.text()).then(t=>{document.getElementById('status').textContent=t;}); } }";
    html += "function m(d){ cmd(d); }";
    html += "function s(){ if(document.getElementById('mode').value==='momentary'){ cmd('stop'); } }";
    html += "function val(p,v){ let c = p.toUpperCase()+':'+v; if(useWS){ socket.send(c); } else { fetch('/'+p+'?val='+v); } }";
    html += "function expr(m){ let c = 'FACE:'+m.toUpperCase(); if(useWS){ socket.send(c); } else { fetch('/expression?val='+m); } }";
    html += "function say(){ let t = document.getElementById('ttsInput').value; if(t){ fetch('/say?text='+encodeURIComponent(t)); document.getElementById('ttsInput').value=''; } }";
    
    html += "window.onload = initWS;";
    
    html += "// Intercom Logic\n";
    html += "const micBtn = document.getElementById('micBtn');";
    html += "let mediaRecorder;";

    html += "micBtn.onmousedown = async () => {";
    html += "    try {";
    html += "        micBtn.style.background = 'linear-gradient(45deg, #ff0000, #990000)';";
    html += "        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });";
    html += "        mediaRecorder = new MediaRecorder(stream);";
    html += "        mediaRecorder.ondataavailable = (e) => {";
    html += "            fetch('/voice', { method: 'POST', body: e.data });";
    html += "        };";
    html += "        mediaRecorder.start(100); ";
    html += "    } catch(e) { console.error('Mic Error:', e); }";
    html += "};";

    html += "micBtn.onmouseup = () => {";
    html += "    micBtn.style.background = '';";
    html += "    if(mediaRecorder && mediaRecorder.state !== 'inactive') {";
    html += "        mediaRecorder.stop();";
    html += "        mediaRecorder.stream.getTracks().forEach(t => t.stop());";
    html += "    }";
    html += "};";
    html += "</script></body></html>";
    return html;
}

#endif
