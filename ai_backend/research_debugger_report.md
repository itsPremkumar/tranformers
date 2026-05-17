# Targeted Deep Research AI Validation Report

**Date:** 2026-05-17 17:06:18

## Test Summary
| Test Case | Status | Latency (ms) | Keywords Checked |
|---|---|---|---|
| SGE AI Overview Research | PASS | 72516.72 | artificial, intelligence, SAY: |
| News Perspective Research | PASS | 61258.58 | SpaceX, Starship, launch, SAY:, thinking, clear answer |

## Detailed Results
### SGE AI Overview Research
**Prompt:** Do deep research to explain what is ai
**Response:** `["SAY:Here is what I found: \r [ACTION] ======= VISUAL DEEP RESEARCH START =======\r Original Request: 'Do deep research to explain what is ai'\r \r [RESEARCH PLAN] Generated 3 Exhaustive Research Perspectives:\r   - Technical/Core M"]`

### News Perspective Research
**Prompt:** Do deep research on latest news about SpaceX Starship launches
**Response:** `["SAY:Here is what I found: \r [ACTION] ======= VISUAL DEEP RESEARCH START =======\r Original Request: 'Do deep research on latest news about SpaceX Starship launches'\r \r [RESEARCH PLAN] Generated 3 Exhaustive Research Perspective"]`


## Logs
```
[17:03:57] ==================================================================
[17:03:57] 🚀 STARTING ADVANCED RESEARCH GRADER & SCRAEP DEBUGGER TEST RUN 🚀
[17:03:57] ==================================================================
[17:03:59] 
[TEST CASE] SGE AI Overview Research
[17:03:59] --- Sending Research Prompt: Do deep research to explain what is ai ---
[17:05:06] Received WS Text: SAY:I can see the camera feed, but I'm having trouble identifying everything clearly.
[17:05:06] Received WS Text: SAY:Here is what I found:  [ACTION] ======= VISUAL DEEP RESEARCH START ======= Original Request: 'Do deep research to explain what is ai'  [RESEARCH PLAN] Generated 3 Exhaustive Research Perspectives:   - Technical/Core M
[17:05:11] Status: PASS (72516.72ms)
[17:05:14] 
[TEST CASE] News Perspective Research
[17:05:14] --- Sending Research Prompt: Do deep research on latest news about SpaceX Starship launches ---
[17:06:12] Received WS Text: SAY:I can see the camera feed, but I'm having trouble identifying everything clearly.
[17:06:13] Received WS Text: SAY:Here is what I found:  [ACTION] ======= VISUAL DEEP RESEARCH START ======= Original Request: 'Do deep research on latest news about SpaceX Starship launches'  [RESEARCH PLAN] Generated 3 Exhaustive Research Perspective
[17:06:15] Status: PASS (61258.58ms)
[17:06:18] 
Research Grader Run Complete.
[17:06:18] 
[ADVANCED DEBUGGER] Collecting and structuring raw scraped research data...
[17:06:18] [DEBUGGER] Processing current_run.json content for query: 'Do deep research on latest news about SpaceX Starship launches'
[17:06:18] [DEBUGGER ITEM] Structuring detailed data for: https://www.google.com/search?q=Do%20deep%20research%20on%20latest%20news%20about%20SpaceX%20Starship%20launches
[17:06:18] [DEBUGGER ITEM] Structuring detailed data for: https://phys.org/news/2025-08-spacex-starship-tuesday-night-days.html
[17:06:18] [DEBUGGER ITEM] Structuring detailed data for: https://phys.org/news/2025-10-spacex-starship-flight-monday.html
[17:06:18] [DEBUGGER ITEM] Structuring detailed data for: https://en.wikipedia.org/wiki/List_of_Starship_launches
[17:06:18] [DEBUGGER ITEM] Structuring detailed data for: https://news.google.com/stories/CAAqNggKIjBDQklTSGpvSmMzUnZjbmt0TXpZd1NoRUtEd2kyaTlLTEVSR2NZdEdGWHdvR1R5Z0FQAQ?hl=en-IN&gl=IN&ceid=IN:en
[17:06:18] [DEBUGGER ITEM] Structuring detailed data for: https://news.google.com/stories/CAAqNggKIjBDQklTSGpvSmMzUnZjbmt0TXpZd1NoRUtEd2kyaTlLTEVSRXFMZWRBUGNzYmRpZ0FQAQ?hl=en-IN&gl=IN&ceid=IN:en
[17:06:18] [DEBUGGER ITEM] Structuring detailed data for: https://www.youtube.com/watch?v=b28zbsnk-48
[17:06:18] [DEBUGGER SUCCESS] Compiled detailed raw audit payload for line-by-line verification at: C:\one\tranformers\ai_backend\app\debug_screenshots\research_debugger_audit.json
```
