"""RLHF (Reinforcement Learning from Human Feedback) Intelligence Engine for JARVIS.

Continuously captures user feedback (thumbs up/down, corrections, verbal praise/critique),
updates learned policy reward weights, and dynamically aligns JARVIS's behavior in real-time.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from jarvis.backend.database.rlhf import (
    init_rlhf_tables,
    save_feedback,
    upsert_policy_rule,
    get_active_policy_rules,
    get_feedback_logs,
    toggle_policy_rule,
    delete_policy_rule,
    get_rlhf_metrics
)

logger = logging.getLogger("JARVIS.RLHF")

# Initialize SQLite tables on import
try:
    init_rlhf_tables()
except Exception as e:
    logger.warning(f"Could not initialize RLHF tables on module import: {e}")


class RLHFEngine:
    def __init__(self):
        pass

    def record_human_feedback(
        self,
        context_type: str,
        prompt_or_input: str,
        action_or_output: str,
        feedback_type: str,
        user_correction: Optional[str] = None,
        category: str = "general"
    ) -> Dict[str, Any]:
        """Record explicit or implicit human feedback, adjust policy weights, and extract rules."""
        # 1. Determine reward score
        if feedback_type == "positive":
            reward = 1.0
        elif feedback_type == "negative":
            reward = -1.0
        elif feedback_type == "correction":
            reward = 2.0
        else:
            reward = 0.5

        # 2. Extract or distill policy rule if correction provided
        learned_rule = None
        if user_correction and user_correction.strip():
            learned_rule = self._distill_rule_from_correction(user_correction, prompt_or_input, category)
            if learned_rule:
                upsert_policy_rule(learned_rule, category, reward_delta=2.0)
                logger.info(f"RLHF Learned New Policy Rule: '{learned_rule}' (Reward +2.0)")

        # 3. Save feedback into database
        fb_id = save_feedback(
            context_type=context_type,
            prompt_or_input=prompt_or_input,
            action_or_output=action_or_output,
            feedback_type=feedback_type,
            reward_score=reward,
            user_correction=user_correction,
            learned_rule=learned_rule,
            category=category
        )

        logger.info(f"Recorded RLHF feedback #{fb_id} [{feedback_type.upper()}] Reward: {reward:+.1f} in category '{category}'")

        return {
            "feedback_id": fb_id,
            "feedback_type": feedback_type,
            "reward_score": reward,
            "learned_rule": learned_rule,
            "status": "RECORDED"
        }

    def _distill_rule_from_correction(self, correction: str, prompt: str, category: str) -> str:
        """Heuristic and pattern-based rule distillation from user correction text."""
        cleaned = correction.strip()
        cleaned_lower = cleaned.lower()

        # Remove leading trigger phrases
        for prefix in [
            "always remember to", "remember to", "from now on", "always",
            "never", "don't ever", "don't", "please make sure to",
            "aage se", "yaad rakhna", "hamesha", "kabhi mat"
        ]:
            if cleaned_lower.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                cleaned_lower = cleaned.lower()
                break

        # Standardize formatting
        if any(w in cleaned_lower for w in ["never", "don't", "mat karo"]):
            rule = f"Avoid: {cleaned.capitalize()}"
        else:
            rule = f"Prefer: {cleaned.capitalize()}"

        # Clean trailing punctuation
        rule = rule.rstrip(".!?,")
        return f"{rule}."

    def detect_dialogue_feedback(
        self,
        current_user_message: str,
        previous_assistant_message: Optional[str] = None
    ) -> Optional[Tuple[str, str, Optional[str]]]:
        """Detect if the user's conversational message represents feedback, correction, or praise.

        Returns: (feedback_type, category, user_correction_text) or None
        """
        msg = current_user_message.strip()
        lower = msg.lower()

        # 1. Explicit Teaching / Policy Commands
        teaching_triggers = [
            "from now on", "always remember", "remember to always", "never do that again",
            "make sure to always", "don't ever", "aage se yaad rakhna", "aage se hamesha",
            "next time do", "agli baar"
        ]
        for trigger in teaching_triggers:
            if trigger in lower:
                return ("correction", "persona", msg)

        # 2. Negative Feedback / Disapproval
        negative_triggers = [
            "no that's wrong", "that is wrong", "you are wrong", "galat hai",
            "not like this", "aisa nahi", "don't do that", "that's terrible",
            "bad response", "stop doing that", "too long", "too slow", "bekaar hai"
        ]
        if any(t == lower or lower.startswith(t) or f" {t}" in lower for t in negative_triggers):
            # Check if followed by correction explanation (e.g. "No that's wrong, I meant football")
            parts = re.split(r"[,;]|\bbut\b|\binstead\b|\bi meant\b", msg, flags=re.IGNORECASE)
            correction = parts[1].strip() if len(parts) > 1 and len(parts[1].strip()) > 3 else None
            return ("correction" if correction else "negative", "persona", correction)

        # 3. Positive Reinforcement / Praise
        positive_triggers = [
            "great job", "good job", "perfect", "well done", "awesome", "shabash",
            "love this", "bohot badhiya", "sahi hai", "excellent work", "spot on",
            "exactly what i wanted", "nice work"
        ]
        if any(t == lower or lower.startswith(t) or f" {t}" in lower for t in positive_triggers):
            return ("positive", "persona", None)

        return None

    def get_in_context_policy_prompt(self, max_rules: int = 6) -> str:
        """Generate high-priority RLHF learned preferences for injection into system prompts."""
        rules = get_active_policy_rules(min_weight=1.0)
        if not rules:
            return ""

        top_rules = rules[:max_rules]
        lines = [
            "--- REINFORCEMENT LEARNING FROM HUMAN FEEDBACK (ACTIVE RLHF POLICIES) ---",
            "The following preferences and rules were learned directly from Boss's feedback and corrections:",
        ]
        for r in top_rules:
            weight_str = f"+{r['reward_weight']:.1f}" if r['reward_weight'] >= 0 else f"{r['reward_weight']:.1f}"
            lines.append(f"• [Reward {weight_str}] {r['rule_text']}")
        lines.append("CRITICAL: Strictly adhere to these learned human preferences above standard defaults.")
        lines.append("------------------------------------------------------------------------")

        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        """Aggregate metrics and top active rules for the frontend HUD."""
        metrics = get_rlhf_metrics()
        rules = get_active_policy_rules()
        recent_feedback = get_feedback_logs(limit=10)

        return {
            "metrics": metrics,
            "rules": rules,
            "recent_feedback": recent_feedback
        }


rlhf_engine = RLHFEngine()

