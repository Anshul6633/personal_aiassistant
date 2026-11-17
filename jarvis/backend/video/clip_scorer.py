"""Candidate Clip Scoring Engine with 6-Factor Algorithmic Weights.

Enforces:
- Hook strength: 25%
- Story completeness: 20%
- Information value: 20%
- Engagement potential: 15%
- Audio quality: 10%
- Visual quality: 10%
Total: 100 points.

Also performs Non-Maximum Suppression (NMS) to eliminate duplicate/overlapping clip windows.
"""

import math
from typing import List, Dict, Any


class ClipScorer:
    def __init__(self):
        # Explicit scoring factor weights
        self.W_HOOK = 0.25
        self.W_STORY = 0.20
        self.W_INFO = 0.20
        self.W_ENGAGEMENT = 0.15
        self.W_AUDIO = 0.10
        self.W_VISUAL = 0.10

    def compute_scores(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weighted score out of 100 for a candidate segment."""
        # Factors are normalized 0-100
        hook = float(candidate.get("hook_strength", 70.0))
        story = float(candidate.get("story_completeness", 75.0))
        info = float(candidate.get("info_value", 70.0))
        engagement = float(candidate.get("engagement_potential", 70.0))
        audio = float(candidate.get("audio_quality", 85.0))
        visual = float(candidate.get("visual_quality", 85.0))

        total = (
            hook * self.W_HOOK +
            story * self.W_STORY +
            info * self.W_INFO +
            engagement * self.W_ENGAGEMENT +
            audio * self.W_AUDIO +
            visual * self.W_VISUAL
        )

        candidate["hook_score"] = round(hook, 1)
        candidate["story_score"] = round(story, 1)
        candidate["info_score"] = round(info, 1)
        candidate["engagement_score"] = round(engagement, 1)
        candidate["audio_score"] = round(audio, 1)
        candidate["visual_score"] = round(visual, 1)
        candidate["total_score"] = round(total, 1)
        return candidate

    def remove_duplicates(self, candidates: List[Dict[str, Any]], iou_threshold: float = 0.35) -> List[Dict[str, Any]]:
        """Remove overlapping candidate segments using Non-Maximum Suppression."""
        if not candidates:
            return []

        # Sort descending by total_score
        sorted_candidates = sorted(candidates, key=lambda x: x.get("total_score", 0), reverse=True)
        selected: List[Dict[str, Any]] = []

        for cand in sorted_candidates:
            c_start = cand["start_time"]
            c_end = cand["end_time"]
            overlap_found = False

            for sel in selected:
                s_start = sel["start_time"]
                s_end = sel["end_time"]

                # Calculate 1D Intersection over Union (IoU) of time range
                intersection = max(0.0, min(c_end, s_end) - max(c_start, s_start))
                union = max(c_end, s_end) - min(c_start, s_start)

                if union > 0 and (intersection / union) > iou_threshold:
                    overlap_found = True
                    break

            if not overlap_found:
                selected.append(cand)

        return selected

    def rank_and_filter(self, candidates: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """Score, filter duplicates, and rank the top K best clips."""
        scored = [self.compute_scores(c) for c in candidates]
        deduped = self.remove_duplicates(scored)
        return deduped[:top_k]


clip_scorer = ClipScorer()

