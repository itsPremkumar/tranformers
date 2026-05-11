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

    async def get_response(self, user_prompt: str, robot_name: str, image=None, hw_status: dict = None):
        """The single unified entry point for AI logic with robot-specific memory and hardware awareness."""
        
        # 0. Load Robot-Specific Memory (Run in thread to avoid blocking)
        history, knowledge = await asyncio.to_thread(memory_manager.get_robot_memory, robot_name)
        history_text = "\n".join(history[-5:]) # Last 5 exchanges
        
        # 1. Build Final Prompt
        system_prompt = self.get_system_prompt(robot_name)
        
        status_text = ""
        if hw_status:
            status_text = f"\nCURRENT HARDWARE STATUS:\n- Battery: {hw_status.get('battery', 0)}%\n- Mode: {hw_status.get('mode', 'Unknown')}\n- Obstacle Distance: {hw_status.get('distance', 0)}cm\n"

        full_prompt = f"{system_prompt}\n{status_text}\nKNOWLEDGE OF USER/ENVIRONMENT: {knowledge}\n\nPAST CONVERSATION:\n{history_text}\n\nUser: {user_prompt}"

        # 2. Try Gemini (Primary with Function Calling)
        raw_response = None
        if self.gemini_client:
            try:
                chat = self.gemini_client.start_chat(enable_automatic_function_calling=True)
                content = [full_prompt, image] if image else full_prompt
                # Use async call for Gemini
                response = await chat.send_message_async(content)
                raw_response = self.format_response(response.text)
            except Exception as e:
                print(f"[LLM] Gemini Error: {e}")

        # 3. Fallbacks / Local LLM Path
        if not raw_response:
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
                raw_response = json.dumps([f"SAY:I am currently processing. Please try again."])

        # 4. Save Interaction to Persistent Memory (Run in thread)
        await asyncio.to_thread(memory_manager.save_interaction, robot_name, user_prompt, raw_response)
        
        return raw_response

    def format_response(self, text):
        try:
            clean = text.replace("```json", "").replace("```", "").strip()
            json.loads(clean)
            return clean
        except:
            return json.dumps([f"SAY:{text}"])

    def get_system_prompt(self, robot_name: str):
        # Find the profile for this robot name
        profile = {"name": robot_name, "persona": "A helpful robot.", "language": "en"}
        for ws, p in self.manager.robot_profiles.items():
            if p['name'] == robot_name:
                profile = p
                break
                
        return f"""
You are the advanced AI brain for {profile['name']}. 
Persona: {profile['persona']}
Preferred Language: {profile['language']}

CRITICAL TASK VALIDATION:
1. Before performing any task, check the 'CURRENT HARDWARE STATUS' provided.
2. If Battery < 10%, decline physical tasks and say "I am not able to do this task because my energy is too low."
3. If a task requires vision (like tracking) but the camera feed is missing, decline it.
4. If a task is physically impossible for a robot of your type, decline it politely.
5. If feasible, acknowledge and start immediately.

ROBOT COMMANDS (Always return as a JSON list of strings):
- CMD:FORWARD, CMD:BACKWARD, CMD:LEFT, CMD:RIGHT, CMD:STOP
- CMD:TRANSFORM (Car Mode), CMD:WALK (Robot Mode)
- CMD:PLAY_BALL, CMD:COLLECT_WASTE
- PAN:0-180, TILT:0-180
- FACE:mood
- SAY:Your speech text

If a user asks to play or clean, use the specific task commands.
"""
