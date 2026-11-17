"""Timeline State and Editing Operations Engine for JARVIS Video Studio."""

import logging
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from jarvis.backend.video.studio.models import StudioProject, StudioClip, StudioTrack, ClipTextProps

logger = logging.getLogger("JARVIS.Studio.TimelineEngine")


class TimelineEngine:
    """Performs frame-accurate non-destructive operations on timeline project models."""

    @staticmethod
    def split_clip(project: StudioProject, clip_id: str, split_time: float) -> Tuple[StudioProject, Optional[StudioClip]]:
        """Split a clip at timeline time into two contiguous clips."""
        target_clip = next((c for c in project.clips if c.id == clip_id), None)
        if not target_clip:
            logger.warning(f"Clip {clip_id} not found for split")
            return project, None

        clip_start = target_clip.start_time
        clip_end = target_clip.start_time + target_clip.duration

        # Ensure split point is inside the clip bounds
        if split_time <= clip_start + 0.1 or split_time >= clip_end - 0.1:
            logger.warning(f"Split point {split_time}s is outside valid clip bounds [{clip_start}, {clip_end}]")
            return project, None

        first_duration = split_time - clip_start
        second_duration = clip_end - split_time

        # Calculate media in/out offsets
        speed = target_clip.speed or 1.0
        media_split_point = target_clip.in_point + (first_duration * speed)
        original_out_point = target_clip.out_point

        # 1. Update left clip
        target_clip.duration = round(first_duration, 3)
        target_clip.out_point = round(media_split_point, 3)

        # 2. Create right clip
        new_clip = target_clip.model_copy(deep=True)
        new_clip.id = str(uuid.uuid4())[:8]
        new_clip.name = f"{target_clip.name} (Part 2)"
        new_clip.start_time = round(split_time, 3)
        new_clip.duration = round(second_duration, 3)
        new_clip.in_point = round(media_split_point, 3)
        new_clip.out_point = original_out_point

        project.clips.append(new_clip)
        # Recalculate total project duration
        TimelineEngine._recalc_duration(project)
        return project, new_clip

    @staticmethod
    def trim_clip(
        project: StudioProject,
        clip_id: str,
        new_in_point: Optional[float] = None,
        new_out_point: Optional[float] = None
    ) -> StudioProject:
        """Trim start or end of a clip non-destructively."""
        clip = next((c for c in project.clips if c.id == clip_id), None)
        if not clip:
            return project

        speed = clip.speed or 1.0

        if new_in_point is not None:
            delta_in = new_in_point - clip.in_point
            clip.in_point = max(0.0, new_in_point)
            clip.start_time = max(0.0, clip.start_time + (delta_in / speed))
            clip.duration = max(0.2, (clip.out_point - clip.in_point) / speed)

        if new_out_point is not None:
            clip.out_point = max(clip.in_point + 0.2, new_out_point)
            clip.duration = max(0.2, (clip.out_point - clip.in_point) / speed)

        TimelineEngine._recalc_duration(project)
        return project

    @staticmethod
    def move_clip(
        project: StudioProject,
        clip_id: str,
        target_track_id: str,
        target_start_time: float
    ) -> StudioProject:
        """Reposition clip across time and target track."""
        clip = next((c for c in project.clips if c.id == clip_id), None)
        if not clip:
            return project

        clip.track_id = target_track_id
        clip.start_time = max(0.0, round(target_start_time, 3))
        TimelineEngine._recalc_duration(project)
        return project

    @staticmethod
    def delete_clip(project: StudioProject, clip_id: str, ripple: bool = False) -> StudioProject:
        """Delete clip with optional ripple delete on the same track."""
        clip = next((c for c in project.clips if c.id == clip_id), None)
        if not clip:
            return project

        deleted_track = clip.track_id
        deleted_start = clip.start_time
        deleted_duration = clip.duration

        project.clips = [c for c in project.clips if c.id != clip_id]

        if ripple:
            # Shift subsequent clips on the same track backward
            for c in project.clips:
                if c.track_id == deleted_track and c.start_time >= deleted_start:
                    c.start_time = max(0.0, round(c.start_time - deleted_duration, 3))

        TimelineEngine._recalc_duration(project)
        return project

    @staticmethod
    def duplicate_clip(project: StudioProject, clip_id: str) -> Tuple[StudioProject, Optional[StudioClip]]:
        """Duplicate clip placed directly after the source clip."""
        clip = next((c for c in project.clips if c.id == clip_id), None)
        if not clip:
            return project, None

        dup = clip.model_copy(deep=True)
        dup.id = str(uuid.uuid4())[:8]
        dup.name = f"{clip.name} (Copy)"
        dup.start_time = round(clip.start_time + clip.duration, 3)

        project.clips.append(dup)
        TimelineEngine._recalc_duration(project)
        return project, dup

    @staticmethod
    def add_text_clip(
        project: StudioProject,
        text: str,
        start_time: float,
        duration: float = 4.0,
        preset: str = "podcast"
    ) -> StudioClip:
        """Insert a styled text/subtitle overlay clip on the text track."""
        text_track = next((t for t in project.tracks if t.type == "text"), project.tracks[0])

        font = "Arial"
        color = "#FFFFFF"
        highlight = "#FFFF00"
        if preset == "mrbeast":
            font = "Impact"
            color = "#00FFFF"
            highlight = "#FFFF00"
        elif preset == "cyberpunk":
            font = "Impact"
            color = "#00FFFF"
            highlight = "#39FF14"
        elif preset == "podcast":
            font = "Arial Bold"
            color = "#FFFF00"
            highlight = "#39FF14"

        clip = StudioClip(
            id=str(uuid.uuid4())[:8],
            track_id=text_track.id,
            name=f"Title: {text[:20]}",
            source_type="text",
            start_time=round(start_time, 3),
            duration=round(duration, 3),
            in_point=0.0,
            out_point=round(duration, 3),
            text_props=ClipTextProps(
                text=text,
                font=font,
                font_size=60,
                color=color,
                highlight_color=highlight,
                outline_color="#000000",
                outline_width=4
            )
        )
        project.clips.append(clip)
        TimelineEngine._recalc_duration(project)
        return clip

    @staticmethod
    def to_opentimelineio(project: StudioProject) -> Any:
        """Convert project into OpenTimelineIO schema for industry interchange."""
        try:
            import opentimelineio as otio
            timeline = otio.schema.Timeline(name=project.name)
            rate = float(project.fps or 30)

            for trk in project.tracks:
                kind = otio.schema.TrackKind.Video if trk.type in ("video", "text", "image") else otio.schema.TrackKind.Audio
                otio_track = otio.schema.Track(name=trk.name, kind=kind)

                track_clips = sorted([c for c in project.clips if c.track_id == trk.id], key=lambda x: x.start_time)
                current_time = 0.0

                for c in track_clips:
                    # Insert gap if clip does not start immediately
                    if c.start_time > current_time:
                        gap_dur = c.start_time - current_time
                        gap = otio.schema.Gap(
                            source_range=otio.opentime.TimeRange(
                                start_time=otio.opentime.RationalTime(0, rate),
                                duration=otio.opentime.RationalTime(round(gap_dur * rate), rate)
                            )
                        )
                        otio_track.append(gap)
                        current_time = c.start_time

                    clip_range = otio.opentime.TimeRange(
                        start_time=otio.opentime.RationalTime(round(c.in_point * rate), rate),
                        duration=otio.opentime.RationalTime(round(c.duration * rate), rate)
                    )
                    media_ref = otio.schema.ExternalReference(
                        target_url=c.source_file or c.source_url or ""
                    )
                    otio_clip = otio.schema.Clip(
                        name=c.name,
                        source_range=clip_range,
                        media_reference=media_ref
                    )
                    otio_track.append(otio_clip)
                    current_time += c.duration

                timeline.tracks.append(otio_track)
            return timeline
        except ImportError:
            logger.warning("OpenTimelineIO package not installed")
            return None

    @staticmethod
    def to_fcpxml(project: StudioProject, output_path: str) -> str:
        """Export project to Apple Final Cut Pro XML (FCPXML v1.9) for DaVinci Resolve."""
        fcpxml = ET.Element("fcpxml", version="1.9")
        resources = ET.SubElement(fcpxml, "resources")

        frame_rate = int(project.fps or 30)
        frame_dur_str = f"1/{frame_rate}s"

        fmt = ET.SubElement(
            resources, "format",
            id="r1",
            name=f"FFVideoFormat{project.height}p{frame_rate}",
            frameDuration=frame_dur_str,
            width=str(project.width),
            height=str(project.height)
        )

        library = ET.SubElement(fcpxml, "library")
        event = ET.SubElement(library, "event", name="JARVIS Studio Event")
        project_elem = ET.SubElement(event, "project", name=project.name)

        total_dur_str = f"{int(project.duration * frame_rate)}/{frame_rate}s"
        sequence = ET.SubElement(project_elem, "sequence", format="r1", duration=total_dur_str)
        spine = ET.SubElement(sequence, "spine")

        # Process main video track clips in order
        main_clips = sorted([c for c in project.clips if c.source_type == "video"], key=lambda x: x.start_time)

        for idx, c in enumerate(main_clips, 1):
            dur_str = f"{int(c.duration * frame_rate)}/{frame_rate}s"
            offset_str = f"{int(c.start_time * frame_rate)}/{frame_rate}s"
            start_str = f"{int(c.in_point * frame_rate)}/{frame_rate}s"

            asset_id = f"r_asset_{idx}"
            file_url = f"file:///{Path(c.source_file or '').resolve().as_posix()}" if c.source_file else ""
            ET.SubElement(
                resources, "asset",
                id=asset_id,
                name=c.name,
                src=file_url,
                format="r1",
                duration=dur_str
            )

            clip_elem = ET.SubElement(
                spine, "asset-clip",
                ref=asset_id,
                name=c.name,
                offset=offset_str,
                duration=dur_str,
                start=start_str
            )

            # Add markers for subtitles or cuts
            if c.text_props and c.text_props.text:
                ET.SubElement(
                    clip_elem, "marker",
                    start=start_str,
                    duration="1/30s",
                    value=c.text_props.text
                )

        tree = ET.ElementTree(fcpxml)
        ET.indent(tree, space="  ", level=0)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        return output_path

    @staticmethod
    def _recalc_duration(project: StudioProject):
        """Update total duration based on latest clip end time."""
        if not project.clips:
            project.duration = 30.0
            return
        max_end = max((c.start_time + c.duration for c in project.clips), default=30.0)
        project.duration = max(10.0, round(max_end + 2.0, 1))


timeline_engine = TimelineEngine()
