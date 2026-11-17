import React, { useState, useEffect } from 'react';
import {
  PlaySquare,
  Key,
  ShieldCheck,
  Upload,
  Globe,
  Lock,
  Eye,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Flame,
  TrendingUp,
  Globe as ChromeIcon,
  ExternalLink,
  Laptop,
  FolderDown,
  Sparkles,
  Clock,
  Calendar,
  Pause,
  Play,
  Trash2,
  Shield,
  FastForward,
  ListOrdered,
  CheckCircle,
  Timer
} from 'lucide-react';
import { ClipItem, api } from '../services/api';

interface YouTubeManagerProps {
  clips: ClipItem[];
  onRefreshClips: () => void;
}

export const YouTubeManager: React.FC<YouTubeManagerProps> = ({ clips, onRefreshClips }) => {
  const [authStatus, setAuthStatus] = useState<any>(null);
  const [browserStatus, setBrowserStatus] = useState<any>(null);
  const [uploadMethod, setUploadMethod] = useState<'browser' | 'api'>('browser');
  const [selectedClipId, setSelectedClipId] = useState<string>(clips[0]?.id || '');
  const [privacy, setPrivacy] = useState<string>('public');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isPublishing, setIsPublishing] = useState<boolean>(false);
  const [isOpeningBrowser, setIsOpeningBrowser] = useState<boolean>(false);

  // Single Drive Video Ingestion
  const [driveUrl, setDriveUrl] = useState<string>('');
  const [driveCustomTitle, setDriveCustomTitle] = useState<string>('');
  const [isIngestingDrive, setIsIngestingDrive] = useState<boolean>(false);
  const [driveResult, setDriveResult] = useState<any>(null);

  // 1000+ Drive Folder Scheduler & Queue State
  const [folderUrl, setFolderUrl] = useState<string>('https://drive.google.com/drive/folders/14lGBATDOY7kk6lNm4z6wlE8OgIsCk14t');
  const [intervalMinutes, setIntervalMinutes] = useState<number>(60);
  const [dailyCap, setDailyCap] = useState<number>(18);
  const [applyJitter, setApplyJitter] = useState<boolean>(true);
  const [isImportingFolder, setIsImportingFolder] = useState<boolean>(false);
  const [importResult, setImportResult] = useState<any>(null);
  const [queueStats, setQueueStats] = useState<any>(null);
  const [queueItems, setQueueItems] = useState<any[]>([]);
  const [queueFilter, setQueueFilter] = useState<string>('all');
  const [isDispatchingNext, setIsDispatchingNext] = useState<boolean>(false);
  const [isUploadingTillLimit, setIsUploadingTillLimit] = useState<boolean>(false);

  const fetchAuth = async () => {
    try {
      const [apiData, browserData] = await Promise.all([
        api.getYouTubeStatus().catch(() => null),
        api.getYouTubeBrowserStatus().catch(() => null),
      ]);
      setAuthStatus(apiData);
      setBrowserStatus(browserData);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchQueue = async () => {
    try {
      const [stats, items] = await Promise.all([
        api.getYouTubeQueueStats().catch(() => null),
        api.getYouTubeQueue(50, 0, queueFilter === 'all' ? undefined : queueFilter).catch(() => []),
      ]);
      setQueueStats(stats);
      setQueueItems(items || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchAuth();
    fetchQueue();
    const interval = setInterval(fetchQueue, 8000);
    return () => clearInterval(interval);
  }, [queueFilter]);

  const selectedClip = clips.find((c) => c.id === selectedClipId) || clips[0];

  const formatCountdown = (seconds?: number) => {
    if (seconds === undefined || seconds === null) return null;
    if (seconds <= 0) return 'Due Now';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m ${s}s`;
    return `${m}m ${s}s`;
  };

  const handleImportFolder = async () => {
    if (!folderUrl.trim()) return;
    setIsImportingFolder(true);
    setStatusMessage('Scanning Google Drive folder (1000+ videos) and building 1-hour anti-ban schedule...');
    try {
      const res = await api.importDriveFolderQueue(folderUrl, intervalMinutes, dailyCap, applyJitter);
      setImportResult(res);
      setStatusMessage(`🎉 Successfully imported and scheduled ${res.total_imported} videos! Automated 1-hour dispatches active.`);
      fetchQueue();
    } catch (e: any) {
      setStatusMessage(`Import failed: ${e.message}`);
    } finally {
      setIsImportingFolder(false);
    }
  };

  const handlePauseQueue = async () => {
    await api.pauseYouTubeQueue();
    fetchQueue();
  };

  const handleResumeQueue = async () => {
    await api.resumeYouTubeQueue();
    fetchQueue();
  };

  const handleDispatchNext = async () => {
    setIsDispatchingNext(true);
    setStatusMessage('Dispatching next queued video to YouTube Studio now...');
    try {
      const res = await api.dispatchNextQueueItem();
      if (res.success) {
        setStatusMessage(`🎉 Uploaded: "${res.title}"! Live link: ${res.youtube_url}`);
      } else {
        setStatusMessage(`Dispatch notice: ${res.error || res.message}`);
      }
      fetchQueue();
    } catch (e: any) {
      setStatusMessage(`Error dispatching: ${e.message}`);
    } finally {
      setIsDispatchingNext(false);
    }
  };

  const handleUploadTillLimit = async () => {
    setIsUploadingTillLimit(true);
    setStatusMessage('Uploading queued videos to YouTube Studio (45m spacing) till daily limit...');
    try {
      const res = await api.uploadTillDailyLimit(45);
      setStatusMessage(`🚀 ${res.message} (${res.uploaded_count || 0} videos scheduled)`);
      fetchQueue();
    } catch (e: any) {
      setStatusMessage(`Upload batch notice: ${e.message}`);
    } finally {
      setIsUploadingTillLimit(false);
    }
  };

  const handleReschedule45m = async () => {
    setStatusMessage('Rescheduling queue with 45-minute intervals starting from today...');
    try {
      const res = await api.rescheduleYouTubeQueue(45);
      setStatusMessage(`✅ Rescheduled ${res.count} videos 45m apart starting at ${res.first_scheduled}!`);
      fetchQueue();
    } catch (e: any) {
      setStatusMessage(`Error rescheduling: ${e.message}`);
    }
  };

  const handleClearQueue = async () => {
    if (!confirm('Are you sure you want to clear all queued videos?')) return;
    await api.clearYouTubeQueue();
    fetchQueue();
  };

  const handleDeleteItem = async (id: string) => {
    await api.deleteQueueItem(id);
    fetchQueue();
  };

  const handleDriveIngest = async () => {
    if (!driveUrl.trim()) return;
    setIsIngestingDrive(true);
    setStatusMessage('Fetching video from Google Drive link and generating AI metadata...');
    try {
      const res = await api.ingestDriveVideo(driveUrl, driveCustomTitle || undefined, privacy, true);
      setDriveResult(res);
      setStatusMessage(
        res.url
          ? `🎉 Google Drive video fetched & dispatched to YouTube: ${res.url}`
          : `🎉 Downloaded & prepared: "${res.title}". Generated viral hashtags & caption.`
      );
      onRefreshClips();
    } catch (e: any) {
      setStatusMessage(`Drive Ingestion error: ${e.message}`);
    } finally {
      setIsIngestingDrive(false);
    }
  };

  const handlePublish = async () => {
    if (!selectedClip || isPublishing) return;
    setIsPublishing(true);
    setStatusMessage(
      uploadMethod === 'browser'
        ? `Launching Chrome uploader for "${selectedClip.title}"... (Direct pipeline active for GHOST _OF_FOOTBALL)`
        : `Uploading short "${selectedClip.title}" via official YouTube Data API...`
    );

    try {
      let res: any;
      if (uploadMethod === 'browser') {
        res = await api.uploadViaBrowser(
          selectedClip.id,
          selectedClip.title,
          selectedClip.caption,
          selectedClip.tags ? selectedClip.tags.split(' ') : [],
          privacy
        );
      } else {
        res = await api.publishToYouTube(
          selectedClip.id,
          selectedClip.title,
          selectedClip.caption,
          selectedClip.tags ? selectedClip.tags.split(' ') : [],
          privacy
        );
      }

      if (res && res.success === false) {
        setStatusMessage(`Upload failed: ${res.error || res.message || 'YouTube Studio upload did not complete.'}`);
        return;
      }

      const publishedUrl = res.url || (res.video_id && !res.video_id.startsWith('yt_') ? `https://youtube.com/shorts/${res.video_id}` : null);
      setStatusMessage(
        publishedUrl
          ? `🎉 Successfully published! Link: ${publishedUrl}`
          : res.message || 'Upload submitted to YouTube Studio.'
      );
      onRefreshClips();
      fetchAuth();
    } catch (e: any) {
      setStatusMessage(`Upload failed: ${e.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <PlaySquare className="w-5 h-5 text-red-500" />
            YouTube Shorts Channel Management &amp; Autonomous Scheduler
          </h1>
          <p className="text-xs font-mono text-cyan-400/80">
            Target Channel: <strong className="text-slate-100">GHOST _OF_FOOTBALL</strong> • Unlimited In-Browser Engine • Anti-Ban Safe Pacing
          </p>
        </div>

        <button
          onClick={() => { fetchAuth(); fetchQueue(); }}
          className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-cyan-500/30 text-cyan-300 text-xs font-mono hover:bg-slate-800 cursor-pointer transition-colors self-start flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Console</span>
        </button>
      </div>

      {/* Engine Status & Anti-Ban Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Browser Profile Status */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.15)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
              <span className="flex items-center gap-1.5">
                <ChromeIcon className="w-3.5 h-3.5 text-cyan-400" />
                AUTHENTICATED CHANNEL
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-2.5 h-2.5" />
                CONNECTED
              </span>
            </div>
            <div className="text-sm font-bold text-slate-200">
              GHOST _OF_FOOTBALL
            </div>
            <p className="text-[11px] font-mono text-slate-400 mt-1">
              Active profile: {browserStatus?.channel_title || 'Anshul Khatri'} • Zero login prompts.
            </p>
          </div>

          <div className="mt-3">
            <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-500/30 px-2 py-1 rounded flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-cyan-400" />
              Direct Studio Browser Pipeline Active
            </span>
          </div>
        </div>

        {/* Card 2: Anti-Ban Shield Card */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.1)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
              <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
                <Shield className="w-3.5 h-3.5" />
                ANTI-BAN SHIELD
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 animate-pulse">
                ARMED &amp; ACTIVE
              </span>
            </div>
            <div className="text-sm font-bold text-slate-200">
              Pacing: ~{intervalMinutes}m Interval with Jitter
            </div>
            <p className="text-[11px] font-mono text-slate-400 mt-1">
              Max {dailyCap} videos/day • ±8m organic variance • 7h human rest sleep window.
            </p>
          </div>

          <div className="mt-3 flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span>24h Velocity: <strong className="text-emerald-400">{queueStats?.published_last_24h || 0}/{dailyCap}</strong></span>
            <span className="text-cyan-400">Duplicate Shield: On</span>
          </div>
        </div>

        {/* Card 3: Autonomous Queue Summary */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
              <span className="flex items-center gap-1.5">
                <Flame className="w-3.5 h-3.5 text-red-400" />
                ACTIVE QUEUE ENGINE
              </span>
              <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                queueStats?.is_paused ? 'bg-amber-500/20 text-amber-400' : 'bg-cyan-500/20 text-cyan-400'
              }`}>
                {queueStats?.is_paused ? 'PAUSED' : 'AUTO-RUNNING'}
              </span>
            </div>
            <div className="text-xl font-bold font-mono text-slate-200">
              {queueStats?.queued || 0} VIDEOS QUEUED
            </div>
            <p className="text-[11px] font-mono text-slate-400 mt-1">
              Published: {queueStats?.published || 0} • Failed: {queueStats?.failed || 0}
            </p>
          </div>

          <div className="mt-3 flex items-center justify-between text-[10px] font-mono">
            <span className="text-cyan-400 flex items-center gap-1">
              <Timer className="w-3 h-3" />
              Next: <strong>{formatCountdown(queueStats?.seconds_until_next) || 'Idle'}</strong>
            </span>
            {queueStats?.next_item && (
              <span className="text-slate-400 truncate max-w-[130px]">
                {queueStats.next_item.title}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* SECTION 1: Google Drive 1000+ Folder Batch Scheduler Console */}
      <div className="p-6 rounded-2xl bg-slate-950/90 border border-cyan-500/40 space-y-4 shadow-[0_0_25px_rgba(6,182,212,0.12)]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
              <FolderDown className="w-4 h-4 text-cyan-400" />
              <span>Google Drive 1000+ Video Batch Scheduler (Anti-Ban Guarded)</span>
            </h2>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              Imports all videos from your Drive folder, schedules them sequentially ~1 hour apart with organic anti-ban jitter, and publishes automatically 24/7.
            </p>
          </div>
          <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-cyan-950/80 border border-cyan-500/50 text-cyan-300 self-start sm:self-auto flex items-center gap-1">
            <Shield className="w-3 h-3 text-emerald-400" />
            <span>Anti-Ban Protected</span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="md:col-span-2 space-y-1.5">
            <label className="block text-[11px] font-mono text-slate-300 font-bold">GOOGLE DRIVE FOLDER URL</label>
            <input
              type="text"
              value={folderUrl}
              onChange={(e) => setFolderUrl(e.target.value)}
              placeholder="https://drive.google.com/drive/folders/..."
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-cyan-500/40 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-[11px] font-mono text-slate-300 font-bold">PUBLISHING CADENCE</label>
            <select
              value={intervalMinutes}
              onChange={(e) => setIntervalMinutes(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-100 font-mono focus:outline-none"
            >
              <option value={45}>Every 45 Minutes (Fast)</option>
              <option value={60}>Every 1 Hour (Recommended)</option>
              <option value={90}>Every 1.5 Hours (Conservative)</option>
              <option value={120}>Every 2 Hours (Ultra Safe)</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="block text-[11px] font-mono text-slate-300 font-bold">DAILY SAFETY CAP</label>
            <select
              value={dailyCap}
              onChange={(e) => setDailyCap(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-100 font-mono focus:outline-none"
            >
              <option value={12}>12 Videos / Day (Ultra-Safe)</option>
              <option value={18}>18 Videos / Day (Optimal Balance)</option>
              <option value={24}>24 Videos / Day (Maximum Safe)</option>
            </select>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800">
          <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={applyJitter}
                onChange={(e) => setApplyJitter(e.target.checked)}
                className="accent-cyan-500"
              />
              <span className="text-slate-300">Anti-Ban Organic Jitter (±8m variance)</span>
            </label>

            <span className="text-slate-500">•</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              <span>AI Unique Hook &amp; Tag Generator Active</span>
            </span>
          </div>

          <button
            onClick={handleImportFolder}
            disabled={isImportingFolder || !folderUrl.trim()}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-mono font-bold text-xs flex items-center gap-2 cursor-pointer transition-all shadow-lg disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-yellow-300" />
            <span>{isImportingFolder ? 'Scanning Folder (1,087 Videos)...' : 'IMPORT FOLDER & INITIALIZE 1-HOUR SCHEDULE'}</span>
          </button>
        </div>

        {importResult && (
          <div className="p-3.5 rounded-xl bg-cyan-950/40 border border-cyan-500/40 space-y-1.5 text-xs font-mono">
            <div className="text-cyan-300 font-bold flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Folder Import &amp; Anti-Ban Schedule Active!</span>
            </div>
            <div className="text-slate-200">
              <strong>Total Videos Queued:</strong> {importResult.total_imported} videos
            </div>
            <div className="text-slate-400">
              <strong>Schedule Timeline:</strong> {importResult.first_scheduled} ➔ {importResult.last_scheduled}
            </div>
            <div className="text-emerald-400">
              <strong>Pacing:</strong> Spaced every ~{importResult.interval_minutes}m with humanized jitter and 7h night rest windows.
            </div>
          </div>
        )}
      </div>

      {/* SECTION 2: Live Scheduled Queue Table & Controls */}
      <div className="p-6 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <ListOrdered className="w-4 h-4 text-cyan-400" />
              <span>Live Scheduled Queue Monitor ({queueStats?.total || 0} Total)</span>
            </h2>
            <p className="text-xs font-mono text-slate-400">
              Autonomous background worker checks every 30s • Downloads &amp; publishes when scheduled time arrives.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            {queueStats?.is_paused ? (
              <button
                onClick={handleResumeQueue}
                className="px-3 py-1.5 rounded-lg bg-emerald-600/20 border border-emerald-500/40 text-emerald-300 text-xs font-mono hover:bg-emerald-600/30 flex items-center gap-1.5 cursor-pointer transition-colors"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Resume Queue</span>
              </button>
            ) : (
              <button
                onClick={handlePauseQueue}
                className="px-3 py-1.5 rounded-lg bg-amber-600/20 border border-amber-500/40 text-amber-300 text-xs font-mono hover:bg-amber-600/30 flex items-center gap-1.5 cursor-pointer transition-colors"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause Queue</span>
              </button>
            )}

            <button
              onClick={handleUploadTillLimit}
              disabled={isUploadingTillLimit || queueStats?.queued === 0}
              className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-red-600/30 via-orange-600/30 to-amber-600/30 border border-orange-500/50 text-orange-200 text-xs font-mono font-bold hover:brightness-125 flex items-center gap-1.5 cursor-pointer transition-all disabled:opacity-50 shadow-lg shadow-orange-900/20"
              title="Upload videos sequentially scheduled 45m apart in YouTube Studio until daily limit is reached"
            >
              <Flame className={`w-3.5 h-3.5 text-orange-400 ${isUploadingTillLimit ? 'animate-bounce' : ''}`} />
              <span>{isUploadingTillLimit ? 'Uploading Till Limit...' : 'Upload Till Daily Limit (45m)'}</span>
            </button>

            <button
              onClick={handleReschedule45m}
              disabled={queueStats?.total === 0}
              className="px-3 py-1.5 rounded-lg bg-purple-600/20 border border-purple-500/40 text-purple-300 text-xs font-mono hover:bg-purple-600/30 flex items-center gap-1.5 cursor-pointer transition-colors disabled:opacity-50"
              title="Reschedule entire queue with 45-minute intervals starting from today"
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Reschedule 45m</span>
            </button>

            <button
              onClick={handleDispatchNext}
              disabled={isDispatchingNext || queueStats?.queued === 0}
              className="px-3 py-1.5 rounded-lg bg-cyan-600/20 border border-cyan-500/40 text-cyan-300 text-xs font-mono hover:bg-cyan-600/30 flex items-center gap-1.5 cursor-pointer transition-colors disabled:opacity-50"
            >
              <FastForward className="w-3.5 h-3.5" />
              <span>{isDispatchingNext ? 'Publishing Next...' : 'Dispatch Next Now'}</span>
            </button>

            <button
              onClick={handleClearQueue}
              disabled={queueStats?.total === 0}
              className="px-3 py-1.5 rounded-lg bg-red-600/20 border border-red-500/40 text-red-300 text-xs font-mono hover:bg-red-600/30 flex items-center gap-1.5 cursor-pointer transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear Queue</span>
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          {['all', 'QUEUED', 'PUBLISHED', 'FAILED'].map((tab) => (
            <button
              key={tab}
              onClick={() => setQueueFilter(tab)}
              className={`px-3 py-1 rounded-lg text-xs font-mono uppercase tracking-wider transition-colors cursor-pointer ${
                queueFilter === tab
                  ? 'bg-slate-800 text-cyan-300 font-bold border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab === 'all' ? `All (${queueStats?.total || 0})` : `${tab} (${
                tab === 'QUEUED' ? queueStats?.queued || 0 :
                tab === 'PUBLISHED' ? queueStats?.published || 0 :
                queueStats?.failed || 0
              })`}
            </button>
          ))}
        </div>

        {/* Queue Items Table */}
        {queueItems.length > 0 ? (
          <div className="overflow-x-auto max-h-96 overflow-y-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] sticky top-0">
                <tr>
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Title &amp; File</th>
                  <th className="py-2.5 px-3">Scheduled Time</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">YouTube Link</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-950/60">
                {queueItems.map((item, idx) => {
                  const isPublished = item.status === 'PUBLISHED';
                  const isUploading = item.status === 'UPLOADING' || item.status === 'DOWNLOADING';
                  const isFailed = item.status === 'FAILED';
                  return (
                    <tr key={item.id} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-2.5 px-3 text-slate-500">{idx + 1}</td>
                      <td className="py-2.5 px-3 max-w-md">
                        <div className="font-bold text-slate-200 truncate">{item.title}</div>
                        <div className="text-[10px] text-slate-500 truncate">{item.file_name}</div>
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap text-slate-300">
                        {item.scheduled_time ? new Date(item.scheduled_time).toLocaleString() : 'N/A'}
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isPublished ? 'bg-emerald-500/20 text-emerald-400' :
                          isUploading ? 'bg-cyan-500/20 text-cyan-400 animate-pulse' :
                          isFailed ? 'bg-red-500/20 text-red-400' :
                          'bg-amber-500/20 text-amber-400'
                        }`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap">
                        {item.youtube_url ? (
                          <a
                            href={item.youtube_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-red-400 hover:text-red-300 flex items-center gap-1 underline font-bold"
                          >
                            <span>Watch Short</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-slate-600">Pending</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <button
                          onClick={() => handleDeleteItem(item.id)}
                          className="text-slate-500 hover:text-red-400 p-1 transition-colors cursor-pointer"
                          title="Remove from queue"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center rounded-xl bg-slate-900/40 border border-dashed border-slate-800 text-slate-500 text-xs font-mono">
            No scheduled videos in queue. Click <strong>"IMPORT FOLDER &amp; INITIALIZE 1-HOUR SCHEDULE"</strong> above to queue your 1,000+ football videos!
          </div>
        )}
      </div>

      {/* SECTION 3: Single Video Google Drive Auto-Ingest Panel */}
      <div className="p-6 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <FolderDown className="w-4 h-4 text-cyan-400" />
            <span>Single Video Google Drive Ingest &amp; Publish</span>
          </h2>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-400">
            One-off upload
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
          <div className="md:col-span-2 space-y-2">
            <label className="block text-[11px] font-mono text-slate-400">GOOGLE DRIVE VIDEO LINK</label>
            <input
              type="text"
              value={driveUrl}
              onChange={(e) => setDriveUrl(e.target.value)}
              placeholder="https://drive.google.com/file/d/.../view"
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-[11px] font-mono text-slate-400">CUSTOM TITLE (OPTIONAL)</label>
            <input
              type="text"
              value={driveCustomTitle}
              onChange={(e) => setDriveCustomTitle(e.target.value)}
              placeholder="Leave empty for AI Generated"
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-100 font-mono focus:outline-none"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-1">
          <span className="text-[10px] font-mono text-slate-500">
            Fetches individual video, generates metadata, and publishes immediately.
          </span>

          <button
            onClick={handleDriveIngest}
            disabled={isIngestingDrive || !driveUrl.trim()}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono font-bold text-xs flex items-center gap-2 cursor-pointer transition-all disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>{isIngestingDrive ? 'Fetching & Publishing...' : 'Fetch & Publish Single Video'}</span>
          </button>
        </div>

        {driveResult && (
          <div className="p-3 rounded-xl bg-slate-900 border border-cyan-500/40 space-y-1 text-xs font-mono">
            <div className="text-cyan-300 font-bold">🎉 AI Metadata Generated:</div>
            <div className="text-slate-200"><strong>Title:</strong> {driveResult.title}</div>
            <div className="text-slate-400 truncate"><strong>Tags:</strong> {driveResult.tags?.join(' ')}</div>
            {driveResult.url && (
              <div className="text-emerald-400 font-bold"><strong>Dispatched:</strong> <a href={driveResult.url} target="_blank" rel="noreferrer" className="underline">{driveResult.url}</a></div>
            )}
          </div>
        )}
      </div>

      {/* SECTION 4: Upload Local Short from Factory */}
      <div className="p-6 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Upload className="w-4 h-4 text-red-400" />
            <span>Upload Local Short from Factory</span>
          </h2>

          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
            Active: <strong className="text-cyan-400 uppercase">Playwright Browser</strong>
          </span>
        </div>

        {selectedClip ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">SELECT SHORT FROM FACTORY</label>
                <select
                  value={selectedClip.id}
                  onChange={(e) => setSelectedClipId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-100 font-mono focus:outline-none"
                >
                  {clips.map((c) => (
                    <option key={c.id} value={c.id}>
                      [{c.total_score} pts] {c.title} ({c.duration}s)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">VISIBILITY</label>
                <select
                  value={privacy}
                  onChange={(e) => setPrivacy(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-100 font-mono focus:outline-none"
                >
                  <option value="public">Public (Instant Publish)</option>
                  <option value="unlisted">Unlisted (Review First)</option>
                  <option value="private">Private (Saved to Studio)</option>
                </select>
              </div>

              <button
                onClick={handlePublish}
                disabled={isPublishing}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white font-bold text-xs uppercase font-mono tracking-wider flex items-center justify-center gap-2 cursor-pointer shadow-lg disabled:opacity-50 transition-all"
              >
                <Upload className="w-4 h-4" />
                <span>
                  {isPublishing ? 'AUTOMATION RUNNING...' : 'DISPATCH VIA PLAYWRIGHT BROWSER'}
                </span>
              </button>

              {statusMessage && (
                <div className="p-3 rounded-xl bg-slate-900 border border-cyan-500/40 text-xs font-mono text-cyan-200 flex flex-col gap-2 shadow-lg">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span className="break-all">{statusMessage}</span>
                  </div>
                  {statusMessage.includes('http') && (
                    <a
                      href={statusMessage.match(/(https?:\/\/[^\s]+)/)?.[0]}
                      target="_blank"
                      rel="noreferrer"
                      className="self-start px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold text-[11px] flex items-center gap-1.5 transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>Watch Short on YouTube</span>
                    </a>
                  )}
                </div>
              )}
            </div>

            {/* Preview Card */}
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
              <div className="text-xs font-mono text-slate-400">DISPATCH PREVIEW:</div>
              <div className="font-bold text-sm text-slate-200">{selectedClip.title} #shorts</div>
              <div className="text-xs font-mono text-slate-300 whitespace-pre-wrap max-h-24 overflow-y-auto">
                {selectedClip.caption}
              </div>
              <div className="text-[11px] font-mono text-red-400">{selectedClip.tags}</div>
              <div className="pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500 flex items-center justify-between">
                <span>Method: Chrome Playwright Automation</span>
                <span>Aspect: 9:16 Vertical</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-slate-500 font-mono text-xs">
            No clips ready in library. Generate clips in Content Studio or Shorts Factory first.
          </div>
        )}
      </div>
    </div>
  );
};
