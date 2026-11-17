import React, { useState, useEffect } from 'react';
import {
  PlaySquare,
  Flame,
  Sparkles,
  Download,
  Share2,
  Clock,
  Layers,
  CheckCircle2,
  Upload,
  Globe,
  Copy,
  Calendar,
  Check,
  Video,
  Zap,
  Activity,
  Terminal,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  Cpu,
  Tv,
  Radio
} from 'lucide-react';
import { ClipItem, api } from '../services/api';

interface ShortsFactoryProps {
  clips: ClipItem[];
  onRefreshClips: () => void;
}

export const ShortsFactory: React.FC<ShortsFactoryProps> = ({ clips, onRefreshClips }) => {
  const [sourcePath, setSourcePath] = useState('');
  const [targetCount, setTargetCount] = useState(3);
  const [targetDuration, setTargetDuration] = useState(45);
  const [isRendering, setIsRendering] = useState(false);
  const [selectedClip, setSelectedClip] = useState<ClipItem | null>(clips[0] || null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [privacy, setPrivacy] = useState('schedule');
  const [autoPublish, setAutoPublish] = useState(true);
  const [intervalMinutes, setIntervalMinutes] = useState(45);
  const [copiedDesc, setCopiedDesc] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  // --- 1-Click Viral Autopilot State ---
  const [autopilotPreset, setAutopilotPreset] = useState<string>('mrbeast');
  const [customAutopilotUrl, setCustomAutopilotUrl] = useState<string>('');
  const [autopilotClipsCount, setAutopilotClipsCount] = useState<number>(4);
  const [autopilotInterval, setAutopilotInterval] = useState<number>(45);
  const [autopilotUploadTillLimit, setAutopilotUploadTillLimit] = useState<boolean>(true);
  const [autopilotPlatform, setAutopilotPlatform] = useState<'both' | 'youtube' | 'instagram'>('both');
  const [autopilotStatus, setAutopilotStatus] = useState<any>(null);
  const [isAutopilotRunning, setIsAutopilotRunning] = useState<boolean>(false);
  const [showAutopilotLogs, setShowAutopilotLogs] = useState<boolean>(true);

  useEffect(() => {
    let timer: any = null;
    const checkStatus = async () => {
      try {
        let st = await api.getViralAutopilotStatus();
        if ((!st || st.status === 'IDLE') && isAutopilotRunning) {
          const liveSt = await api.getLivestreamStatus();
          if (liveSt && (liveSt.status === 'RUNNING' || liveSt.status === 'COMPLETED')) {
            st = liveSt;
          }
        }
        setAutopilotStatus(st);
        if (st && st.status === 'RUNNING') {
          setIsAutopilotRunning(true);
        } else if (isAutopilotRunning && st && (st.status === 'COMPLETED' || st.status === 'ERROR')) {
          setIsAutopilotRunning(false);
          onRefreshClips();
        }
      } catch (err) {
        // ignore polling errors
      }
    };

    checkStatus();
    timer = setInterval(checkStatus, 3500);
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isAutopilotRunning]);

  React.useEffect(() => {
    if (!selectedClip && clips.length > 0) {
      setSelectedClip(clips[0]);
    }
  }, [clips, selectedClip]);

  const showNotice = (msg: string) => {
    setActionNotice(msg);
    setTimeout(() => setActionNotice(null), 4000);
  };

  const isYouTubeUrl = (url: string) => {
    return /^(https?:\/\/)?(www\.|m\.)?(youtube\.com|youtu\.be)\/.+/i.test(url.trim());
  };

  const handleLaunchAutopilot = async () => {
    setIsAutopilotRunning(true);
    showNotice('⚡ Launching 1-Click Viral Autopilot Engine...');
    try {
      if (autopilotPreset === 'livestream') {
        const requiredDuration = Math.max(90, autopilotClipsCount * 45);
        const res = await api.clipLivestream({
          urlOrTopic: customAutopilotUrl.trim() || undefined,
          durationSeconds: requiredDuration,
          numClips: autopilotClipsCount,
          targetClipDuration: 30.0,
          stylePreset: 'mrbeast',
          autoUpload: true,
          visibility: 'public'
        });
        if (res.status === 'LIVESTREAM_CLIPPING_STARTED') {
          showNotice(`🔴 Live Stream capture started! Capturing ${requiredDuration}s rolling slice & auto-publishing ${autopilotClipsCount} vertical shorts to YouTube Studio...`);
        } else {
          showNotice(res.message || 'Live stream clipping initiated.');
        }
        return;
      }

      const isCustom = autopilotPreset === 'custom';
      const isUrl = isYouTubeUrl(customAutopilotUrl);
      const res = await api.startViralAutopilot({
        youtubeUrl: isCustom && isUrl ? customAutopilotUrl.trim() : undefined,
        searchTopic: isCustom && !isUrl && customAutopilotUrl.trim() ? customAutopilotUrl.trim() : undefined,
        preset: !isCustom ? autopilotPreset : undefined,
        numClips: autopilotClipsCount,
        intervalMinutes: autopilotInterval,
        uploadTillLimit: autopilotUploadTillLimit,
        platform: autopilotPlatform,
        privacy: 'public'
      });
      if (res.success) {
        showNotice('🚀 1-Click Viral Autopilot sequence started! Full automation running till upload limit.');
      } else {
        showNotice(res.message || 'Autopilot already active.');
      }
    } catch (e: any) {
      setIsAutopilotRunning(false);
      showNotice(`Autopilot failed to start: ${e.message}`);
    }
  };

  const handleStartShortsBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourcePath.trim() || isRendering) return;

    setIsRendering(true);
    const isYt = isYouTubeUrl(sourcePath);
    const msg = isYt
      ? `Ingesting YouTube video -> Cutting ${targetCount} viral shorts${autoPublish ? ' -> Auto-publishing spaced 45m apart' : ''}...`
      : `Cutting ${targetCount} YouTube Shorts (<=60s) from local source...`;
    showNotice(msg);

    try {
      if (isYt) {
        await api.generateClipsFromYouTube(
          sourcePath.trim(),
          targetCount,
          targetDuration,
          'podcast',
          autoPublish,
          intervalMinutes,
          privacy
        );
      } else {
        await api.generateClips(
          sourcePath.trim(),
          targetCount,
          targetDuration,
          'podcast',
          autoPublish,
          intervalMinutes,
          privacy
        );
      }

      setTimeout(() => {
        onRefreshClips();
        setIsRendering(false);
        showNotice(
          autoPublish
            ? `YouTube Shorts generated & queued for YouTube Studio release (spaced ${intervalMinutes}m apart)!`
            : 'YouTube Shorts generated successfully!'
        );
      }, 6000);
    } catch (e: any) {
      setIsRendering(false);
      showNotice(`Error: ${e.message}`);
    }
  };

  const handleUploadShort = async (clip: ClipItem) => {
    setIsUploading(true);
    showNotice(`Uploading Short "${clip.title}" directly to YouTube Studio...`);
    try {
      const res = await api.uploadViaBrowser(
        clip.id,
        clip.title,
        clip.caption,
        clip.tags ? clip.tags.split(' ') : [],
        privacy
      );
      showNotice(res.message || `Uploaded Short "${clip.title}" to YouTube Studio!`);
      onRefreshClips();
    } catch (e: any) {
      // Fallback to queue endpoint if direct browser upload has an active profile lock
      try {
        const res2 = await api.publishToYouTube(
          clip.id,
          clip.title,
          clip.caption,
          clip.tags ? clip.tags.split(' ') : [],
          privacy
        );
        showNotice(res2.message || `Queued Short "${clip.title}" for YouTube upload!`);
        onRefreshClips();
      } catch (err2: any) {
        showNotice(`YouTube error: ${e.message}`);
      }
    } finally {
      setIsUploading(false);
    }
  };

  const copyDescription = () => {
    if (!selectedClip) return;
    navigator.clipboard.writeText(selectedClip.caption);
    setCopiedDesc(true);
    setTimeout(() => setCopiedDesc(false), 2000);
  };

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <PlaySquare className="w-5 h-5 text-red-500" />
            YouTube Shorts Autonomous Factory
          </h1>
          <p className="text-xs font-mono text-cyan-400/80">
            Paste YouTube Link • Autonomous 9:16 Re-framing • SEO Proper Description • 45m Pacing Auto-Publish
          </p>
        </div>

        <button
          onClick={onRefreshClips}
          className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-cyan-500/30 text-cyan-300 text-xs font-mono hover:bg-slate-800 cursor-pointer transition-colors self-start"
        >
          Refresh Shorts ({clips.length})
        </button>
      </div>

      {/* 1-Click Viral Autopilot Command Center */}
      <div className="p-6 rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-black border-2 border-red-500/50 shadow-[0_0_40px_rgba(239,68,68,0.25)] relative overflow-hidden">
        {/* Ambient Top Glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-red-500/20 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/40 text-[10px] font-mono uppercase tracking-widest font-bold flex items-center gap-1.5">
                  <Zap className="w-3 h-3 text-red-400 animate-pulse" />
                  1-Click Autonomous Viral Engine
                </span>
                {autopilotStatus?.status === 'RUNNING' && (
                  <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-[10px] font-mono animate-pulse flex items-center gap-1">
                    <Activity className="w-3 h-3" /> Live
                  </span>
                )}
              </div>
              <h2 className="text-lg font-black text-white uppercase tracking-wider mt-1 flex items-center gap-2">
                Viral YouTuber Clipper &amp; Auto-Publish Autopilot
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Study top viral creator patterns • Extract 6-factor hooks • 9:16 vertical render with karaoke captions • SEO proper descriptions • Upload spaced 45m till daily limit reached
              </p>
            </div>

            {autopilotStatus?.daily_limit_reached && (
              <div className="px-3 py-1.5 rounded-xl bg-amber-500/20 border border-amber-500/50 text-amber-300 text-xs font-mono flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>Daily Limit Hit • Paused Safely</span>
              </div>
            )}
          </div>

          {/* Preset Selector Chips */}
          <div>
            <label className="block text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-2 font-bold">
              Select Viral Creator Preset or Custom Target:
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-2">
              {[
                { id: 'mrbeast', label: 'MrBeast', icon: '⚡', desc: 'Energy & Challenge' },
                { id: 'football', label: 'Football', icon: '⚽', desc: 'Skills & Goals 4K' },
                { id: 'rogan', label: 'Joe Rogan', icon: '🎙️', desc: 'Curiosity & Secrets' },
                { id: 'huberman', label: 'Huberman', icon: '🧠', desc: 'Science & Dopamine' },
                { id: 'speed', label: 'IShowSpeed', icon: '🔥', desc: 'Chaos & Comedy' },
                { id: 'livestream', label: 'Live Stream', icon: '🔴', desc: 'Ongoing Live Feed' },
                { id: 'custom', label: 'Custom URL', icon: '🔗', desc: 'Paste Any Link/Topic' }
              ].map((p) => {
                const isSelected = autopilotPreset === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setAutopilotPreset(p.id)}
                    className={`p-3 rounded-2xl border text-left transition-all cursor-pointer relative ${
                      isSelected
                        ? 'bg-gradient-to-b from-red-600/30 to-red-950/60 border-red-400 shadow-[0_0_15px_rgba(239,68,68,0.4)] text-white'
                        : 'bg-slate-950/80 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="text-lg mb-1">{p.icon}</div>
                    <div className="text-xs font-bold leading-tight">{p.label}</div>
                    <div className="text-[10px] opacity-75 font-mono truncate">{p.desc}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Livestream Input (if livestream selected) */}
          {autopilotPreset === 'livestream' && (
            <div className="p-3.5 rounded-2xl bg-slate-950/90 border border-red-500/40 space-y-2">
              <label className="block text-xs font-mono text-red-400 font-bold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping inline-block" />
                Ongoing Live Stream Target (URL or Topic, leave blank to auto-discover random active stream):
              </label>
              <input
                type="text"
                value={customAutopilotUrl}
                onChange={(e) => setCustomAutopilotUrl(e.target.value)}
                placeholder="e.g. https://www.youtube.com/watch?v=... or 'news live' (or leave empty for random live stream)"
                className="w-full px-3.5 py-2.5 rounded-xl bg-black border border-red-500/40 text-xs text-slate-100 font-mono focus:outline-none focus:border-red-400"
              />
            </div>
          )}

          {/* Custom URL or Search Topic Input (if custom selected) */}
          {autopilotPreset === 'custom' && (
            <div className="p-3.5 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-2">
              <label className="block text-xs font-mono text-cyan-300 font-bold">
                Enter YouTube Video URL or Viral Search Topic:
              </label>
              <input
                type="text"
                value={customAutopilotUrl}
                onChange={(e) => setCustomAutopilotUrl(e.target.value)}
                placeholder="e.g. https://www.youtube.com/watch?v=... or 'insane champions league goals'"
                className="w-full px-3.5 py-2.5 rounded-xl bg-black border border-cyan-500/40 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>
          )}

          {/* Parameters & 1-Click Launch Button */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
            <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
              <div className="flex items-center gap-1.5 text-slate-300">
                <Layers className="w-4 h-4 text-red-400" />
                <span>Clips to Extract:</span>
                <select
                  value={autopilotClipsCount}
                  onChange={(e) => setAutopilotClipsCount(Number(e.target.value))}
                  className="px-2 py-1 rounded-lg bg-slate-900 border border-slate-700 text-red-300 font-mono"
                >
                  <option value={2}>2 Clips</option>
                  <option value={3}>3 Clips</option>
                  <option value={4}>4 Clips (Recommended)</option>
                  <option value={6}>6 Clips (Deep batch)</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5 text-slate-300">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span>Interval:</span>
                <span className="px-2 py-1 rounded-lg bg-slate-900 border border-slate-700 text-cyan-300 font-bold font-mono">
                  45 Minutes (Anti-Shadowban)
                </span>
              </div>

                              <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-mono">Platform:</span>
                  <div className="flex gap-1 bg-black/60 p-1 rounded-xl border border-white/10">
                    {(['both', 'youtube', 'instagram'] as const).map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setAutopilotPlatform(p)}
                        className={`px-3 py-1 text-xs rounded-lg font-bold transition-all ${
                          autopilotPlatform === p
                            ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-md'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        {p === 'both' ? 'Both (YT + IG)' : p === 'youtube' ? 'YouTube' : 'Instagram'}
                      </button>
                    ))}
                  </div>
                </div>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 select-none">
                <input
                  type="checkbox"
                  checked={autopilotUploadTillLimit}
                  onChange={(e) => setAutopilotUploadTillLimit(e.target.checked)}
                  className="w-4 h-4 accent-red-500 cursor-pointer rounded"
                />
                <span className="text-xs font-bold text-slate-200">
                  Upload Till Daily Limit Reached
                </span>
              </label>
            </div>

            <button
              onClick={handleLaunchAutopilot}
              disabled={isAutopilotRunning || (autopilotPreset === 'custom' && !customAutopilotUrl.trim())}
              className="px-6 py-3 rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-amber-600 hover:from-red-500 hover:to-rose-500 text-white font-black text-xs uppercase tracking-wider shadow-[0_0_25px_rgba(239,68,68,0.5)] cursor-pointer disabled:opacity-50 transition-all flex items-center gap-2"
            >
              <Zap className={`w-4 h-4 ${isAutopilotRunning ? 'animate-spin' : ''}`} />
              <span>{isAutopilotRunning ? 'AUTOPILOT ACTIVELY RUNNING...' : '⚡ LAUNCH 1-CLICK VIRAL AUTOPILOT'}</span>
            </button>
          </div>

          {/* Real-time Status Card & Progress */}
          {autopilotStatus && autopilotStatus.status !== 'IDLE' && (
            <div className="mt-4 p-4 rounded-2xl bg-black/80 border border-red-500/40 space-y-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${autopilotStatus.status === 'RUNNING' ? 'bg-cyan-400 animate-ping' : autopilotStatus.status === 'COMPLETED' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                  <span className="font-bold text-slate-200">
                    STATUS: {autopilotStatus.status}
                  </span>
                  <span className="text-slate-400">•</span>
                  <span className="text-cyan-300">{autopilotStatus.step}</span>
                </div>
                <span className="text-red-400 font-bold">{autopilotStatus.progress_percent}%</span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                <div
                  className="h-full bg-gradient-to-r from-red-500 via-rose-500 to-cyan-400 transition-all duration-500"
                  style={{ width: `${autopilotStatus.progress_percent}%` }}
                />
              </div>

              {/* Source Video & Uploads Summary */}
              {autopilotStatus.source_info && (
                <div className="flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-300 bg-slate-950/60 p-2 rounded-xl border border-slate-800">
                  <div className="flex items-center gap-2 truncate max-w-xl">
                    <Tv className="w-3.5 h-3.5 text-red-400 shrink-0" />
                    <span className="truncate">Source: <strong className="text-white">{autopilotStatus.source_info.title}</strong></span>
                    {autopilotStatus.source_info.uploader && (
                      <span className="text-slate-500">by {autopilotStatus.source_info.uploader}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-cyan-400">
                      Clips: {autopilotStatus.clips_produced?.length || 0}
                    </span>
                    <span className="text-emerald-400 font-bold">
                      Scheduled: {autopilotStatus.uploads_completed?.length || 0}
                    </span>
                  </div>
                </div>
              )}

              {/* Terminal Logs Toggle */}
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1">
                  <span className="flex items-center gap-1">
                    <Terminal className="w-3 h-3 text-red-400" /> Real-time Autopilot Output Log
                  </span>
                  <button
                    onClick={() => setShowAutopilotLogs(!showAutopilotLogs)}
                    className="text-cyan-400 hover:underline cursor-pointer"
                  >
                    {showAutopilotLogs ? 'Hide Terminal' : 'Show Terminal'}
                  </button>
                </div>
                {showAutopilotLogs && autopilotStatus.log && autopilotStatus.log.length > 0 && (
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-900 font-mono text-[10px] text-emerald-400 max-h-36 overflow-y-auto space-y-1">
                    {autopilotStatus.log.slice(-12).map((lg: string, idx: number) => (
                      <div key={idx} className="leading-relaxed opacity-90">{lg}</div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Production Trigger Console */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-red-500/30 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
            <Flame className="w-4 h-4 text-red-500" />
            Produce YouTube Shorts Batch from URL or File
          </div>
          <span className="text-[11px] font-mono text-slate-400">Strict &lt;60s Viral Window</span>
        </div>

        <form onSubmit={handleStartShortsBatch} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
            <div className="md:col-span-6">
              <label className="block text-xs font-mono text-slate-400 mb-1 flex items-center justify-between">
                <span>SOURCE VIDEO (PASTE YOUTUBE URL OR LOCAL PATH)</span>
                {sourcePath && isYouTubeUrl(sourcePath) && (
                  <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                    <Globe className="w-3 h-3" /> YouTube Link Detected
                  </span>
                )}
              </label>
              <input
                type="text"
                value={sourcePath}
                onChange={(e) => setSourcePath(e.target.value)}
                placeholder="Paste YouTube link: https://www.youtube.com/watch?v=... or local path"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-red-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-red-400"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-mono text-slate-400 mb-1">
                DURATION TARGET
              </label>
              <select
                value={targetDuration}
                onChange={(e) => setTargetDuration(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-red-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-red-400"
              >
                <option value={15}>15s (Ultra High Completion)</option>
                <option value={30}>30s (Balanced Viral Hook)</option>
                <option value={45}>45s (Story Arc - Best)</option>
                <option value={59}>59s (Max YouTube Shorts)</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-mono text-slate-400 mb-1">
                NUM CLIPS
              </label>
              <select
                value={targetCount}
                onChange={(e) => setTargetCount(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-red-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-red-400"
              >
                <option value={1}>1 Clip</option>
                <option value={2}>2 Clips</option>
                <option value={3}>3 Clips (Standard)</option>
                <option value={5}>5 Clips (Full Batch)</option>
                <option value={8}>8 Clips (Max)</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <button
                type="submit"
                disabled={isRendering || !sourcePath.trim()}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white font-bold text-xs uppercase tracking-wider shadow-lg disabled:opacity-50 cursor-pointer transition-all flex items-center justify-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                <span>{isRendering ? 'PROCESSING...' : 'GENERATE & CLIP'}</span>
              </button>
            </div>
          </div>

          {/* Autonomous YouTube Auto-Publish Settings */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-red-500/20 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="autoPublishYt"
                checked={autoPublish}
                onChange={(e) => setAutoPublish(e.target.checked)}
                className="w-4 h-4 accent-red-500 cursor-pointer rounded"
              />
              <label htmlFor="autoPublishYt" className="text-xs font-mono text-slate-200 cursor-pointer flex items-center gap-1.5 font-bold">
                <Globe className="w-3.5 h-3.5 text-red-400" />
                Auto-Publish to YouTube Shorts after clipping
              </label>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <div className="flex items-center gap-1.5 text-slate-400">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>Pacing Interval:</span>
                <select
                  value={intervalMinutes}
                  onChange={(e) => setIntervalMinutes(Number(e.target.value))}
                  disabled={!autoPublish}
                  className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-cyan-300 font-mono disabled:opacity-50"
                >
                  <option value={30}>30 mins</option>
                  <option value={45}>45 mins (Recommended)</option>
                  <option value={60}>60 mins</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5 text-slate-400">
                <Calendar className="w-3.5 h-3.5 text-emerald-400" />
                <span>Release Mode:</span>
                <select
                  value={privacy}
                  onChange={(e) => setPrivacy(e.target.value)}
                  disabled={!autoPublish}
                  className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-emerald-300 font-mono disabled:opacity-50"
                >
                  <option value="schedule">Schedule (Spaced 45m)</option>
                  <option value="public">Public (Immediate)</option>
                </select>
              </div>
            </div>
          </div>
        </form>

        {actionNotice && (
          <div className="mt-3 p-2.5 rounded-lg bg-red-950/80 border border-red-400 text-xs font-mono text-red-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{actionNotice}</span>
          </div>
        )}
      </div>

      {/* Main Studio View */}
      {selectedClip && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Vertical Video Player */}
          <div className="lg:col-span-5 flex flex-col items-center">
            <div className="w-full max-w-[280px] aspect-[9/16] rounded-2xl overflow-hidden bg-slate-900 border border-red-500/40 shadow-2xl relative">
              {selectedClip.video_url ? (
                <video
                  key={selectedClip.video_url}
                  src={selectedClip.video_url}
                  controls
                  autoPlay
                  loop
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="flex items-center justify-center h-full text-slate-500 text-xs font-mono">
                  No preview available
                </div>
              )}
            </div>
            <div className="mt-2 text-xs font-mono text-slate-400">
              YouTube Shorts 9:16 • {selectedClip.duration}s
            </div>
          </div>

          {/* YouTube Metadata & Upload */}
          <div className="lg:col-span-7 space-y-4">
            <div className="p-6 rounded-2xl bg-slate-950/80 border border-red-500/25 space-y-4">
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 rounded-full bg-red-500/20 text-red-300 border border-red-500/40 text-xs font-mono font-bold">
                  VIRAL SCORE {selectedClip.total_score}/100
                </span>
                <span className="text-xs font-mono text-slate-400">
                  Status: {selectedClip.published_youtube === 1 ? '✅ Scheduled / Published' : '⚡ Ready'}
                </span>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">
                  SHORTS TITLE (OPTIMIZED FOR HIGH CTR)
                </label>
                <h2 className="text-sm font-bold text-slate-100 bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                  {selectedClip.title}
                </h2>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-mono text-slate-400">
                    PROPER YOUTUBE SEO DESCRIPTION (WITH CTAS, ATTRIBUTION & HASHTAGS)
                  </label>
                  <button
                    onClick={copyDescription}
                    className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
                  >
                    {copiedDesc ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedDesc ? 'Copied!' : 'Copy'}</span>
                  </button>
                </div>
                <div className="p-3.5 max-h-48 overflow-y-auto rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed select-text">
                  {selectedClip.caption}
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">TAGS & KEYWORDS</label>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-red-300 font-mono">
                  {selectedClip.tags}
                </div>
              </div>

              {/* Upload Controls */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <select
                  value={privacy}
                  onChange={(e) => setPrivacy(e.target.value)}
                  className="px-3 py-2 rounded-xl bg-slate-900 border border-red-500/30 text-xs text-slate-200 font-mono focus:outline-none"
                >
                  <option value="schedule">Schedule as Public</option>
                  <option value="public">Public (Immediate)</option>
                  <option value="unlisted">Unlisted (Review)</option>
                  <option value="private">Private</option>
                </select>

                <button
                  onClick={() => handleUploadShort(selectedClip)}
                  disabled={isUploading}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white font-bold text-xs uppercase font-mono tracking-wider flex items-center gap-2 cursor-pointer shadow-lg transition-all disabled:opacity-50"
                >
                  <Upload className="w-4 h-4" />
                  <span>{isUploading ? 'Uploading...' : 'Publish to YouTube Studio'}</span>
                </button>

                <a
                  href={selectedClip.video_url}
                  download
                  className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono flex items-center gap-2 cursor-pointer transition-colors"
                >
                  <Download className="w-4 h-4 text-red-400" />
                  <span>Download MP4</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Shorts Gallery */}
      <div className="pt-4">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Layers className="w-4 h-4 text-red-500" />
          Ready YouTube Shorts ({clips.length})
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
          {clips.map((c) => (
            <div
              key={c.id}
              onClick={() => setSelectedClip(c)}
              className={`cursor-pointer rounded-xl overflow-hidden bg-slate-950 border transition-all ${
                selectedClip?.id === c.id
                  ? 'border-red-500 shadow-lg scale-105'
                  : 'border-slate-800 hover:border-red-500/50'
              }`}
            >
              <div className="aspect-[9/16] bg-slate-900 relative">
                {c.thumb_url && <img src={c.thumb_url} alt={c.title} className="w-full h-full object-cover" />}
                <div className="absolute top-1 right-1 px-1.5 py-0.5 rounded bg-slate-950/80 text-[9px] font-mono text-red-400 font-bold">
                  {c.total_score}
                </div>
                {c.published_youtube === 1 && (
                  <div className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-emerald-950/90 border border-emerald-500 text-[8px] font-mono text-emerald-300 font-bold">
                    SCHEDULED
                  </div>
                )}
              </div>
              <div className="p-2">
                <div className="text-[11px] font-bold text-slate-200 truncate">{c.title}</div>
                <div className="text-[10px] text-slate-400 font-mono">{c.duration}s</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
