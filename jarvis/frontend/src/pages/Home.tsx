import React, { useState } from 'react';
import { ArcReactor } from '../components/ArcReactor';
import { AudioWaveform } from '../components/AudioWaveform';
import { JarvisState, ClipItem, api } from '../services/api';
import { useVoiceInput } from '../services/voice';
import {
  Send,
  Zap,
  HardDrive,
  Cpu,
  Layers,
  Film,
  TrendingUp,
  CheckCircle2,
  Clock,
  Mic,
  MicOff,
  Brain,
  UploadCloud,
  ShieldCheck,
  Flame,
  Sparkles
} from 'lucide-react';

interface HomeProps {
  state: JarvisState | null;
  clips: ClipItem[];
  onNavigate: (section: any) => void;
  onRefreshClips: () => void;
}

export const Home: React.FC<HomeProps> = ({
  state,
  clips,
  onNavigate,
  onRefreshClips
}) => {
  const [command, setCommand] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [portalSummary, setPortalSummary] = useState<any>(null);
  const [brainNotice, setBrainNotice] = useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    const fetchPortalSummary = async () => {
      try {
        const sum = await api.getPortalSummary();
        if (active && sum) {
          setPortalSummary(sum);
        }
      } catch (err) {
        // silent polling catch
      }
    };
    fetchPortalSummary();
    const interval = setInterval(fetchPortalSummary, 3500);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const handleLaunchBrainAutopilot = async (preset: string) => {
    setBrainNotice(`Engaging JARVIS Master Brain for ${preset.toUpperCase()}... Finding viral video, clipping & auto-publishing!`);
    try {
      const res = await api.startViralAutopilot({
        preset,
        platform: 'both',
        privacy: 'public',
        uploadTillLimit: true
      });
      if (res && res.success) {
        setBrainNotice(`🚀 JARVIS Brain Active: Ingesting viral ${preset} content and generating vertical shorts!`);
      } else {
        setBrainNotice(res?.message || 'Autopilot already actively running.');
      }
    } catch (err: any) {
      setBrainNotice(`Failed to trigger: ${err.message}`);
    }
    setTimeout(() => setBrainNotice(null), 5000);
  };

  // Voice Input Integration on Home HUD
  const {
    isListening,
    toggleListening,
    interimTranscript
  } = useVoiceInput({
    onFinalTranscript: (text) => {
      if (text && text.trim()) {
        setCommand(text);
      }
    }
  });

  const handleSubmitDirective = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim() || isExecuting) return;

    setIsExecuting(true);
    try {
      await api.orchestrateDirective(command);
      setCommand('');
      setTimeout(onRefreshClips, 2000);
    } catch (err) {
      console.error(err);
    } finally {
      setIsExecuting(false);
    }
  };

  const cpu = state?.metrics?.cpu_percent ?? 0;
  const ram = state?.metrics?.ram_percent ?? 0;
  const ramUsed = state?.metrics?.ram_used_gb ?? 0;
  const ramTotal = state?.metrics?.ram_total_gb ?? 0;
  const diskFree = state?.metrics?.disk_free_gb ?? 0;
  const gpu = state?.metrics?.gpu_name ?? 'NVIDIA RTX 4050';

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner: Iron Man Arc Reactor & Neural Hub */}
      <div className="relative rounded-2xl bg-gradient-to-b from-slate-900/90 via-slate-950/80 to-slate-950/90 border border-cyan-500/25 p-8 shadow-cyan-glow overflow-hidden">
        {/* Holographic background decorative grid lines */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#00f2fe0a_1px,transparent_1px),linear-gradient(to_bottom,#00f2fe0a_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

        <div className="relative z-10 flex flex-col items-center text-center">
          {/* Arc Reactor Core */}
          <div
            onClick={() => onNavigate('talk')}
            className="mb-6 cursor-pointer hover:scale-105 transition-transform"
            title="Click to Talk to JARVIS"
          >
            <ArcReactor
              status={state?.status || 'IDLE'}
              micLevel={state?.mic_level || 0}
              size={240}
            />
          </div>

          <h1 className="text-3xl font-black tracking-wider text-slate-100 uppercase">
            JUST A RATHER VERY INTELLIGENT SYSTEM
          </h1>
          <p className="mt-2 text-sm text-cyan-300/80 max-w-xl font-mono">
            {state?.status_message || "Online and standing by for your directive, Boss."}
          </p>

          {/* Live Waveform Spectrum */}
          <div className="mt-5 w-full max-w-md">
            <AudioWaveform
              micLevel={state?.mic_level || 0}
              isActive={state?.mic_active || state?.status === 'SPEAKING'}
              barsCount={32}
            />
          </div>

          {/* Master Directive Input Bar */}
          <form
            onSubmit={handleSubmitDirective}
            className="mt-6 w-full max-w-2xl flex items-center gap-2 p-1.5 rounded-xl bg-slate-950/90 border border-cyan-500/40 shadow-cyan-sm focus-within:border-cyan-400 transition-all"
          >
            <div className="pl-3 text-cyan-400">
              <Zap className="w-5 h-5" />
            </div>
            <input
              type="text"
              value={isListening && interimTranscript ? interimTranscript : command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder={isListening ? "Listening to your voice directive..." : "Give JARVIS a mission (e.g. 'Create 5 viral shorts from podcast video')..."}
              className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none font-mono"
            />
            {/* Voice Directive Button */}
            <button
              type="button"
              onClick={toggleListening}
              className={`p-2.5 rounded-lg border transition-all cursor-pointer flex items-center justify-center ${
                isListening
                  ? 'bg-red-500/20 border-red-500 text-red-400 animate-pulse shadow-red-500/40'
                  : 'bg-slate-900 border-cyan-500/30 text-cyan-400 hover:border-cyan-400'
              }`}
              title={isListening ? 'Listening (Click to cancel)' : 'Click to Speak Directive'}
            >
              {isListening ? <Mic className="w-4 h-4 text-red-400" /> : <Mic className="w-4 h-4 text-cyan-400" />}
            </button>
            <button
              type="submit"
              disabled={isExecuting || !command.trim()}
              className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase tracking-wider flex items-center gap-2 cursor-pointer disabled:opacity-50 transition-all"
            >
              <span>{isExecuting ? 'PLANNING...' : 'EXECUTE'}</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Quick Mission Preset Pills */}
          <div className="mt-3 flex flex-wrap items-center justify-center gap-2 max-w-2xl text-[11px] font-mono">
            {[
              { label: '⚡ Produce 3 Viral Shorts', cmd: 'Create 3 viral shorts from sample video' },
              { label: '🎙️ Talk with Jarvis', nav: 'talk' },
              { label: '🖥️ Inspect Screen', nav: 'desktop' },
              { label: '🔥 Research Viral Hooks', nav: 'research' },
              { label: '📁 Browse Source Videos', nav: 'files' }
            ].map((pill, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  if (pill.cmd) {
                    setCommand(pill.cmd);
                  } else if (pill.nav) {
                    onNavigate(pill.nav);
                  }
                }}
                className="px-3 py-1 rounded-full bg-slate-900/90 hover:bg-cyan-500/20 border border-cyan-500/20 hover:border-cyan-400 text-slate-300 hover:text-cyan-300 transition-all cursor-pointer shadow-sm"
              >
                {pill.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Active Autonomous Task Banner (if task active) */}
      {state?.active_task_id && (
        <div className="p-4 rounded-xl bg-slate-900/80 border border-yellow-500/40 flex flex-col gap-2">
          <div className="flex justify-between items-center text-xs font-mono">
            <span className="text-yellow-400 flex items-center gap-2">
              <Clock className="w-4 h-4 animate-spin" />
              ACTIVE TASK: {state.active_task_title || state.active_task_id}
            </span>
            <span className="text-slate-300 font-bold">{state.task_progress}%</span>
          </div>
          <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-yellow-500/20">
            <div
              className="bg-gradient-to-r from-yellow-500 to-amber-400 h-full transition-all duration-300"
              style={{ width: `${state.task_progress}%` }}
            />
          </div>
        </div>
      )}

      {/* 🧠 JARVIS MASTER BRAIN: AUTONOMOUS OPERATIONS & PORTAL TELEMETRY */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-cyan-500/40 shadow-[0_0_30px_rgba(6,182,212,0.15)] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950 shadow-md">
              <Brain className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-black text-slate-100 uppercase tracking-wider font-mono">
                  JARVIS Master Brain: Live Portal Operations
                </h2>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              </div>
              <p className="text-xs font-mono text-cyan-300/80">
                {portalSummary?.brain?.detail || "Autonomous link discovery, 6-factor AI clipping, and public dispatch active."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider border ${
              portalSummary?.brain?.autopilot_running
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse'
                : portalSummary?.uploading?.is_uploading
                ? 'bg-red-500/20 text-red-300 border-red-500/40 animate-pulse'
                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
            }`}>
              {portalSummary?.brain?.activity || 'AUTONOMOUS STANDBY'}
            </span>
          </div>
        </div>

        {/* Live Active Mission Banner (if Autopilot is running) */}
        {portalSummary?.brain?.autopilot_running && (
          <div className="p-3.5 rounded-xl bg-black/60 border border-amber-500/30 space-y-2 font-mono">
            <div className="flex justify-between items-center text-xs">
              <span className="text-amber-400 font-bold flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 animate-spin text-amber-400" />
                ACTIVE AUTONOMOUS PIPELINE: {portalSummary?.brain?.active_step}
              </span>
              <span className="text-slate-200 font-bold">{portalSummary?.brain?.progress_percent}%</span>
            </div>
            <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-amber-500/30">
              <div
                className="h-full bg-gradient-to-r from-amber-500 to-rose-500 transition-all duration-500"
                style={{ width: `${portalSummary?.brain?.progress_percent}%` }}
              />
            </div>
          </div>
        )}

        {/* Next Scheduled Video or Live Uploading Status */}
        {portalSummary?.uploading?.next_item && (
          <div className="p-3.5 rounded-xl bg-black/40 border border-cyan-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-2 font-mono text-xs">
            <div className="flex items-center gap-2 truncate">
              <UploadCloud className="w-4 h-4 text-cyan-400 shrink-0" />
              <span className="text-slate-400">NEXT DUE SHORT:</span>
              <span className="text-slate-200 font-bold truncate">
                {portalSummary.uploading.next_item.title}
              </span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-300 text-[11px]">
                {portalSummary.uploading.seconds_until_next ? `Due in ${Math.floor(portalSummary.uploading.seconds_until_next / 60)}m` : 'Due Now'}
              </span>
              <span className="px-2 py-0.5 rounded bg-red-950 border border-red-500/40 text-red-300 text-[11px] font-bold">
                Public (Auto)
              </span>
            </div>
          </div>
        )}

        {/* Portal Telemetry Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-center font-mono">
            <div className="text-[10px] text-slate-400 uppercase">Library Ready Clips</div>
            <div className="text-lg font-black text-cyan-400">{portalSummary?.library?.ready_clips ?? clips.length}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-center font-mono">
            <div className="text-[10px] text-slate-400 uppercase">Queued for Dispatch</div>
            <div className="text-lg font-black text-yellow-400">{portalSummary?.queue?.queued ?? 0}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-center font-mono">
            <div className="text-[10px] text-slate-400 uppercase">Published Today</div>
            <div className="text-lg font-black text-emerald-400">{portalSummary?.queue?.published_today ?? 0}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-center font-mono">
            <div className="text-[10px] text-slate-400 uppercase">Anti-Ban Pacing</div>
            <div className="text-xs font-bold text-emerald-400 mt-1 flex items-center justify-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>45m Safe Guard</span>
            </div>
          </div>
        </div>

        {/* 1-Click Autonomous Brain Triggers */}
        <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800/80">
          <div className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
            <Flame className="w-4 h-4 text-orange-400" />
            <span>Launch Brain Mission:</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {[
              { label: '⚽ Auto-Clip Football & Publish', preset: 'football' },
              { label: '🤑 Auto-Clip MrBeast & Publish', preset: 'mrbeast' },
              { label: '🎙️ Auto-Clip Podcasts & Publish', preset: 'rogan' },
              { label: '🧠 Auto-Clip Huberman & Publish', preset: 'huberman' }
            ].map((btn, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleLaunchBrainAutopilot(btn.preset)}
                className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-600/30 to-blue-600/30 hover:from-cyan-500 hover:to-blue-600 border border-cyan-500/40 text-cyan-200 hover:text-white font-mono text-xs font-bold transition-all cursor-pointer shadow-sm"
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>

        {brainNotice && (
          <div className="p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-500/50 text-xs font-mono text-cyan-200 animate-fadeIn text-center">
            {brainNotice}
          </div>
        )}
      </div>

      {/* Telemetry Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* CPU Gauge */}
        <div
          onClick={() => onNavigate('desktop')}
          className="p-4 rounded-xl bg-slate-900/60 border border-cyan-500/20 backdrop-blur-md cursor-pointer hover:border-cyan-400 transition-all"
        >
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span>CPU UTILIZATION</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-cyan-300 font-mono">{cpu}%</div>
          <div className="w-full bg-slate-950 h-1.5 rounded-full mt-2 overflow-hidden">
            <div className="bg-cyan-400 h-full" style={{ width: `${cpu}%` }} />
          </div>
        </div>

        {/* RAM Gauge */}
        <div
          onClick={() => onNavigate('settings')}
          className="p-4 rounded-xl bg-slate-900/60 border border-blue-500/20 backdrop-blur-md cursor-pointer hover:border-blue-400 transition-all"
        >
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span>MEMORY CONSUMPTION</span>
            <Layers className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-black text-blue-300 font-mono">{ram}%</div>
          <div className="text-[11px] font-mono text-slate-400 mt-1">
            {ramUsed} GB / {ramTotal} GB
          </div>
        </div>

        {/* GPU Card */}
        <div
          onClick={() => onNavigate('settings')}
          className="p-4 rounded-xl bg-slate-900/60 border border-emerald-500/20 backdrop-blur-md cursor-pointer hover:border-emerald-400 transition-all"
        >
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span>DEDICATED GPU</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-sm font-bold text-emerald-300 truncate font-mono">{gpu}</div>
          <div className="text-[11px] font-mono text-emerald-400/80 mt-1">CUDA 13.3 Acceleration Active</div>
        </div>

        {/* Disk Space */}
        <div
          onClick={() => onNavigate('files')}
          className="p-4 rounded-xl bg-slate-900/60 border border-purple-500/20 backdrop-blur-md cursor-pointer hover:border-purple-400 transition-all"
        >
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span>DRIVE C: FREE STORAGE</span>
            <HardDrive className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-purple-300 font-mono">{diskFree} GB</div>
          <div className="text-[11px] font-mono text-slate-400 mt-1">Local Model & Video Buffer Ready</div>
        </div>
      </div>

      {/* Recent Autonomous Clips Showcase */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-cyan-500/20">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Film className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-bold text-slate-100 uppercase tracking-wide">
              Recent Autonomous Clips ({clips.length})
            </h2>
          </div>
          <button
            onClick={() => onNavigate('studio')}
            className="text-xs font-mono text-cyan-400 hover:text-cyan-300 cursor-pointer"
          >
            Open Content Studio →
          </button>
        </div>

        {clips.length === 0 ? (
          <div className="text-center py-8 text-slate-500 font-mono text-sm">
            No clips rendered yet. Use the directive bar or Reels Factory to produce your first batch!
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {clips.slice(0, 3).map((clip) => (
              <div
                key={clip.id}
                onClick={() => onNavigate('studio')}
                className="rounded-xl overflow-hidden bg-slate-950 border border-cyan-500/20 hover:border-cyan-400 hover:scale-[1.02] cursor-pointer transition-all flex flex-col shadow-cyan-sm"
              >
                <div className="relative aspect-[9/16] max-h-64 bg-slate-900 overflow-hidden flex items-center justify-center">
                  {clip.thumb_url ? (
                    <img
                      src={clip.thumb_url}
                      alt={clip.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <Film className="w-10 h-10 text-cyan-500/40" />
                  )}
                  <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-slate-950/80 border border-cyan-400/40 text-[10px] font-mono text-cyan-300 font-bold">
                    SCORE {clip.total_score}
                  </div>
                </div>

                <div className="p-3 flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-slate-200 line-clamp-1">{clip.title}</h3>
                    <p className="text-[11px] text-slate-400 line-clamp-2 mt-1">{clip.summary}</p>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-[10px] font-mono text-cyan-400/80">
                    <span>{clip.duration}s • 9:16</span>
                    <span className="text-emerald-400">READY</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

