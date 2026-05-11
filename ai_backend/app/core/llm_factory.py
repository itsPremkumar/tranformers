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
from app.core.memory import memory_manager

class LLMFactory:
    def __init__(self, manager):
        self.manager = manager
        
        # Tools registration for Gemini
        self.tools = [move_robot, set_camera_gimbal, transform_robot, web_search, wiki_lookup, play_youtube]
        
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
            clean_history.append(msg)
        
        history_text = "\n".join(clean_history[-5:]) # Last 5 clean exchanges
        
        # 1. Build Final Prompt
        system_prompt = self.get_system_prompt(robot_name)
        
        status_text = ""
        if hw_status:
            status_text = f"\nCURRENT HARDWARE STATUS:\n- Battery: {hw_status.get('battery', 0)}%\n- Mode: {hw_status.get('mode', 'Unknown')}\n- Obstacle Distance: {hw_status.get('distance', 0)}cm\n"

        search_text = f"\nLIVE INTERNET SEARCH RESULTS:\n{internet_context}\n" if internet_context else ""
        full_prompt = f"{system_prompt}\n{status_text}{search_text}\nKNOWLEDGE OF USER/ENVIRONMENT: {knowledge}\n\nPAST CONVERSATION:\n{history_text}\n\nUser: {user_prompt}"
        print(f"\n[DEBUG] --- FINAL PROMPT SENT TO AI ---\n{full_prompt}\n[DEBUG] ---------------------------------")

        # 2. Local LLM Path (Primary)
        raw_response = None
        try:
            print(f"[LLM] Using Local Model ({settings.OLLAMA_MODEL}) for {robot_name}")
            
            # Prepare message with image support for Ollama
            message = {'role': 'user', 'content': full_prompt}
            if image:
                # Convert PIL Image to base64
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                message['images'] = [img_str]
            
            res = await asyncio.to_thread(ollama.chat, model=settings.OLLAMA_MODEL, messages=[message])
            raw_response = self.format_response(res['message']['content'])
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

        if not raw_response:
            raw_response = json.dumps([f"SAY:I am currently processing. Please try again."])

        # 4. Save Interaction to Persistent Memory (Run in thread)
        await asyncio.to_thread(memory_manager.save_interaction, robot_name, user_prompt, raw_response)
        
        return raw_response

    def format_response(self, text):
        try:
            clean = text.replace("```json", "").replace("```", "").strip()
            # Try to fix single quotes common in hallucinated JSON lists
            if clean.startswith("[") and clean.endswith("]"):
                clean = clean.replace("'", '"')
            
            parsed = json.loads(clean)
            
            # Prevent hallucinated coordinates from being treated as valid commands
            if isinstance(parsed, list) and len(parsed) > 0 and any(isinstance(x, (int, float)) for x in parsed):
                raise ValueError("Model hallucinated coordinates")
                
            return clean
        except:
            clean_text = text.replace('"', '').replace("'", "").replace('[', '').replace(']', '').strip()
            if clean_text.startswith("SAY:"):
                clean_text = clean_text[4:].strip()
                
            if not clean_text or any(char.isdigit() for char in clean_text[:5]):
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
                f"You are {robot_name}, a friendly and intelligent robot. "
                f"Persona: A helpful robot. Reply in a natural, conversational way. "
                "You must ONLY reply with a valid JSON list of strings. "
                "If you want to speak, start the string with 'SAY:'. "
                "Example: [\"SAY:Hello! I am ready.\"]"
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

If a user asks to play or clean, use the specific task commands.
"""
