"""Multi-Disk Storage Router & Secondary Drive Overflow Engine.

Monitors disk usage across local drives (C:, D:, etc.).
When Primary Drive (C:) free space drops below a threshold (default 10 GB),
it automatically switches active output and media storage to the secondary drive (e.g. D:\\jarvis_media\\output),
preventing disk exhaustion during heavy 24/7 video processing and livestream recording.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("JARVIS.StorageRouter")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PRIMARY_OUTPUT_ROOT = WORKSPACE_ROOT / "jarvis" / "output"
DEFAULT_SECONDARY_DRIVE = "D:"
SECONDARY_MEDIA_DIR = Path("D:/jarvis_media/output")
PRIMARY_THRESHOLD_GB = 10.0  # Trigger overflow when primary has less than 10 GB free


class StorageRouter:
    def __init__(self, primary_threshold_gb: float = PRIMARY_THRESHOLD_GB):
        self.primary_threshold_gb = primary_threshold_gb
        self.primary_root = PRIMARY_OUTPUT_ROOT
        self.secondary_root = SECONDARY_MEDIA_DIR
        self._ensure_directories(self.primary_root)

    def _ensure_directories(self, root: Path):
        """Ensure standard subdirectories exist in target storage root."""
        subdirs = ["reels", "shorts", "videos", "compilations", "thumbnails", "subtitles", "audio", "livestreams", "temp_audio", "queue_downloads"]
        for sub in subdirs:
            try:
                (root / sub).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.debug(f"Could not create folder {root / sub}: {e}")

    @staticmethod
    def get_drive_usage(drive_path: str) -> Dict[str, Any]:
        """Return disk usage metrics for a specific drive root (e.g. 'C:\\' or 'D:\\')."""
        try:
            total, used, free = shutil.disk_usage(drive_path)
            total_gb = round(total / (1024 ** 3), 2)
            used_gb = round(used / (1024 ** 3), 2)
            free_gb = round(free / (1024 ** 3), 2)
            pct_used = round((used / total) * 100, 1) if total > 0 else 0
            return {
                "drive": drive_path,
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "percent_used": pct_used,
                "accessible": True
            }
        except Exception as e:
            return {
                "drive": drive_path,
                "total_gb": 0,
                "used_gb": 0,
                "free_gb": 0,
                "percent_used": 0,
                "accessible": False,
                "error": str(e)
            }

    def get_all_drives_status(self) -> Dict[str, Any]:
        """Scan all standard Windows drives and report storage status."""
        drives = []
        for letter in ["C", "D", "E", "F"]:
            root = f"{letter}:\\"
            if Path(root).exists():
                stat = self.get_drive_usage(root)
                if stat["accessible"]:
                    drives.append(stat)

        c_stat = self.get_drive_usage("C:\\")
        is_overflow = c_stat["free_gb"] < self.primary_threshold_gb
        active_root = self.secondary_root if (is_overflow and self.is_secondary_available()) else self.primary_root

        return {
            "drives": drives,
            "primary_free_gb": c_stat["free_gb"],
            "threshold_gb": self.primary_threshold_gb,
            "overflow_active": is_overflow,
            "active_output_root": str(active_root),
            "secondary_available": self.is_secondary_available()
        }

    def is_secondary_available(self) -> bool:
        """Check if secondary D: drive exists and is writable."""
        try:
            d_root = Path(f"{DEFAULT_SECONDARY_DRIVE}\\")
            if not d_root.exists():
                return False
            d_stat = self.get_drive_usage(f"{DEFAULT_SECONDARY_DRIVE}\\")
            return d_stat["free_gb"] > 5.0
        except Exception:
            return False

    def get_active_output_root(self) -> Path:
        """Resolve current active output directory based on primary drive free space.
        
        If Drive C: has less than threshold GB free (e.g. 10 GB), routes all new
        files to the high-capacity secondary storage drive (D:\\jarvis_media\\output).
        """
        c_stat = self.get_drive_usage("C:\\")
        if c_stat["free_gb"] < self.primary_threshold_gb and self.is_secondary_available():
            self._ensure_directories(self.secondary_root)
            return self.secondary_root
        return self.primary_root

    def get_output_dir(self, subfolder: str = "") -> Path:
        """Get the active directory for a specific subfolder (e.g. 'reels', 'shorts', 'compilations')."""
        root = self.get_active_output_root()
        target = root / subfolder if subfolder else root
        target.mkdir(parents=True, exist_ok=True)
        return target

    def resolve_output_path(self, subfolder: str, filename: str) -> Path:
        """Generate a complete destination path on the best available storage drive."""
        out_dir = self.get_output_dir(subfolder)
        return out_dir / filename

    def migrate_idle_media_to_secondary(self, dry_run: bool = False) -> Dict[str, Any]:
        """Safely migrate non-queued heavy files (old livestreams, temp files, large outputs)
        from Drive C: to Drive D: to immediately liberate gigabytes on Drive C:.
        """
        if not self.is_secondary_available():
            return {"success": False, "error": "Secondary drive (D:) is not available."}

        self._ensure_directories(self.secondary_root)
        moved_files = []
        freed_bytes = 0

        # Subfolders eligible for migration
        candidate_folders = ["livestreams", "temp_audio", "queue_downloads", "compilations"]

        for folder_name in candidate_folders:
            src_dir = self.primary_root / folder_name
            dst_dir = self.secondary_root / folder_name

            if not src_dir.exists():
                continue

            for f in src_dir.glob("*.*"):
                try:
                    if f.is_file():
                        size = f.stat().st_size
                        dest_file = dst_dir / f.name
                        if not dry_run:
                            shutil.move(str(f), str(dest_file))
                        freed_bytes += size
                        moved_files.append({"file": f.name, "size_mb": round(size / (1024 * 1024), 2), "folder": folder_name})
                except Exception as e:
                    logger.warning(f"Could not migrate {f.name}: {e}")

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        freed_gb = round(freed_bytes / (1024 * 1024 * 1024), 2)
        logger.info(f"💾 Storage Migration Complete: Moved {len(moved_files)} files ({freed_gb} GB freed on Drive C:)")

        return {
            "success": True,
            "dry_run": dry_run,
            "moved_count": len(moved_files),
            "freed_mb": freed_mb,
            "freed_gb": freed_gb,
            "moved_files": moved_files[:25]
        }


storage_router = StorageRouter()
