import React, { useState } from 'react';
import {
  Settings,
  Shield,
  Sliders,
  Volume2,
  Cpu,
  Terminal,
  CheckCircle2,
  Zap,
  Info
} from 'lucide-react';
import { JarvisState } from '../services/api';

interface SettingsPageProps {
  state: JarvisState | null;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ state }) => {
  const [autonomyMode, setAutonomyMode] = useState(state?.autonomy_mode || 'SUPERVISED');
  const [selectedModel, setSelectedModel] = useState(state?.active_model || 'qwen2.5:1.5b');
  const [voice, setVoice] = useState('en-US-ChristopherNeural');
  const [dailyTarget, setDailyTarget] = useState(30);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
          <Settings className="w-5 h-5 text-cyan-400" />
          JARVIS Core Architecture & Personality Settings
        </h1>
        <p className="text-xs font-mono text-cyan-400/80">Configure Autonomy, Speech Synthesis, and Local AI Runtimes</p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Autonomy Level */}
        <div className="p-6 rounded-2xl bg-slate-950/80 border border-cyan-500/25 space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-100 uppercase tracking-wider">
            <Shield className="w-4 h-4 text-cyan-400" />
            Autonomous Permission Gates
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              {
                id: 'MANUAL',
                title: 'Manual Mode',
                desc: 'JARVIS asks for explicit confirmation before every computer automation and clip render.'
              },
              {
                id: 'SUPERVISED',
                title: 'Supervised Mode (Recommended)',
                desc: 'Automatically research, clip, transcribe, and edit. Always ask before publishing or deleting.'
              },
              {
                id: 'PREAPPROVED_AUTONOMOUS',
                title: 'Preapproved Autonomous',
                desc: 'Executes entire end-to-end 30-clip daily production and publishing queues within safety bounds.'
              }
            ].map((m) => (
              <div
                key={m.id}
                onClick={() => setAutonomyMode(m.id as any)}
                className={`cursor-pointer p-4 rounded-xl border transition-all ${
                  autonomyMode === m.id
                    ? 'bg-cyan-500/15 border-cyan-400 shadow-cyan-sm'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between text-xs font-bold font-mono">
                  <span className={autonomyMode === m.id ? 'text-cyan-300' : 'text-slate-300'}>
                    {m.title}
                  </span>
                  {autonomyMode === m.id && <CheckCircle2 className="w-4 h-4 text-cyan-400" />}
                </div>
                <p className="mt-2 text-[11px] text-slate-400 leading-normal">{m.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Local AI Model Selection */}
        <div className="p-6 rounded-2xl bg-slate-950/80 border border-cyan-500/25 space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-100 uppercase tracking-wider">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Local AI Intelligence Engine (Ollama)
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                PRIMARY LLM MODEL
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
              >
                <option value="qwen2.5:1.5b">Qwen 2.5 1.5B (Active • Ultra Fast • Low VRAM)</option>
                <option value="qwen2.5:3b">Qwen 2.5 3B (High Reasoning • 1.9GB)</option>
                <option value="qwen2.5:7b">Qwen 2.5 7B (Maximum Intelligence • 4.7GB)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                DAILY CLIPS TARGET
              </label>
              <input
                type="number"
                min={1}
                max={50}
                value={dailyTarget}
                onChange={(e) => setDailyTarget(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>
        </div>

        {/* Speech Synthesis & Audio Engine */}
        <div className="p-6 rounded-2xl bg-slate-950/80 border border-cyan-500/25 space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-100 uppercase tracking-wider">
            <Volume2 className="w-4 h-4 text-cyan-400" />
            Voice Synthesis & Accent
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                NEURAL VOICE PROFILE
              </label>
              <select
                value={voice}
                onChange={(e) => setVoice(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
              >
                <option value="en-US-ChristopherNeural">Christopher (Avengers JARVIS English)</option>
                <option value="en-US-GuyNeural">Guy (Natural American Male)</option>
                <option value="hi-IN-MadhurNeural">Madhur (Hindi / Hinglish Male)</option>
                <option value="hi-IN-SwaraNeural">Swara (Hindi Female)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                WAKE WORD ACTIVATION
              </label>
              <div className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-cyan-500/30 text-xs font-mono text-cyan-300">
                Trigger Phrase: "Hey Jarvis" (openWakeWord / Energy VAD)
              </div>
            </div>
          </div>
        </div>

        {/* Save button */}
        <div className="flex items-center justify-between">
          <button
            type="submit"
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase font-mono tracking-wider shadow-cyan-sm cursor-pointer transition-all flex items-center gap-2"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Save Preferences</span>
          </button>

          {saved && (
            <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5 animate-pulse">
              <CheckCircle2 className="w-4 h-4" />
              Settings updated successfully!
            </span>
          )}
        </div>
      </form>
    </div>
  );
};

