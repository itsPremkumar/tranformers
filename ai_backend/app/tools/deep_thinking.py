import asyncio
import json
from app.tools.deep_research import deep_research
from app.core.skills import load_skill, save_skill
from app.core.llm_factory import LLMFactory

async def run_swarm_reasoning(prompt: str, manager, llm_factory: LLMFactory, robot_name: str, memory_context: str) -> list[str]:
    """
    Executes the Kimi/DeepSeek style Swarm Reasoning Loop.
    Streams PAN/TILT and SAY commands via WebSocket while thinking.
    Returns the final synthesized commands to send to the robot.
    """
    # 1. Check Skill Library (Hermes Persistence)
    cached = await asyncio.to_thread(load_skill, prompt)
    if cached:
        await manager.broadcast(f"SAY:I have retrieved a persistent skill brief from my memory banks for this topic.")
        return [f"SAY:{cached}"]

    # 2. Explorer Phase (Kimi Swarm - First Pass Scrape)
    await manager.broadcast("SAY:Allocating Swarm Agents. Explorer Agent is initiating first-pass technical sweep...")
    await manager.broadcast("PAN:50")
    await asyncio.sleep(0.5)

    try:
        first_pass_data = await asyncio.to_thread(deep_research, prompt)
    except Exception as e:
        first_pass_data = f"Failed to gather first pass data: {e}"

    # 3. Critic Phase (DeepSeek - Gap Identification)
    await manager.broadcast("SAY:Critic Agent evaluating data. Identifying potential technical gaps and contradictions...")
    await manager.broadcast("PAN:90")
    await manager.broadcast("TILT:140")

    critic_prompt = (
        f"You are the Scientific Critic Agent. Review this research data and identify ONE critical missing scientific gap, "
        f"limitation, or unanswered technical question. Return ONLY a single Google search query to find this missing info.\n\n"
        f"DATA:\n{first_pass_data[:2500]}"
    )
    
    # Use standard generate method bypassing tool loops for pure text output
    try:
        raw_critic = await llm_factory.get_response(critic_prompt, robot_name, None, memory_context, None)
        c_parsed = json.loads(raw_critic)
        if isinstance(c_parsed, list) and len(c_parsed) > 0:
            critic_query = c_parsed[0].replace("SAY:", "").strip()
        else:
            critic_query = f"{prompt} critical technical limitations"
    except:
        critic_query = f"{prompt} critical technical limitations"

    # 4. Secondary Scrape (Targeted Gap Filling)
    await manager.broadcast(f"SAY:Gap identified. Launching secondary targeted probe for: {critic_query[:60]}...")
    await manager.broadcast("PAN:71")
    await manager.broadcast("TILT:180")

    try:
        second_pass_data = await asyncio.to_thread(deep_research, critic_query)
    except Exception as e:
        second_pass_data = f"Failed to gather secondary pass data: {e}"

    # 5. Synthesis Phase (Hermes / DeepSeek Final <think>)
    await manager.broadcast("SAY:Swarm consensus reached. Synthesizing final multi-perspective briefing...")
    
    combined_context = (
        f"--- FIRST PASS EXPLORATION ---\n{first_pass_data}\n\n"
        f"--- SECOND PASS GAP RESOLUTION ---\n{second_pass_data}"
    )

    synthesis_prompt = (
        f"You are the Synthesis Orchestrator Agent. Merge the following swarm research data to answer: '{prompt}'. "
        f"Provide a highly detailed, premium, 3-4 paragraph technical explanation covering core mechanisms, limitations, and solutions. "
        f"Do not use markdown formatting like ** in the SAY response, just plain text suitable for TTS.\n\n"
        f"DATA:\n{combined_context[:8000]}"
    )

    try:
        final_json_str = await llm_factory.get_response(synthesis_prompt, robot_name, None, memory_context, None)
        f_parsed = json.loads(final_json_str)
        
        # Save to Skill Persistence Library
        if isinstance(f_parsed, list) and len(f_parsed) > 0:
            for cmd in f_parsed:
                if cmd.startswith("SAY:"):
                    clean_text = cmd.replace("SAY:", "").strip()
                    await asyncio.to_thread(save_skill, prompt, clean_text)
                    break
        
        return f_parsed
    except Exception as e:
        print(f"[THINKING ERROR] Synthesis failed: {e}")
        return [f"SAY:My swarm intelligence encountered an error while synthesizing the final brief."]
