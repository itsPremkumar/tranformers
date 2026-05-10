# 📚 Robot Brain: LLM Guide Index

This directory contains dedicated guides for the high-end AI models supported by the Transformer Robot.

## 🌟 Primary Choices
1.  **[Gemini 2.0 Omni](gemini_2_omni.md)**: The state-of-the-art cloud brain for vision and reasoning.
2.  **[Llama-Omni 2](llama_omni_2.md)**: The best local model for instant, native speech-to-speech interaction.

## 🧠 Specialized Capabilities
3.  **[DeepSeek R1](deepseek_r1.md)**: The "Thinking" brain for complex logic and instruction following.
4.  **[Llama 4 Maverick](llama_4_maverick.md)**: The premier all-rounder for persona, conversation, and general control.

---

## 🛠️ How to Swap Models
To change the robot's brain, simply update the `GEMINI_MODEL` or `OLLAMA_MODEL` variables in your `.env` file:

```bash
# Example: Switching to the Thinking Brain
OLLAMA_MODEL="deepseek-r1"
```
