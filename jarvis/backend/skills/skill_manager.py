"""Modular Skill Manager for JARVIS.

Inspired by Leon AI (leon-ai/leon) packages architecture.
Dynamically scans and registers skills from jarvis/backend/skills/ directory.
"""

import json
import logging
import importlib.util
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("JARVIS.SkillManager")
SKILLS_DIR = Path(__file__).parent


class SkillManager:
    def __init__(self):
        self.skills: Dict[str, Dict[str, Any]] = {}
        self.discover_skills()

    def discover_skills(self):
        """Scan skills directory for skill.json manifests and action modules."""
        self.skills.clear()
        if not SKILLS_DIR.exists():
            return

        for skill_dir in SKILLS_DIR.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("__"):
                manifest_file = skill_dir / "skill.json"
                actions_file = skill_dir / "actions.py"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                        skill_name = manifest.get("name", skill_dir.name)
                        self.skills[skill_name] = {
                            "manifest": manifest,
                            "path": str(skill_dir),
                            "actions_module": str(actions_file) if actions_file.exists() else None
                        }
                        logger.info(f"Loaded modular skill: '{skill_name}' (v{manifest.get('version', '1.0.0')})")
                    except Exception as e:
                        logger.error(f"Failed to load skill at {skill_dir}: {e}")

    def list_skills(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": name,
                "version": data["manifest"].get("version", "1.0.0"),
                "description": data["manifest"].get("description", ""),
                "intents": data["manifest"].get("intents", [])
            }
            for name, data in self.skills.items()
        ]


skill_manager = SkillManager()

