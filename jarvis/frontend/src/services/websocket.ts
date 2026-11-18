/**
 * Real-time Bidirectional WebSocket Hook for JARVIS
 */

import { useEffect, useRef, useState } from 'react';
import { JarvisState } from './api';

export function useJarvisWebSocket() {
  const [state, setState] = useState<JarvisState | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let wsUrl = '';
    const saved = typeof window !== 'undefined' ? localStorage.getItem('jarvis_backend_url') : null;
    const envWs = (import.meta as any).env?.VITE_WS_URL;
    const envBackend = (import.meta as any).env?.VITE_BACKEND_URL;

    if (envWs) {
      wsUrl = envWs;
    } else if (envBackend) {
      const wsProto = envBackend.startsWith('https') ? 'wss:' : 'ws:';
      const cleanHost = envBackend.replace(/^https?:\/\//, '').replace(/\/+$/, '');
      wsUrl = `${wsProto}//${cleanHost}/ws`;
    } else if (saved) {
      const wsProto = saved.startsWith('https') ? 'wss:' : 'ws:';
      const cleanHost = saved.replace(/^https?:\/\//, '').replace(/\/+$/, '');
      wsUrl = `${wsProto}//${cleanHost}/ws`;
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${window.location.host}/ws`;
    }

    let reconnectTimer: any = null;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'STATE_UPDATE' || msg.type === 'INITIAL_STATE') {
              setState(msg.data);
            }
          } catch (e) {
            console.error('Failed to parse WS message:', e);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          reconnectTimer = setTimeout(connect, 2000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (e) {
        reconnectTimer = setTimeout(connect, 3000);
      }
    };

    connect();

    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const sendAction = (action: string, payload: Record<string, any> = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, ...payload }));
    }
  };

  return { state, isConnected, sendAction };
}

