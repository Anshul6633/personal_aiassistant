import React, { useState, useEffect } from 'react';
import {
  Monitor,
  MousePointer,
  Keyboard,
  Lock,
  Layers,
  RefreshCw,
  AppWindow,
  Terminal,
  Play,
  CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';

export const DesktopControl: React.FC = () => {
  const [screenPreview, setScreenPreview] = useState<string | null>(null);
  const [activeWindow, setActiveWindow] = useState<string>('Detecting...');
  const [typeText, setTypeText] = useState<string>('');
  const [actionStatus, setActionStatus] = useState<string>('Ready');
  const [isLoadingScreen, setIsLoadingScreen] = useState(false);

  const fetchScreenshot = async () => {
    setIsLoadingScreen(true);
    try {
      const data = await api.getScreenPreview();
      if (data.preview_base64) {
        setScreenPreview(data.preview_base64);
      }
    } catch (err) {
      console.error('Failed to capture screen:', err);
    } finally {
      setIsLoadingScreen(false);
    }
  };

  useEffect(() => {
    fetchScreenshot();
  }, []);

  const handleLaunchApp = async (appName: string) => {
    setActionStatus(`Launching ${appName}...`);
    try {
      await api.executeTool('launch_application', { app_name: appName });
      setActionStatus(`Application ${appName} launched.`);
      setTimeout(fetchScreenshot, 1500);
    } catch (err) {
      setActionStatus(`Error launching ${appName}`);
    }
  };

  const handleType = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!typeText.trim()) return;
    setActionStatus(`Typing: "${typeText}"`);
    try {
      await api.executeTool('type_text', { text: typeText });
      setTypeText('');
      setActionStatus('Text typed into active window.');
      setTimeout(fetchScreenshot, 1000);
    } catch (err) {
      setActionStatus('Error typing text');
    }
  };

  const handleMinimizeAll = async () => {
    setActionStatus('Minimizing all windows (Win+D)...');
    await api.executeTool('minimize_all', {});
    setTimeout(fetchScreenshot, 800);
  };

  const handleLockPC = async () => {
    setActionStatus('Locking Windows workstation...');
    await api.executeTool('lock_pc', {});
  };

  return (
    <div className="space-y-6 pb-12 max-w-6xl mx-auto">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Monitor className="w-5 h-5 text-cyan-400" />
            Desktop Observation & Computer-Use Agent
          </h1>
          <p className="text-xs font-mono text-cyan-400/80">Permission-Guarded Screen Inspection & GUI Automation</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">STATUS:</span>
          <span className="px-2.5 py-1 rounded bg-slate-900 border border-cyan-500/30 text-cyan-300">
            {actionStatus}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Live Screen Observation */}
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-2xl bg-slate-950/80 border border-cyan-500/25 p-4 shadow-cyan-glow">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-cyan-500/15 text-xs font-mono">
              <span className="text-slate-300 flex items-center gap-2">
                <Monitor className="w-4 h-4 text-cyan-400" />
                PRIMARY DISPLAY (1920x1200 / 1080p)
              </span>
              <button
                onClick={fetchScreenshot}
                disabled={isLoadingScreen}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-cyan-500/30 text-cyan-300 cursor-pointer transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingScreen ? 'animate-spin' : ''}`} />
                <span>Refresh View</span>
              </button>
            </div>

            <div className="relative aspect-video rounded-xl overflow-hidden bg-slate-900 flex items-center justify-center border border-slate-800">
              {screenPreview ? (
                <img
                  src={screenPreview}
                  alt="Desktop Screen Capture"
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="text-slate-500 font-mono text-xs flex flex-col items-center gap-2">
                  <Monitor className="w-8 h-8 text-cyan-500/40" />
                  <span>Capturing screen stream...</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Col: Controlled Desktop Actions */}
        <div className="space-y-4">
          {/* Quick App Launcher */}
          <div className="p-4 rounded-xl bg-slate-900/70 border border-cyan-500/20 backdrop-blur-md">
            <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-2">
              <AppWindow className="w-4 h-4 text-cyan-400" />
              Quick Application Launcher
            </h2>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              {[
                { name: 'Google Chrome', id: 'chrome' },
                { name: 'VS Code', id: 'code' },
                { name: 'Notepad', id: 'notepad' },
                { name: 'File Explorer', id: 'explorer' },
                { name: 'Calculator', id: 'calculator' },
                { name: 'Task Manager', id: 'taskmanager' }
              ].map((app) => (
                <button
                  key={app.id}
                  onClick={() => handleLaunchApp(app.id)}
                  className="p-2.5 rounded-lg bg-slate-950 border border-cyan-500/20 hover:border-cyan-400 text-slate-300 hover:text-cyan-300 text-left transition-colors flex items-center gap-2 cursor-pointer"
                >
                  <Play className="w-3 h-3 text-cyan-400" />
                  <span className="truncate">{app.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Simulate Keyboard Typing */}
          <div className="p-4 rounded-xl bg-slate-900/70 border border-cyan-500/20 backdrop-blur-md">
            <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Keyboard className="w-4 h-4 text-cyan-400" />
              Type into Active Window
            </h2>
            <form onSubmit={handleType} className="space-y-2">
              <input
                type="text"
                value={typeText}
                onChange={(e) => setTypeText(e.target.value)}
                placeholder="Type text string..."
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
              />
              <button
                type="submit"
                disabled={!typeText.trim()}
                className="w-full py-2 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 text-cyan-300 font-mono text-xs font-bold disabled:opacity-40 transition-colors cursor-pointer"
              >
                Send Keystrokes
              </button>
            </form>
          </div>

          {/* Quick System Controls */}
          <div className="p-4 rounded-xl bg-slate-900/70 border border-cyan-500/20 backdrop-blur-md space-y-2">
            <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Desktop Shortcuts
            </h2>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <button
                onClick={handleMinimizeAll}
                className="p-2 rounded-lg bg-slate-950 border border-slate-700 hover:border-cyan-400 text-slate-300 hover:text-cyan-300 transition-colors cursor-pointer"
              >
                Show Desktop (Win+D)
              </button>
              <button
                onClick={handleLockPC}
                className="p-2 rounded-lg bg-slate-950 border border-red-500/30 hover:border-red-400 text-red-300 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Lock className="w-3.5 h-3.5" />
                Lock PC
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

