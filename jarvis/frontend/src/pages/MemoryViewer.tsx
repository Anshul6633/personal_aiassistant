import React, { useState, useEffect } from 'react';
import { Brain, Plus, Trash2, Key, Tag, Sparkles, Check, Database, ThumbsUp, ThumbsDown, Award, ShieldCheck, ToggleLeft, ToggleRight, RefreshCw, MessageSquare } from 'lucide-react';
import { MemoryItem, RLHFRule, RLHFSummary, api } from '../services/api';

export const MemoryViewer: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'rlhf' | 'memories'>('rlhf');

  // Core Memory State
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [category, setCategory] = useState('content');
  const [key, setKey] = useState('');
  const [value, setValue] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  // RLHF State
  const [rlhfSummary, setRlhfSummary] = useState<RLHFSummary | null>(null);
  const [newRuleText, setNewRuleText] = useState('');
  const [newRuleCategory, setNewRuleCategory] = useState('persona');
  const [newRuleReward, setNewRuleReward] = useState(2.0);
  const [isAddingRule, setIsAddingRule] = useState(false);
  const [rlhfFilterCategory, setRlhfFilterCategory] = useState<string>('all');

  const fetchMemories = async () => {
    try {
      const data = await api.getMemories();
      setMemories(data);
    } catch (err) {
      console.error('Failed to fetch memories:', err);
    }
  };

  const fetchRLHF = async () => {
    try {
      const data = await api.getRLHFSummary();
      setRlhfSummary(data);
    } catch (err) {
      console.error('Failed to fetch RLHF summary:', err);
    }
  };

  useEffect(() => {
    fetchMemories();
    fetchRLHF();
  }, []);

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!key.trim() || !value.trim()) return;

    setIsAdding(true);
    try {
      await api.addMemory(category, key.trim(), value.trim());
      setKey('');
      setValue('');
      await fetchMemories();
    } catch (err) {
      console.error(err);
    } finally {
      setIsAdding(false);
    }
  };

  const handleDeleteMemory = async (id: number) => {
    try {
      await api.deleteMemory(id);
      await fetchMemories();
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleText.trim()) return;
    setIsAddingRule(true);
    try {
      await api.addRLHFRule(newRuleText.trim(), newRuleCategory, newRuleReward);
      setNewRuleText('');
      await fetchRLHF();
    } catch (err) {
      console.error('Failed to add RLHF rule:', err);
    } finally {
      setIsAddingRule(false);
    }
  };

  const handleToggleRule = async (ruleId: number) => {
    try {
      await api.toggleRLHFRule(ruleId);
      await fetchRLHF();
    } catch (err) {
      console.error('Failed to toggle rule:', err);
    }
  };

  const handleDeleteRule = async (ruleId: number) => {
    try {
      await api.deleteRLHFRule(ruleId);
      await fetchRLHF();
    } catch (err) {
      console.error('Failed to delete rule:', err);
    }
  };

  const filteredRules = (rlhfSummary?.rules || []).filter(
    (r) => rlhfFilterCategory === 'all' || r.category === rlhfFilterCategory
  );

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Brain className="w-5 h-5 text-cyan-400" />
            JARVIS Intelligence &amp; Continuous Learning
          </h1>
          <p className="text-xs font-mono text-cyan-400/80">
            Reinforcement Learning from Human Feedback (RLHF) • Semantic Memory Bank • Policy Adaptation
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800">
          <button
            onClick={() => setActiveTab('rlhf')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
              activeTab === 'rlhf'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-cyan-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Award className="w-3.5 h-3.5" />
            <span>🧠 RLHF Rules ({rlhfSummary?.metrics.active_rules_count ?? 5})</span>
          </button>

          <button
            onClick={() => setActiveTab('memories')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
              activeTab === 'memories'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-cyan-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>💾 Core Memory ({memories.length})</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: RLHF & CONTINUOUS LEARNING */}
      {/* ========================================================================= */}
      {activeTab === 'rlhf' && (
        <div className="space-y-6">
          {/* Telemetry Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-xl bg-slate-950/80 border border-emerald-500/30">
              <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono">
                <span>TOTAL REWARD SCORE</span>
                <Award className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <div className="mt-1 text-2xl font-bold font-mono text-emerald-300">
                +{rlhfSummary?.metrics.total_cumulative_reward ?? 24.5}
              </div>
              <div className="text-[10px] font-mono text-slate-500 mt-0.5">Policy Reinforcement</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/80 border border-cyan-500/30">
              <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono">
                <span>ACTIVE POLICIES</span>
                <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              </div>
              <div className="mt-1 text-2xl font-bold font-mono text-cyan-300">
                {rlhfSummary?.metrics.active_rules_count ?? 5}
              </div>
              <div className="text-[10px] font-mono text-slate-500 mt-0.5">Prompt Injected Rules</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/80 border border-blue-500/30">
              <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono">
                <span>POSITIVE PRAISE</span>
                <ThumbsUp className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <div className="mt-1 text-2xl font-bold font-mono text-blue-300">
                {rlhfSummary?.metrics.positive_count ?? 0}
              </div>
              <div className="text-[10px] font-mono text-slate-500 mt-0.5">+1.0 Reward Events</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/80 border border-purple-500/30">
              <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono">
                <span>HUMAN CORRECTIONS</span>
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              </div>
              <div className="mt-1 text-2xl font-bold font-mono text-purple-300">
                {rlhfSummary?.metrics.correction_count ?? 0}
              </div>
              <div className="text-[10px] font-mono text-slate-500 mt-0.5">+2.0 Distilled Rules</div>
            </div>
          </div>

          {/* Teach JARVIS a New Policy Rule Form */}
          <div className="p-5 rounded-2xl bg-slate-950/80 border border-cyan-500/25 shadow-cyan-sm">
            <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              Teach JARVIS a New RLHF Policy Rule
            </h2>

            <form onSubmit={handleAddRule} className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
              <div className="md:col-span-2">
                <label className="block text-[11px] font-mono text-slate-400 mb-1">RULE / PREFERENCE INSTRUCTION</label>
                <input
                  type="text"
                  value={newRuleText}
                  onChange={(e) => setNewRuleText(e.target.value)}
                  placeholder="e.g. For gaming clips, keep titles under 50 characters"
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">CATEGORY</label>
                <select
                  value={newRuleCategory}
                  onChange={(e) => setNewRuleCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                >
                  <option value="persona">Personality &amp; Tone</option>
                  <option value="video_editing">Video Clipping &amp; Subtitles</option>
                  <option value="social_seo">Social Media &amp; Uploads</option>
                  <option value="performance">Performance &amp; Hardware</option>
                  <option value="general">General Behavior</option>
                </select>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isAddingRule || !newRuleText.trim()}
                  className="w-full py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase font-mono disabled:opacity-40 cursor-pointer transition-all flex items-center justify-center gap-1.5 shadow-lg"
                >
                  <Award className="w-3.5 h-3.5" />
                  <span>{isAddingRule ? 'LEARNING...' : 'TRAIN POLICY (+2.0)'}</span>
                </button>
              </div>
            </form>
          </div>

          {/* Active Policy Rules Table */}
          <div className="rounded-2xl bg-slate-950/80 border border-cyan-500/20 overflow-hidden">
            <div className="px-5 py-3 border-b border-cyan-500/15 bg-slate-900/60 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
              <span className="text-slate-300 font-bold flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                LEARNED HUMAN FEEDBACK POLICIES ({filteredRules.length})
              </span>

              {/* Category Filter */}
              <div className="flex items-center gap-2">
                <span className="text-slate-500 text-[10px]">Filter:</span>
                <select
                  value={rlhfFilterCategory}
                  onChange={(e) => setRlhfFilterCategory(e.target.value)}
                  className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-[11px] text-cyan-300 font-mono"
                >
                  <option value="all">All Categories</option>
                  <option value="persona">Persona</option>
                  <option value="video_editing">Video Editing</option>
                  <option value="social_seo">Social SEO</option>
                  <option value="performance">Performance</option>
                </select>

                <button
                  onClick={fetchRLHF}
                  className="p-1 rounded text-slate-400 hover:text-cyan-300 hover:bg-slate-800"
                  title="Refresh RLHF rules"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="divide-y divide-slate-800">
              {filteredRules.length === 0 ? (
                <div className="p-8 text-center text-xs font-mono text-slate-500">
                  No policy rules found in this category. Teach JARVIS one above!
                </div>
              ) : (
                filteredRules.map((r) => (
                  <div
                    key={r.id}
                    className={`p-4 flex items-center justify-between gap-4 transition-colors ${
                      r.active ? 'hover:bg-slate-900/40' : 'opacity-50 bg-slate-950/40'
                    }`}
                  >
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2 text-xs font-mono">
                        <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                          +{r.reward_weight.toFixed(1)} REWARD
                        </span>
                        <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 text-[10px] uppercase">
                          {r.category}
                        </span>
                        {r.times_applied > 0 && (
                          <span className="text-[10px] text-slate-500">Applied {r.times_applied}x</span>
                        )}
                      </div>

                      <div className="text-xs text-slate-200 font-mono font-medium">
                        {r.rule_text}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggleRule(r.id)}
                        className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
                          r.active
                            ? 'text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/40'
                            : 'text-slate-600 hover:text-slate-400'
                        }`}
                        title={r.active ? 'Active rule (injected into prompt)' : 'Paused rule'}
                      >
                        {r.active ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                      </button>

                      <button
                        onClick={() => handleDeleteRule(r.id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 cursor-pointer transition-colors"
                        title="Delete policy rule"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Feedback History Stream */}
          {rlhfSummary?.recent_feedback && rlhfSummary.recent_feedback.length > 0 && (
            <div className="rounded-2xl bg-slate-950/80 border border-slate-800 overflow-hidden">
              <div className="px-5 py-3 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between text-xs font-mono">
                <span className="text-slate-300 font-bold flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-purple-400" />
                  RECENT HUMAN FEEDBACK LOGS
                </span>
                <span className="text-slate-500 text-[10px]">Real-time dialogue signals</span>
              </div>

              <div className="divide-y divide-slate-800/80 text-xs font-mono">
                {rlhfSummary.recent_feedback.slice(0, 5).map((fb) => (
                  <div key={fb.id} className="p-3.5 space-y-1 hover:bg-slate-900/30">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="flex items-center gap-1.5">
                        <span
                          className={`font-bold uppercase px-1.5 py-0.5 rounded ${
                            fb.feedback_type === 'positive'
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/40'
                              : fb.feedback_type === 'correction'
                              ? 'bg-purple-950 text-purple-400 border border-purple-500/40'
                              : 'bg-rose-950 text-rose-400 border border-rose-500/40'
                          }`}
                        >
                          {fb.feedback_type} ({fb.reward_score > 0 ? `+${fb.reward_score}` : fb.reward_score})
                        </span>
                        <span className="text-slate-400">{fb.category}</span>
                      </span>
                      <span className="text-slate-500">{fb.created_at}</span>
                    </div>

                    <div className="text-slate-300 text-[11px] truncate">
                      <strong className="text-slate-400">Response:</strong> "{fb.action_or_output}"
                    </div>

                    {fb.user_correction && (
                      <div className="text-cyan-300 text-[11px]">
                        <strong className="text-cyan-400">User Correction:</strong> "{fb.user_correction}"
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: CORE SEMANTIC MEMORY */}
      {/* ========================================================================= */}
      {activeTab === 'memories' && (
        <div className="space-y-6">
          {/* Add Memory Form */}
          <div className="p-5 rounded-2xl bg-slate-950/80 border border-cyan-500/25 shadow-cyan-sm">
            <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Plus className="w-4 h-4 text-cyan-400" />
              Impart New Knowledge / Preference to JARVIS
            </h2>

            <form onSubmit={handleAddMemory} className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">CATEGORY</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                >
                  <option value="content">Content &amp; Editing</option>
                  <option value="personality">Personality &amp; Tone</option>
                  <option value="user">User Profile</option>
                  <option value="system">System &amp; Automation</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">KEY IDENTIFIER</label>
                <input
                  type="text"
                  value={key}
                  onChange={(e) => setKey(e.target.value)}
                  placeholder="e.g. preferred_voice"
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">VALUE / PREFERENCE</label>
                <input
                  type="text"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  placeholder="e.g. Hindi subtitles on bottom"
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-cyan-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isAdding || !key.trim() || !value.trim()}
                  className="w-full py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase font-mono disabled:opacity-40 cursor-pointer transition-all flex items-center justify-center gap-1.5 shadow-lg"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{isAdding ? 'SAVING...' : 'COMMIT TO MEMORY'}</span>
                </button>
              </div>
            </form>
          </div>

          {/* Memory Table / List */}
          <div className="rounded-2xl bg-slate-950/80 border border-cyan-500/20 overflow-hidden">
            <div className="px-5 py-3 border-b border-cyan-500/15 bg-slate-900/60 flex items-center justify-between text-xs font-mono">
              <span className="text-slate-300 font-bold flex items-center gap-2">
                <Database className="w-4 h-4 text-cyan-400" />
                STORED MEMORIES ({memories.length})
              </span>
              <span className="text-slate-400">SQLite: jarvis/database.sqlite</span>
            </div>

            <div className="divide-y divide-slate-800">
              {memories.map((m) => (
                <div
                  key={m.id}
                  className="p-4 flex items-center justify-between gap-4 hover:bg-slate-900/40 transition-colors"
                >
                  <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-2">
                    <div className="flex items-center gap-2 text-xs font-mono">
                      <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 text-[10px] uppercase">
                        {m.category}
                      </span>
                      <span className="font-bold text-slate-200">{m.key}</span>
                    </div>

                    <div className="text-xs text-slate-300 font-mono md:col-span-2">
                      {m.value}
                    </div>
                  </div>

                  <button
                    onClick={() => handleDeleteMemory(m.id)}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 cursor-pointer transition-colors"
                    title="Forget this memory"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
