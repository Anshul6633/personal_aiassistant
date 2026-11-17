import React, { useState, useEffect } from 'react';
import {
  Camera,
  Key,
  Globe,
  Upload,
  CheckCircle2,
  RefreshCw,
  ShieldCheck,
  Flame,
  Smartphone,
  Sparkles,
  ExternalLink,
  Laptop,
  CheckCircle,
  AlertTriangle,
  Play,
  Film,
  Hash,
  Clock,
  Layers,
  FolderOpen
} from 'lucide-react';
import { ClipItem, api } from '../services/api';

interface InstagramManagerProps {
  clips: ClipItem[];
  onRefreshClips: () => void;
}

export const InstagramManager: React.FC<InstagramManagerProps> = ({ clips, onRefreshClips }) => {
  const [authStatus, setAuthStatus] = useState<any>(null);
  const [browserStatus, setBrowserStatus] = useState<any>(null);
  const [isOpeningBrowser, setIsOpeningBrowser] = useState<boolean>(false);

  // Content Selection Source: 'clips' (Factory) vs 'studio' (Exports & Local)
  const [sourceMode, setSourceMode] = useState<'clips' | 'local'>('clips');
  const [selectedClipId, setSelectedClipId] = useState<string>(clips[0]?.id || '');
  const [localVideos, setLocalVideos] = useState<any[]>([]);
  const [selectedLocalPath, setSelectedLocalPath] = useState<string>('');

  // Post Configuration
  const [caption, setCaption] = useState<string>('');
  const [useHeadless, setUseHeadless] = useState<boolean>(false);
  const [isPublishing, setIsPublishing] = useState<boolean>(false);
  const [publishProgress, setPublishProgress] = useState<string | null>(null);
  const [publishResult, setPublishResult] = useState<any>(null);

  // Direct Credentials & Stealth Auth
  const [usernameInput, setUsernameInput] = useState<string>('clipperwithout');
  const [passwordInput, setPasswordInput] = useState<string>('akhatri@777');
  const [showDirectAuth, setShowDirectAuth] = useState<boolean>(false);
  const [isAutoLoggingIn, setIsAutoLoggingIn] = useState<boolean>(false);

  // Suggested viral hashtags
  const suggestedHashtags = [
    '#reels',
    '#viral',
    '#trending',
    '#explorepage',
    '#fyp',
    '#creator',
    '#football',
    '#motivation',
    '#podcast',
    '#shorts',
    '#instagramreels'
  ];

  const fetchAuth = async () => {
    try {
      const [general, browser] = await Promise.all([
        api.getInstagramStatus().catch(() => null),
        api.getInstagramBrowserStatus().catch(() => null),
      ]);
      setAuthStatus(general);
      setBrowserStatus(browser);
    } catch (e) {
      console.error('Failed to fetch Instagram status:', e);
    }
  };

  const fetchLocalFiles = async () => {
    try {
      const files = await api.browseLocalVideos();
      setLocalVideos(files);
      if (files.length > 0 && !selectedLocalPath) {
        setSelectedLocalPath(files[0].path);
      }
    } catch (e) {
      console.error('Failed to fetch local files:', e);
    }
  };

  useEffect(() => {
    fetchAuth();
    fetchLocalFiles();
  }, []);

  // Sync selected clip caption
  useEffect(() => {
    if (sourceMode === 'clips') {
      const clip = clips.find((c) => c.id === selectedClipId) || clips[0];
      if (clip) {
        setCaption(clip.caption || `${clip.title}\n\n#reels #viral #explorepage`);
      }
    } else if (sourceMode === 'local') {
      const f = localVideos.find((v) => v.path === selectedLocalPath) || localVideos[0];
      if (f) {
        const cleanName = f.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' ');
        setCaption(`🔥 ${cleanName}\n\n#reels #viral #explorepage #trending`);
      }
    }
  }, [selectedClipId, selectedLocalPath, sourceMode, clips, localVideos]);

  // Open native Chrome for sign-in
  const handleOpenBrowserLogin = async () => {
    setIsOpeningBrowser(true);
    setPublishProgress('Launching Chrome for Instagram sign-in...');
    try {
      const res = await api.openInstagramBrowserLogin();
      setPublishProgress(res.message || 'Chrome window opened! Sign in to Instagram, then click Refresh.');

      // Poll status every 3s for 60s
      let checks = 0;
      const interval = setInterval(async () => {
        checks++;
        const browser = await api.getInstagramBrowserStatus().catch(() => null);
        if (browser?.logged_in) {
          setBrowserStatus(browser);
          setPublishProgress(`🎉 Instagram Connected as ${browser.username || 'Creator'}!`);
          clearInterval(interval);
          setIsOpeningBrowser(false);
          fetchAuth();
        } else if (checks > 20) {
          clearInterval(interval);
          setIsOpeningBrowser(false);
        }
      }, 3000);
    } catch (e: any) {
      setPublishProgress(`Error opening browser: ${e.message}`);
      setIsOpeningBrowser(false);
    }
  };

  // Auto-fill & Stealth Sign-in
  const handleAutoLogin = async () => {
    setIsAutoLoggingIn(true);
    setPublishProgress('Launching Chrome & typing credentials with anti-ban stealth cadence...');
    try {
      const res = await api.autoLoginInstagram(usernameInput, passwordInput);
      setPublishProgress(res.message || 'Credentials submitted! If Instagram displays a 1-time reCAPTCHA puzzle, please complete it in Chrome.');

      // Poll status every 3s for 180s
      let checks = 0;
      const interval = setInterval(async () => {
        checks++;
        const browser = await api.getInstagramBrowserStatus().catch(() => null);
        if (browser?.logged_in) {
          setBrowserStatus(browser);
          setPublishProgress(`🎉 Instagram Successfully Authenticated as @${browser.username || usernameInput}!`);
          clearInterval(interval);
          setIsAutoLoggingIn(false);
          fetchAuth();
        } else if (checks > 60) {
          clearInterval(interval);
          setIsAutoLoggingIn(false);
        }
      }, 3000);
    } catch (e: any) {
      setPublishProgress(`Auto-login notice: ${e.message}`);
      setIsAutoLoggingIn(false);
    }
  };

  // Append hashtag
  const toggleHashtag = (tag: string) => {
    if (caption.includes(tag)) {
      setCaption(caption.replace(tag, '').replace(/\s{2,}/g, ' ').trim());
    } else {
      setCaption(`${caption.trim()} ${tag}`);
    }
  };

  // Publish Reel
  const handlePublish = async () => {
    if (isPublishing) return;
    setIsPublishing(true);
    setPublishResult(null);
    setPublishProgress('Initializing Instagram Reel automation sequence...');

    try {
      const options =
        sourceMode === 'clips'
          ? {
              clipId: selectedClipId,
              caption: caption,
              headless: useHeadless,
              method: 'browser',
            }
          : {
              videoPath: selectedLocalPath,
              caption: caption,
              headless: useHeadless,
              method: 'browser',
            };

      setPublishProgress('Uploading vertical Reel & applying 9:16 crop formatting...');
      const res = await api.publishToInstagram(options);

      if (res.success) {
        setPublishResult(res);
        setPublishProgress('🎉 Success! Your Reel has been published to Instagram!');
        onRefreshClips();
        fetchAuth();
      } else {
        setPublishProgress(`Upload notice: ${res.error || res.message || 'Check terminal output'}`);
      }
    } catch (e: any) {
      setPublishProgress(`Publish error: ${e.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  const selectedClip = clips.find((c) => c.id === selectedClipId) || clips[0];
  const selectedLocal = localVideos.find((v) => v.path === selectedLocalPath) || localVideos[0];
  const activeVideoUrl =
    sourceMode === 'clips' ? selectedClip?.video_url : selectedLocal ? `/output/exports/${selectedLocal.name}` : null;

  const isConnected = Boolean(browserStatus?.logged_in || authStatus?.connected);

  return (
    <div className="space-y-6 pb-12 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Camera className="w-5 h-5 text-pink-500 animate-pulse" />
            Instagram Professional & Reels Automation Hub
          </h1>
          <p className="text-xs font-mono text-cyan-400/80">
            Zero-API Quota Browser Automation • Anti-Ban Typing Cadence • 9:16 Vertical Cropping
          </p>
        </div>

        <button
          onClick={() => {
            fetchAuth();
            fetchLocalFiles();
          }}
          className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-cyan-500/30 text-cyan-300 text-xs font-mono hover:bg-slate-800 cursor-pointer transition-colors self-start flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Status</span>
        </button>
      </div>

      {/* Account Telemetry & Safety Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Connection Status Card */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-pink-500/25 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
              <span className="flex items-center gap-1.5">
                <Laptop className="w-3.5 h-3.5 text-pink-400" />
                INSTAGRAM SESSION
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold ${
                  isConnected
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                }`}
              >
                {isConnected ? 'ONLINE • READY' : 'STANDBY • SIGN-IN'}
              </span>
            </div>

            <div className="text-sm font-bold text-slate-200 truncate">
              {browserStatus?.username || (isConnected ? 'Authenticated Creator' : 'Not Signed In')}
            </div>
            <p className="text-[11px] font-mono text-slate-400 mt-1">
              {isConnected
                ? 'Persistent session active in jarvis/browser_profile. Unlimited daily Reel uploads.'
                : 'Sign into Instagram in native Chrome once to unlock automated posting.'}
            </p>
          </div>

          <div className="mt-3 space-y-2">
            {!isConnected ? (
              <>
                <button
                  onClick={handleAutoLogin}
                  disabled={isAutoLoggingIn}
                  className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-pink-500 via-rose-500 to-purple-600 hover:from-pink-400 hover:to-purple-500 text-white font-mono text-xs font-bold flex items-center justify-center gap-1.5 cursor-pointer shadow-lg shadow-pink-500/25 transition-all disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{isAutoLoggingIn ? 'AUTHENTICATING STEALTH...' : 'STEALTH SIGN-IN (@clipperwithout)'}</span>
                </button>

                <div className="flex gap-1.5">
                  <button
                    onClick={handleOpenBrowserLogin}
                    disabled={isOpeningBrowser}
                    className="flex-1 py-1.5 px-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-cyan-300 font-mono text-[10px] flex items-center justify-center gap-1 cursor-pointer transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span>Open Browser</span>
                  </button>
                  <button
                    onClick={() => setShowDirectAuth(!showDirectAuth)}
                    className="py-1.5 px-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-200 font-mono text-[10px] cursor-pointer"
                  >
                    {showDirectAuth ? 'Hide Creds' : 'Edit Creds'}
                  </button>
                </div>

                {showDirectAuth && (
                  <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2 text-[10px] font-mono">
                    <div>
                      <span className="text-slate-400 block mb-0.5">Username:</span>
                      <input
                        type="text"
                        value={usernameInput}
                        onChange={(e) => setUsernameInput(e.target.value)}
                        className="w-full bg-slate-950 px-2 py-1 rounded border border-slate-700 text-slate-200 text-xs"
                      />
                    </div>
                    <div>
                      <span className="text-slate-400 block mb-0.5">Password:</span>
                      <input
                        type="password"
                        value={passwordInput}
                        onChange={(e) => setPasswordInput(e.target.value)}
                        className="w-full bg-slate-950 px-2 py-1 rounded border border-slate-700 text-slate-200 text-xs"
                      />
                    </div>
                  </div>
                )}
              </>
            ) : (
              <button
                onClick={handleOpenBrowserLogin}
                className="w-full py-1.5 px-3 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-cyan-300 font-mono text-[11px] flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
              >
                <ExternalLink className="w-3 h-3" />
                <span>Switch / Verify Account</span>
              </button>
            )}
          </div>
        </div>

        {/* Anti-Ban & Execution Safeguards */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-pink-500/25 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-pink-400" />
                ANTI-BAN ENGINE
              </span>
              <span className="text-[10px] font-mono text-emerald-400 font-bold">STEALTH ACTIVE</span>
            </div>
            <div className="text-sm font-bold text-slate-200">Human Cadence & 9:16 Auto-Crop</div>
            <p className="text-[10px] font-mono text-slate-400 mt-1">
              Keystroke delays (25-50ms), randomized mouse sweeps, and native Chrome fingerprint prevent bot flags.
            </p>
          </div>

          <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between">
            <span className="text-[11px] font-mono text-slate-300">Headless Background Mode:</span>
            <button
              onClick={() => setUseHeadless(!useHeadless)}
              className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold cursor-pointer transition-all ${
                useHeadless
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-400'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {useHeadless ? 'HEADLESS (SILENT)' : 'VISIBLE BROWSER'}
            </button>
          </div>
        </div>

        {/* Daily Target & Peak Viral Times */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-pink-500/25 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
              <span className="flex items-center gap-1.5">
                <Flame className="w-3.5 h-3.5 text-pink-400" />
                DAILY REELS GOAL
              </span>
              <span className="text-[10px] font-mono text-pink-400 font-bold">5 - 10 REELS / DAY</span>
            </div>
            <div className="text-sm font-bold text-slate-200">Optimal Instagram Peak Times</div>
            <div className="grid grid-cols-2 gap-1.5 mt-2 text-[10px] font-mono text-slate-300">
              <div className="p-1 rounded bg-slate-900 border border-slate-800 text-center">☀️ 9:00 AM (Commute)</div>
              <div className="p-1 rounded bg-slate-900 border border-slate-800 text-center">🥪 12:30 PM (Lunch)</div>
              <div className="p-1 rounded bg-slate-900 border border-slate-800 text-center">🌆 5:30 PM (Evening)</div>
              <div className="p-1 rounded bg-slate-900 border border-slate-800 text-center">🌙 8:30 PM (Prime)</div>
            </div>
          </div>
          <div className="text-[10px] font-mono text-cyan-400/80 mt-2 text-right">
            Interval: Every 2-3 hours for algorithmic compounding
          </div>
        </div>
      </div>

      {/* Main Dispatch Station */}
      <div className="p-6 rounded-2xl bg-slate-950/80 border border-pink-500/25 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Upload className="w-4 h-4 text-pink-400" />
            <span>Publish Reel to Instagram</span>
          </h2>

          {/* Source Tabs: Factory Clips vs Studio Exports */}
          <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
            <button
              onClick={() => setSourceMode('clips')}
              className={`px-3 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
                sourceMode === 'clips'
                  ? 'bg-pink-500/20 text-pink-300 border border-pink-500/40 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Film className="w-3.5 h-3.5" />
              <span>Reels Factory Clips ({clips.length})</span>
            </button>
            <button
              onClick={() => setSourceMode('local')}
              className={`px-3 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
                sourceMode === 'local'
                  ? 'bg-pink-500/20 text-pink-300 border border-pink-500/40 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FolderOpen className="w-3.5 h-3.5" />
              <span>Studio Exports & Local ({localVideos.length})</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Media Selector & Caption Editor (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            {/* Video Picker */}
            {sourceMode === 'clips' ? (
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">
                  SELECT REEL FROM FACTORY LIBRARY
                </label>
                <select
                  value={selectedClipId}
                  onChange={(e) => setSelectedClipId(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-pink-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-pink-400 cursor-pointer"
                >
                  {clips.map((c) => (
                    <option key={c.id} value={c.id}>
                      [{c.total_score} pts] {c.title} ({c.duration}s) {c.published_instagram ? '• (ALREADY POSTED)' : ''}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">
                  SELECT EXPORTED VIDEO FILE OR LOCAL DISK MEDIA
                </label>
                <select
                  value={selectedLocalPath}
                  onChange={(e) => setSelectedLocalPath(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-pink-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-pink-400 cursor-pointer"
                >
                  {localVideos.map((v) => (
                    <option key={v.path} value={v.path}>
                      {v.name} ({v.size_mb} MB) - {v.folder}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Caption & Details Editor */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-mono">
                <label className="text-slate-300 font-bold flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-pink-400" />
                  <span>Instagram Caption & Hooks</span>
                </label>
                <span className={`text-[10px] ${caption.length > 2000 ? 'text-amber-400' : 'text-slate-400'}`}>
                  {caption.length} / 2200 chars
                </span>
              </div>
              <textarea
                rows={5}
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                placeholder="Write an engaging Instagram caption with hook, value points, and call to action..."
                className="w-full p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 font-mono focus:outline-none focus:border-pink-400 resize-none leading-relaxed"
              />
            </div>

            {/* 1-Click Viral Hashtags */}
            <div className="space-y-1.5">
              <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                <Hash className="w-3 h-3 text-pink-400" />
                <span>1-Click Viral Hashtag Pills:</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {suggestedHashtags.map((tag) => {
                  const isActive = caption.includes(tag);
                  return (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => toggleHashtag(tag)}
                      className={`px-2 py-0.5 rounded-lg text-[10px] font-mono cursor-pointer transition-all ${
                        isActive
                          ? 'bg-pink-500/30 text-pink-300 border border-pink-400 font-bold'
                          : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                      }`}
                    >
                      {tag}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Dispatch Action */}
            <button
              onClick={handlePublish}
              disabled={isPublishing || !isConnected}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-pink-500 via-rose-500 to-purple-600 hover:from-pink-400 hover:to-purple-500 text-white font-bold text-xs uppercase font-mono tracking-wider flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-pink-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all mt-2"
            >
              <Camera className="w-4 h-4" />
              <span>
                {isPublishing
                  ? 'AUTOMATING INSTAGRAM UPLOAD...'
                  : !isConnected
                  ? 'CONNECT INSTAGRAM TO PUBLISH'
                  : 'DISPATCH REEL TO INSTAGRAM'}
              </span>
            </button>

            {/* Live Progress or Result Notice */}
            {publishProgress && (
              <div
                className={`p-3 rounded-xl border text-xs font-mono flex items-center gap-2.5 transition-all ${
                  publishResult?.success
                    ? 'bg-emerald-950/80 border-emerald-500/60 text-emerald-300'
                    : isPublishing
                    ? 'bg-pink-950/60 border-pink-500/60 text-pink-300 animate-pulse'
                    : 'bg-slate-900 border-slate-700 text-slate-300'
                }`}
              >
                {publishResult?.success ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <Sparkles className="w-4 h-4 text-pink-400 shrink-0 animate-spin" />
                )}
                <span className="leading-snug">{publishProgress}</span>
              </div>
            )}
          </div>

          {/* Right Column: 9:16 Instagram Reel Mockup & Preview (5 cols) */}
          <div className="lg:col-span-5 flex flex-col items-center">
            <div className="text-xs font-mono text-slate-400 mb-2 flex items-center gap-1.5 self-start">
              <Smartphone className="w-3.5 h-3.5 text-pink-400" />
              <span>INSTAGRAM REEL LIVE MOCKUP</span>
            </div>

            {/* Smartphone 9:16 Bezel */}
            <div className="w-[260px] sm:w-[280px] h-[520px] rounded-[36px] bg-black border-4 border-slate-800 shadow-2xl relative overflow-hidden flex flex-col justify-between p-2">
              {/* Dynamic Island / Notch */}
              <div className="absolute top-3 left-1/2 -translate-x-1/2 w-24 h-4 bg-slate-900 rounded-full z-30" />

              {/* Video Player or Fallback */}
              {activeVideoUrl ? (
                <video
                  src={activeVideoUrl}
                  controls
                  playsInline
                  className="absolute inset-0 w-full h-full object-cover z-10"
                />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center p-4 text-center z-10 bg-slate-950">
                  <Film className="w-12 h-12 text-slate-700 mb-2" />
                  <span className="text-xs font-mono text-slate-500">Select video above to preview Reel</span>
                </div>
              )}

              {/* Reel Overlay UI Elements */}
              <div className="relative z-20 flex justify-between items-center px-2 pt-5">
                <span className="text-white text-xs font-bold font-mono tracking-wider drop-shadow-md">Reels</span>
                <Camera className="w-4 h-4 text-white drop-shadow-md" />
              </div>

              {/* Bottom Caption & Engagement Sidebar */}
              <div className="relative z-20 flex items-end justify-between p-2 pb-4 bg-gradient-to-t from-black/85 via-black/40 to-transparent">
                {/* Account & Caption */}
                <div className="space-y-1.5 max-w-[190px]">
                  <div className="flex items-center gap-1.5">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-pink-500 to-amber-500 flex items-center justify-center text-[10px] font-bold text-white shadow">
                      IG
                    </div>
                    <span className="text-white text-xs font-bold drop-shadow">
                      {browserStatus?.username || 'your_channel'}
                    </span>
                  </div>
                  <p className="text-white text-[10px] line-clamp-3 drop-shadow font-sans leading-tight">
                    {caption || 'No caption yet...'}
                  </p>
                </div>

                {/* Right Side Reel Icons */}
                <div className="flex flex-col items-center gap-3 text-white">
                  <div className="flex flex-col items-center text-[9px] drop-shadow">
                    <span className="text-base">❤️</span>
                    <span>14.2k</span>
                  </div>
                  <div className="flex flex-col items-center text-[9px] drop-shadow">
                    <span className="text-base">💬</span>
                    <span>342</span>
                  </div>
                  <div className="flex flex-col items-center text-[9px] drop-shadow">
                    <span className="text-base">🚀</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
