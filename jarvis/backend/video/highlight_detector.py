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

                    # Calculate information and story completeness heuristics
                    completeness = 70.0
                    if segments[j]["text"].strip().endswith((".", "!", "?")):
                        completeness += 15.0

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
        """Use local Ollama to craft viral title, engaging caption, and high-CTR hashtags."""
        prompt = f"""You are a viral social media video editor for YouTube Shorts and Instagram Reels.
Analyze this video clip transcript and produce metadata:

TRANSCRIPT:
"{candidate['text']}"

Output valid JSON ONLY with this schema:
{{
  "title": "Short punchy click-worthy title (under 50 chars)",
  "caption": "Engaging description with a question for viewers",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
  "hook_rating": 85
}}"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
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
            logger.warning(f"Could not enrich candidate with AI: {e}")

        # Fallback default metadata
        candidate["title"] = candidate["text"][:45] + "..."
        candidate["caption"] = candidate["text"][:150]
        candidate["tags"] = "#shorts #reels #viral #podcast #trending"
        return candidate


highlight_detector = HighlightDetector()

