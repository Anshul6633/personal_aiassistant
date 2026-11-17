import React, { useState } from 'react';
import {
  Camera,
  Flame,
  Sparkles,
  Play,
  Copy,
  Check,
  Download,
  Share2,
  Clock,
  Layers,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { ClipItem, api } from '../services/api';

interface ReelsFactoryProps {
  clips: ClipItem[];
  onRefreshClips: () => void;
}

export const ReelsFactory: React.FC<ReelsFactoryProps> = ({ clips, onRefreshClips }) => {
  const [sourcePath, setSourcePath] = useState('jarvis/tests/sample_podcast.mp4');
  const [targetCount, setTargetCount] = useState(5);
  const [targetDuration, setTargetDuration] = useState(45);
  const [isRendering, setIsRendering] = useState(false);
  const [selectedClip, setSelectedClip] = useState<ClipItem | null>(clips[0] || null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  React.useEffect(() => {
    if (!selectedClip && clips.length > 0) {
      setSelectedClip(clips[0]);
    }
  }, [clips, selectedClip]);

  const showNotice = (msg: string) => {
    setActionNotice(msg);
    setTimeout(() => setActionNotice(null), 3000);
  };

  const handleStartReelsBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourcePath.trim() || isRendering) return;

    setIsRendering(true);
    showNotice(`Generating batch of ${targetCount} Instagram Reels (9:16)...`);

    try {
      await api.generateClips(sourcePath, targetCount, targetDuration);
      setTimeout(() => {
        onRefreshClips();
        setIsRendering(false);
        showNotice('Reels generated and ready in factory!');
      }, 5000);
    } catch (e: any) {
      setIsRendering(false);
      showNotice(`Error: ${e.message}`);
    }
  };

  const handlePublishReel = async (clip: ClipItem) => {
    try {
      const res = await api.publishToInstagram(clip.id, clip.caption);
      showNotice(res.message || `Queued Reel "${clip.title}" for publishing!`);
      onRefreshClips();
    } catch (e: any) {
      showNotice(`Instagram error: ${e.message}`);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Camera className="w-5 h-5 text-pink-400" />
            Instagram Reels Autonomous Factory
          </h1>
          <p className="text-xs font-mono text-cyan-400/80">
            9:16 Vertical Reframing • 30–50 Daily Batch Scaling • Audio Sync & Captions
          </p>
        </div>

        <button
          onClick={onRefreshClips}
          className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-cyan-500/30 text-cyan-300 text-xs font-mono hover:bg-slate-800 cursor-pointer transition-colors self-start"
        >
          Refresh Reels ({clips.length})
        </button>
      </div>

      {/* Production Trigger Console */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-pink-500/30 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="text-xs font-bold text-pink-300 uppercase tracking-wider flex items-center gap-2">
            <Flame className="w-4 h-4 text-pink-400" />
            Produce Instagram Reels Batch
          </div>
          <span className="text-[11px] font-mono text-slate-400">Target: 30-50 Daily Output</span>
        </div>

        <form onSubmit={handleStartReelsBatch} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div className="md:col-span-2">
            <label className="block text-xs font-mono text-slate-400 mb-1">
              SOURCE VIDEO (PODCAST / INTERVIEW)
            </label>
            <input
              type="text"
              value={sourcePath}
              onChange={(e) => setSourcePath(e.target.value)}
              placeholder="e.g. jarvis/tests/sample_podcast.mp4"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-pink-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-pink-400"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">
              BATCH SIZE
            </label>
            <select
              value={targetCount}
              onChange={(e) => setTargetCount(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-pink-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-pink-400"
            >
              <option value={1}>1 Reel (Test)</option>
              <option value={3}>3 Viral Reels</option>
              <option value={5}>5 Daily Batch Reels</option>
              <option value={10}>10 Batch Reels</option>
              <option value={30}>30 Maximum Daily Target</option>
            </select>
          </div>

          <div>
            <button
              type="submit"
              disabled={isRendering || !sourcePath.trim()}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-400 hover:to-purple-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg disabled:opacity-50 cursor-pointer transition-all flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isRendering ? 'PRODUCING REELS...' : 'GENERATE REELS'}</span>
            </button>
          </div>
        </form>

        {actionNotice && (
          <div className="mt-3 p-2.5 rounded-lg bg-pink-950/80 border border-pink-400 text-xs font-mono text-pink-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{actionNotice}</span>
          </div>
        )}
      </div>

      {/* Main Studio View */}
      {selectedClip && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Reel Vertical Player */}
          <div className="lg:col-span-5 flex flex-col items-center">
            <div className="w-full max-w-[280px] aspect-[9/16] rounded-2xl overflow-hidden bg-slate-900 border border-pink-500/40 shadow-2xl relative">
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
              Aspect 9:16 • {selectedClip.duration}s • 1080x1920
            </div>
          </div>

          {/* Reel Details & Publishing */}
          <div className="lg:col-span-7 space-y-4">
            <div className="p-6 rounded-2xl bg-slate-950/80 border border-pink-500/25 space-y-4">
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 rounded-full bg-pink-500/20 text-pink-300 border border-pink-500/40 text-xs font-mono font-bold">
                  REEL SCORE {selectedClip.total_score}/100
                </span>
                <span className="text-xs font-mono text-slate-400">ID: {selectedClip.id}</span>
              </div>

              <h2 className="text-lg font-bold text-slate-100">{selectedClip.title}</h2>
              <p className="text-xs text-slate-300 font-mono">{selectedClip.summary}</p>

              {/* Instagram Caption & Hashtags */}
              <div className="space-y-2">
                <label className="block text-xs font-mono text-slate-400">INSTAGRAM CAPTION</label>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 font-mono whitespace-pre-wrap">
                  {selectedClip.caption}
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-mono text-slate-400">OPTIMIZED REELS HASHTAGS (30 LIMIT)</label>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs text-pink-300 font-mono">
                  {selectedClip.tags}
                </div>
              </div>

              {/* Publish / Download Buttons */}
              <div className="flex flex-wrap gap-3 pt-2">
                <button
                  onClick={() => handlePublishReel(selectedClip)}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-400 hover:to-purple-500 text-white font-bold text-xs uppercase font-mono tracking-wider flex items-center gap-2 cursor-pointer shadow-lg transition-all"
                >
                  <Camera className="w-4 h-4" />
                  <span>Publish to Instagram Reels</span>
                </button>

                <a
                  href={selectedClip.video_url}
                  download
                  className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono flex items-center gap-2 cursor-pointer transition-colors"
                >
                  <Download className="w-4 h-4 text-pink-400" />
                  <span>Download MP4</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reel Gallery */}
      <div className="pt-4">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Layers className="w-4 h-4 text-pink-400" />
          Ready Instagram Reels ({clips.length})
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
          {clips.map((c) => (
            <div
              key={c.id}
              onClick={() => setSelectedClip(c)}
              className={`cursor-pointer rounded-xl overflow-hidden bg-slate-950 border transition-all ${
                selectedClip?.id === c.id
                  ? 'border-pink-500 shadow-lg scale-105'
                  : 'border-slate-800 hover:border-pink-500/50'
              }`}
            >
              <div className="aspect-[9/16] bg-slate-900 relative">
                {c.thumb_url && <img src={c.thumb_url} alt={c.title} className="w-full h-full object-cover" />}
                <div className="absolute top-1 right-1 px-1.5 py-0.5 rounded bg-slate-950/80 text-[9px] font-mono text-pink-300 font-bold">
                  {c.total_score}
                </div>
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
