"""YouTube Shorts & Reels Metadata & Proper Description Generator.

Generates high-CTR, SEO-optimized titles, comprehensive descriptions,
fair-use source attribution, community engagement CTAs, and targeted hashtags.
"""

import re
import random
from typing import Dict, Any, List, Optional


def generate_proper_youtube_description(
    title: str,
    summary: str,
    transcript_quote: Optional[str] = None,
    source_title: Optional[str] = None,
    source_channel: Optional[str] = None,
    source_url: Optional[str] = None,
    tags: Optional[List[str]] = None,
    channel_name: str = "GHOST _OF_FOOTBALL"
) -> str:
    """Generate a high-converting, professional, and SEO-rich YouTube Shorts description.
    
    Includes:
    1. Hook & Headline
    2. Contextual Story / Clip Breakdown
    3. Notable Quote from Commentary/Dialogue
    4. Community Engagement Calls-to-Action (Like, Subscribe, Comment)
    5. Full Source Attribution & Fair-Use Notice
    6. Targeted High-Volume Search Tags and Viral Hashtags
    """
    clean_title = title.replace("#Shorts", "").replace("#shorts", "").strip()
    clean_summary = summary.strip() if summary else "Watch this unforgettable highlight in high definition!"

    desc_lines = [
        f"⚡ {clean_title}",
        "",
        "📖 CLIP BREAKDOWN:",
        f"{clean_summary}",
        ""
    ]

    # Add memorable dialogue/commentary quote if available
    if transcript_quote and len(transcript_quote.strip()) > 10:
        quote_snippet = transcript_quote.strip().replace("\n", " ")[:180]
        desc_lines.extend([
            f'💬 Commentary / Quote: "{quote_snippet}"',
            ""
        ])

    # Detect niche/topic
    combined_text = f"{title} {summary} {source_title or ''}".lower()
    is_football = any(k in combined_text for k in ["football", "soccer", "goal", "ronaldo", "messi", "mbappe", "bellingham", "yamal", "haaland"])

    if is_football:
        cta_question = "💬 Comment below: Who is the greatest player in football history?"
        channel_display = channel_name
        base_tags = ["Shorts", "YouTubeShorts", "Football", "Soccer", "Viral", "Trending"]
        bottom_tags = "#shorts #viral #trending #football #soccer #fyp #foryou #sports"
    else:
        # Gaming / GTA 6 / Streamer high-growth niche
        cta_question = "💬 Comment below: What would you do in this situation? Drop a W or L! 👇"
        channel_display = "Viral Gaming Hub" if "football" in channel_name.lower() else channel_name
        base_tags = ["Shorts", "YouTubeShorts", "GTA6", "GTA", "Gaming", "GamingShorts", "ViralGaming", "CarryMinati", "Trending", "Clutch"]
        bottom_tags = "#shorts #gta6 #gaming #gamingshorts #viral #trending #fyp #foryou #carryminati"

    # Engagement CTAs
    desc_lines.extend([
        "🔥 ENJOYED THIS EDIT? SUPPORT THE CHANNEL:",
        f"🔔 SUBSCRIBE to @{channel_display.replace(' ', '')} for daily high-energy viral gaming moments!",
        "👍 Hit LIKE if this was an absolute clutch!",
        cta_question,
        ""
    ])

    # Fair-use / Source Attribution
    if source_title or source_channel or source_url:
        desc_lines.append("🎬 SOURCE & CREDITS:")
        if source_title:
            desc_lines.append(f"• Original Video: {source_title}")
        if source_channel:
            desc_lines.append(f"• Creator / Channel: {source_channel}")
        if source_url:
            desc_lines.append(f"• Original Link: {source_url}")
        desc_lines.append("")

    if tags:
        for t in tags:
            clean_t = re.sub(r"[#,\s]", "", t).strip()
            if clean_t and clean_t not in base_tags:
                base_tags.append(clean_t)

    # Format hashtags (up to 12 hashtags)
    hashtags_str = " ".join([f"#{t}" for t in base_tags[:12]])
    desc_lines.extend([
        "🏷️ HASHTAGS:",
        hashtags_str,
        "",
        "---",
        bottom_tags
    ])

    return "\n".join(desc_lines)


def format_viral_shorts_title(raw_title: str) -> str:
    """Format title to strictly adhere to YouTube Shorts viral CTR standards (<100 chars, emojis, #Shorts).
    
    Dynamically applies high-CTR emotional trigger emojis based on the topic.
    """
    clean = re.sub(r"#(shorts|reels|gta6|gaming|viral)", "", raw_title, flags=re.IGNORECASE).strip()
    clean = re.sub(r"\.(mp4|mov|avi|mkv)$", "", clean, flags=re.IGNORECASE).strip()
    clean = clean.replace("_", " ")

    lower = clean.lower()
    if any(k in lower for k in ["football", "soccer", "ronaldo", "messi", "scored", "mbappe", "champions league"]):
        emojis = ["⚽🔥", "⚽⚡", "👑⚽", "🥶⚽", "🤯⚽", "🏆⚡"]
    elif any(k in lower for k in ["money", "rich", "million", "billion", "car", "supercar"]):
        emojis = ["💸🔥", "💰🤯", "🤑⚡", "🔥💸", "💎🚀"]
    else:
        # Gaming / Action / GTA 6 / Streamer Climax
        emojis = ["💀🔥", "🤯💥", "😱🔥", "🎮⚡", "😭💀", "🚨💥", "🔥🎮", "🥶💀", "👀🔥", "🚀💥"]

    emoji = random.choice(emojis)

    formatted = f"{clean.title()} {emoji} #Shorts"
    if len(formatted) > 95:
        max_len = 90 - len(emoji) - len(" #Shorts")
        formatted = f"{clean[:max_len].strip()}... {emoji} #Shorts"

    return formatted


def generate_viral_instagram_caption(
    title: str,
    summary: str,
    transcript_quote: Optional[str] = None,
    source_title: Optional[str] = None,
    source_channel: Optional[str] = None,
    source_url: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> str:
    """Format high-engagement Instagram Reels caption with hook, value, CTA, creator credit, and 15+ hashtags."""
    lines = []

    # 1. First-line visual hook
    clean_title = re.sub(r"#shorts|#reels", "", title, flags=re.IGNORECASE).strip()
    lines.append(f"🔥 {clean_title}")
    lines.append("")

    # 2. Quote or punchy summary
    if transcript_quote:
        lines.append(f'"{transcript_quote.strip()}"')
        lines.append("")
    elif summary:
        lines.append(summary.strip())
        lines.append("")

    # 3. High-Conversion Engagement & Share trigger (Sends Per Reach Multiplier)
    dm_prompts = [
        "🚀 Send this to a friend who always fails the mission! 💀",
        "🚀 Send this to your friend who drives like this in GTA 💀🚗",
        "Tag your duo who would choke this mission immediately 😂👇",
        "Bro really thought he had 200 IQ in GTA 6 😭 W or L move? 👇",
        "Send this to the group chat... this had me crying 😭💀",
        "Unreal clutch from the stream! Rate this 1-10 below! 🔥🚀"
    ]
    lines.extend([
        random.choice(dm_prompts),
        "👇 Drop a W or L in the comments!",
        "⚡ Follow @clipperwithout for daily viral gaming moments!"
    ])
    lines.append("")

    # 4. Fair Use & Creator Credit
    if source_channel or source_title:
        credit = source_channel or source_title
        lines.append(f"🎥 Video Credit / Source: @{credit}")
        lines.append("⚠️ For entertainment & educational purposes under fair use.")
        lines.append("")

    # 5. Targeted Instagram Hashtags (Strict 3-5 limit for modern algorithm optimization)
    base_hashtags = []
    combined_text = f"{title} {summary} {source_title or ''}".lower()
    if any(k in combined_text for k in ["football", "soccer", "goal", "ronaldo", "messi", "mbappe"]):
        base_hashtags = ["football", "soccer", "cr7", "messi", "reels"]
    elif any(k in combined_text for k in ["gta", "gaming", "carry", "vice", "stream", "heist", "clutch", "play", "gameplay"]):
        base_hashtags = ["gta6", "gaming", "gamingclips", "carryminati", "reels"]
    elif any(k in combined_text for k in ["mrbeast", "challenge", "win", "beast"]):
        base_hashtags = ["mrbeast", "gaming", "challenge", "viral", "reels"]
    elif any(k in combined_text for k in ["podcast", "rogan", "huberman", "mindset"]):
        base_hashtags = ["podcast", "mindset", "motivation", "wisdom", "reels"]
    else:
        base_hashtags = ["gaming", "gta6", "gamingclips", "viral", "reels"]

    if tags:
        for t in tags:
            ct = t.strip().lstrip("#")
            if ct and ct.lower() not in [x.lower() for x in base_hashtags]:
                base_hashtags.insert(0, ct)

    tag_str = " ".join([f"#{t}" for t in base_hashtags[:5]])
    lines.append(tag_str)

    return "\n".join(lines)


