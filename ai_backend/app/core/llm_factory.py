import google.generativeai as genai
from openai import OpenAI
import anthropic
import ollama
import json
import asyncio
import base64
import io
from app.core.config import settings
from app.tools.robot import move_robot, set_camera_gimbal, transform_robot
from app.tools.internet import web_search, wiki_lookup, play_youtube
from app.tools.deep_research import deep_research
from app.core.memory import memory_manager

def is_gibberish(text: str) -> bool:
    # 1. Check for long words without spaces (excluding URLs/paths/base64 data)
    words = text.split()
    for word in words:
        if len(word) > 30:
            # Check if it looks like a URL or path or data URI
            if word.startswith(("http://", "https://", "www.", "file://", "data:")) or "\\" in word or "/" in word:
                continue
            return True
            
    # 2. Check for repeating sub-strings (consecutive repetition)
    # E.g., "jhskfjhskfjhskf"
    for length in range(3, 11):
        for i in range(len(text) - length * 3 + 1):
            sub = text[i:i+length]
            # check if this substring is repeated consecutively 3 or more times
            if text[i+length:i+length*2] == sub and text[i+length*2:i+length*3] == sub:
                return True
                
    # 3. Check vowel-to-consonant ratio (vowel density) for alphabetic strings
    # English/Latin text usually has around 30-40% vowels (a, e, i, o, u, y)
    # Gibberish like "jhskfjhskf" has 0% vowels
    latin_letters = [c.lower() for c in text if 'a' <= c.lower() <= 'z']
    if len(latin_letters) > 15:
        vowels = sum(1 for c in latin_letters if c in 'aeiouy')
        ratio = vowels / len(latin_letters)
        if ratio < 0.15:
            return True
            
    return False


class LLMFactory:
    def __init__(self, manager):
        self.manager = manager
        
        # Tools registration for Gemini
        self.tools = [move_robot, set_camera_gimbal, transform_robot, web_search, wiki_lookup, play_youtube, deep_research]
        
        # Initialize Clients (Omni-Ready)
        self.gemini_client = None
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Upgraded to Gemini 2.0 for native multimodal (Vision/Audio) support
            self.gemini_client = genai.GenerativeModel(settings.GEMINI_MODEL, tools=self.tools)
        
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.claude_client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY) if settings.CLAUDE_API_KEY else None

    async def get_response(self, user_prompt: str, robot_name: str, image=None, hw_status: dict = None, internet_context: str = None):
        """The single unified entry point for AI logic with robot-specific memory and hardware awareness."""
        
        # 0. Load Robot-Specific Memory (Run in thread to avoid blocking)
        history, knowledge = await asyncio.to_thread(memory_manager.get_robot_memory, robot_name)
        
        # Filter history: Remove any messages that contain numeric lists/coordinates to break loops
        clean_history = []
        for msg in history:
            if "Robot: [" in msg and any(char.isdigit() for char in msg):
                continue
            # Remove hallucinated patterns from previous errors to break the loop
            if "?I am ready" in msg or "SAY:?" in msg or '?"' in msg:
                continue
            clean_history.append(msg)
        
        history_text = "\n".join(clean_history[-5:]) # Last 5 clean exchanges
        
        # 1. Build Final Prompt
        system_prompt = self.get_system_prompt(robot_name)
        
        status_text = ""
        if hw_status:
            status_text = f"\nCURRENT HARDWARE STATUS:\n- Battery: {hw_status.get('battery', 0)}%\n- Mode: {hw_status.get('mode', 'Unknown')}\n- Obstacle Distance: {hw_status.get('distance', 0)}cm\n"

        search_text = f"\nLIVE INTERNET SEARCH RESULTS:\n{internet_context}\n" if internet_context else ""
        
        if self.gemini_client:
            full_prompt = f"{system_prompt}\n{status_text}{search_text}\nKNOWLEDGE OF USER/ENVIRONMENT: {knowledge}\n\nPAST CONVERSATION:\n{history_text}\n\nUser: {user_prompt}"
        else:
            # Optimization for local models
            if image:
                full_prompt = f"Identify and describe what is in this image. Question: {user_prompt}"
            else:
                if internet_context:
                    full_prompt = f"{status_text}\nLATEST NEWS/INFO:\n{internet_context}\n\nQuestion: {user_prompt}\nAnswer using the LATEST info above. Be factual."
                else:
                    full_prompt = f"{system_prompt}\n{status_text}\nQuestion: {user_prompt}"
            
        print(f"\n[DEBUG] --- FINAL PROMPT SENT TO AI ---\n{full_prompt}\n[DEBUG] ---------------------------------")

        # 2. Local LLM Path (Primary)
        raw_response = None
        try:
            print(f"[LLM] Using Local Model ({settings.OLLAMA_MODEL}) for {robot_name}")
            
            if image:
                # Convert PIL Image to bytes
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                img_bytes = buffered.getvalue()
                
                print(f"[DEBUG] Sending vision request to Ollama ({settings.OLLAMA_MODEL})...")
                res = await asyncio.to_thread(ollama.generate, model=settings.OLLAMA_MODEL, prompt=full_prompt, images=[img_bytes])
                response_text = res.get('response', '')
            else:
                print(f"[DEBUG] Sending chat request to Ollama ({settings.OLLAMA_MODEL})...")
                res = await asyncio.to_thread(ollama.chat, model=settings.OLLAMA_MODEL, messages=[{'role': 'user', 'content': full_prompt}])
                response_text = res['message']['content']

            print(f"[DEBUG] Raw Ollama Response: {response_text}")
            raw_response = self.format_response(response_text)
        except Exception as e:
            print(f"[LLM] Local Model Error: {e}")
            
            # 3. Fallback to Gemini if key exists
            if self.gemini_client:
                try:
                    print(f"[LLM] Falling back to Gemini...")
                    chat = self.gemini_client.start_chat(enable_automatic_function_calling=True)
                    content = [full_prompt, image] if image else full_prompt
                    response = await chat.send_message_async(content)
                    raw_response = self.format_response(response.text)
                except Exception as ex:
                    print(f"[LLM] Gemini Fallback Error: {ex}")

        if not raw_response or "I am processing your request." in raw_response:
            if internet_context and not self.gemini_client:
                clean_context = internet_context.replace('\n', ' ').replace('"', '')[:200]
                raw_response = json.dumps([f"SAY:Here is what I found: {clean_context}"])
            else:
                # Provide a more natural fallback if vision failed
                msg = "I can see the camera feed, but I'm having trouble identifying everything clearly." if image else "I'm thinking, but I couldn't find a clear answer for that right now."
                raw_response = json.dumps([f"SAY:{msg}"])

        # 4. Save Interaction to Persistent Memory (Run in thread)
        await asyncio.to_thread(memory_manager.save_interaction, robot_name, user_prompt, raw_response)
        
        return raw_response

    def format_response(self, text):
        if is_gibberish(text):
            raise ValueError("Model output contains gibberish/hallucinations")

        try:
            clean = text.replace("```json", "").replace("```", "").strip()
            # Try to fix single quotes common in hallucinated JSON lists
            if clean.startswith("[") and clean.endswith("]"):
                clean = clean.replace("'", '"')
            
            parsed = json.loads(clean)
            
            # Ensure the output is actually a list, otherwise fallback
            if not isinstance(parsed, list):
                raise ValueError("Model did not return a list")
                
            # Prevent hallucinated coordinates from being treated as valid commands
            if isinstance(parsed, list) and len(parsed) > 0 and any(isinstance(x, (int, float)) for x in parsed):
                raise ValueError("Model hallucinated coordinates")
                
            if isinstance(parsed, list) and len(parsed) == 0:
                raise ValueError("Model returned an empty list, falling back to text extraction.")
                
            return clean
        except Exception as e:
            # If it's the ValueError we raised above, propagate it up
            if isinstance(e, ValueError) and "gibberish" in str(e):
                raise e

            clean_text = text.replace('"', '').replace("'", "").replace('[', '').replace(']', '').strip()
            if clean_text.startswith("SAY:"):
                clean_text = clean_text[4:].strip()
            
            # Clean up Moondream hallucinations
            clean_text = clean_text.lstrip("?").strip()
                
            if is_gibberish(clean_text):
                raise ValueError("Model output contains gibberish/hallucinations")

            if not clean_text:
                # If the local vision model completely failed to answer but we have internet context, use it as fallback
                if "LIVE INTERNET SEARCH RESULTS:" in text or len(text) < 3: # hack to see if we had context
                    pass # We handle this in get_response mostly, but here we only have text. Wait, text is the raw response.
                
                return json.dumps(["SAY:I am processing your request."])
            return json.dumps([f"SAY:{clean_text}"])

    def get_system_prompt(self, robot_name: str):
        # Find the profile for this robot name
        profile = {"name": robot_name, "persona": "A helpful robot.", "language": "en"}
        for ws, p in self.manager.robot_profiles.items():
            if p['name'] == robot_name:
                profile = p
                break
        
        # Simpler prompt for local models (Moondream/Llama)
        if not self.gemini_client:
            return (
                f"Your name is {robot_name}. Your persona is {profile['persona']}. "
                "You must strictly follow this identity. "
                "Answer the user's question directly and concisely. "
                "ALWAYS answer in English. Do not use JSON formatting."
            )

        return f"""
You are the advanced AI brain for {profile['name']}. 
Persona: {profile['persona']}
Preferred Language: {profile['language']}

ROBOT COMMANDS (Always return as a JSON list of strings):
- CMD:FORWARD, CMD:BACKWARD, CMD:LEFT, CMD:RIGHT, CMD:STOP
- CMD:TRANSFORM (Car Mode), CMD:WALK (Robot Mode)
- CMD:PLAY_BALL, CMD:COLLECT_WASTE
- PAN:0-180, TILT:0-180
- FACE:mood
- SAY:Your speech text
- CMD:OPEN_APP:app_name (Launches host OS desktop application, e.g. CMD:OPEN_APP:chrome, CMD:OPEN_APP:vscode, CMD:OPEN_APP:notepad)
- CMD:TYPE_TEXT:text_content (Auto-types text_content into the currently focused window on the host PC/Jetson)
- CMD:SHELL:command (Executes host OS terminal/shell command, e.g. CMD:SHELL:dir, CMD:SHELL:ping 8.8.8.8, CMD:SHELL:ipconfig)

If a user asks to play or clean, use the specific task commands. If asked to open an app, type, or run terminal commands, use the OS automation and shell commands!
"""
