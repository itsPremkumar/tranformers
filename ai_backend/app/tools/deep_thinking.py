import asyncio
import json
import os
import time
from app.tools.deep_research import run_research_subprocess, RUN_LOG_PATH
from app.core.skills import load_skill, save_skill
from app.core.llm_factory import LLMFactory

def compile_research_audit_report(all_pages: list, original_prompt: str, final_brief: str):
    """Compiles a complete visual markdown audit report detailing the live browser scraper actions."""
    audit_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'research_audit_report.md'))
    
    lines = [
        "# Visual Swarm Research Debugger Audit Report",
        f"**Original Query:** `{original_prompt}`",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 🔍 Swarm Execution Timeline & Scraped Content",
        "| Perspective | Website Title | Loaded URL | Load Time | Chars Scraped | Screenshot Link |",
        "|---|---|---|---|---|---|",
    ]
    
    for page in all_pages:
        p_name = page.get("perspective", "Unknown")
        title = page.get("title", "No Title").replace("|", "-")
        url = page.get("url", "No URL")
        load_time = f"{page.get('load_time_ms', 0)}ms"
        chars = page.get("chars_scraped", 0)
        
        screenshot_path = page.get("screenshot")
        if screenshot_path:
            clean_path = screenshot_path.replace('\\', '/')
            scr_link = f"[View Screenshot](file:///{clean_path})"
        else:
            scr_link = "*No Screenshot*"
            
        lines.append(f"| {p_name} | {title} | [{url[:40]}...]({url}) | {load_time} | {chars} | {scr_link} |")
        
    lines.append("")
    lines.append("## 📝 Live Synthesis Breakthrough Output")
    lines.append(f"```text\n{final_brief}\n```")
    
    try:
        with open(audit_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        print(f"[AUDITOR] Successfully generated research audit report at: {audit_path}")
    except Exception as e:
        print(f"[AUDITOR ERROR] Failed writing audit report: {e}")

async def run_swarm_reasoning(prompt: str, manager, llm_factory: LLMFactory, robot_name: str, memory_context: str) -> list[str]:
    """
    Executes the Kimi/DeepSeek style Swarm Reasoning Loop.
    Streams PAN/TILT and SAY commands via WebSocket while thinking.
    Returns the final synthesized commands to send to the robot.
    """
    # 1. Check Skill Library (Hermes Persistence)
    cached = await asyncio.to_thread(load_skill, prompt)
    if cached:
        await manager.send_command(f"SAY:I have retrieved a persistent skill brief from my memory banks for this topic.")
        return [f"SAY:{cached}"]

    all_visited_pages = []

    # 2. Explorer Phase (Kimi Swarm - First Pass Scrape)
    await manager.send_command("SAY:Allocating Swarm Agents. Explorer Agent is initiating first-pass technical sweep...")
    await manager.send_command("PAN:50")
    await asyncio.sleep(0.5)

    try:
        first_pass_data = await run_research_subprocess(prompt)
        # Parse explorer pages from current_run.json
        if os.path.exists(RUN_LOG_PATH):
            with open(RUN_LOG_PATH, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                all_visited_pages.extend(log_data.get("pages_visited", []))
    except Exception as e:
        first_pass_data = f"Failed to gather first pass data: {e}"

    # 3. Critic Phase (DeepSeek - Gap Identification)
    await manager.send_command("CMD:OLED_THINK")
    await manager.send_command("SAY:Critic Agent evaluating data. Identifying potential technical gaps and contradictions...")
    await manager.send_command("PAN:90")
    await manager.send_command("TILT:140")

    critic_prompt = (
        f"You are the Scientific Critic Agent. Review this research data and identify ONE critical missing scientific gap, "
        f"limitation, or unanswered technical question. Return ONLY a single Google search query to find this missing info.\n\n"
        f"DATA:\n{first_pass_data[:2500]}"
    )
    
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
    await manager.send_command(f"SAY:Gap identified. Launching secondary targeted probe for: {critic_query[:60]}...")
    await manager.send_command("PAN:71")
    await manager.send_command("TILT:180")

    try:
        second_pass_data = await run_research_subprocess(critic_query)
        # Parse critic pages from current_run.json
        if os.path.exists(RUN_LOG_PATH):
            with open(RUN_LOG_PATH, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                all_visited_pages.extend(log_data.get("pages_visited", []))
    except Exception as e:
        second_pass_data = f"Failed to gather secondary pass data: {e}"

    # 5. Synthesis Phase (Hermes / DeepSeek Final <think>)
    await manager.send_command("CMD:OLED_NORMAL")
    await manager.send_command("SAY:Swarm consensus reached. Synthesizing final multi-perspective briefing...")
    
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
        
        # Save to Skill Persistence Library and Compile Audit Report
        if isinstance(f_parsed, list) and len(f_parsed) > 0:
            for cmd in f_parsed:
                if cmd.startswith("SAY:"):
                    clean_text = cmd.replace("SAY:", "").strip()
                    await asyncio.to_thread(save_skill, prompt, clean_text)
                    compile_research_audit_report(all_visited_pages, prompt, clean_text)
                    break
        
        return f_parsed
    except Exception as e:
        print(f"[THINKING ERROR] Synthesis failed: {e}")
        return [f"SAY:My swarm intelligence encountered an error while synthesizing the final brief."]
