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

    # Engagement CTAs
    desc_lines.extend([
        "🔥 ENJOYED THIS EDIT? SUPPORT THE CHANNEL:",
        f"🔔 SUBSCRIBE to @{channel_name.replace(' ', '')} for daily high-energy edits & viral moments!",
        "👍 Hit LIKE if this gave you chills!",
        "💬 Comment below: Who is the greatest player in football history?",
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

    # SEO tags & viral hashtags
    base_tags = ["Shorts", "YouTubeShorts", "Football", "Soccer", "Viral", "Trending", "GHOST_OF_FOOTBALL"]
    if tags:
        for t in tags:
            clean_t = re.sub(r"[#,\s]", "", t).strip()
            if clean_t and clean_t not in base_tags:
                base_tags.append(clean_t)

    # Detect entity keywords from title and summary to boost relevant hashtags
    combined_text = f"{title} {summary} {source_title or ''}".lower()
    entities = [
        ("mbappe", ["Mbappe", "KylianMbappe", "RealMadrid", "France"]),
        ("haaland", ["Haaland", "ErlingHaaland", "ManCity"]),
        ("ronaldo", ["Ronaldo", "CR7", "AlNassr"]),
        ("messi", ["Messi", "InterMiami", "Argentina"]),
        ("yamal", ["LamineYamal", "Barcelona"]),
        ("vinicius", ["ViniJr", "RealMadrid", "Brazil"]),
        ("bellingham", ["Bellingham", "RealMadrid", "England"]),
        ("neymar", ["Neymar", "Santos", "Brazil"]),
        ("champions league", ["UCL", "ChampionsLeague"]),
        ("world cup", ["WorldCup", "FIFAWorldCup"])
    ]
    for key, related in entities:
        if key in combined_text:
            for r in related:
                if r not in base_tags:
                    base_tags.append(r)

    # Format hashtags (up to 12 hashtags)
    hashtags_str = " ".join([f"#{t}" for t in base_tags[:12]])
    desc_lines.extend([
        "🏷️ HASHTAGS:",
        hashtags_str,
        "",
        "---",
        "#shorts #viral #trending #football #soccer #fyp #foryou #sports"
    ])

    return "\n".join(desc_lines)


def format_viral_shorts_title(raw_title: str) -> str:
    """Format title to strictly adhere to YouTube Shorts viral CTR standards (<100 chars, emojis, #Shorts)."""
    clean = re.sub(r"#shorts", "", raw_title, flags=re.IGNORECASE).strip()
    clean = re.sub(r"\.(mp4|mov|avi|mkv)$", "", clean, flags=re.IGNORECASE).strip()
    clean = clean.replace("_", " ")

    football_emojis = ["⚽🔥", "⚽⚡", "👑⚽", "🥶⚽", "🤯⚽", "🏆⚡"]
    emoji = random.choice(football_emojis)

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

    # 3. Engagement trigger
    lines.extend([
        "👇 Drop your thoughts in the comments!",
        "⚡ Follow @clipperwithout for more viral daily content!"
    ])
    lines.append("")

    # 4. Fair Use & Creator Credit
    if source_channel or source_title:
        credit = source_channel or source_title
        lines.append(f"🎥 Video Credit / Source: @{credit}")
        lines.append("⚠️ For entertainment & educational purposes under fair use.")
        lines.append("")

    # 5. Targeted Instagram Hashtags (15-20)
    base_hashtags = [
        "reels", "viralreels", "explorepage", "trending", "instareels",
        "fyp", "foryou", "viral", "reelsinstagram", "contentcreator"
    ]
    if tags:
        for t in tags:
            ct = t.strip().lstrip("#")
            if ct and ct.lower() not in [x.lower() for x in base_hashtags]:
                base_hashtags.append(ct)

    combined_text = f"{title} {summary} {source_title or ''}".lower()
    if any(k in combined_text for k in ["football", "soccer", "goal", "ronaldo", "messi", "mbappe"]):
        base_hashtags.extend(["football", "soccer", "cr7", "messi", "skills", "goals", "ucl"])
    elif any(k in combined_text for k in ["mrbeast", "challenge", "win", "beast"]):
        base_hashtags.extend(["mrbeast", "challenge", "youtube", "gaming", "funnymoments"])
    elif any(k in combined_text for k in ["podcast", "rogan", "huberman", "mindset"]):
        base_hashtags.extend(["podcast", "mindset", "motivation", "wisdom", "success"])

    tag_str = " ".join([f"#{t}" for t in base_hashtags[:18]])
    lines.append(tag_str)

    return "\n".join(lines)


