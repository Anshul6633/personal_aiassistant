"""Master Autonomous Agent Orchestrator & Task Planner for JARVIS.

Translates high-level natural language instructions into coordinated multi-step execution plans.
Coordinates voice, computer vision, video clipping, desktop control, and social publishing.
"""

import os
import uuid
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from jarvis.backend.config.settings import settings, WORKSPACE_ROOT
from jarvis.backend.database.db import get_db_connection
from jarvis.backend.core.state import state_manager, AssistantState
from jarvis.backend.video.pipeline import video_pipeline
from jarvis.backend.video.source_manager import source_manager
from jarvis.backend.automation.tool_registry import tool_registry
from jarvis.backend.agents.buddy import jarvis_buddy
from jarvis.backend.agents.researcher import content_researcher
from jarvis.backend.voice.tts import tts_engine

logger = logging.getLogger("JARVIS.Orchestrator")


class AgentOrchestrator:
    def __init__(self):
        pass

    async def plan_and_execute(self, user_command: str) -> Dict[str, Any]:
        """Analyze high-level user command, formulate a task plan, and execute."""
        task_id = str(uuid.uuid4())[:8]
        await state_manager.set_status(AssistantState.PLANNING, f"Analyzing directive: '{user_command[:45]}...'")
        await state_manager.update(active_task_id=task_id, active_task_title=user_command, task_progress=5)

        # 1. Classify command intent using local Ollama
        intent_prompt = f"""You are the master brain of JARVIS. Classify the user instruction into a structured plan.
USER INSTRUCTION: "{user_command}"

Output valid JSON ONLY with this schema:
{{
  "action_type": "VIDEO_CLIPPING | DESKTOP_AUTOMATION | RESEARCH | CHAT | SYSTEM_STATUS",
  "plan_steps": ["Step 1 description", "Step 2 description", "Step 3 description"],
  "spoken_acknowledgment": "Witty, proactive Avengers-style JARVIS confirmation in English or Hindi as appropriate",
  "parameters": {{
    "folder": "folder path if mentioned or default Videos",
    "clip_count": 5,
    "target_platform": "all | youtube | instagram",
    "app_name": "chrome | vscode | notepad | etc",
    "query": "topic"
  }}
}}"""

        classification = None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": "qwen2.5:1.5b",
                        "prompt": intent_prompt,
                        "format": "json",
                        "stream": False
                    }
                )
                if res.status_code == 200:
                    classification = json.loads(res.json().get("response", "{}"))
        except Exception as e:
            logger.warning(f"Ollama intent planning failed: {e}")

        # Fallback heuristic classification if LLM JSON fails
        if not classification or "action_type" not in classification:
            cmd_lower = user_command.lower()
            if any(w in cmd_lower for w in ["clip", "short", "reel", "podcast", "video", "cut", "subtitle"]):
                classification = {
                    "action_type": "VIDEO_CLIPPING",
                    "plan_steps": ["Scan source videos", "Transcribe audio", "Score hooks", "Render 9:16 vertical clips"],
                    "spoken_acknowledgment": "Understood Boss! Initializing the video clipping factory right away.",
                    "parameters": {"clip_count": 5, "target_platform": "all"}
                }
            elif any(w in cmd_lower for w in ["open", "launch", "chrome", "vscode", "minimize", "screen", "click", "mouse"]):
                classification = {
                    "action_type": "DESKTOP_AUTOMATION",
                    "plan_steps": ["Inspect desktop state", "Execute GUI action"],
                    "spoken_acknowledgment": "Right away Boss. Executing desktop control.",
                    "parameters": {"app_name": "chrome"}
                }
            elif any(w in cmd_lower for w in ["research", "trend", "viral", "idea", "topic"]):
                classification = {
                    "action_type": "RESEARCH",
                    "plan_steps": ["Analyze public trends", "Generate viral hooks"],
                    "spoken_acknowledgment": "On it, Boss. Gathering viral content intelligence.",
                    "parameters": {"query": user_command}
                }
            else:
                classification = {
                    "action_type": "CHAT",
                    "plan_steps": ["Formulate response"],
                    "spoken_acknowledgment": "Thinking...",
                    "parameters": {}
                }

        # 2. Speak immediate acknowledgment
        ack_speech = classification.get("spoken_acknowledgment", "Understood Boss. Executing task.")
        await state_manager.set_status(AssistantState.SPEAKING, ack_speech)
        await tts_engine.synthesize(ack_speech)

        # 3. Execute according to plan
        action = classification.get("action_type")
        result_data = {}

        if action == "VIDEO_CLIPPING":
            # Search for videos in user videos folder or tests folder
            videos_folder = classification.get("parameters", {}).get("folder")
            if not videos_folder or not os.path.exists(videos_folder):
                videos_folder = str(WORKSPACE_ROOT / "jarvis" / "tests")

            found_videos = source_manager.scan_folder_for_videos(videos_folder)
            if not found_videos:
                # Check user home Videos folder
                user_vids = str(Path.home() / "Videos")
                found_videos = source_manager.scan_folder_for_videos(user_vids)

            if found_videos:
                target_video = found_videos[0]
                clip_count = int(classification.get("parameters", {}).get("clip_count", 3))
                clips = await video_pipeline.process_video(
                    target_video,
                    num_clips=clip_count,
                    target_duration=45.0,
                    task_id=task_id
                )
                result_data = {"status": "SUCCESS", "clips_created": len(clips), "clips": clips}
                completion_speech = f"Task complete, Boss! I've produced {len(clips)} vertical clips ready for publishing."
                await tts_engine.synthesize(completion_speech)
            else:
                result_data = {"status": "NO_VIDEOS_FOUND", "message": "No source videos found in target folder."}

        elif action == "DESKTOP_AUTOMATION":
            app = classification.get("parameters", {}).get("app_name", "notepad")
            res = tool_registry.execute_tool("launch_application", {"app_name": app})
            result_data = res

        elif action == "RESEARCH":
            query = classification.get("parameters", {}).get("query", "AI Podcasts")
            ideas = await content_researcher.get_viral_ideas(niche=query, count=5)
            result_data = {"status": "SUCCESS", "ideas": ideas}

        else:
            # Direct chat response
            chat_reply = await jarvis_buddy.generate_response(user_command)
            await tts_engine.synthesize(chat_reply)
            result_data = {"status": "SUCCESS", "response": chat_reply}

        await state_manager.set_status(AssistantState.IDLE, "All systems nominal.")
        await state_manager.update(task_progress=100)
        return {
            "task_id": task_id,
            "classification": classification,
            "result": result_data
        }


orchestrator = AgentOrchestrator()

