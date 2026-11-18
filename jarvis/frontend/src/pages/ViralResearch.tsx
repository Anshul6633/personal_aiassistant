import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, Sparkles, Flame, Copy, Check, Hash, Lightbulb, Compass, 
  Share2, MessageSquare, Repeat, Zap, ShieldCheck, Globe, CheckCircle2 
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
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [appliedSuccess, setAppliedSuccess] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const fetchResearch = async (targetNiche: string = niche) => {
    setLoading(true);
    try {
      const [resultIdeas, brandingRes, trendsData, planData] = await Promise.all([
        api.getViralIdeas(targetNiche, 6),
        fetch(`/api/research/branding?niche=${encodeURIComponent(targetNiche)}`).then(r => r.json()).catch(() => null),
        api.getResearchTrends(targetNiche).catch(() => null),
        api.getGrowthPlan().catch(() => null)
      ]);

      setIdeas(resultIdeas || []);
      setBranding(brandingRes);
      setTrends(trendsData);
      setGrowthPlan(planData);
    } catch (err) {
      console.error('Research error:', err);
    } finally {
      setLoading(false);
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
