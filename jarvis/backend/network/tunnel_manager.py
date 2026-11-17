"""Live Public Tunnel Manager for JARVIS Production Deployment.

Provides 1-click live public HTTPS access via localtunnel / Cloudflare tunnel
allowing the user to access and control JARVIS from anywhere in the world on mobile
(cellular 4G/5G or remote Wi-Fi) with zero manual port-forwarding or router configuration.
"""

import os
import re
import socket
import logging
import threading
import subprocess
from typing import Optional, Dict, Any

logger = logging.getLogger("JARVIS.TunnelManager")


class TunnelManager:
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._public_url: Optional[str] = None
        self._status: str = "STOPPED"  # STOPPED, CONNECTING, ACTIVE, ERROR
        self._lock = threading.Lock()
        self._port: int = 8000
        self._monitor_thread: Optional[threading.Thread] = None

    def get_local_ip(self) -> str:
        """Detect current LAN IP address for local Wi-Fi connectivity."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except Exception:
                return "127.0.0.1"

    def get_status(self) -> Dict[str, Any]:
        """Return live status of network interfaces and tunnels."""
        with self._lock:
            local_ip = self.get_local_ip()
            return {
                "status": self._status,
                "public_url": self._public_url,
                "local_ip": local_ip,
                "port": self._port,
                "local_url": f"http://localhost:{self._port}",
                "lan_url": f"http://{local_ip}:{self._port}",
                "is_active": self._status == "ACTIVE" and self._public_url is not None
            }

    def start_tunnel(self, port: int = 8000) -> Dict[str, Any]:
        """Launch background localtunnel process to generate live HTTPS endpoint."""
        with self._lock:
            if self._process and self._process.poll() is None and self._public_url:
                logger.info(f"Tunnel already active: {self._public_url}")
                return self.get_status()

            self._port = port
            self._status = "CONNECTING"
            self._public_url = None

            def _run():
                cmd = ["npx.cmd" if os.name == "nt" else "npx", "--yes", "localtunnel", "--port", str(port)]
                try:
                    logger.info(f"Starting tunnel process: {' '.join(cmd)}")
                    self._process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )

                    for line in iter(self._process.stdout.readline, ""):
                        if not line:
                            break
                        line_str = line.strip()
                        logger.info(f"[Tunnel] {line_str}")
                        # Match 'your url is: https://...'
                        m = re.search(r"your url is:\s*(https?://[^\s]+)", line_str, re.IGNORECASE)
                        if m:
                            with self._lock:
                                self._public_url = m.group(1).strip()
                                self._status = "ACTIVE"
                            logger.info(f"🚀 JARVIS Live Public Tunnel established: {self._public_url}")

                    ret = self._process.wait()
                    with self._lock:
                        self._status = "STOPPED"
                        self._public_url = None
                    logger.info(f"Tunnel process terminated with code {ret}")
                except Exception as e:
                    logger.error(f"Tunnel execution failed: {e}")
                    with self._lock:
                        self._status = "ERROR"
                        self._public_url = None

            self._monitor_thread = threading.Thread(target=_run, daemon=True)
            self._monitor_thread.start()

        return self.get_status()

    def stop_tunnel(self) -> Dict[str, Any]:
        """Terminate the active tunnel process."""
        with self._lock:
            if self._process and self._process.poll() is None:
                try:
                    self._process.terminate()
                except Exception as e:
                    logger.warning(f"Error terminating tunnel: {e}")
            self._process = None
            self._public_url = None
            self._status = "STOPPED"
            logger.info("Tunnel stopped.")
        return self.get_status()


tunnel_manager = TunnelManager()

