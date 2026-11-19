"""AI Highlight Detection & Standalone Segment Boundary Identifier.

Analyzes timestamped Whisper transcripts to discover standalone hooks,
educational stories, emotional moments, and high-impact discussions.
"""

import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from jarvis.backend.config.settings import settings
from jarvis.backend.agents.buddy import jarvis_buddy

logger = logging.getLogger("JARVIS.HighlightDetector")

# Common viral hook indicator keywords
HOOK_TRIGGER_WORDS = [
    "secret", "mistake", "never", "always", "truth", "why", "how to",
    "the reason", "shocking", "million", "future", "nobody", "stop doing",
    "actually", "crazy", "warning", "lesson", "biggest", "rule", "money"
]


class HighlightDetector:
    def __init__(self):
        pass

    def create_candidate_windows(
        self,
        transcript_data: Dict[str, Any],
        min_duration: float = 20.0,
        max_duration: float = 65.0,
        target_duration: float = 45.0
    ) -> List[Dict[str, Any]]:
        """Slice Whisper segments into coherent standalone candidate windows."""
        segments = transcript_data.get("segments", [])
        if not segments:
            return []

        candidates = []
        n = len(segments)

        for i in range(n):
            # 2026 Golden Rule #1: 0.0s Climax Injection - snap exactly to first word speech start (zero dead air)
            seg_words = segments[i].get("words", [])
            if seg_words and "start" in seg_words[0]:
                seg_start = seg_words[0]["start"]
            else:
                seg_start = segments[i]["start"]

            current_text = []
            hook_strength = 60.0

            # Inspect opening line for hook markers
            opening_text = segments[i]["text"].lower()
            if any(w in opening_text for w in HOOK_TRIGGER_WORDS) or opening_text.endswith("?"):
                hook_strength += 25.0

            for j in range(i, n):
                current_text.append(segments[j]["text"])
                seg_end = segments[j]["end"]
                duration = seg_end - seg_start

                if min_duration <= duration <= max_duration:
                    full_window_text = " ".join(current_text)
                    word_count = len(full_window_text.split())

                    # Calculate information and story completeness heuristics (Golden Rule #2 Audio Loop design)
                    completeness = 70.0
                    end_text = segments[j]["text"].strip()
                    if end_text.endswith((".", "!", "?")):
                        completeness += 15.0
                    # If ending word connects grammatically back to opening clause, award retention bonus
                    first_word = opening_text.split()[0] if opening_text.split() else ""
                    last_word = end_text.lower().split()[-1].strip(".,!?") if end_text.split() else ""
                    if last_word in ("because", "and", "so", "which", "wait", "like", "when", "that"):
                        completeness += 20.0  # Endless loop multiplier

                    engagement = min(95.0, 60.0 + (word_count / duration) * 8.0)

                    candidates.append({
                        "start_time": round(seg_start, 2),
                        "end_time": round(seg_end, 2),
                        "duration": round(duration, 2),
                        "text": full_window_text,
                        "hook_strength": min(100.0, hook_strength),
                        "story_completeness": min(100.0, completeness),
                        "info_value": 75.0,
                        "engagement_potential": min(100.0, engagement),
                        "audio_quality": 88.0,
                        "visual_quality": 88.0,
                    })

                if duration > max_duration:
                    break

        return candidates

    async def enrich_with_ai(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Craft viral title, engaging caption, and high-CTR hashtags using Groq Cloud or local Ollama."""
        from jarvis.backend.database.memory import memory_manager
        prompt = f"""You are a viral social media video editor for YouTube Shorts and Instagram Reels.
Analyze this video clip transcript and produce metadata:

TRANSCRIPT:
"{candidate['text']}"

Output valid JSON ONLY with this schema:
{{
  "title": "Short punchy click-worthy title (under 50 chars)",
  "caption": "Engaging description with a question for viewers",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
  "debate_comment": "Binary polarizing debate question for pinned comment (e.g. Did he throw? Comment 🔥 for YES or 💀 for NO!)",
  "hook_rating": 85
}}"""

        # Priority 1: Groq Cloud LPU (Ultra-fast, zero-cost, works on Render & cloud)
        groq_key = settings.GROQ_API_KEY or memory_manager.get_memory("groq_api_key")
        if groq_key:
            for g_model in ["llama-3.3-70b-versatile", "qwen/qwen3.8-27b"]:
                try:
                    payload = {
                        "model": g_model,
                        "messages": [
                            {"role": "system", "content": "You are a viral short-form video metadata expert. Respond ONLY with valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.5,
                        "max_tokens": 180
                    }
                    async with httpx.AsyncClient(timeout=8.0) as client:
                        res = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {groq_key}"},
                            json=payload
                        )
                        if res.status_code == 200:
                            data = json.loads(res.json()["choices"][0]["message"]["content"])
                            candidate["title"] = data.get("title", candidate["text"][:45] + "...")
                            candidate["caption"] = data.get("caption", candidate["text"][:120] + "...")
                            candidate["tags"] = " ".join(data.get("hashtags", ["#shorts", "#reels", "#viral"]))
                            if data.get("debate_comment"):
                                candidate["debate_comment"] = data["debate_comment"]
                            return candidate
                except Exception as ge:
                    logger.debug(f"Groq enrich note ({g_model}): {ge}")

        # Priority 2: Local Ollama (fast timeout so it never hangs if Ollama is stopped)
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": "qwen2.5:1.5b",
                        "prompt": prompt,
                        "format": "json",
                        "stream": False
                    }
                )
                if res.status_code == 200:
                    data = json.loads(res.json().get("response", "{}"))
                    candidate["title"] = data.get("title", "High-Impact Highlight")
                    candidate["caption"] = data.get("caption", candidate["text"][:120] + "...")
                    candidate["tags"] = " ".join(data.get("hashtags", ["#shorts", "#reels", "#viral"]))
                    return candidate
        except Exception as e:
            logger.debug(f"Ollama enrich pass: {e}")

        # Priority 3: Fallback default metadata
        candidate["title"] = candidate["text"][:45] + "..."
        candidate["caption"] = candidate["text"][:150]
        candidate["tags"] = "#shorts #reels #viral #podcast #trending"
        return candidate


highlight_detector = HighlightDetector()

