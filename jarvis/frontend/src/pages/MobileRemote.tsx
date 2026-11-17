import React, { useState, useEffect, useRef } from 'react';
import {
  Smartphone,
  Mic,
  MicOff,
  Send,
  Volume2,
  VolumeX,
  Volume1,
  Lock,
  Layers,
  Camera,
  PlaySquare,
  Sparkles,
  Zap,
  Radio,
  Cpu,
  Database,
  Battery,
  BatteryCharging,
  ShieldAlert,
  CheckCircle2,
  Copy,
  Check,
  RefreshCw,
  TrendingUp,
  Flame,
  Film
} from 'lucide-react';
import { api, JarvisState } from '../services/api';

interface MobileRemoteProps {
  state: JarvisState | null;
  onNavigate: (section: any) => void;
}

export const MobileRemote: React.FC<MobileRemoteProps> = ({ state, onNavigate }) => {
  const [inputText, setInputText] = useState('');
  const [chatLog, setChatLog] = useState<Array<{ role: 'user' | 'assistant'; text: string }>>([
    { role: 'assistant', text: "Hello Boss! Mobile Command Hub is active. What directive shall we run?" }
  ]);
  const [isSending, setIsSending] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [mobileInfo, setMobileInfo] = useState<{ mobile_url?: string; lan_ip?: string }>({});
  const [copied, setCopied] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<any>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    api.getMobileInfo().then(info => {
      setMobileInfo(info);
    }).catch(err => console.warn('Could not load mobile info:', err));
  }, []);

  // Web Speech API for mobile voice recognition
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setInputText(transcript);
          handleSend(transcript);
        }
      };

      recognition.onerror = () => setIsRecording(false);
      recognition.onend = () => setIsRecording(false);
      recognitionRef.current = recognition;
    }
  }, []);

  const toggleVoice = () => {
    if (!recognitionRef.current) {
      flashNotice("Speech recognition not supported in this browser. Please type below.");
      return;
    }
    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (e) {
        setIsRecording(false);
      }
    }
  };

  const flashNotice = (msg: string) => {
    setActionNotice(msg);
    setTimeout(() => setActionNotice(null), 3000);
  };

  const handleSend = async (customPrompt?: string) => {
    const prompt = customPrompt || inputText;
    if (!prompt.trim() || isSending) return;

    setChatLog(prev => [...prev, { role: 'user', text: prompt }]);
    if (!customPrompt) setInputText('');
    setIsSending(true);

    try {
      const res = await api.sendChat(prompt);
      setChatLog(prev => [...prev, { role: 'assistant', text: res.reply }]);
      if (res.audio_url && audioPlayerRef.current) {
        audioPlayerRef.current.src = res.audio_url;
        audioPlayerRef.current.play().catch(e => console.log('Mobile audio autoplay prevented:', e));
      }
    } catch (e: any) {
      setChatLog(prev => [...prev, { role: 'assistant', text: `Error: ${e.message}` }]);
    } finally {
      setIsSending(false);
    }
  };

  const handleTool = async (toolName: string, params: any, successLabel: string) => {
    flashNotice(`Executing: ${successLabel}...`);
    try {
      const res = await api.executeTool(toolName, params);
      if (res.success) {
        flashNotice(`✔ ${successLabel}`);
      } else {
        flashNotice(`Error: ${res.error || 'Failed'}`);
      }
    } catch (e: any) {
      flashNotice(`Error: ${e.message}`);
    }
  };

  const handleCopyLink = () => {
    const url = mobileInfo.mobile_url || window.location.href;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const cpu = state?.metrics?.cpu_percent ?? 0;
  const ram = state?.metrics?.ram_percent ?? 0;
  const bat = state?.metrics?.battery_percent;
  const isPlugged = state?.metrics?.is_plugged;

  return (
    <div className="max-w-2xl mx-auto space-y-5 pb-12">
      <audio ref={audioPlayerRef} className="hidden" />

      {/* Top Mobile Status Header Card */}
      <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-cyan-500/30 shadow-xl">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
              <Smartphone className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-bold text-white tracking-wide flex items-center gap-2">
                MOBILE COMMAND HUB
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  ONLINE
                </span>
              </h2>
              <p className="text-[11px] font-mono text-cyan-400/80">Control JARVIS from your phone</p>
            </div>
          </div>

          <button
            onClick={() => api.getState()}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Live Hardware Telemetry Pills */}
        <div className="grid grid-cols-3 gap-2 text-xs font-mono">
          <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5"><Cpu className="w-3.5 h-3.5 text-cyan-400" /> CPU</span>
            <span className="font-bold text-cyan-300">{cpu}%</span>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5"><Database className="w-3.5 h-3.5 text-blue-400" /> RAM</span>
            <span className="font-bold text-blue-300">{ram}%</span>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5">
              {isPlugged ? <BatteryCharging className="w-3.5 h-3.5 text-emerald-400" /> : <Battery className="w-3.5 h-3.5 text-yellow-400" />}
              BAT
            </span>
            <span className="font-bold text-slate-200">{bat !== null && bat !== undefined ? `${bat}%` : 'AC'}</span>
          </div>
        </div>

        {actionNotice && (
          <div className="mt-3 p-2.5 rounded-xl bg-cyan-500/20 border border-cyan-500/50 text-cyan-300 text-xs font-mono text-center animate-in fade-in">
            {actionNotice}
          </div>
        )}
      </div>

      {/* Siri Voice & Chat Dialogue Box */}
      <div className="p-4 sm:p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
          <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            SIRI INSTANT VOICE & CHAT
          </span>
          <span className="text-[10px] font-mono text-cyan-400">100% LOCAL</span>
        </div>

        {/* Scrollable Conversation Stream */}
        <div className="h-44 overflow-y-auto space-y-2.5 p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs">
          {chatLog.map((msg, i) => (
            <div
              key={i}
              className={`p-2.5 rounded-xl max-w-[88%] leading-relaxed ${
                msg.role === 'user'
                  ? 'ml-auto bg-cyan-600 text-white rounded-tr-none'
                  : 'bg-slate-900 text-slate-200 border border-slate-800 rounded-tl-none font-medium'
              }`}
            >
              {msg.text}
            </div>
          ))}
          {isSending && (
            <div className="p-2.5 rounded-xl bg-slate-900/60 text-cyan-400 border border-slate-800 animate-pulse text-xs">
              JARVIS is thinking...
            </div>
          )}
        </div>

        {/* Quick Voice Chips */}
        <div className="flex gap-1.5 overflow-x-auto pb-1 text-[11px] font-mono">
          {[
            "clip a gta 6 video",
            "clip ongoing livestream",
            "how is my pc",
            "upload next short",
            "lock pc"
          ].map((chip) => (
            <button
              key={chip}
              onClick={() => handleSend(chip)}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 whitespace-nowrap active:scale-95 transition-transform"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Input Bar with Touch Mic */}
        <div className="flex gap-2">
          <button
            onClick={toggleVoice}
            className={`p-3 rounded-xl border flex items-center justify-center transition-all active:scale-95 cursor-pointer ${
              isRecording
                ? 'bg-red-600 border-red-500 text-white animate-pulse shadow-lg shadow-red-500/30'
                : 'bg-slate-800 border-slate-700 text-cyan-400 hover:bg-slate-700'
            }`}
            title="Voice Touch-to-Talk"
          >
            {isRecording ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
          </button>

          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Tell JARVIS to clip, search, or automate..."
            className="flex-1 px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />

          <button
            onClick={() => handleSend()}
            disabled={isSending || !inputText.trim()}
            className="p-3 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 rounded-xl font-bold flex items-center justify-center transition-transform active:scale-95 cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 1-Touch Autonomous Content Creation Buttons */}
      <div className="p-4 sm:p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            1-TOUCH CONTENT CREATION & AUTOPILOT
          </span>
          <button
            onClick={() => onNavigate('shorts')}
            className="text-[11px] font-mono text-cyan-400 hover:underline"
          >
            Full Studio →
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <button
            onClick={() => handleSend("clip a gta 6 video")}
            className="p-3.5 rounded-xl bg-gradient-to-br from-purple-900/40 to-slate-900 border border-purple-500/30 hover:border-purple-400 text-left transition-transform active:scale-95 cursor-pointer"
          >
            <div className="text-purple-400 font-bold text-xs flex items-center gap-1.5 mb-1">
              <Flame className="w-4 h-4" /> GTA 6 Autopilot
            </div>
            <div className="text-[10px] text-slate-400">Extracts 9:16 viral shorts & queues uploads</div>
          </button>

          <button
            onClick={() => handleSend("make reels on mrbeast")}
            className="p-3.5 rounded-xl bg-gradient-to-br from-red-900/40 to-slate-900 border border-red-500/30 hover:border-red-400 text-left transition-transform active:scale-95 cursor-pointer"
          >
            <div className="text-red-400 font-bold text-xs flex items-center gap-1.5 mb-1">
              <Zap className="w-4 h-4" /> MrBeast Autopilot
            </div>
            <div className="text-[10px] text-slate-400">High-retention 6-factor hooks</div>
          </button>

          <button
            onClick={() => handleSend("clip ongoing livestream")}
            className="p-3.5 rounded-xl bg-gradient-to-br from-rose-900/40 to-slate-900 border border-rose-500/30 hover:border-rose-400 text-left transition-transform active:scale-95 cursor-pointer"
          >
            <div className="text-rose-400 font-bold text-xs flex items-center gap-1.5 mb-1">
              <Radio className="w-4 h-4 animate-pulse" /> Clip Live Stream
            </div>
            <div className="text-[10px] text-slate-400">Dual-HLS FFmpeg rolling slice & auto-publish</div>
          </button>

          <button
            onClick={() => handleSend("upload next short")}
            className="p-3.5 rounded-xl bg-gradient-to-br from-emerald-900/40 to-slate-900 border border-emerald-500/30 hover:border-emerald-400 text-left transition-transform active:scale-95 cursor-pointer"
          >
            <div className="text-emerald-400 font-bold text-xs flex items-center gap-1.5 mb-1">
              <PlaySquare className="w-4 h-4" /> Dispatch Upload
            </div>
            <div className="text-[10px] text-slate-400">Publishes next queued short to YouTube Studio</div>
          </button>
        </div>
      </div>

      {/* Desktop Remote Control Actions */}
      <div className="p-4 sm:p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
            <Smartphone className="w-4 h-4 text-cyan-400" />
            WORKSTATION DESKTOP REMOTE
          </span>
          <button
            onClick={() => onNavigate('desktop')}
            className="text-[11px] font-mono text-cyan-400 hover:underline"
          >
            Desktop HUD →
          </button>
        </div>

        {/* Volume & Audio Strip */}
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => handleTool('control_volume', { action: 'mute' }, 'Volume Toggled')}
            className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 flex items-center justify-center gap-1.5 active:scale-95 transition-transform"
          >
            <VolumeX className="w-4 h-4 text-rose-400" />
            Mute
          </button>
          <button
            onClick={() => handleTool('control_volume', { action: 'down' }, 'Volume Decreased')}
            className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 flex items-center justify-center gap-1.5 active:scale-95 transition-transform"
          >
            <Volume1 className="w-4 h-4 text-blue-400" />
            Vol -
          </button>
          <button
            onClick={() => handleTool('control_volume', { action: 'up' }, 'Volume Increased')}
            className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 flex items-center justify-center gap-1.5 active:scale-95 transition-transform"
          >
            <Volume2 className="w-4 h-4 text-emerald-400" />
            Vol +
          </button>
        </div>

        {/* Desktop Quick Shortcuts */}
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => handleTool('capture_screen', {}, 'Screenshot Captured')}
            className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 flex items-center justify-center gap-1.5 active:scale-95 transition-transform"
          >
            <Camera className="w-4 h-4 text-cyan-400" />
            Screenshot
          </button>
          <button
            onClick={() => handleTool('minimize_all', {}, 'All Windows Minimized')}
            className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 flex items-center justify-center gap-1.5 active:scale-95 transition-transform"
          >
            <Layers className="w-4 h-4 text-amber-400" />
            Minimize All
          </button>
          <button
            onClick={() => handleTool('lock_pc', {}, 'Workstation Locked')}
            className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 flex items-center justify-center gap-1.5 active:scale-95 transition-transform"
          >
            <Lock className="w-4 h-4 text-purple-400" />
            Lock PC
          </button>
        </div>

        {/* Launch Favorite Apps */}
        <div className="pt-2">
          <div className="text-[11px] font-mono text-slate-400 mb-1.5">QUICK APP LAUNCHERS:</div>
          <div className="grid grid-cols-4 gap-2 text-xs font-mono">
            {[
              { name: 'Chrome', id: 'chrome' },
              { name: 'VS Code', id: 'code' },
              { name: 'Spotify', id: 'spotify' },
              { name: 'Notepad', id: 'notepad' }
            ].map((app) => (
              <button
                key={app.id}
                onClick={() => handleTool('launch_application', { app_name: app.id }, `${app.name} Launched`)}
                className="py-2 px-2.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-300 text-center active:scale-95 transition-all truncate"
              >
                {app.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* LAN Link Info Card */}
      <div className="p-4 rounded-xl bg-slate-950/80 border border-cyan-500/20 text-xs font-mono flex items-center justify-between">
        <div className="truncate mr-2">
          <div className="text-slate-400 text-[10px]">CURRENT PHONE ACCESS URL:</div>
          <div className="text-cyan-300 font-bold truncate">{mobileInfo.mobile_url || window.location.href}</div>
        </div>
        <button
          onClick={handleCopyLink}
          className="px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 flex items-center gap-1.5 active:scale-95 transition-transform cursor-pointer"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
    </div>
  );
};

