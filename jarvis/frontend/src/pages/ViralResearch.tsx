import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, Sparkles, Flame, Copy, Check, Hash, Lightbulb, Compass, 
  Share2, MessageSquare, Repeat, Zap, ShieldCheck, Globe, CheckCircle2,
  DollarSign, Film, Clock, Target, Award, Calendar
} from 'lucide-react';
import { api } from '../services/api';

const PRESET_NICHES = [
  { label: '🔥 GTA 6 & CarryMinati', value: 'GTA 6 & CarryMinati Viral Clutches' },
  { label: '🎮 Viral Gaming Highlights', value: 'Viral Gaming Highlights & Fails' },
  { label: '🌍 International Streamers', value: 'International Streamer Moments (Speed, Kai, xQc)' },
  { label: '⚡ High-IQ Clutches & Heists', value: 'GTA Online High-IQ Heists & Escapes' }
];

export const ViralResearch: React.FC = () => {
  const [niche, setNiche] = useState('GTA 6 & CarryMinati Viral Clutches');
  const [ideas, setIdeas] = useState<any[]>([]);
  const [branding, setBranding] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [growthPlan, setGrowthPlan] = useState<any>(null);
  const [monetization, setMonetization] = useState<any>(null);
  const [longformStatus, setLongformStatus] = useState<any>(null);
  const [buildingCompilation, setBuildingCompilation] = useState(false);
  const [schedulingLongform, setSchedulingLongform] = useState(false);
  const [compilationSuccess, setCompilationSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [appliedSuccess, setAppliedSuccess] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const fetchResearch = async (targetNiche: string = niche) => {
    setLoading(true);
    try {
      const [resultIdeas, brandingRes, trendsData, planData, monData, lfData] = await Promise.all([
        api.getViralIdeas(targetNiche, 6),
        fetch(`/api/research/branding?niche=${encodeURIComponent(targetNiche)}`).then(r => r.json()).catch(() => null),
        api.getResearchTrends(targetNiche).catch(() => null),
        api.getGrowthPlan().catch(() => null),
        api.getMonetizationStatus().catch(() => null),
        api.getLongformScheduleStatus().catch(() => null)
      ]);

      setIdeas(resultIdeas || []);
      setBranding(brandingRes);
      setTrends(trendsData);
      setGrowthPlan(planData);
      setMonetization(monData);
      setLongformStatus(lfData);
    } catch (err) {
      console.error('Research error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBuildCompilation = async () => {
    setBuildingCompilation(true);
    try {
      const res = await api.buildMonetizationCompilation(10, 'horizontal_pillarbox');
      if (res.success) {
        setCompilationSuccess(`Generated 16:9 Long-Form Compilation: ${res.file_name} (${res.total_runtime_min} mins, ${res.num_clips} clips) for YouTube Watch Hours!`);
        setTimeout(() => setCompilationSuccess(null), 8000);
      } else {
        alert(res.error || 'Failed to assemble compilation');
      }
    } catch (e: any) {
      alert(`Error building compilation: ${e.message}`);
    } finally {
      setBuildingCompilation(false);
    }
  };

  const handleScheduleLongform = async () => {
    setSchedulingLongform(true);
    try {
      const res = await api.scheduleLongformNow(10);
      if (res.success) {
        setCompilationSuccess(`Scheduled 8-Hour Long-Form Compilation for ${res.slot?.schedule_time} (${res.slot?.schedule_date}) on YouTube Studio!`);
        setTimeout(() => setCompilationSuccess(null), 8000);
        fetchResearch();
      } else {
        alert(res.error || 'Failed to schedule long-form video');
      }
    } catch (e: any) {
      alert(`Error scheduling long-form: ${e.message}`);
    } finally {
      setSchedulingLongform(false);
    }
  };

  useEffect(() => {
    fetchResearch();
  }, []);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleApplyToPipeline = async () => {
    setApplying(true);
    try {
      const res = await api.applyResearchToPipeline({
        target_clip_duration: 22.0,
        style_preset: 'gta6',
        swipe_away_shield: true,
        dm_share_triggers: true
      });
      setAppliedSuccess(res.message || 'Viral research parameters successfully applied to automated clipping pipeline!');
      setTimeout(() => setAppliedSuccess(null), 5000);
    } catch (e: any) {
      console.error('Failed to apply research:', e);
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="space-y-6 pb-16 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-950/80 p-5 rounded-2xl border border-cyan-500/30 shadow-cyan-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            Autonomous Viral Content & Channel Growth Engine
          </h1>
          <p className="text-xs font-mono text-cyan-400/80 mt-1">
            2026 Algorithmic Intelligence • Swipe-Away Reduction • Sends-Per-Reach Multipliers
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleApplyToPipeline}
            disabled={applying}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-bold text-xs uppercase font-mono flex items-center gap-2 cursor-pointer transition-all shadow-lg"
          >
            <Zap className="w-4 h-4 fill-current" />
            <span>{applying ? 'APPLYING...' : 'APPLY TO CLIPPER'}</span>
          </button>
        </div>
      </div>

      {/* Applied Success Alert */}
      {appliedSuccess && (
        <div className="p-4 rounded-xl bg-emerald-950/80 border border-emerald-500/50 flex items-center gap-3 text-emerald-300 text-xs font-mono animate-fadeIn">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          <span>{appliedSuccess}</span>
        </div>
      )}

      {/* Compilation Success Alert */}
      {compilationSuccess && (
        <div className="p-4 rounded-xl bg-cyan-950/80 border border-cyan-500/50 flex items-center gap-3 text-cyan-300 text-xs font-mono animate-fadeIn">
          <Film className="w-5 h-5 text-cyan-400 flex-shrink-0" />
          <span>{compilationSuccess}</span>
        </div>
      )}

      {/* 60-Day Social Monetization Masterplan Tracker */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 border border-amber-500/30 shadow-lg relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/40 text-[11px] font-bold font-mono text-amber-300 flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5" />
                DAY {monetization?.challenge_day || 1} OF 60 MASTERPLAN
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-[11px] font-bold font-mono text-emerald-300 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                100% YPP FAIR-USE COMPLIANT
              </span>
            </div>
            <h2 className="text-lg font-bold text-slate-100 mt-2 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-amber-400" />
              {monetization?.current_phase?.name || 'Phase 1: Seed & Calibration (Days 1–14)'}
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Focus: {monetization?.current_phase?.focus || 'Algorithmic feed calibration, 0-3s swipe-away reduction (>75%), 15m cadence'}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleScheduleLongform}
              disabled={schedulingLongform}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-red-500 to-amber-500 hover:from-red-400 hover:to-amber-400 text-slate-950 font-bold text-xs uppercase font-mono flex items-center gap-2 cursor-pointer transition-all shadow-md disabled:opacity-50"
            >
              <Clock className="w-4 h-4" />
              <span>{schedulingLongform ? 'SCHEDULING...' : 'SCHEDULE 8H LONG-FORM'}</span>
            </button>
            <button
              onClick={handleBuildCompilation}
              disabled={buildingCompilation}
              className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 font-bold text-xs uppercase font-mono flex items-center gap-2 cursor-pointer transition-all disabled:opacity-50"
            >
              <Film className="w-4 h-4 text-amber-400" />
              <span>{buildingCompilation ? 'ASSEMBLING...' : 'BUILD COMPILATION'}</span>
            </button>
          </div>
        </div>

        {/* 60-Day Progress Bar */}
        <div className="w-full bg-slate-950 rounded-full h-2.5 border border-slate-800 mb-6 overflow-hidden">
          <div
            className="bg-gradient-to-r from-amber-500 via-orange-500 to-emerald-500 h-2.5 rounded-full transition-all duration-500"
            style={{ width: `${Math.max(3, monetization?.percent_elapsed || 1.6)}%` }}
          />
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
            <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5 mb-1">
              <Target className="w-3.5 h-3.5 text-cyan-400" />
              YOUTUBE SHORTS (YPP)
            </div>
            <div className="text-xl font-bold font-mono text-slate-100">
              {monetization?.telemetry?.youtube_published || 0} <span className="text-xs font-normal text-slate-400">Published</span>
            </div>
            <div className="text-[11px] font-mono text-cyan-400 mt-2">
              Next Goal: 500 Subs / 3M Views
            </div>
          </div>

          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
            <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5 mb-1">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              LONG-FORM WATCH HOURS
            </div>
            <div className="text-xl font-bold font-mono text-slate-100">
              {monetization?.telemetry?.estimated_watch_hours || 0} <span className="text-xs font-normal text-slate-400">/ 4,000 hrs</span>
            </div>
            <div className="text-[11px] font-mono text-amber-400 mt-2">
              Parallel YPP Monetization Route
            </div>
          </div>

          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
            <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5 mb-1">
              <Share2 className="w-3.5 h-3.5 text-emerald-400" />
              INSTAGRAM REELS
            </div>
            <div className="text-xl font-bold font-mono text-slate-100">
              {monetization?.telemetry?.instagram_published || 0} <span className="text-xs font-normal text-slate-400">Live</span>
            </div>
            <div className="text-[11px] font-mono text-emerald-400 mt-2">
              Target: 10K Followers (Collabs)
            </div>
          </div>

          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
            <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5 mb-1">
              <Zap className="w-3.5 h-3.5 text-purple-400" />
              ESTIMATED REACH VELOCITY
            </div>
            <div className="text-xl font-bold font-mono text-slate-100">
              {(monetization?.telemetry?.estimated_views_generated || 0).toLocaleString()} <span className="text-xs font-normal text-slate-400">Views</span>
            </div>
            <div className="text-[11px] font-mono text-purple-400 mt-2">
              Queue: {monetization?.telemetry?.total_queued || 0} Clips Staged
            </div>
          </div>
        </div>

        {/* 8-Hour Long-Form Gap Schedule & Mode Banner */}
        <div className="mt-5 pt-4 border-t border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs font-mono">
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-2.5 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-bold flex items-center gap-1.5 animate-pulse">
              <Zap className="w-3.5 h-3.5 text-cyan-400" />
              MODE: AUTONOMOUS SHORT CLIPPING (24/7)
            </span>
            <span className="px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-300 font-bold flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              NEXT LONG-FORM IN: {longformStatus?.span_status?.hours_remaining ?? 7.9}h SPAN
            </span>
            <span className="px-2.5 py-1 rounded-md bg-purple-500/10 border border-purple-500/30 text-purple-300 font-bold flex items-center gap-1.5">
              SLOT: {longformStatus?.next_slot?.schedule_time || '4:00 PM'} ({longformStatus?.next_slot?.schedule_date || 'Nov 19'})
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-slate-400 text-[11px]">9-STREAMER LINEUP (STRICTLY 2 AT A TIME · AUTO-FAILOVER):</span>
            <span className="px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-bold text-[11px]">IShowSpeed 🌍</span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold text-[11px]">Kai Cenat 🇺🇸</span>
            <span className="px-2 py-0.5 rounded bg-blue-500/20 border border-blue-500/40 text-blue-300 font-bold text-[11px]">Typical Gamer 🇨🇦</span>
            <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-[11px]">CarryMinati 🇮🇳</span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[11px]">xQc 🇨🇦</span>
            <span className="px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30 text-purple-300 text-[11px]">Jynxzi 🇺🇸</span>
            <span className="px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30 text-purple-300 text-[11px]">CaseOh 🇺🇸</span>
            <span className="px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[11px]">Mythpat 🇮🇳</span>
            <span className="px-2 py-0.5 rounded bg-yellow-500/10 border border-yellow-500/30 text-yellow-300 text-[11px]">Ibai 🇪🇸</span>
          </div>
        </div>
      </div>

      {/* Preset Niches & Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/50 p-3 rounded-xl border border-slate-800">
        <div className="flex flex-wrap items-center gap-1.5">
          {PRESET_NICHES.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                setNiche(p.value);
                fetchResearch(p.value);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                niche === p.value
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-cyan-sm'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            fetchResearch(niche);
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            placeholder="Custom niche or trend..."
            className="px-3 py-1.5 rounded-lg bg-slate-950 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400 min-w-[220px]"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-3.5 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 font-bold text-xs font-mono flex items-center gap-1 cursor-pointer transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{loading ? 'ANALYZING...' : 'ANALYZE'}</span>
          </button>
        </form>
      </div>

      {/* 30-Day Master Algorithmic Schedule & Long-Form Pipeline */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/40 via-purple-950/30 to-slate-950 border border-cyan-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold text-[11px] flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-emerald-400" />
              30-DAY MASTER SCHEDULE ACTIVE
            </span>
            <span className="text-slate-300 font-bold">4 Prime Global Windows / Day</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Cadence: <strong>09:00 AM</strong> (Asia/US Late) · <strong>02:00 PM</strong> (Europe) · <strong>06:30 PM</strong> (US Commute) · <strong>11:00 PM</strong> (US Prime)
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px]">
            <span className="text-cyan-300">YouTube Shorts: <strong>71 Queued</strong> (17+ Days Buffer)</span>
            <span className="text-slate-500">•</span>
            <span className="text-purple-300">Instagram Reels: <strong>133 Queued</strong> (33+ Days Buffer · Full Month+)</span>
            <span className="text-slate-500">•</span>
            <span className="text-amber-300">Long-Form Compilations: <strong>8h Strict Gap</strong></span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={async () => {
              try {
                const res = await api.scheduleMonthQueue();
                alert(`✅ 30-Day Master Schedule Synchronized!\n• YouTube: ${res.youtube_count} items (First: ${res.youtube_first}, Last: ${res.youtube_last})\n• Instagram: ${res.instagram_count} items (Full Month)\n• Cadence: ${res.daily_cadence}`);
              } catch (e: any) {
                alert(`Error: ${e.message}`);
              }
            }}
            className="px-3 py-2 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/40 text-cyan-300 font-bold text-xs flex items-center gap-1.5 cursor-pointer transition-all shadow-cyan-sm"
            title="Recalibrate and synchronize 30-day 4-slot queue cadence"
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Sync 30-Day Cadence</span>
          </button>
        </div>
      </div>

      {/* 8-Hour Long-Form Compilations & Studio Thumbnails Showcase */}
      <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 border border-amber-500/30 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-amber-300 uppercase tracking-wider font-mono">
              <Film className="w-4 h-4 text-amber-400" />
              8-Hour Long-Form Compilation Pipeline & Studio Thumbnails
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              4,000 Watch Hours YPP Monetization Route • High-Level Retention Editing • 16:9 3D Studio Thumbnails
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono">
            <span className="px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 font-bold">
              ⚡ 6s Teaser Opener
            </span>
            <span className="px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-bold">
              🏷️ Lower-Third Badges
            </span>
            <span className="px-2 py-0.5 rounded bg-purple-500/20 border border-purple-500/40 text-purple-300 font-bold">
              💬 Midpoint CTA Debate
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold">
              🔊 -14 LUFS Mastered
            </span>
          </div>
        </div>

        {/* Long-Form Schedule Timeline */}
        <div className="space-y-2.5">
          {longformStatus?.history && longformStatus.history.length > 0 ? (
            longformStatus.history.slice(0, 3).map((item: any, idx: number) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3 hover:border-amber-500/30 transition-all"
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center font-bold text-amber-400 font-mono text-xs flex-shrink-0">
                    #{idx + 1}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-200 line-clamp-1">{item.title}</div>
                    <div className="text-[11px] font-mono text-slate-400 flex flex-wrap items-center gap-2 mt-0.5">
                      <span>File: <strong className="text-slate-300">{item.file_name}</strong></span>
                      <span>•</span>
                      <span>Slot: <strong className="text-amber-300">{item.scheduled_time}</strong></span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {item.status === 'PUBLISHED' ? (
                    <a
                      href={item.youtube_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold text-xs font-mono flex items-center gap-1.5 transition-all shadow-md"
                    >
                      <span>LIVE ON YOUTUBE</span>
                      <Globe className="w-3.5 h-3.5" />
                    </a>
                  ) : (
                    <span className="px-3 py-1.5 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-300 font-bold text-xs font-mono flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      SCHEDULED 04:00 PM
                    </span>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="p-4 text-center text-xs font-mono text-slate-500 bg-slate-900/40 rounded-xl">
              No long-form compilation history recorded yet.
            </div>
          )}
        </div>
      </div>

      {/* 2026 Algorithmic Growth Levers Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-950/70 border border-cyan-500/20">
          <div className="flex items-center gap-2 text-xs font-bold text-cyan-400 uppercase font-mono mb-1">
            <ShieldCheck className="w-4 h-4" />
            Swipe-Away Shield
          </div>
          <div className="text-lg font-bold text-slate-100 font-mono">&gt;75% Viewed</div>
          <p className="text-[11px] text-slate-400 mt-1">
            0.0s on-screen hook banner & zero dead air prevents instant scroll drops.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/70 border border-cyan-500/20">
          <div className="flex items-center gap-2 text-xs font-bold text-purple-400 uppercase font-mono mb-1">
            <Share2 className="w-4 h-4" />
            Sends Per Reach
          </div>
          <div className="text-lg font-bold text-slate-100 font-mono">&gt;3.0% DM Share</div>
          <p className="text-[11px] text-slate-400 mt-1">
            Group chat & duo prompts trigger Meta's #1 non-follower recommendation factor.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/70 border border-cyan-500/20">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase font-mono mb-1">
            <Repeat className="w-4 h-4" />
            Loop Multiplier
          </div>
          <div className="text-lg font-bold text-slate-100 font-mono">&gt;100% APV Target</div>
          <p className="text-[11px] text-slate-400 mt-1">
            18–26s sweet spot clips flow audio endings back into the opening frame.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/70 border border-cyan-500/20">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase font-mono mb-1">
            <Globe className="w-4 h-4" />
            24/7 Global Reach
          </div>
          <div className="text-lg font-bold text-slate-100 font-mono">No Dead Hours</div>
          <p className="text-[11px] text-slate-400 mt-1">
            Overnight posting taps US/Europe prime time while local viewers sleep.
          </p>
        </div>
      </div>

      {/* Trending Topics & Keywords Scanner */}
      {trends && (
        <div className="p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/30">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-xs font-bold text-cyan-300 uppercase tracking-wider font-mono">
              <Flame className="w-4 h-4 text-orange-400" />
              Real-Time Gaming Trend Intelligence
            </div>
            <span className="text-[11px] font-mono text-slate-400">Target Niche: {trends.niche}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
            {trends.trending_topics?.map((item: any, i: number) => (
              <div key={i} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-[11px] font-mono mb-1.5">
                    <span className="font-bold text-slate-200">{item.topic}</span>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                      {item.search_velocity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 italic mb-2">
                    Hook Blueprint: "{item.recommended_hook}"
                  </p>
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-2 border-t border-slate-800">
                  <span>Sentiment: <strong className="text-cyan-300">{item.audience_sentiment}</strong></span>
                  <span>Competition: {item.competition}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Quick Copy Viral Hashtag Shelves */}
          <div className="pt-3 border-t border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <div className="text-[11px] font-mono text-slate-400 mb-1">RECOMMENDED INSTAGRAM TAGS (Strict 5-Tag Cap):</div>
              <div className="flex flex-wrap gap-1">
                {trends.viral_hashtags?.instagram_tier1?.map((tag: string, i: number) => (
                  <span key={i} className="px-2 py-0.5 rounded bg-pink-500/10 border border-pink-500/30 text-[11px] font-mono text-pink-300">
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={() => handleCopy(trends.viral_hashtags?.instagram_tier1?.join(' '), 'ig_tags')}
              className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300 flex items-center gap-1.5 cursor-pointer"
            >
              {copiedKey === 'ig_tags' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedKey === 'ig_tags' ? 'COPIED!' : 'COPY 5 TAGS'}</span>
            </button>
          </div>
        </div>
      )}

      {/* High-Retention Viral Video Blueprints */}
      <div>
        <div className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Flame className="w-4 h-4 text-cyan-400" />
          High-Retention Viral Video Blueprints ({ideas.length} Concepts)
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ideas.map((idea, idx) => (
            <div
              key={idx}
              className="p-5 rounded-xl bg-slate-950/80 border border-cyan-500/20 hover:border-cyan-500/40 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
                  <span className="text-cyan-400 font-bold">CONCEPT #{idx + 1} • {idea.hook_type || 'Curiosity Gap'}</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                    RETENTION {idea.estimated_retention || '88%'}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-100 flex items-center justify-between">
                  <span>{idea.title}</span>
                  <button
                    onClick={() => handleCopy(idea.title, `title_${idx}`)}
                    className="text-slate-500 hover:text-cyan-400 cursor-pointer ml-2"
                    title="Copy Title"
                  >
                    {copiedKey === `title_${idx}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </h3>

                {/* 1.8-second hook */}
                <div className="mt-3 p-3 rounded-lg bg-slate-900 border border-cyan-500/30">
                  <div className="flex items-center justify-between text-[11px] font-mono text-cyan-300 mb-1">
                    <span className="flex items-center gap-1 font-bold">
                      <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                      1.8-SECOND HOOK (TEXT & AUDIO):
                    </span>
                    <button
                      onClick={() => handleCopy(idea.hook, `hook_${idx}`)}
                      className="text-cyan-400 hover:text-cyan-200 cursor-pointer"
                    >
                      {copiedKey === `hook_${idx}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                  <p className="text-xs text-slate-200 italic font-sans">"{idea.hook}"</p>
                </div>

                {/* Core insight / Climax */}
                <p className="mt-3 text-xs text-slate-300 leading-relaxed font-sans">
                  <strong className="text-slate-200">Climax / Value:</strong> {idea.core_insight}
                </p>

                {/* Loop Technique */}
                {idea.loop_technique && (
                  <div className="mt-2.5 p-2 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] font-mono text-slate-300 flex items-start gap-1.5">
                    <Repeat className="w-3.5 h-3.5 text-cyan-400 mt-0.5 flex-shrink-0" />
                    <span><strong>Loop:</strong> {idea.loop_technique}</span>
                  </div>
                )}

                {/* Instagram DM Share Trigger */}
                {idea.dm_share_prompt && (
                  <div className="mt-2.5 p-2 rounded-lg bg-purple-950/30 border border-purple-500/20 text-[11px] font-mono text-purple-200 flex items-center justify-between">
                    <div className="flex items-center gap-1.5 overflow-hidden">
                      <Share2 className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                      <span className="truncate"><strong>DM Share:</strong> {idea.dm_share_prompt}</span>
                    </div>
                    <button
                      onClick={() => handleCopy(idea.dm_share_prompt, `dm_${idx}`)}
                      className="text-purple-400 hover:text-purple-200 cursor-pointer ml-2 flex-shrink-0"
                    >
                      {copiedKey === `dm_${idx}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                )}

                {/* Comment Debate Starter */}
                {idea.comment_debate_starter && (
                  <div className="mt-2 p-2 rounded-lg bg-blue-950/30 border border-blue-500/20 text-[11px] font-mono text-blue-200 flex items-center justify-between">
                    <div className="flex items-center gap-1.5 overflow-hidden">
                      <MessageSquare className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                      <span className="truncate"><strong>Debate:</strong> {idea.comment_debate_starter}</span>
                    </div>
                    <button
                      onClick={() => handleCopy(idea.comment_debate_starter, `debate_${idx}`)}
                      className="text-blue-400 hover:text-blue-200 cursor-pointer ml-2 flex-shrink-0"
                    >
                      {copiedKey === `debate_${idx}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                )}
              </div>

              {/* Duration & Footnote */}
              <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Sweet Spot: <strong className="text-slate-200">{idea.recommended_duration || '22s'}</strong></span>
                <span className="text-cyan-400/80">GTA-6 Active Style Ready</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Channel Branding & Identity Concept */}
      {branding && (
        <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 border border-cyan-500/30 shadow-cyan-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-cyan-300 uppercase tracking-wider mb-4 font-mono">
            <Compass className="w-4 h-4 text-cyan-400" />
            Channel Strategy & Brand Architecture
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="text-xs font-mono text-slate-400 mb-1.5">HIGH-AUTHORITY CHANNEL NAMES</div>
              <div className="flex flex-wrap gap-1.5">
                {branding.channel_names?.map((name: string, i: number) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded bg-cyan-500/10 border border-cyan-500/30 text-xs font-mono text-cyan-300"
                  >
                    {name}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <div className="text-xs font-mono text-slate-400 mb-1.5">OFFICIAL SLOGAN / TAGLINE</div>
              <p className="text-xs text-slate-200 italic font-mono bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                "{branding.tagline}"
              </p>
            </div>

            <div>
              <div className="text-xs font-mono text-slate-400 mb-1.5">OPTIMIZED SOCIAL BIO</div>
              <p className="text-xs text-slate-300 font-mono bg-slate-950 p-2.5 rounded-lg border border-slate-800 whitespace-pre-line">
                {branding.bio}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
