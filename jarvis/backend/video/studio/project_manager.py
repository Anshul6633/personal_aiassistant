"""Project Management Engine for JARVIS Video Studio."""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from jarvis.backend.config.settings import OUTPUT_DIR
from jarvis.backend.database.db import get_db_connection
from jarvis.backend.video.studio.models import StudioProject, StudioTrack, StudioClip

logger = logging.getLogger("JARVIS.Studio.ProjectManager")

PROJECTS_DIR = OUTPUT_DIR / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


class ProjectManager:
    """Manages project persistence, serialization, auto-save, and asset references."""

    @staticmethod
    def create_default_tracks() -> List[StudioTrack]:
        """Generate standard 5-track editing structure."""
        return [
            StudioTrack(id="T1", name="Text & Titles", type="text", order=0),
            StudioTrack(id="V2", name="Video Overlay / B-Roll", type="video", order=1),
            StudioTrack(id="V1", name="Main Video", type="video", order=2),
            StudioTrack(id="A1", name="Primary Audio / Dialogue", type="audio", order=3),
            StudioTrack(id="A2", name="Music & Sound FX", type="audio", order=4),
        ]

    def create_new_project(
        self,
        name: str = "New Cinematic Timeline",
        aspect_ratio: str = "16:9",
        fps: int = 30
    ) -> StudioProject:
        """Create a fresh Studio Project with configured tracks."""
        width = 1920
        height = 1080
        if aspect_ratio == "9:16":
            width = 1080
            height = 1920
        elif aspect_ratio == "1:1":
            width = 1080
            height = 1080
        elif aspect_ratio == "4:5":
            width = 1080
            height = 1350

        proj = StudioProject(
            id=str(uuid.uuid4())[:8],
            name=name,
            aspect_ratio=aspect_ratio,
            width=width,
            height=height,
            fps=fps,
            duration=30.0,
            tracks=self.create_default_tracks(),
            clips=[]
        )
        self.save_project(proj)
        logger.info(f"Created new project '{proj.name}' ({proj.id}) [{proj.aspect_ratio}]")
        return proj

    def save_project(self, project: StudioProject) -> StudioProject:
        """Save project to SQLite database and local JSON file."""
        project.updated_at = time.time()
        proj_dict = project.model_dump()
        json_str = json.dumps(proj_dict, indent=2)

        # 1. Save JSON to disk
        json_path = PROJECTS_DIR / f"{project.id}.jrvp"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_str)

        # 2. Save/Update in SQLite database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO studio_projects (id, name, aspect_ratio, width, height, fps, duration, timeline_json, thumbnail_url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                aspect_ratio = excluded.aspect_ratio,
                width = excluded.width,
                height = excluded.height,
                fps = excluded.fps,
                duration = excluded.duration,
                timeline_json = excluded.timeline_json,
                thumbnail_url = excluded.thumbnail_url,
                updated_at = CURRENT_TIMESTAMP
        """, (
            project.id,
            project.name,
            project.aspect_ratio,
            project.width,
            project.height,
            project.fps,
            project.duration,
            json_str,
            project.thumbnail_url
        ))
        conn.commit()
        conn.close()
        return project

    def load_project(self, project_id: str) -> Optional[StudioProject]:
        """Load a project by ID from SQLite or JSON fallback."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT timeline_json FROM studio_projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()

        if row and row["timeline_json"]:
            try:
                data = json.loads(row["timeline_json"])
                return StudioProject(**data)
            except Exception as e:
                logger.error(f"Error parsing SQLite project {project_id}: {e}")

        # Fallback to local JSON file
        json_path = PROJECTS_DIR / f"{project_id}.jrvp"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return StudioProject(**data)
            except Exception as e:
                logger.error(f"Error reading JSON project {project_id}: {e}")

        return None

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all recent projects with summary metadata."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, aspect_ratio, width, height, fps, duration, thumbnail_url, updated_at
            FROM studio_projects
            ORDER BY updated_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for r in rows:
            results.append(dict(r))

        # If empty, create initial demo project
        if not results:
            demo = self.create_new_project(name="My First Studio Edit", aspect_ratio="16:9")
            results.append({
                "id": demo.id,
                "name": demo.name,
                "aspect_ratio": demo.aspect_ratio,
                "width": demo.width,
                "height": demo.height,
                "fps": demo.fps,
                "duration": demo.duration,
                "thumbnail_url": demo.thumbnail_url,
                "updated_at": str(demo.updated_at)
            })

        return results

    def duplicate_project(self, project_id: str) -> Optional[StudioProject]:
        """Clone an existing project under a new ID and title."""
        original = self.load_project(project_id)
        if not original:
            return None

        new_proj = original.model_copy(deep=True)
        new_proj.id = str(uuid.uuid4())[:8]
        new_proj.name = f"{original.name} (Copy)"
        new_proj.created_at = time.time()
        new_proj.updated_at = time.time()

        # Generate fresh clip IDs to maintain uniqueness
        for clip in new_proj.clips:
            clip.id = str(uuid.uuid4())[:8]

        self.save_project(new_proj)
        return new_proj

    def delete_project(self, project_id: str) -> bool:
        """Remove a project from database and filesystem."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM studio_projects WHERE id = ?", (project_id,))
        conn.commit()
        conn.close()

        json_path = PROJECTS_DIR / f"{project_id}.jrvp"
        if json_path.exists():
            try:
                json_path.unlink()
            except Exception:
                pass
        return True


project_manager = ProjectManager()

