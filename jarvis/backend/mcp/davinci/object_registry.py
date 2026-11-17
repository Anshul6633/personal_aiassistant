"""
DaVinci Resolve MCP Object Registry for Project JARVIS.
Stores live COM/C++ pointer objects and maps them to stable, JSON-serializable string IDs.
Adapted from lordhoell/davinci-resolve-mcp pattern.
"""

import time
import uuid
import threading
from typing import Any, Dict, List, Optional


class ResolveObjectRegistry:
    """Thread-safe in-memory registry mapping string IDs to live Resolve objects."""

    def __init__(self):
        self._lock = threading.Lock()
        self._registry: Dict[str, Any] = {}
        self._type_map: Dict[str, str] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._created_at: Dict[str, float] = {}

    def register(self, obj: Any, obj_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Register a live Resolve object and return a JSON-safe ID."""
        if obj is None:
            raise ValueError("Cannot register None object")
        
        with self._lock:
            # Check if this exact object is already registered
            for existing_id, existing_obj in self._registry.items():
                if existing_obj is obj:
                    if metadata:
                        self._metadata[existing_id].update(metadata)
                    return existing_id

            clean_type = obj_type.lower().replace(" ", "_")
            short_id = uuid.uuid4().hex[:8]
            obj_id = f"{clean_type}_{short_id}"

            self._registry[obj_id] = obj
            self._type_map[obj_id] = obj_type
            self._metadata[obj_id] = metadata or {}
            self._created_at[obj_id] = time.time()
            return obj_id

    def get(self, obj_id: str) -> Optional[Any]:
        """Retrieve a live object by ID."""
        with self._lock:
            return self._registry.get(obj_id)

    def get_type(self, obj_id: str) -> Optional[str]:
        """Get the registered type name of an object."""
        with self._lock:
            return self._type_map.get(obj_id)

    def get_metadata(self, obj_id: str) -> Dict[str, Any]:
        """Get metadata associated with an object."""
        with self._lock:
            return dict(self._metadata.get(obj_id, {}))

    def unregister(self, obj_id: str) -> bool:
        """Remove an object from the registry."""
        with self._lock:
            if obj_id in self._registry:
                del self._registry[obj_id]
                self._type_map.pop(obj_id, None)
                self._metadata.pop(obj_id, None)
                self._created_at.pop(obj_id, None)
                return True
            return False

    def clear(self) -> int:
        """Clear all registered objects (used on project switch or reconnect)."""
        with self._lock:
            count = len(self._registry)
            self._registry.clear()
            self._type_map.clear()
            self._metadata.clear()
            self._created_at.clear()
            return count

    def list_objects(self) -> List[Dict[str, Any]]:
        """Return a serializable list of all registered objects."""
        with self._lock:
            result = []
            for obj_id in self._registry.keys():
                result.append({
                    "id": obj_id,
                    "type": self._type_map.get(obj_id, "Unknown"),
                    "metadata": self._metadata.get(obj_id, {}),
                    "age_seconds": round(time.time() - self._created_at.get(obj_id, time.time()), 2)
                })
            return result

    def __len__(self) -> int:
        with self._lock:
            return len(self._registry)


# Global singleton registry
registry = ResolveObjectRegistry()

