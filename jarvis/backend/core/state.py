"""Reactive System State and Real-time Broadcast Engine for JARVIS."""

import os
import asyncio
import json
import logging
import psutil
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger("JARVIS.State")


class AssistantState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    EDITING = "EDITING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"


class SystemMetrics(BaseModel):
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    disk_free_gb: float = 0.0
    battery_percent: Optional[float] = None
    is_plugged: Optional[bool] = None
    gpu_name: str = "NVIDIA GeForce RTX 4050"
    vram_used_mb: float = 0.0
    vram_total_mb: float = 6141.0


class JarvisState(BaseModel):
    status: AssistantState = AssistantState.IDLE
    status_message: str = "Systems online and standing by."
    current_thought: str = ""
    active_task_id: Optional[str] = None
    active_task_title: Optional[str] = None
    task_progress: int = 0
    current_speech: str = ""
    mic_active: bool = False
    mic_level: float = 0.0
    autonomy_mode: str = "SUPERVISED"
    active_model: str = "qwen2.5:1.5b"
    metrics: SystemMetrics = Field(default_factory=SystemMetrics)
    last_update: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StateManager:
    _instance = None

    def __init__(self):
        self.state = JarvisState()
        self.listeners: List[Any] = []
        self._lock = asyncio.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._monitoring_task: Optional[asyncio.Task] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = StateManager()
        return cls._instance

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._lock = asyncio.Lock()

    def update_metrics(self):
        """Poll Windows system metrics using psutil."""
        try:
            mem = psutil.virtual_memory()
            disk_path = "C:\\" if os.name == "nt" else "/"
            disk = psutil.disk_usage(disk_path)
            battery = psutil.sensors_battery()

            self.state.metrics.cpu_percent = psutil.cpu_percent(interval=None)
            self.state.metrics.ram_percent = mem.percent
            self.state.metrics.ram_used_gb = round(mem.used / (1024**3), 2)
            self.state.metrics.ram_total_gb = round(mem.total / (1024**3), 2)
            self.state.metrics.disk_free_gb = round(disk.free / (1024**3), 2)

            if battery:
                self.state.metrics.battery_percent = battery.percent
                self.state.metrics.is_plugged = battery.power_plugged
        except Exception as e:
            logger.warning(f"Error reading system metrics: {e}")

    async def set_status(self, status: AssistantState, message: Optional[str] = None):
        self.state.status = status
        if message:
            self.state.status_message = message
        self.state.last_update = datetime.utcnow().isoformat()
        await self.broadcast()

    async def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self.state, k):
                setattr(self.state, k, v)
        self.state.last_update = datetime.utcnow().isoformat()
        await self.broadcast()

    def register_client(self, websocket):
        if websocket not in self.listeners:
            self.listeners.append(websocket)

    def unregister_client(self, websocket):
        if websocket in self.listeners:
            self.listeners.remove(websocket)

    async def broadcast(self, custom_payload: Optional[Dict[str, Any]] = None):
        if not self.listeners:
            return
        if custom_payload is not None:
            payload = json.dumps(custom_payload)
        else:
            payload = json.dumps({"type": "STATE_UPDATE", "data": self.state.model_dump()})

        disconnected = []
        for ws in self.listeners:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)
        for dead in disconnected:
            if dead in self.listeners:
                self.listeners.remove(dead)

    def dispatch_from_thread(self, coro):
        """Thread-safe dispatch for coroutines called from background worker threads."""
        if self._loop and self._loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, self._loop)
        return None

    async def start_metrics_loop(self):
        while True:
            self.update_metrics()
            await self.broadcast()
            await asyncio.sleep(2.0)


state_manager = StateManager.get_instance()

