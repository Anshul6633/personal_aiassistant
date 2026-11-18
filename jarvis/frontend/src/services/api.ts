/**
 * JARVIS REST API Client
 */

export interface SystemMetrics {
  cpu_percent: number;
  ram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  disk_free_gb: number;
  battery_percent?: number | null;
  is_plugged?: boolean | null;
  gpu_name: string;
  vram_used_mb: number;
  vram_total_mb: number;
}

export interface JarvisState {
  status: 'IDLE' | 'LISTENING' | 'THINKING' | 'PLANNING' | 'EXECUTING' | 'EDITING' | 'SPEAKING' | 'ERROR';
  status_message: string;
  current_thought: string;
  active_task_id: string | null;
  active_task_title: string | null;
  task_progress: number;
  current_speech: string;
  mic_active: boolean;
  mic_level: number;
  autonomy_mode: 'MANUAL' | 'SUPERVISED' | 'PREAPPROVED_AUTONOMOUS';
  active_model: string;
  metrics: SystemMetrics;
  last_update: string;
}

export interface ClipItem {
  id: string;
  source_file: string;
  title: string;
  summary: string;
  hook_strength: number;
  story_completeness: number;
  info_value: number;
  engagement_potential: number;
  audio_quality: number;
  visual_quality: number;
  total_score: number;
  start_time: number;
  end_time: number;
  duration: number;
  output_path: string;
  thumbnail_path: string;
  subtitles_path: string;
  tags: string;
  caption: string;
  status: string;
  published_youtube: number;
  published_instagram: number;
  created_at: string;
  video_url?: string;
  thumb_url?: string;
}

export interface MemoryItem {
  id: number;
  category: string;
  key: string;
  value: string;
  confidence: number;
  updated_at: string;
}

export interface RLHFRule {
  id: number;
  rule_text: string;
  category: string;
  reward_weight: number;
  confidence: number;
  active: boolean;
  times_applied: number;
  updated_at: string;
}

export interface RLHFFeedbackLog {
  id: number;
  context_type: string;
  prompt_or_input: string;
  action_or_output: string;
  feedback_type: 'positive' | 'negative' | 'correction';
  reward_score: number;
  user_correction?: string | null;
  learned_rule?: string | null;
  category: string;
  created_at: string;
}

export interface RLHFSummary {
  metrics: {
    total_feedback: number;
    positive_count: number;
    negative_count: number;
    correction_count: number;
    active_rules_count: number;
    total_cumulative_reward: number;
  };
  rules: RLHFRule[];
  recent_feedback: RLHFFeedbackLog[];
}

export interface CaptionStyle {
  id: string;
  name: string;
  tag: string;
  font: string;
  primary_color: string;
  highlight_color: string;
  outline_color: string;
  sample: string;
  desc: string;
  size: number;
}

export interface StudioTransform {
  scale_x: number;
  scale_y: number;
  position_x: number;
  position_y: number;
  rotation: number;
  flip_h: boolean;
  flip_v: boolean;
  opacity: number;
}

export interface StudioFilters {
  brightness: number;
  contrast: number;
  saturation: number;
  temperature: number;
  tint: number;
  blur: number;
  sharpen: number;
  vignette: number;
  color_splash?: boolean;
  color_splash_x?: number;
  color_splash_y?: number;
  color_splash_radius?: number;
  preset_name?: string;
  lift?: number;
  gamma?: number;
  gain?: number;
  transition?: string;
}

export interface StudioTextProps {
  text: string;
  font: string;
  font_size: number;
  color: string;
  highlight_color: string;
  outline_color: string;
  outline_width: number;
  bg_color?: string;
  alignment: string;
  is_subtitle: boolean;
  karaoke_mode: boolean;
  sticker_emoji?: string;
  animation?: 'bounce' | 'pulse' | 'glow' | 'none';
}

export interface StudioClip {
  id: string;
  track_id: string;
  name: string;
  source_type: 'video' | 'audio' | 'image' | 'text' | 'subtitle' | 'sticker';
  source_file?: string;
  source_url?: string;
  start_time: number;
  duration: number;
  in_point: number;
  out_point: number;
  speed: number;
  volume: number;
  fade_in: number;
  fade_out: number;
  transform: StudioTransform;
  filters: StudioFilters;
  text_props?: StudioTextProps;
}

export interface StudioTrack {
  id: string;
  name: string;
  type: 'video' | 'audio' | 'text' | 'subtitle' | 'image';
  locked: boolean;
  muted: boolean;
  visible: boolean;
  volume: number;
  order: number;
}

export interface StudioProject {
  id: string;
  name: string;
  aspect_ratio: '16:9' | '9:16' | '1:1' | '4:5';
  width: number;
  height: number;
  fps: number;
  duration: number;
  tracks: StudioTrack[];
  clips: StudioClip[];
  created_at: number;
  updated_at: number;
  thumbnail_url?: string;
}

export interface ExportRequest {
  project_id: string;
  resolution: string;
  aspect_ratio: string;
  codec: string;
  fps: number;
  bitrate_kbps: number;
  export_audio_only: boolean;
}

export interface MobileNetworkInfo {
  success: boolean;
  lan_ip: string;
  production_port?: number;
  dev_port?: number;
  mobile_url: string;
  lan_url?: string;
  public_url?: string | null;
  is_tunnel_active?: boolean;
  tunnel_status?: string;
  qr_code_url: string;
  lan_qr_code_url?: string;
  instructions: string;
}

export interface TunnelStatus {
  status: 'STOPPED' | 'CONNECTING' | 'ACTIVE' | 'ERROR';
  public_url: string | null;
  local_ip: string;
  port: number;
  local_url: string;
  lan_url: string;
  is_active: boolean;
}

// Dynamic Remote Backend Resolver (Enables 100% full-fledged Vercel deployment with local workstation agent)
export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('jarvis_backend_url');
    if (saved) return saved.replace(/\/+$/, '');
  }
  const envUrl = (import.meta as any).env?.VITE_BACKEND_URL;
  if (envUrl) return envUrl.replace(/\/+$/, '');
  return '';
}

if (typeof window !== 'undefined' && window.fetch) {
  const nativeFetch = window.fetch.bind(window);
  window.fetch = (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    if (typeof input === 'string' && (input.startsWith('/api') || input.startsWith('/output'))) {
      const base = getApiBaseUrl();
      if (base) {
        input = `${base}${input}`;
      }
    }
    return nativeFetch(input, init);
  };
}

export const api = {
  async getMobileInfo(): Promise<MobileNetworkInfo> {
    const res = await fetch('/api/network/mobile-info');
    return res.json();
  },

  async getTunnelStatus(): Promise<TunnelStatus> {
    const res = await fetch('/api/network/tunnel');
    return res.json();
  },

  async startTunnel(): Promise<TunnelStatus> {
    const res = await fetch('/api/network/tunnel/start', { method: 'POST' });
    return res.json();
  },

  async stopTunnel(): Promise<TunnelStatus> {
    const res = await fetch('/api/network/tunnel/stop', { method: 'POST' });
    return res.json();
  },

  async getState(): Promise<JarvisState> {
    const res = await fetch('/api/state');
    return res.json();
  },

  async sendChat(message: string, sessionId = 'default_session'): Promise<{ reply: string; audio_url?: string }> {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId, synthesize_audio: true }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Server error (${res.status}): ${errText}`);
    }
    return res.json();
  },

  async orchestrateDirective(command: string): Promise<any> {
    const res = await fetch('/api/orchestrate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    });
    return res.json();
  },

  async triggerEmergencyStop(): Promise<void> {
    await fetch('/api/emergency-stop', { method: 'POST' });
  },

  async resetEmergency(): Promise<void> {
    await fetch('/api/reset-emergency', { method: 'POST' });
  },

  async getClips(): Promise<ClipItem[]> {
    const res = await fetch('/api/clips');
    return res.json();
  },

  async generateClips(
    videoPath: string,
    numClips = 3,
    targetDuration = 45,
    stylePreset = 'podcast',
    autoPublishYouTube = false,
    publishIntervalMinutes = 45,
    privacy = 'schedule'
  ): Promise<any> {
    const res = await fetch('/api/clips/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_path: videoPath,
        num_clips: numClips,
        target_duration: targetDuration,
        style_preset: stylePreset,
        auto_publish_youtube: autoPublishYouTube,
        publish_interval_minutes: publishIntervalMinutes,
        privacy: privacy
      }),
    });
    return res.json();
  },

  async generateClipsFromYouTube(
    youtubeUrl: string,
    numClips = 3,
    targetDuration = 45,
    stylePreset = 'podcast',
    autoPublishYouTube = true,
    publishIntervalMinutes = 45,
    privacy = 'schedule'
  ): Promise<any> {
    const res = await fetch('/api/clips/generate-from-youtube', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        youtube_url: youtubeUrl,
        num_clips: numClips,
        target_duration: targetDuration,
        style_preset: stylePreset,
        auto_publish_youtube: autoPublishYouTube,
        publish_interval_minutes: publishIntervalMinutes,
        privacy: privacy
      }),
    });
    return res.json();
  },

  async getViralAutopilotPresets(): Promise<any[]> {
    const res = await fetch('/api/autopilot/presets');
    return res.json();
  },

  async getViralAutopilotStatus(): Promise<any> {
    const res = await fetch('/api/autopilot/status');
    return res.json();
  },

  async getPortalSummary(): Promise<any> {
    const res = await fetch('/api/portal/summary');
    return res.json();
  },

  async startViralAutopilot(params: {
    youtubeUrl?: string;
    preset?: string;
    searchTopic?: string;
    numClips?: number;
    targetDuration?: number;
    intervalMinutes?: number;
    uploadTillLimit?: boolean;
    platform?: 'both' | 'youtube' | 'instagram';
    privacy?: 'public' | 'unlisted' | 'private';
  }): Promise<any> {
    const res = await fetch('/api/autopilot/viral-start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        youtube_url: params.youtubeUrl || null,
        preset: params.preset || null,
        search_topic: params.searchTopic || null,
        num_clips: params.numClips ?? 4,
        target_duration: params.targetDuration ?? 45,
        interval_minutes: params.intervalMinutes ?? 45,
        upload_till_limit: params.uploadTillLimit ?? true,
        platform: params.platform ?? 'both',
        privacy: params.privacy ?? 'public',
      }),
    });
    return res.json();
  },

  async getScreenPreview(): Promise<{ width: number; height: number; preview_base64: string }> {
    const res = await fetch('/api/screen/preview');
    return res.json();
  },

  async clipLivestream(params: {
    urlOrTopic?: string;
    durationSeconds?: number;
    numClips?: number;
    targetClipDuration?: number;
    stylePreset?: string;
    autoUpload?: boolean;
    visibility?: string;
  }): Promise<any> {
    const res = await fetch('/api/livestream/clip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url_or_topic: params.urlOrTopic || null,
        duration_seconds: params.durationSeconds ?? 45,
        num_clips: params.numClips ?? 2,
        target_clip_duration: params.targetClipDuration ?? 30.0,
        style_preset: params.stylePreset ?? 'podcast',
        auto_upload: params.autoUpload ?? false,
        visibility: params.visibility ?? 'public',
      }),
    });
    return res.json();
  },

  async getLivestreamStatus(): Promise<any> {
    const res = await fetch('/api/livestream/status');
    return res.json();
  },

  async discoverLivestreams(topic?: string, limit: number = 5): Promise<any[]> {
    const q = topic ? `?topic=${encodeURIComponent(topic)}&limit=${limit}` : `?limit=${limit}`;
    const res = await fetch(`/api/livestream/discover${q}`);
    return res.json();
  },

  async executeTool(toolName: string, parameters: Record<string, any> = {}): Promise<any> {
    const res = await fetch('/api/tools/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_name: toolName, parameters }),
    });
    return res.json();
  },

  async getMemories(): Promise<MemoryItem[]> {
    const res = await fetch('/api/memories');
    return res.json();
  },

  async addMemory(category: string, key: string, value: string): Promise<any> {
    const res = await fetch('/api/memories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, key, value }),
    });
    return res.json();
  },

  async deleteMemory(id: number): Promise<any> {
    const res = await fetch(`/api/memories/${id}`, { method: 'DELETE' });
    return res.json();
  },

  // --- RLHF (Reinforcement Learning from Human Feedback) ---
  async submitRLHFFeedback(data: {
    context_type?: string;
    prompt_or_input: string;
    action_or_output: string;
    feedback_type: 'positive' | 'negative' | 'correction';
    user_correction?: string;
    category?: string;
  }): Promise<any> {
    const res = await fetch('/api/rlhf/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async getRLHFRules(category?: string): Promise<RLHFRule[]> {
    const res = await fetch(category ? `/api/rlhf/rules?category=${category}` : '/api/rlhf/rules');
    return res.json();
  },

  async addRLHFRule(rule_text: string, category = 'general', reward_weight = 2.0): Promise<any> {
    const res = await fetch('/api/rlhf/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule_text, category, reward_weight }),
    });
    return res.json();
  },

  async toggleRLHFRule(ruleId: number): Promise<any> {
    const res = await fetch(`/api/rlhf/rules/${ruleId}/toggle`, { method: 'POST' });
    return res.json();
  },

  async deleteRLHFRule(ruleId: number): Promise<any> {
    const res = await fetch(`/api/rlhf/rules/${ruleId}`, { method: 'DELETE' });
    return res.json();
  },

  async getRLHFSummary(): Promise<RLHFSummary> {
    const res = await fetch('/api/rlhf/summary');
    return res.json();
  },

  async getYouTubeStatus(): Promise<any> {
    const res = await fetch('/api/social/youtube');
    return res.json();
  },

  async getYouTubeBrowserStatus(): Promise<any> {
    const res = await fetch('/api/social/youtube/browser-status');
    return res.json();
  },

  async openYouTubeBrowserLogin(): Promise<any> {
    const res = await fetch('/api/social/youtube/browser-login', { method: 'POST' });
    return res.json();
  },

  async uploadViaBrowser(clipId: string, title: string, description: string, tags: string[] = [], privacy = 'public'): Promise<any> {
    const res = await fetch('/api/social/youtube/browser-upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_id: clipId, title, description, tags, privacy, headless: false })
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err);
    }
    return res.json();
  },

  async publishToYouTube(clipId: string, title: string, description: string, tags: string[] = [], privacy = 'public'): Promise<any> {
    const res = await fetch('/api/social/youtube/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_id: clipId, title, description, tags, privacy }),
    });
    return res.json();
  },

  async getInstagramStatus(): Promise<any> {
    const res = await fetch('/api/social/instagram');
    return res.json();
  },

  async getInstagramBrowserStatus(): Promise<any> {
    const res = await fetch('/api/social/instagram/browser-status');
    return res.json();
  },

  async openInstagramBrowserLogin(): Promise<any> {
    const res = await fetch('/api/social/instagram/browser-login', { method: 'POST' });
    return res.json();
  },

  async autoLoginInstagram(username = 'clipperwithout', password = ''): Promise<any> {
    const res = await fetch('/api/social/instagram/auto-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    return res.json();
  },

  async publishToInstagram(
    options:
      | {
          clipId?: string;
          videoPath?: string;
          caption: string;
          tags?: string[];
          headless?: boolean;
          method?: string;
        }
      | string,
    legacyCaption?: string
  ): Promise<any> {
    const payload =
      typeof options === 'string'
        ? { clip_id: options, caption: legacyCaption || '' }
        : {
            clip_id: options.clipId,
            video_path: options.videoPath,
            caption: options.caption,
            tags: options.tags,
            headless: options.headless ?? false,
            method: options.method ?? 'browser',
          };

    const res = await fetch('/api/social/instagram/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.json();
  },

  async scheduleInstagramReel(options: {
    videoPath?: string;
    clipId?: string;
    caption: string;
    scheduledTime: string;
    tags?: string[];
  }): Promise<any> {
    const res = await fetch('/api/social/instagram/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_path: options.videoPath,
        clip_id: options.clipId,
        caption: options.caption,
        scheduled_time: options.scheduledTime,
        tags: options.tags,
      }),
    });
    return res.json();
  },

  async getInstagramQueue(limit = 50, offset = 0, status?: string): Promise<any[]> {
    let url = `/api/social/instagram/queue?limit=${limit}&offset=${offset}`;
    if (status) url += `&status=${status}`;
    const res = await fetch(url);
    return res.json();
  },

  async deleteInstagramQueueItem(itemId: string): Promise<any> {
    const res = await fetch(`/api/social/instagram/queue/${itemId}`, { method: 'DELETE' });
    return res.json();
  },

  async browseLocalVideos(): Promise<any[]> {
    const res = await fetch('/api/files/browse');
    return res.json();
  },

  async openInExplorer(path: string): Promise<any> {
    const res = await fetch('/api/files/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    return res.json();
  },

  async renderCustomClip(clipId: string, stylePreset = 'podcast', trimSilence = false): Promise<any> {
    const res = await fetch('/api/video/render-custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_id: clipId, style_preset: stylePreset, trim_silence: trimSilence }),
    });
    return res.json();
  },

  async transcribeAudio(audioBlob: Blob, filename = 'speech.wav'): Promise<{ text: string; language: string; duration: number }> {
    const formData = new FormData();
    formData.append('file', audioBlob, filename);
    const res = await fetch('/api/voice/transcribe', {
      method: 'POST',
      body: formData,
    });
    return res.json();
  },

  async speakText(text: string, playLocal = false): Promise<{ status: string; audio_url: string }> {
    const res = await fetch('/api/voice/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, play_local: playLocal }),
    });
    return res.json();
  },

  async stopVoice(): Promise<{ status: string }> {
    const res = await fetch('/api/voice/stop', { method: 'POST' });
    return res.json();
  },

  async getViralIdeas(niche?: string, count: number = 6): Promise<any[]> {
    const q = niche ? `?niche=${encodeURIComponent(niche)}&count=${count}` : `?count=${count}`;
    const res = await fetch(`/api/research/ideas${q}`);
    return res.json();
  },

  async getResearchTrends(niche: string = 'gaming'): Promise<any> {
    const res = await fetch(`/api/research/trends?niche=${encodeURIComponent(niche)}`);
    return res.json();
  },

  async getGrowthPlan(): Promise<any> {
    const res = await fetch('/api/research/growth-plan');
    return res.json();
  },

  async applyResearchToPipeline(payload: any = {}): Promise<any> {
    const res = await fetch('/api/research/apply-to-pipeline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.json();
  },

  async getAuditLogs(): Promise<any[]> {
    const res = await fetch('/api/audit-logs');
    return res.json();
  },

  async downloadYouTube(url: string, autoClip = true, numClips = 5, duration = 45, stylePreset = 'podcast'): Promise<any> {
    const res = await fetch('/api/youtube/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, auto_clip: autoClip, num_clips: numClips, target_duration: duration, style_preset: stylePreset }),
    });
    return res.json();
  },

  async getCaptionStyles(): Promise<CaptionStyle[]> {
    const res = await fetch('/api/video/caption-styles');
    return res.json();
  },

  async getYouTubeMeta(url: string): Promise<any> {
    const res = await fetch('/api/youtube/metadata', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    return res.json();
  },

  async getDownloadedPodcasts(): Promise<any[]> {
    const res = await fetch('/api/youtube/podcasts');
    return res.json();
  },

  async splitLongVideo(videoPath: string, numClips = 5, duration = 45, stylePreset = 'podcast'): Promise<any> {
    const res = await fetch('/api/video/split-long', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_path: videoPath, num_clips: numClips, target_duration: duration, style_preset: stylePreset }),
    });
    return res.json();
  },

  async resetPipeline(): Promise<any> {
    const res = await fetch('/api/pipeline/reset', { method: 'POST' });
    return res.json();
  },

  async getDaVinciStatus(): Promise<any> {
    const res = await fetch('/api/davinci/status');
    return res.json();
  },

  async exportDaVinciTimeline(videoPath?: string, timelineName?: string, clipIds?: string[]): Promise<any> {
    const res = await fetch('/api/davinci/export-timeline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_path: videoPath, timeline_name: timelineName, clip_ids: clipIds }),
    });
    return res.json();
  },

  async openDaVinciFolder(): Promise<any> {
    const res = await fetch('/api/davinci/open-folder', { method: 'POST' });
    return res.json();
  },

  async getDaVinciMcpStatus(): Promise<any> {
    const res = await fetch('/api/davinci/mcp/status');
    return res.json();
  },

  async getDaVinciMcpCatalog(): Promise<any> {
    const res = await fetch('/api/davinci/mcp/catalog');
    return res.json();
  },

  async callDaVinciMcpTool(tool: string, args: Record<string, any> = {}): Promise<any> {
    const res = await fetch('/api/davinci/mcp/call', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool, arguments: args }),
    });
    return res.json();
  },

  async switchDaVinciPage(page: string): Promise<any> {
    const res = await fetch('/api/davinci/mcp/page', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page }),
    });
    return res.json();
  },

  async createDaVinciProject(name: string, verticalShorts: boolean = true): Promise<any> {
    const res = await fetch('/api/davinci/mcp/project/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, vertical_shorts: verticalShorts }),
    });
    return res.json();
  },

  async startDaVinciRender(): Promise<any> {
    const res = await fetch('/api/davinci/mcp/render', { method: 'POST' });
    return res.json();
  },

  async getDaVinciRenderStatus(): Promise<any> {
    const res = await fetch('/api/davinci/mcp/render-status');
    return res.json();
  },

  async getDaVinciRegistry(): Promise<any> {
    const res = await fetch('/api/davinci/mcp/registry');
    return res.json();
  },

  async executeDaVinciTool(tool: string, args: Record<string, any> = {}): Promise<any> {
    const res = await fetch('/api/davinci/mcp/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool, arguments: args }),
    });
    return res.json();
  },

  // --- JARVIS Video Studio API ---
  async listStudioProjects(): Promise<StudioProject[]> {
    const res = await fetch('/api/studio/projects');
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async createStudioProject(name: string, aspectRatio = '16:9', fps = 30): Promise<StudioProject> {
    const res = await fetch('/api/studio/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, aspect_ratio: aspectRatio, fps }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getStudioProject(id: string): Promise<StudioProject> {
    const res = await fetch(`/api/studio/projects/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async saveStudioProject(id: string, project: StudioProject): Promise<StudioProject> {
    const res = await fetch(`/api/studio/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(project),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async deleteStudioProject(id: string): Promise<{ success: boolean; deleted_id: string }> {
    const res = await fetch(`/api/studio/projects/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async duplicateStudioProject(id: string): Promise<StudioProject> {
    const res = await fetch(`/api/studio/projects/${id}/duplicate`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async splitStudioClip(id: string, clipId: string, splitTime: number): Promise<{ project: StudioProject; new_clip: StudioClip }> {
    const res = await fetch(`/api/studio/projects/${id}/split`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_id: clipId, split_time: splitTime }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async executeStudioAIEdit(
    id: string,
    command: string,
    clipId?: string,
    playheadTime?: number
  ): Promise<{ success: boolean; action: string; message: string; project: StudioProject; export_triggered?: boolean; export_job_id?: string }> {
    const res = await fetch(`/api/studio/projects/${id}/ai-edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, selected_clip_id: clipId, playhead_time: playheadTime }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async exportStudioProject(id: string, req: Partial<ExportRequest>): Promise<{ job_id: string; status: string; project_id: string }> {
    const res = await fetch(`/api/studio/projects/${id}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: id, ...req }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getStudioJobStatus(jobId: string): Promise<any> {
    const res = await fetch(`/api/studio/jobs/${jobId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async listStudioJobs(): Promise<any[]> {
    const res = await fetch('/api/studio/jobs');
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async exportStudioFcpxml(id: string): Promise<{ success: boolean; fcpxml_path: string; download_url: string; project_name: string }> {
    const res = await fetch(`/api/studio/projects/${id}/export-fcpxml`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async importClippedToStudio(id?: string, videoPath?: string, name?: string, startTime?: number): Promise<any> {
    const cleanId = id && id.trim() && id !== 'undefined' && id !== 'null' ? encodeURIComponent(id.trim()) : '';
    const targetUrl = cleanId ? `/api/studio/projects/${cleanId}/import-clipped` : `/api/studio/projects/import-clipped`;
    const res = await fetch(targetUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_path: videoPath, name, start_time: startTime, project_id: id }),
    });
    if (!res.ok) {
      const errRaw = await res.text();
      let msg = errRaw;
      try {
        const parsed = JSON.parse(errRaw);
        if (parsed.detail) {
          msg = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
        }
      } catch {}
      throw new Error(msg);
    }
    return res.json();
  },

  async uploadStudioMedia(file: File): Promise<{ success: boolean; filename: string; path: string; url: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/studio/upload', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async ingestDriveVideo(driveUrl: string, customTitle?: string, privacy?: string, autoUpload?: boolean): Promise<any> {
    const res = await fetch('/api/social/drive/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        drive_url: driveUrl,
        custom_title: customTitle,
        privacy: privacy || 'public',
        auto_upload: autoUpload !== undefined ? autoUpload : true,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Drive ingestion failed' }));
      throw new Error(err.detail || 'Drive ingestion failed');
    }
    return res.json();
  },

  async importDriveFolderQueue(folderUrl: string, intervalMinutes = 60, dailyCap = 18, applyJitter = true): Promise<any> {
    const res = await fetch('/api/social/youtube/queue/import-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        folder_url: folderUrl,
        interval_minutes: intervalMinutes,
        daily_cap: dailyCap,
        apply_jitter: applyJitter
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to import folder' }));
      throw new Error(err.detail || 'Failed to import folder');
    }
    return res.json();
  },

  async getYouTubeQueue(limit = 50, offset = 0, status?: string): Promise<any[]> {
    let url = `/api/social/youtube/queue?limit=${limit}&offset=${offset}`;
    if (status) url += `&status=${status}`;
    const res = await fetch(url);
    return res.json();
  },

  async getYouTubeQueueStats(): Promise<any> {
    const res = await fetch('/api/social/youtube/queue/stats');
    return res.json();
  },

  async pauseYouTubeQueue(): Promise<any> {
    const res = await fetch('/api/social/youtube/queue/pause', { method: 'POST' });
    return res.json();
  },

  async resumeYouTubeQueue(): Promise<any> {
    const res = await fetch('/api/social/youtube/queue/resume', { method: 'POST' });
    return res.json();
  },

  async dispatchNextQueueItem(): Promise<any> {
    const res = await fetch('/api/social/youtube/queue/dispatch-next', { method: 'POST' });
    return res.json();
  },

  async deleteQueueItem(itemId: string): Promise<any> {
    const res = await fetch(`/api/social/youtube/queue/${itemId}`, { method: 'DELETE' });
    return res.json();
  },

  async clearYouTubeQueue(): Promise<any> {
    const res = await fetch('/api/social/youtube/queue', { method: 'DELETE' });
    return res.json();
  },

  async rescheduleYouTubeQueue(intervalMinutes = 45): Promise<any> {
    const res = await fetch('/api/social/youtube/queue/reschedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interval_minutes: intervalMinutes }),
    });
    return res.json();
  },

  async uploadTillDailyLimit(intervalMinutes = 45): Promise<any> {
    const res = await fetch('/api/social/youtube/queue/upload-till-limit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interval_minutes: intervalMinutes }),
    });
    return res.json();
  }
};

