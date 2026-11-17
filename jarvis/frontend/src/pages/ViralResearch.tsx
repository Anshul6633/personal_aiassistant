import React, { useState, useEffect } from 'react';
import { TrendingUp, Sparkles, Flame, Copy, Check, Hash, Lightbulb, Compass } from 'lucide-react';
import { api } from '../services/api';

export const ViralResearch: React.FC = () => {
  const [niche, setNiche] = useState('Technology & AI Podcasts');
  const [ideas, setIdeas] = useState<any[]>([]);
  const [branding, setBranding] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const fetchResearch = async () => {
    setLoading(true);
    try {
      const resultIdeas = await api.getViralIdeas(niche);
      setIdeas(resultIdeas);

      const res = await fetch(`/api/research/branding?niche=${encodeURIComponent(niche)}`);
      const brandingData = await res.json();
      setBranding(brandingData);
    } catch (err) {
      console.error('Research error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResearch();
  }, []);

  const handleCopyHook = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="space-y-6 pb-12 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            Autonomous Viral Content Researcher
          </h1>
          <p className="text-xs font-mono text-cyan-400/80">
            Public Trend Intelligence • High-CTR Hooks • Channel Branding Strategy
          </p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            fetchResearch();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            placeholder="Target Niche (e.g. AI Podcasts)..."
            className="px-3.5 py-1.5 rounded-lg bg-slate-950 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase font-mono flex items-center gap-1.5 cursor-pointer transition-all shadow-cyan-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{loading ? 'ANALYZING...' : 'RESEARCH'}</span>
          </button>
        </form>
      </div>

      {/* Channel Branding Concept Card */}
      {branding && (
        <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 border border-cyan-500/30 shadow-cyan-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-cyan-300 uppercase tracking-wider mb-4">
            <Compass className="w-4 h-4 text-cyan-400" />
            Channel Strategy & Brand Architecture
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="text-xs font-mono text-slate-400 mb-1">SUGGESTED CHANNEL NAMES</div>
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
              <div className="text-xs font-mono text-slate-400 mb-1">OFFICIAL SLOGAN / TAGLINE</div>
              <p className="text-xs text-slate-200 italic font-mono bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                "{branding.tagline}"
              </p>
            </div>

            <div>
              <div className="text-xs font-mono text-slate-400 mb-1">OPTIMIZED SOCIAL BIO</div>
              <p className="text-xs text-slate-300 font-mono bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                {branding.bio}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Viral Hook & Clip Concepts Grid */}
      <div>
        <div className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Flame className="w-4 h-4 text-cyan-400" />
          High-Retention Viral Video Blueprints
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ideas.map((idea, idx) => (
            <div
              key={idx}
              className="p-5 rounded-xl bg-slate-950/80 border border-cyan-500/20 hover:border-cyan-500/40 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
                  <span className="text-cyan-400 font-bold">CONCEPT #{idx + 1}</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    EST. RETENTION {idea.estimated_retention || '85%'}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-100">{idea.title}</h3>

                {/* The 3-second hook */}
                <div className="mt-3 p-3 rounded-lg bg-slate-900 border border-cyan-500/30">
                  <div className="flex items-center justify-between text-[11px] font-mono text-cyan-300 mb-1">
                    <span className="flex items-center gap-1">
                      <Lightbulb className="w-3.5 h-3.5" />
                      3-SECOND VISUAL / AUDIO HOOK:
                    </span>
                    <button
                      onClick={() => handleCopyHook(idea.hook, idx)}
                      className="text-cyan-400 hover:text-cyan-200 cursor-pointer"
                    >
                      {copiedIndex === idx ? (
                        <Check className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                  </div>
                  <p className="text-xs text-slate-200 italic font-sans">"{idea.hook}"</p>
                </div>

                {/* Core insight */}
                <p className="mt-3 text-xs text-slate-300 leading-relaxed font-sans">
                  <strong className="text-slate-200">Value Drop:</strong> {idea.core_insight}
                </p>
              </div>

              {/* Call to action & Duration */}
              <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Duration: {idea.recommended_duration || '45s'}</span>
                <span className="text-slate-300">CTA: "{idea.call_to_action}"</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

