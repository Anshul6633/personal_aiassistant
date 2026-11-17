"""Autonomous Viral Content Researcher & Channel Branding Assistant.

Researches trending topics, generates high-CTR hooks, scripts, content calendars,
and channel branding concepts using local Ollama intelligence (zero paid API cost).
"""

import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from jarvis.backend.config.settings import settings

logger = logging.getLogger("JARVIS.Researcher")


class ContentResearcher:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.PRIMARY_MODEL
        self.fallback = settings.FALLBACK_MODEL

    async def get_viral_ideas(self, niche: str = "Technology & AI Podcasts", count: int = 5) -> List[Dict[str, Any]]:
        """Generate high-performing Shorts & Reels concepts with hooks, scripts, and target audience."""
        prompt = f"""You are a master viral YouTube Shorts & Instagram Reels producer.
Generate {count} viral content ideas for the niche: "{niche}".

Return valid JSON ONLY as an array of objects with this exact structure:
[
  {{
    "title": "Punchy Click-worthy Title",
    "hook": "First 3-second visual and audio hook that stops scrolling",
    "core_insight": "The valuable educational or entertaining fact",
    "call_to_action": "High-conversion closing question",
    "estimated_retention": "85%",
    "recommended_duration": "45s"
  }}
]"""

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": "qwen2.5:1.5b",
                        "prompt": prompt,
                        "format": "json",
                        "stream": False
                    }
                )
                if res.status_code == 200:
                    raw_text = res.json().get("response", "[]")
                    data = json.loads(raw_text)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "ideas" in data:
                        return data["ideas"]
        except Exception as e:
            logger.warning(f"Error generating viral ideas: {e}")

        # Fallback pre-curated ideas if model response fails
        return [
            {
                "title": "The AI Tool Nobody Is Talking About",
                "hook": "Stop using basic AI scripts. In 2026, autonomous desktop agents change everything.",
                "core_insight": "Local models running with zero API cost on your own GPU can operate your screen and edit 50 shorts a day.",
                "call_to_action": "Are you ready to run your own AI buddy? Comment below.",
                "estimated_retention": "88%",
                "recommended_duration": "45s"
            },
            {
                "title": "3 Habits That 10x Your Focus",
                "hook": "If you struggle with procrastination, watch this 30-second fix.",
                "core_insight": "Dopamine resets and 45-minute deep work blocks outperform 8 hours of distraction.",
                "call_to_action": "Which habit will you start today?",
                "estimated_retention": "82%",
                "recommended_duration": "30s"
            }
        ]

    async def generate_channel_branding(self, niche: str) -> Dict[str, Any]:
        """Generate channel name options, bios, tagline, and visual branding themes."""
        prompt = f"""You are a top YouTube & Instagram branding strategist.
Generate branding concepts for a new content creator channel in: "{niche}".

Return valid JSON ONLY with this schema:
{{
  "channel_names": ["Name 1", "Name 2", "Name 3", "Name 4"],
  "tagline": "Memorable one-line slogan",
  "bio": "Instagram & YouTube bio under 150 chars with emojis",
  "content_pillars": ["Pillar 1", "Pillar 2", "Pillar 3"],
  "visual_theme": "Color palette and aesthetic description"
}}"""

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": "qwen2.5:1.5b",
                        "prompt": prompt,
                        "format": "json",
                        "stream": False
                    }
                )
                if res.status_code == 200:
                    return json.loads(res.json().get("response", "{}"))
        except Exception as e:
            logger.error(f"Error generating branding: {e}")

        return {
            "channel_names": ["Nexus AI Clips", "Mindset & Code", "The Tech Vanguard", "Autonomous Pulse"],
            "tagline": "Unlocking the Future of AI & Mindset, One Short at a Time.",
            "bio": "⚡ Daily AI Insights, Tech Breakthroughs & High-Impact Motivation. Operated by JARVIS. 🚀",
            "content_pillars": ["AI Breakdowns", "Founder Mindset", "Automation Hacks"],
            "visual_theme": "Dark futuristic aesthetic with cyan and electric blue accents."
        }


content_researcher = ContentResearcher()

