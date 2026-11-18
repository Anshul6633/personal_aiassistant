import React, { useState } from 'react';
import {
  Film,
  Play,
  Share2,
  Copy,
  Check,
  Sparkles,
  Download,
  Flame,
  Award,
  Clock,
  Layers,
  PlaySquare,
  Camera,
  Video,
  Globe,
  ArrowDownToLine,
  Sliders,
  Monitor,
  CheckCircle2,
  AlertCircle,
  Search,
  Code,
  Terminal,
  Wrench,
  Palette,
  Type,
  Trash2
} from 'lucide-react';
import { ClipItem, CaptionStyle, api } from '../services/api';

const DEFAULT_CAPTION_STYLES: CaptionStyle[] = [
  {
    id: "gta6",
    name: "GTA VI Vice Neon",
    tag: "GTA VI Official",
    font: "Impact Heavy",
    primary_color: "#FFFFFF",
    highlight_color: "#FF2A85",
    outline_color: "#180220",
    sample: "VICE CITY 2026 // WANTED ★★★★★",
    desc: "Official GTA VI Vice City aesthetic: brilliant white typography with dual flamingo pink & cyan keyword pops and deep midnight violet outline.",
    size: 84
  },
  {
    id: "podcast",
    name: "Hormozi Viral Pop",
    tag: "Trending",
    font: "Arial Bold",
    primary_color: "#FFFF00",
    highlight_color: "#39FF14",
    outline_color: "#000000",
    sample: "MAKE A MILLION TODAY",
    desc: "Bold yellow dialogue with punchy neon lime keyword pops and thick black outline.",
    size: 72
  },
  {
    id: "mrbeast",
    name: "MrBeast High Impact",
    tag: "High Energy",
    font: "Impact Bold",
    primary_color: "#00FFFF",
    highlight_color: "#FFFF00",
    outline_color: "#000000",
    sample: "WIN $100,000 NOW!",
    desc: "Oversized bold impact font in electric cyan with blazing yellow highlights and 8px stroke.",
    size: 78
  },
  {
    id: "cyberpunk",
    name: "Cyberpunk Neon",
    tag: "Futuristic",
    font: "Impact Neon",
    primary_color: "#00FFFF",
    highlight_color: "#39FF14",
    outline_color: "#FF00FF",
    sample: "THE FUTURE IS HERE",
    desc: "Futuristic neon cyan font glowing against a hot magenta stroke with lime accents.",
    size: 72
  },
  {
    id: "flame",
    name: "Arcade Flame",
    tag: "Gaming",
    font: "Impact Heavy",
    primary_color: "#FFA500",
    highlight_color: "#FFFF00",
    outline_color: "#000000",
    sample: "SMASH IT OR LOSE IT",
    desc: "High-intensity orange & red street aesthetic with burning golden keyword highlights.",
    size: 74
  },
  {
    id: "motivational",
    name: "Regal Gold",
    tag: "Luxury",
    font: "Georgia Serif",
    primary_color: "#FBBF24",
    highlight_color: "#FFFF00",
    outline_color: "#000000",
    sample: "MASTER YOUR MINDSET",
    desc: "Elegant Georgia serif typography with luxury gold leaf and warm amber emphasis.",
    size: 66
  },
  {
    id: "educational",
    name: "Clean Modern",
    tag: "Tutorial",
    font: "Segoe UI",
    primary_color: "#FFFFFF",
    highlight_color: "#00FFFF",
    outline_color: "#000000",
    sample: "HOW THIS ACTUALLY WORKS",
    desc: "Minimal tech and tutorial layout with pure white sans-serif and vibrant cyan cues.",
    size: 64
  },
  {
    id: "news",
    name: "Breaking News",
    tag: "Broadcast",
    font: "Arial Heavy",
    primary_color: "#FFFFFF",
    highlight_color: "#FFD700",
    outline_color: "#8B0000",
    sample: "BREAKING: SPECIAL REPORT",
    desc: "Authoritative broadcast chyron bar with high-contrast text on crimson backing.",
    size: 60
  },
  {
    id: "cinematic",
    name: "Minimal Aesthetic",
    tag: "Cinema",
    font: "Helvetica",
    primary_color: "#E2E8F0",
    highlight_color: "#FFFFFF",
    outline_color: "#000000",
    sample: "a quiet observation",
    desc: "Understated film festival aesthetic with subtle platinum typography and low opacity.",
    size: 56
  }
];

interface ContentStudioProps {
  clips: ClipItem[];
  onRefreshClips: () => void;
}

export const ContentStudio: React.FC<ContentStudioProps> = ({ clips, onRefreshClips }) => {
  const [selectedClip, setSelectedClip] = useState<ClipItem | null>(clips[0] || null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [sourceType, setSourceType] = useState<'youtube' | 'local' | 'davinci'>('youtube');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [videoInputPath, setVideoInputPath] = useState('jarvis/tests/sample_podcast.mp4');
  const [clipCount, setClipCount] = useState(5);
  const [clipDuration, setClipDuration] = useState(45);
  const [stylePreset, setStylePreset] = useState('podcast');
  const [captionStyles, setCaptionStyles] = useState<CaptionStyle[]>(DEFAULT_CAPTION_STYLES);
  const [clipCaptionStyle, setClipCaptionStyle] = useState<string>('podcast');
  const [isRestylingCaption, setIsRestylingCaption] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processMessage, setProcessMessage] = useState('');
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [ytPreview, setYtPreview] = useState<any>(null);
  const [isLoadingMeta, setIsLoadingMeta] = useState(false);

  // DaVinci Resolve MCP States
  const [davinciStatus, setDavinciStatus] = useState<any>(null);
  const [davinciActivePage, setDavinciActivePage] = useState<string>('edit');
  const [davinciProjectName, setDavinciProjectName] = useState<string>('Podcast_Shorts_9x16');
  const [isDavinciLoading, setIsDavinciLoading] = useState<boolean>(false);

  // 440+ MCP Tools Catalog States
  const [mcpCatalog, setMcpCatalog] = useState<any>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [toolSearchQuery, setToolSearchQuery] = useState<string>('');
  const [activeTool, setActiveTool] = useState<any>(null);
  const [toolArgsJson, setToolArgsJson] = useState<string>('{}');
  const [toolExecutionOutput, setToolExecutionOutput] = useState<any>(null);
  const [isExecutingTool, setIsExecutingTool] = useState<boolean>(false);

  const [downloadedPodcasts, setDownloadedPodcasts] = useState<any[]>([]);
  const [taskProgress, setTaskProgress] = useState<number>(0);
  const [activeClippingPodcast, setActiveClippingPodcast] = useState<string | null>(null);
  const [clipFilter, setClipFilter] = useState<string>('all');
  const pollingRef = React.useRef<any>(null);

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  React.useEffect(() => {
    return () => stopPolling();
  }, []);

  const fetchDownloadedPodcasts = async () => {
    try {
      const list = await api.getDownloadedPodcasts();
      setDownloadedPodcasts(list);
    } catch (e: any) {
      console.error("Failed to fetch downloaded podcasts:", e);
    }
  };

  const startPipelinePolling = (onSuccessNotice?: string) => {
    stopPolling();
    setIsProcessing(true);
    let attempts = 0;
    const maxAttempts = 300; // up to 10 minutes (300 * 2s)

    pollingRef.current = setInterval(async () => {
      attempts++;
      try {
        const s = await api.getState();
        if (s) {
          if (s.status_message) {
            setProcessMessage(s.status_message);
          }
          if (typeof s.task_progress === 'number' && s.task_progress > 0) {
            setTaskProgress(s.task_progress);
          }

          // Periodic refresh of clips and downloaded podcasts
          if (attempts % 2 === 0) {
            onRefreshClips();
            fetchDownloadedPodcasts();
          }

          // Check completion
          const isDone =
            s.status === 'IDLE' &&
            attempts >= 3 &&
            (s.task_progress === 100 ||
              s.status_message?.toLowerCase().includes('successfully') ||
              s.status_message?.toLowerCase().includes('produced'));

          if (isDone || attempts >= maxAttempts) {
            stopPolling();
            setIsProcessing(false);
            setActiveClippingPodcast(null);
            setTaskProgress(100);
            onRefreshClips();
            fetchDownloadedPodcasts();
            showNotice(onSuccessNotice || 'Shorts generated successfully!');
            setTimeout(() => {
              setProcessMessage('');
              setTaskProgress(0);
            }, 6000);
          }
        }
      } catch (err) {
        console.error("Pipeline polling error:", err);
      }
    }, 2000);
  };

  React.useEffect(() => {
    fetchDownloadedPodcasts();
    // Auto-resume polling if background pipeline is already running
    api.getState().then((s) => {
      if (s && (s.status === 'EDITING' || s.status === 'EXECUTING' || s.status === 'PLANNING')) {
        setIsProcessing(true);
        setProcessMessage(s.status_message || 'Video pipeline active in background...');
        setTaskProgress(s.task_progress || 10);
        startPipelinePolling('Background video clipping completed!');
      }
    }).catch(() => {});
  }, []);

  React.useEffect(() => {
    api.getCaptionStyles().then((styles) => {
      if (styles && styles.length > 0) {
        setCaptionStyles(styles);
      }
    }).catch((e) => console.error("Error loading caption styles:", e));
  }, []);

  const handleApplyCaptionStyleToClip = async () => {
    if (!selectedClip || isRestylingCaption) return;
    setIsRestylingCaption(true);
    const styleObj = captionStyles.find(s => s.id === clipCaptionStyle);
    showNotice(`Burning "${styleObj?.name || clipCaptionStyle}" caption style onto vertical clip...`);

    try {
      const res = await api.renderCustomClip(selectedClip.id, clipCaptionStyle, false);
      if (res.status === 'SUCCESS' && res.video_url) {
        showNotice(`Applied "${styleObj?.name || clipCaptionStyle}" style successfully!`);
        setSelectedClip(prev => prev ? {
          ...prev,
          video_url: `${res.video_url}?t=${Date.now()}`,
          thumb_url: res.thumb_url ? `${res.thumb_url}?t=${Date.now()}` : prev.thumb_url
        } : null);
        onRefreshClips();
      } else {
        showNotice(`Restyle note: ${res.message || 'Render completed'}`);
      }
    } catch (e: any) {
      showNotice(`Caption style error: ${e.message}`);
    } finally {
      setIsRestylingCaption(false);
    }
  };

  const countPodcastClips = (podcast: any) => {
    if (!clips || !podcast) return 0;
    const pPath = (podcast.file_path || '').toLowerCase();
    const pName = (podcast.filename || '').toLowerCase();
    return clips.filter((c) => {
      if (!c.source_file) return false;
      const s = c.source_file.toLowerCase();
      return s === pPath || (pName && s.includes(pName));
    }).length;
  };



  // Auto-select first clip if none is selected
  React.useEffect(() => {
    if (!selectedClip && clips.length > 0) {
      setSelectedClip(clips[0]);
    }
  }, [clips, selectedClip]);

  const showNotice = (msg: string) => {
    setActionNotice(msg);
    setTimeout(() => setActionNotice(null), 3000);
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    showNotice(`Copied ${id} to clipboard!`);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleQueueYouTube = async (clip: ClipItem) => {
    try {
      const res = await api.publishToYouTube(clip.id, clip.title, clip.caption, clip.tags.split(' '));
      showNotice(res.message || `Queued for YouTube: "${clip.title}"`);
      onRefreshClips();
    } catch (e: any) {
      showNotice(`YouTube error: ${e.message}`);
    }
  };

  const handleQueueInstagram = async (clip: ClipItem) => {
    try {
      const res = await api.publishToInstagram(clip.id, clip.caption);
      showNotice(res.message || `Queued for Instagram: "${clip.title}"`);
      onRefreshClips();
    } catch (e: any) {
      showNotice(`Instagram error: ${e.message}`);
    }
  };

  const handleExportDaVinci = async () => {
    try {
      showNotice("Generating 9:16 vertical DaVinci Resolve FCPXML timeline...");
      const res = await api.exportDaVinciTimeline();
      showNotice(`Exported DaVinci timeline: ${res.filename || 'JARVIS_Shorts.fcpxml'}!`);
      await api.openDaVinciFolder();
    } catch (e: any) {
      showNotice(`DaVinci export error: ${e.message}`);
    }
  };

  const handleClipExistingPodcast = async (podcast: any) => {
    if (isProcessing) return;
    setIsProcessing(true);
    setActiveClippingPodcast(podcast.file_path);
    setTaskProgress(10);
    setProcessMessage(`Autonomous engine ingesting "${podcast.title}" for 9:16 vertical conversion...`);
    try {
      await api.splitLongVideo(podcast.file_path, clipCount, clipDuration, stylePreset);
      showNotice(`Slicing started for "${podcast.title}". Monitoring live progress...`);
      startPipelinePolling(`Successfully sliced "${podcast.title}" into vertical shorts!`);
    } catch (err: any) {
      setProcessMessage(`Error: ${err.message}`);
      setIsProcessing(false);
      setActiveClippingPodcast(null);
      setTaskProgress(0);
    }
  };

  const handleExportPodcastTimeline = async (podcast: any) => {
    try {
      showNotice(`Generating DaVinci Resolve FCPXML timeline for "${podcast.title}"...`);
      const res = await api.exportDaVinciTimeline(podcast.file_path, podcast.title);
      showNotice(`Exported DaVinci timeline: ${res.filename || 'timeline.fcpxml'}!`);
      await api.openDaVinciFolder();
    } catch (e: any) {
      showNotice(`DaVinci export error: ${e.message}`);
    }
  };

  const handleSendPodcastToDaVinciBin = async (podcast: any) => {
    try {
      showNotice(`Sending "${podcast.title}" to DaVinci Resolve Media Pool...`);
      const res = await api.callDaVinciMcpTool('davinci_import_media', {
        file_paths: [podcast.file_path],
        bin_name: 'Podcasts'
      });
      if (res.success) {
        showNotice(res.message || 'Imported into DaVinci Media Pool!');
      } else {
        showNotice(`DaVinci: ${res.error || 'Resolve is offline'}`);
      }
    } catch (e: any) {
      showNotice(`DaVinci error: ${e.message}`);
    }
  };

  const refreshDavinciStatus = async () => {
    setIsDavinciLoading(true);
    try {
      const s = await api.getDaVinciMcpStatus();
      setDavinciStatus(s);
      await loadMcpCatalog();
    } catch (e: any) {
      console.error("DaVinci status error", e);
    } finally {
      setIsDavinciLoading(false);
    }
  };

  const loadMcpCatalog = async () => {
    try {
      const data = await api.getDaVinciMcpCatalog();
      setMcpCatalog(data);
      if (data.categories && data.categories.length > 0 && !activeTool) {
        const firstTool = data.categories[0].tools[0];
        setActiveTool(firstTool);
        initToolArgs(firstTool);
      }
    } catch (e: any) {
      console.error("Catalog load error", e);
    }
  };

  const initToolArgs = (tool: any) => {
    if (!tool || !tool.inputSchema || !tool.inputSchema.properties) {
      setToolArgsJson('{}');
      return;
    }
    const sample: Record<string, any> = {};
    for (const [propName, propDef] of Object.entries<any>(tool.inputSchema.properties)) {
      if (propDef.default !== undefined) {
        sample[propName] = propDef.default;
      } else if (propDef.type === 'string') {
        sample[propName] = '';
      } else if (propDef.type === 'integer' || propDef.type === 'number') {
        sample[propName] = 0;
      } else if (propDef.type === 'boolean') {
        sample[propName] = false;
      } else if (propDef.type === 'array') {
        sample[propName] = [];
      } else {
        sample[propName] = null;
      }
    }
    setToolArgsJson(JSON.stringify(sample, null, 2));
  };

  const handleSelectTool = (tool: any) => {
    setActiveTool(tool);
    initToolArgs(tool);
    setToolExecutionOutput(null);
  };

  const handleExecuteTool = async () => {
    if (!activeTool) return;
    setIsExecutingTool(true);
    setToolExecutionOutput(null);
    try {
      let args = {};
      if (toolArgsJson.trim()) {
        try {
          args = JSON.parse(toolArgsJson);
        } catch (parseErr: any) {
          setToolExecutionOutput({ success: false, error: `Invalid JSON in parameters: ${parseErr.message}` });
          setIsExecutingTool(false);
          return;
        }
      }
      const res = await api.callDaVinciMcpTool(activeTool.name, args);
      setToolExecutionOutput(res);
      showNotice(`Executed ${activeTool.name}`);
    } catch (e: any) {
      setToolExecutionOutput({ success: false, error: e.message });
    } finally {
      setIsExecutingTool(false);
    }
  };

  const handleSwitchDaVinciPage = async (page: string) => {
    try {
      showNotice(`Switching DaVinci Resolve to ${page.toUpperCase()} page...`);
      const res = await api.switchDaVinciPage(page);
      if (res.success) {
        setDavinciActivePage(page);
        showNotice(res.message || `Switched to ${page} page.`);
      } else {
        showNotice(`DaVinci: ${res.error || 'Resolve is offline'}`);
      }
      refreshDavinciStatus();
    } catch (e: any) {
      showNotice(`Page switch error: ${e.message}`);
    }
  };

  const handleCreateShortsProject = async () => {
    try {
      showNotice(`Creating DaVinci project "${davinciProjectName}" (1080x1920)...`);
      const res = await api.createDaVinciProject(davinciProjectName, true);
      if (res.success) {
        showNotice(res.message || 'Project created and configured!');
      } else {
        showNotice(`DaVinci: ${res.error || 'Failed to create project'}`);
      }
      refreshDavinciStatus();
    } catch (e: any) {
      showNotice(`Project creation error: ${e.message}`);
    }
  };

  const handleStartRenderQueue = async () => {
    try {
      showNotice("Starting DaVinci Resolve render queue...");
      const res = await api.startDaVinciRender();
      if (res.success) {
        showNotice(res.message || 'Render queue started!');
      } else {
        showNotice(`DaVinci: ${res.error || 'Failed to start render'}`);
      }
      refreshDavinciStatus();
    } catch (e: any) {
      showNotice(`Render error: ${e.message}`);
    }
  };

  const handleFetchYtMeta = async () => {
    if (!youtubeUrl.trim() || isLoadingMeta) return;
    setIsLoadingMeta(true);
    setProcessMessage('Fetching YouTube metadata and video specs...');
    try {
      const meta = await api.getYouTubeMeta(youtubeUrl);
      setYtPreview(meta);
      setProcessMessage(`Detected: "${meta.title}" (${Math.round(meta.duration / 60)} mins) by ${meta.uploader}`);
    } catch (e: any) {
      setProcessMessage(`Error fetching metadata: ${e.message}`);
    } finally {
      setIsLoadingMeta(false);
    }
  };

  const handleDownloadAndClipYouTube = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!youtubeUrl.trim() || isProcessing) return;

    setIsProcessing(true);
    setTaskProgress(5);
    setProcessMessage(`Downloading YouTube video and queuing ${clipCount} viral shorts...`);

    try {
      const res = await api.downloadYouTube(youtubeUrl, true, clipCount, clipDuration, stylePreset);
      showNotice(`YouTube download started with "${captionStyles.find(s => s.id === stylePreset)?.name || stylePreset}" captions! Producing ${clipCount} shorts.`);
      setProcessMessage(`Download in progress: "${res.title || 'Video'}". AI transcribing and clipping with ${stylePreset} captions...`);
      startPipelinePolling('YouTube video downloaded and converted into vertical shorts!');
    } catch (err: any) {
      setProcessMessage(`Error: ${err.message || 'Download failed'}`);
      setIsProcessing(false);
      setTaskProgress(0);
    }
  };

  const handleRunPipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoInputPath.trim() || isProcessing) return;

    setIsProcessing(true);
    setTaskProgress(5);
    setProcessMessage(`Autonomous engine starting batch of ${clipCount} clips...`);

    try {
      await api.generateClips(videoInputPath, clipCount, clipDuration, stylePreset);
      setProcessMessage(`Pipeline active with ${stylePreset} captions. Transcribing and rendering...`);
      startPipelinePolling(`Batch completed! Produced ${clipCount} vertical shorts.`);
    } catch (err: any) {
      setProcessMessage(`Error: ${err.message || 'Failed to start pipeline'}`);
      setIsProcessing(false);
      setTaskProgress(0);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Film className="w-5 h-5 text-cyan-400" />
            Autonomous Video Factory & YouTube Ingestion
          </h1>
          <p className="text-xs font-mono text-cyan-400/80">
            Download Long Videos • Auto-Slice Multiple 9:16 Shorts • Styled Subtitles
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportDaVinci}
            className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-purple-900/60 to-indigo-900/60 border border-purple-500/40 text-purple-200 text-xs font-mono hover:bg-purple-800/50 cursor-pointer transition-colors flex items-center gap-1.5"
            title="Export 9:16 Vertical FCPXML Timeline for DaVinci Resolve Free or Studio"
          >
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            Export DaVinci Timeline (.xml)
          </button>
          <button
            onClick={onRefreshClips}
            className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-cyan-500/30 text-cyan-300 text-xs font-mono hover:bg-slate-800 cursor-pointer transition-colors"
          >
            Refresh Clips ({clips.length})
          </button>
        </div>
      </div>

      {/* Ingestion & Batch Processing Panel */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-cyan-500/30 shadow-cyan-sm space-y-4">
        {/* Source Mode Tabs */}
        <div className="flex items-center gap-3 border-b border-cyan-500/20 pb-3">
          <button
            onClick={() => setSourceType('youtube')}
            className={`px-4 py-2 rounded-xl text-xs font-mono font-bold uppercase transition-all flex items-center gap-2 cursor-pointer ${
              sourceType === 'youtube'
                ? 'bg-red-500/20 border border-red-500/60 text-red-300 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Video className="w-4 h-4 text-red-400" />
            YouTube Video Ingest & Auto-Clipper
          </button>
          <button
            onClick={() => setSourceType('local')}
            className={`px-4 py-2 rounded-xl text-xs font-mono font-bold uppercase transition-all flex items-center gap-2 cursor-pointer ${
              sourceType === 'local'
                ? 'bg-cyan-500/20 border border-cyan-500/60 text-cyan-300 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Film className="w-4 h-4 text-cyan-400" />
            Local Video Batch Clipper
          </button>
          <button
            onClick={() => { setSourceType('davinci'); refreshDavinciStatus(); }}
            className={`px-4 py-2 rounded-xl text-xs font-mono font-bold uppercase transition-all flex items-center gap-2 cursor-pointer ${
              sourceType === 'davinci'
                ? 'bg-purple-500/20 border border-purple-500/60 text-purple-300 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Layers className="w-4 h-4 text-purple-400" />
            DaVinci Resolve MCP Studio
          </button>
        </div>

        {/* Real-time Autonomous Processing HUD */}
        {isProcessing && (
          <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/80 via-blue-950/80 to-slate-950/80 border border-cyan-500/50 shadow-lg shadow-cyan-950/50 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2 text-cyan-300 font-bold">
                <Sparkles className="w-4 h-4 text-cyan-400 animate-spin" />
                <span className="uppercase tracking-wider">Autonomous Pipeline Active</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-cyan-400 font-bold text-sm">{taskProgress}%</span>
                <button
                  type="button"
                  onClick={async () => {
                    try {
                      await api.resetPipeline();
                      stopPolling();
                      setIsProcessing(false);
                      setTaskProgress(0);
                      setProcessMessage('');
                      showNotice('Pipeline cancelled and reset to idle.');
                    } catch (e: any) {
                      showNotice(`Reset error: ${e.message}`);
                    }
                  }}
                  className="px-2 py-0.5 rounded bg-red-950/70 hover:bg-red-900 border border-red-500/40 text-[10px] text-red-300 cursor-pointer transition-colors"
                  title="Cancel active pipeline and reset status"
                >
                  Cancel / Reset
                </button>
              </div>
            </div>
            {/* Animated Gradient Progress Bar */}
            <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-cyan-500/30">
              <div
                className="bg-gradient-to-r from-cyan-500 via-blue-500 to-emerald-400 h-2.5 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${Math.max(taskProgress, 5)}%` }}
              />
            </div>
            <p className="text-[11px] font-mono text-slate-300 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              <span className="truncate">{processMessage || 'Demuxing audio, transcribing with Faster-Whisper & re-framing to 9:16...'}</span>
            </p>
          </div>
        )}

        {/* YouTube Ingestion Form */}
        {sourceType === 'youtube' ? (
          <div className="space-y-5">
            {/* Quick Sample Presets */}
            <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
              <span className="text-slate-400 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-400" />
                Podcast Presets:
              </span>
              <button
                type="button"
                onClick={() => { setYoutubeUrl('https://www.youtube.com/watch?v=zurNfKQB5Cw'); }}
                className="px-2.5 py-1 rounded-md bg-slate-900 hover:bg-slate-800 border border-red-500/30 text-red-300 transition-colors cursor-pointer"
              >
                Joe Rogan Speech (4m)
              </button>
              <button
                type="button"
                onClick={() => { setYoutubeUrl('https://www.youtube.com/watch?v=0KYvGpvV7Kk'); }}
                className="px-2.5 py-1 rounded-md bg-slate-900 hover:bg-slate-800 border border-red-500/30 text-red-300 transition-colors cursor-pointer"
              >
                Mel Robbins Life Habits (4m)
              </button>
            </div>

            <form onSubmit={handleDownloadAndClipYouTube} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                <div className="md:col-span-5">
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    YOUTUBE URL (PODCAST, INTERVIEW, OR LONG VIDEO)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      value={youtubeUrl}
                      onChange={(e) => setYoutubeUrl(e.target.value)}
                      placeholder="https://www.youtube.com/watch?v=..."
                      className="flex-1 px-3.5 py-2.5 rounded-xl bg-slate-950 border border-cyan-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
                    />
                    <button
                      type="button"
                      onClick={handleFetchYtMeta}
                      disabled={isLoadingMeta || !youtubeUrl.trim()}
                      className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-cyan-500/40 text-xs font-mono text-cyan-300 disabled:opacity-50 transition-colors cursor-pointer"
                    >
                      {isLoadingMeta ? 'Inspecting...' : 'Inspect'}
                    </button>
                  </div>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    NUMBER OF SHORTS
                  </label>
                  <select
                    value={clipCount}
                    onChange={(e) => setClipCount(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-cyan-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
                  >
                    <option value={1}>1 Test Short</option>
                    <option value={3}>3 Viral Shorts</option>
                    <option value={5}>5 Viral Shorts</option>
                    <option value={10}>10 Batch Shorts</option>
                    <option value={20}>20 Multi-Shorts</option>
                  </select>
                </div>

                <div className="md:col-span-3">
                  <label className="block text-xs font-mono text-slate-400 mb-1 flex items-center gap-1">
                    <Palette className="w-3.5 h-3.5 text-cyan-400" />
                    CAPTION STYLE
                  </label>
                  <select
                    value={stylePreset}
                    onChange={(e) => setStylePreset(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-cyan-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
                  >
                    {captionStyles.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.tag})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="md:col-span-2">
                  <button
                    type="submit"
                    disabled={isProcessing || !youtubeUrl.trim()}
                    className="w-full py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-slate-950 font-bold text-xs uppercase tracking-wider shadow-cyan-sm disabled:opacity-50 cursor-pointer transition-all flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    <span>{isProcessing ? 'DOWNLOADING...' : 'DOWNLOAD & CLIP'}</span>
                  </button>
                </div>
              </div>

              {/* YouTube Preview Card if fetched */}
              {ytPreview && (
                <div className="p-3 rounded-xl bg-slate-950/80 border border-red-500/30 flex items-center gap-4">
                  {ytPreview.thumbnail && (
                    <img src={ytPreview.thumbnail} alt="" className="w-24 h-16 object-cover rounded-lg border border-red-500/40" />
                  )}
                  <div className="flex-1 min-w-0">
                    <h4 className="text-xs font-bold text-slate-200 truncate">{ytPreview.title}</h4>
                    <p className="text-[11px] font-mono text-slate-400">
                      Channel: {ytPreview.uploader} • Duration: {Math.round(ytPreview.duration / 60)} mins • Views: {ytPreview.view_count?.toLocaleString() || 'N/A'}
                    </p>
                  </div>
                </div>
              )}
            </form>

            {/* Downloaded Podcasts Ready For Editing */}
            <div className="pt-4 border-t border-cyan-500/20 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Film className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
                    Downloaded Podcasts (Ready for Editing & Auto-Clipping)
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    {downloadedPodcasts.length} Local Files
                  </span>
                </div>
                <button
                  type="button"
                  onClick={fetchDownloadedPodcasts}
                  className="text-[11px] font-mono text-cyan-400 hover:underline cursor-pointer"
                >
                  Refresh List
                </button>
              </div>

              {downloadedPodcasts.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {downloadedPodcasts.map((podcast) => (
                    <div
                      key={podcast.file_path}
                      className="p-3.5 rounded-xl bg-slate-950/80 border border-emerald-500/30 hover:border-emerald-500/60 transition-all space-y-3 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex flex-wrap items-center justify-between gap-1.5 mb-1.5">
                          <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                            <CheckCircle2 className="w-2.5 h-2.5" />
                            READY FOR EDITING
                          </span>
                          {countPodcastClips(podcast) > 0 && (
                            <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center gap-1">
                              <Sparkles className="w-2.5 h-2.5 text-cyan-400" />
                              {countPodcastClips(podcast)} SHORTS READY
                            </span>
                          )}
                          <span className="text-[10px] font-mono text-slate-400">
                            {podcast.size_mb} MB
                          </span>
                        </div>
                        <h4 className="text-xs font-bold text-slate-200 line-clamp-2 leading-snug" title={podcast.title}>
                          {podcast.title}
                        </h4>
                        <p className="text-[10px] font-mono text-slate-400 truncate mt-1" title={podcast.file_path}>
                          {podcast.filename}
                        </p>
                      </div>

                      {/* Quick Actions */}
                      <div className="grid grid-cols-2 gap-1.5 pt-1">
                        <button
                          type="button"
                          onClick={() => handleClipExistingPodcast(podcast)}
                          disabled={isProcessing}
                          className={`py-1.5 px-2 rounded-lg border text-[10px] font-mono font-bold transition-colors flex items-center justify-center gap-1 cursor-pointer ${
                            isProcessing && activeClippingPodcast === podcast.file_path
                              ? 'bg-amber-500/20 border-amber-500/60 text-amber-300 animate-pulse'
                              : 'bg-cyan-600/30 hover:bg-cyan-500/40 border-cyan-500/40 text-cyan-200 disabled:opacity-50'
                          }`}
                          title="Transcribe & Slice into vertical shorts"
                        >
                          {isProcessing && activeClippingPodcast === podcast.file_path ? (
                            <>
                              <Sparkles className="w-3 h-3 text-amber-400 animate-spin" />
                              <span>Slicing ({taskProgress}%)...</span>
                            </>
                          ) : (
                            <>
                              <Flame className="w-3 h-3 text-cyan-400" />
                              <span>Auto-Clip ({clipCount})</span>
                            </>
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleExportPodcastTimeline(podcast)}
                          className="py-1.5 px-2 rounded-lg bg-purple-700/40 hover:bg-purple-600/50 border border-purple-500/40 text-[10px] font-mono font-bold text-purple-200 transition-colors flex items-center justify-center gap-1 cursor-pointer"
                          title="Export 9:16 FCPXML timeline for DaVinci Resolve Free or Studio"
                        >
                          <Layers className="w-3 h-3 text-purple-400" />
                          <span>Export XML</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleSendPodcastToDaVinciBin(podcast)}
                          className="py-1.5 px-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-[10px] font-mono text-slate-300 transition-colors flex items-center justify-center gap-1 cursor-pointer col-span-2"
                          title="Send directly to DaVinci Resolve Media Pool"
                        >
                          <Play className="w-2.5 h-2.5 text-purple-400" />
                          <span>Send to DaVinci Resolve Media Pool</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-slate-950/40 border border-dashed border-slate-800 text-center text-xs font-mono text-slate-500">
                  No downloaded podcast videos found yet. Paste a YouTube URL above and click "Download & Clip".
                </div>
              )}
            </div>
          </div>
        ) : sourceType === 'local' ? (
          /* Local File Processing Form */
          <form onSubmit={handleRunPipeline} className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
            <div className="md:col-span-2">
              <label className="block text-xs font-mono text-slate-400 mb-1">
                LOCAL SOURCE VIDEO PATH
              </label>
              <input
                type="text"
                value={videoInputPath}
                onChange={(e) => setVideoInputPath(e.target.value)}
                placeholder="e.g. C:\Users\Anshul\Videos\podcast.mp4"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-cyan-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                CLIPS COUNT
              </label>
              <select
                value={clipCount}
                onChange={(e) => setClipCount(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-cyan-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
              >
                <option value={1}>1 Test Clip</option>
                <option value={3}>3 Highlight Clips</option>
                <option value={5}>5 Viral Clips</option>
                <option value={10}>10 Batch Clips</option>
                <option value={30}>30 Daily Shorts (Full Target)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1 flex items-center gap-1">
                <Palette className="w-3.5 h-3.5 text-cyan-400" />
                CAPTION STYLE
              </label>
              <select
                value={stylePreset}
                onChange={(e) => setStylePreset(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-cyan-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
              >
                {captionStyles.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <button
                type="submit"
                disabled={isProcessing || !videoInputPath.trim()}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase tracking-wider shadow-cyan-sm disabled:opacity-50 cursor-pointer transition-all flex items-center justify-center gap-2"
              >
                <Flame className="w-4 h-4" />
                <span>{isProcessing ? 'PROCESSING...' : 'PRODUCE CLIPS'}</span>
              </button>
            </div>
          </form>
        ) : (
          /* DaVinci Resolve MCP Studio Controller Panel */
          <div className="space-y-5">
            {/* Connection Status Banner */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 rounded-xl bg-slate-950/80 border border-purple-500/30">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-lg ${davinciStatus?.connected ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-purple-500/20 text-purple-300 border border-purple-500/40'}`}>
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-slate-200">
                      DAVINCI RESOLVE STATUS:
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      davinciStatus?.connected
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : davinciStatus?.running
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : 'bg-purple-900/40 text-purple-300 border border-purple-500/30'
                    }`}>
                      {davinciStatus?.connected ? 'Studio Live Connected' : davinciStatus?.running ? 'Resolve Running (Connecting)' : 'Universal FCPXML Active'}
                    </span>
                  </div>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    {davinciStatus?.connected
                      ? 'Live Python Scripting API active • Direct timeline, bin, and color node control.'
                      : 'Free & Studio Compatible: Automatic FCPXML v1.9 interchange with 9:16 vertical canvas & cut markers.'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={refreshDavinciStatus}
                  disabled={isDavinciLoading}
                  className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-purple-500/30 text-purple-300 text-xs font-mono transition-colors"
                >
                  {isDavinciLoading ? 'Probing...' : 'Probe Resolve'}
                </button>
              </div>
            </div>

            {/* One-Click Page Navigation Bar */}
            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-2 uppercase tracking-wider">
                DaVinci Resolve Workspace Pages (Direct MCP Switching)
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
                {['media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver'].map((page) => (
                  <button
                    key={page}
                    type="button"
                    onClick={() => handleSwitchDaVinciPage(page)}
                    className={`py-2 px-3 rounded-lg text-xs font-mono font-bold uppercase transition-all cursor-pointer border ${
                      davinciActivePage === page
                        ? 'bg-purple-600/40 border-purple-400 text-purple-100 shadow-sm'
                        : 'bg-slate-950/70 border-purple-500/20 text-slate-300 hover:border-purple-400/50 hover:bg-purple-950/30'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Automation Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
              {/* Card 1: 9:16 Shorts Project Setup */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-purple-500/25 space-y-3">
                <div className="flex items-center gap-2 text-purple-300 text-xs font-mono font-bold uppercase">
                  <Monitor className="w-4 h-4 text-purple-400" />
                  <span>Vertical Shorts Project</span>
                </div>
                <input
                  type="text"
                  value={davinciProjectName}
                  onChange={(e) => setDavinciProjectName(e.target.value)}
                  placeholder="Project name"
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-purple-500/30 text-xs text-slate-200 font-mono focus:outline-none focus:border-purple-400"
                />
                <button
                  type="button"
                  onClick={handleCreateShortsProject}
                  className="w-full py-2 rounded-lg bg-purple-700/60 hover:bg-purple-600/70 border border-purple-400/50 text-xs font-mono font-bold text-purple-100 transition-colors"
                >
                  Create 9:16 Project
                </button>
              </div>

              {/* Card 2: Universal FCPXML Timeline */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-purple-500/25 space-y-3">
                <div className="flex items-center gap-2 text-purple-300 text-xs font-mono font-bold uppercase">
                  <Layers className="w-4 h-4 text-purple-400" />
                  <span>FCPXML Interchange</span>
                </div>
                <p className="text-[11px] font-mono text-slate-400 leading-relaxed">
                  Export 1080x1920 vertical timeline with all high-scoring segments, chapters, and marker notes.
                </p>
                <button
                  type="button"
                  onClick={handleExportDaVinci}
                  className="w-full py-2 rounded-lg bg-gradient-to-r from-purple-800/80 to-indigo-800/80 hover:from-purple-700 hover:to-indigo-700 border border-purple-400/50 text-xs font-mono font-bold text-purple-100 transition-colors flex items-center justify-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export .XML Timeline
                </button>
              </div>

              {/* Card 3: Render & Queue Control */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-purple-500/25 space-y-3">
                <div className="flex items-center gap-2 text-purple-300 text-xs font-mono font-bold uppercase">
                  <Sliders className="w-4 h-4 text-purple-400" />
                  <span>Render Automation</span>
                </div>
                <p className="text-[11px] font-mono text-slate-400 leading-relaxed">
                  Add active timeline to Resolve render queue with YouTube 1080p preset and start rendering.
                </p>
                <button
                  type="button"
                  onClick={handleStartRenderQueue}
                  className="w-full py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-purple-500/40 text-xs font-mono font-bold text-purple-300 transition-colors flex items-center justify-center gap-1.5"
                >
                  <Play className="w-3.5 h-3.5" />
                  Start Render Queue
                </button>
              </div>
            </div>

            {/* 440+ MCP Tool Catalog & Live Execution Studio */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-purple-500/30 space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-purple-500/20 pb-3">
                <div>
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-purple-200 flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-purple-400" />
                    Complete DaVinci Resolve MCP Skills Suite ({mcpCatalog?.total_tools || 444} Tools across 11 Categories)
                  </h3>
                  <p className="text-[11px] font-mono text-slate-400">
                    Direct access to the full DaVinci Resolve Python/Fusion Scripting API.
                  </p>
                </div>
                <div className="relative w-full md:w-64">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    value={toolSearchQuery}
                    onChange={(e) => setToolSearchQuery(e.target.value)}
                    placeholder="Filter 444 tools..."
                    className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-900 border border-purple-500/30 text-xs text-slate-100 font-mono focus:outline-none focus:border-purple-400"
                  />
                </div>
              </div>

              {/* 11 Category Selector Pills */}
              <div className="flex flex-wrap gap-1.5 pb-1">
                <button
                  type="button"
                  onClick={() => setSelectedCategory('All')}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-bold transition-all ${
                    selectedCategory === 'All'
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-900/80 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  All ({mcpCatalog?.total_tools || 444})
                </button>
                {(mcpCatalog?.categories || []).map((cat: any) => (
                  <button
                    key={cat.category}
                    type="button"
                    onClick={() => setSelectedCategory(cat.category)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-bold transition-all flex items-center gap-1.5 ${
                      selectedCategory === cat.category
                        ? 'bg-purple-600 text-white shadow-sm'
                        : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                    }`}
                  >
                    <span>{cat.category}</span>
                    <span className="px-1.5 py-0.2 rounded bg-slate-950/60 text-[10px] text-purple-300">
                      {cat.count}
                    </span>
                  </button>
                ))}
              </div>

              {/* Two Column Tool Explorer & Executor */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-4 pt-1">
                {/* Left Column: Tool List (5 cols) */}
                <div className="md:col-span-5 rounded-xl bg-slate-900/60 border border-purple-500/20 p-2 max-h-[360px] overflow-y-auto space-y-1">
                  {(() => {
                    const allTools: any[] = [];
                    if (mcpCatalog?.categories) {
                      for (const cat of mcpCatalog.categories) {
                        if (selectedCategory === 'All' || selectedCategory === cat.category) {
                          for (const t of cat.tools) {
                            if (!toolSearchQuery || t.name.toLowerCase().includes(toolSearchQuery.toLowerCase()) || (t.description && t.description.toLowerCase().includes(toolSearchQuery.toLowerCase()))) {
                              allTools.push(t);
                            }
                          }
                        }
                      }
                    }

                    if (allTools.length === 0) {
                      return (
                        <div className="p-4 text-center text-xs font-mono text-slate-500">
                          {isDavinciLoading ? 'Loading tools catalog...' : 'No matching tools found.'}
                        </div>
                      );
                    }

                    return allTools.map((t) => (
                      <button
                        key={t.name}
                        type="button"
                        onClick={() => handleSelectTool(t)}
                        className={`w-full text-left p-2 rounded-lg text-xs font-mono transition-all block ${
                          activeTool?.name === t.name
                            ? 'bg-purple-600/30 border border-purple-400/60 text-purple-100'
                            : 'hover:bg-slate-800/60 text-slate-300 border border-transparent'
                        }`}
                      >
                        <div className="font-bold truncate text-[11px] text-purple-300">
                          {t.name}
                        </div>
                        <div className="text-[10px] text-slate-400 truncate mt-0.5">
                          {t.description ? t.description.split('\n')[0] : 'No description'}
                        </div>
                      </button>
                    ));
                  })()}
                </div>

                {/* Right Column: Tool Inspector & Executor (7 cols) */}
                <div className="md:col-span-7 rounded-xl bg-slate-900/60 border border-purple-500/20 p-3.5 space-y-3">
                  {activeTool ? (
                    <>
                      <div className="flex items-start justify-between gap-2 border-b border-purple-500/20 pb-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono font-bold text-purple-200">
                              {activeTool.name}
                            </span>
                            <span className="px-2 py-0.5 rounded bg-purple-900/50 text-[10px] font-mono text-purple-300 border border-purple-500/30">
                              {activeTool.category}
                            </span>
                          </div>
                          <p className="text-[11px] font-mono text-slate-400 mt-1 whitespace-pre-line leading-relaxed max-h-20 overflow-y-auto">
                            {activeTool.description || 'Executes native Resolve API method.'}
                          </p>
                        </div>
                      </div>

                      {/* Arguments JSON Input */}
                      <div>
                        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1">
                          <span>PARAMETERS (JSON)</span>
                          <span className="text-purple-400">
                            {activeTool.inputSchema?.required?.length ? `Required: ${activeTool.inputSchema.required.join(', ')}` : 'No required parameters'}
                          </span>
                        </div>
                        <textarea
                          rows={4}
                          value={toolArgsJson}
                          onChange={(e) => setToolArgsJson(e.target.value)}
                          className="w-full p-2.5 rounded-lg bg-slate-950 border border-purple-500/30 text-xs font-mono text-emerald-400 focus:outline-none focus:border-purple-400 resize-none"
                        />
                      </div>

                      {/* Execute Button */}
                      <button
                        type="button"
                        onClick={handleExecuteTool}
                        disabled={isExecutingTool}
                        className="w-full py-2 rounded-lg bg-purple-600 hover:bg-purple-500 border border-purple-400/50 text-xs font-mono font-bold text-white transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                      >
                        <Wrench className="w-3.5 h-3.5" />
                        <span>{isExecutingTool ? 'EXECUTING ON DAVINCI...' : `EXECUTE ${activeTool.name.toUpperCase()}`}</span>
                      </button>

                      {/* Live Output Box */}
                      {toolExecutionOutput && (
                        <div className="rounded-lg bg-slate-950 p-2.5 border border-purple-500/30 space-y-1">
                          <div className="text-[10px] font-mono font-bold text-slate-400 flex items-center justify-between">
                            <span>EXECUTION OUTPUT</span>
                            <span className={toolExecutionOutput.success !== false ? 'text-emerald-400' : 'text-amber-400'}>
                              {toolExecutionOutput.success !== false ? 'COMPLETED' : 'OFFLINE / NOTICE'}
                            </span>
                          </div>
                          <pre className="text-[10px] font-mono text-slate-200 overflow-x-auto max-h-28 p-1.5 bg-slate-900 rounded">
                            {JSON.stringify(toolExecutionOutput, null, 2)}
                          </pre>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="p-8 text-center text-xs font-mono text-slate-500">
                      Select a tool from the catalog to inspect parameters and test live execution.
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Standalone MCP Configuration Snippet */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-purple-500/20 text-xs font-mono space-y-1.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[10px] uppercase font-bold text-purple-300">
                  Model Context Protocol (MCP) Integration for External AI (Claude Code / Desktop / Antigravity)
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy('.\\.venv\\Scripts\\python -m jarvis.backend.mcp.davinci_mcp_server', 'mcp-cmd')}
                  className="text-[10px] text-cyan-400 hover:underline flex items-center gap-1 cursor-pointer"
                >
                  {copiedId === 'mcp-cmd' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  {copiedId === 'mcp-cmd' ? 'Copied' : 'Copy Stdio Command'}
                </button>
              </div>
              <div className="bg-slate-900/90 p-2 rounded text-[11px] text-slate-300 overflow-x-auto select-all">
                python -m jarvis.backend.mcp.davinci_mcp_server
              </div>
            </div>
          </div>
        )}

        {processMessage && (
          <div className="mt-3 text-xs font-mono text-amber-300 animate-pulse flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            <span>{processMessage}</span>
          </div>
        )}
      </div>

      {/* Main Studio Workspace: Player & Inspector */}
      {clips.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Vertical Video Player Preview (4 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="rounded-2xl bg-slate-950 p-4 border border-cyan-500/25 flex flex-col items-center">
              <div className="w-full flex justify-between items-center pb-2 mb-2 border-b border-cyan-500/20 text-xs font-mono text-slate-400">
                <span>9:16 VERTICAL PREVIEW</span>
                <span className="text-cyan-400 font-bold">{selectedClip?.duration}s</span>
              </div>

              <div className="relative w-full max-w-[280px] aspect-[9/16] rounded-xl overflow-hidden bg-slate-900 border border-cyan-500/40 shadow-2xl">
                {selectedClip?.video_url ? (
                  <video
                    key={selectedClip.video_url}
                    src={selectedClip.video_url}
                    controls
                    autoPlay
                    loop
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs font-mono">
                    <Film className="w-10 h-10 mb-2 text-cyan-500/40" />
                    <span>Select clip to preview</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: 6-Factor Algorithmic Score Breakdown & Publishing Metadata (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            {selectedClip && (
              <div className="p-6 rounded-2xl bg-slate-950/80 border border-cyan-500/25 space-y-5">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-0.5 rounded bg-cyan-500/20 border border-cyan-500/40 text-[11px] font-mono text-cyan-300 font-bold">
                      OVERALL SCORE: {selectedClip.total_score}/100
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      ID: {selectedClip.id}
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-slate-100 mt-2">{selectedClip.title}</h2>
                  <p className="text-xs text-slate-300 font-mono mt-1">{selectedClip.summary}</p>
                </div>

                {/* 6-Factor Algorithmic Scoring Grid */}
                <div className="p-4 rounded-xl bg-slate-900/80 border border-cyan-500/20 space-y-2">
                  <div className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Award className="w-4 h-4 text-cyan-400" />
                    Algorithmic Weight Distribution
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs font-mono">
                    <div>
                      <div className="text-slate-400">Hook Strength (25%)</div>
                      <div className="font-bold text-cyan-300">{selectedClip.hook_strength}/100</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Story Completeness (20%)</div>
                      <div className="font-bold text-blue-300">{selectedClip.story_completeness}/100</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Info Value (20%)</div>
                      <div className="font-bold text-purple-300">{selectedClip.info_value}/100</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Engagement (15%)</div>
                      <div className="font-bold text-yellow-300">{selectedClip.engagement_potential}/100</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Audio Quality (10%)</div>
                      <div className="font-bold text-emerald-300">{selectedClip.audio_quality}/100</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Visual Quality (10%)</div>
                      <div className="font-bold text-emerald-300">{selectedClip.visual_quality}/100</div>
                    </div>
                  </div>
                </div>

                {/* Caption Styling & Live Actions Suite */}
                <div className="p-4 rounded-xl bg-slate-900/90 border border-cyan-500/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-amber-400" />
                      <span className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">
                        Caption Styles & Visual Actions
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-cyan-300 px-2 py-0.5 rounded bg-cyan-950 border border-cyan-500/40 uppercase font-bold">
                      Active: {captionStyles.find((s) => s.id === clipCaptionStyle)?.name || clipCaptionStyle}
                    </span>
                  </div>

                  {/* Caption Styles Selector Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {captionStyles.map((style) => {
                      const isSelected = clipCaptionStyle === style.id;
                      return (
                        <button
                          key={style.id}
                          type="button"
                          onClick={() => setClipCaptionStyle(style.id)}
                          className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                            isSelected
                              ? 'bg-cyan-500/20 border-cyan-400 shadow-cyan-sm scale-[1.02]'
                              : 'bg-slate-950/80 border-slate-800 hover:border-cyan-500/40 text-slate-400'
                          }`}
                        >
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-900 text-slate-300">
                                {style.tag}
                              </span>
                              <div className="flex items-center gap-1">
                                <span
                                  className="w-2.5 h-2.5 rounded-full border border-black shrink-0"
                                  style={{ backgroundColor: style.primary_color }}
                                  title={`Primary: ${style.primary_color}`}
                                />
                                <span
                                  className="w-2.5 h-2.5 rounded-full border border-black shrink-0"
                                  style={{ backgroundColor: style.highlight_color }}
                                  title={`Highlight: ${style.highlight_color}`}
                                />
                              </div>
                            </div>
                            <div className={`text-[11px] font-bold font-mono truncate ${isSelected ? 'text-cyan-200' : 'text-slate-200'}`}>
                              {style.name}
                            </div>
                            <p className="text-[9px] font-mono text-slate-400 line-clamp-1 mt-0.5">
                              {style.font}
                            </p>
                          </div>

                          {/* Visual Word-Level Render Preview Badge */}
                          <div
                            className="mt-2 py-1 px-1.5 rounded bg-slate-900/90 text-center font-bold text-[10px] tracking-wider uppercase border border-slate-800"
                            style={{
                              color: style.primary_color,
                              textShadow: `-1px -1px 0 ${style.outline_color}, 1px -1px 0 ${style.outline_color}, -1px 1px 0 ${style.outline_color}, 1px 1px 0 ${style.outline_color}`
                            }}
                          >
                            {style.sample}
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {/* Actions Bar for the selected caption style */}
                  <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
                    <button
                      type="button"
                      onClick={handleApplyCaptionStyleToClip}
                      disabled={isRestylingCaption}
                      className="flex-1 py-2 px-3.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase font-mono tracking-wider shadow-cyan-sm disabled:opacity-50 cursor-pointer transition-all flex items-center justify-center gap-2"
                    >
                      <Sparkles className={`w-3.5 h-3.5 ${isRestylingCaption ? 'animate-spin' : ''}`} />
                      <span>
                        {isRestylingCaption
                          ? 'Burning Subtitles with FFmpeg...'
                          : `Apply "${captionStyles.find((s) => s.id === clipCaptionStyle)?.name || 'Style'}" & Re-render`}
                      </span>
                    </button>

                    {selectedClip.subtitles_path && (
                      <a
                        href={`/output/subtitles/${selectedClip.subtitles_path.split('\\').pop()?.split('/').pop()}`}
                        download
                        className="py-2 px-3 rounded-lg bg-slate-950 hover:bg-slate-900 border border-cyan-500/40 text-cyan-300 text-xs font-mono transition-colors flex items-center gap-1.5 cursor-pointer"
                        title="Download Advanced SubStation Alpha (.ass) Subtitles"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download .ASS</span>
                      </a>
                    )}
                  </div>
                </div>

                {/* Viral Caption & Tags */}
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between items-center text-xs font-mono text-slate-400 mb-1">
                      <span>CAPTION & DESCRIPTION</span>
                      <button
                        onClick={() => handleCopy(selectedClip.caption, 'cap')}
                        className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
                      >
                        {copiedId === 'cap' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        <span>Copy</span>
                      </button>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 font-mono">
                      {selectedClip.caption}
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center text-xs font-mono text-slate-400 mb-1">
                      <span>VIRAL HASHTAGS</span>
                      <button
                        onClick={() => handleCopy(selectedClip.tags, 'tags')}
                        className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
                      >
                        {copiedId === 'tags' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        <span>Copy</span>
                      </button>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-cyan-300 font-mono">
                      {selectedClip.tags}
                    </div>
                  </div>
                </div>

                {/* Notice Toast */}
                {actionNotice && (
                  <div className="p-3 rounded-lg bg-cyan-950/80 border border-cyan-400 text-xs font-mono text-cyan-300 flex items-center gap-2 animate-bounce">
                    <Check className="w-4 h-4 text-emerald-400" />
                    <span>{actionNotice}</span>
                  </div>
                )}

                {/* Quick Publishing Actions */}
                <div className="flex flex-wrap gap-3 pt-2">
                  <a
                    href={selectedClip.video_url}
                    download
                    className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-slate-200 flex items-center gap-2 cursor-pointer transition-colors"
                  >
                    <Download className="w-4 h-4 text-cyan-400" />
                    <span>Download MP4</span>
                  </a>

                  <button
                    onClick={() => handleQueueYouTube(selectedClip)}
                    className="px-4 py-2 rounded-lg bg-red-600/20 hover:bg-red-600/30 border border-red-500/50 text-xs font-mono text-red-300 flex items-center gap-2 cursor-pointer transition-colors"
                  >
                    <PlaySquare className="w-4 h-4" />
                    <span>Queue for YouTube Shorts</span>
                  </button>

                  <button
                    onClick={() => handleQueueInstagram(selectedClip)}
                    className="px-4 py-2 rounded-lg bg-pink-600/20 hover:bg-pink-600/30 border border-pink-500/50 text-xs font-mono text-pink-300 flex items-center gap-2 cursor-pointer transition-colors"
                  >
                    <Camera className="w-4 h-4" />
                    <span>Queue for Instagram Reels</span>
                  </button>

                  <button
                    onClick={async () => {
                      if (window.confirm(`Delete clip "${selectedClip.title}" from storage?`)) {
                        try {
                          const res = await api.deleteClip(selectedClip.id);
                          if (res.success) {
                            showNotice(`Deleted clip and freed ${res.freed_mb} MB!`);
                            setSelectedClip(null);
                            onRefreshClips();
                          } else {
                            showNotice(res.error || 'Failed to delete clip.');
                          }
                        } catch (e: any) {
                          showNotice(`Delete error: ${e.message}`);
                        }
                      }
                    }}
                    className="px-4 py-2 rounded-lg bg-rose-950/40 hover:bg-rose-900/50 border border-rose-500/40 text-xs font-mono text-rose-300 flex items-center gap-2 cursor-pointer transition-colors"
                    title="Delete clip from storage"
                  >
                    <Trash2 className="w-4 h-4 text-rose-400" />
                    <span>Delete Clip</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}

      {/* Grid of All Available Clips */}
      <div className="pt-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            Clip Library ({clips.length})
          </h3>

          {/* Quick Source Filters */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
            <button
              onClick={() => setClipFilter('all')}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${
                clipFilter === 'all'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              All ({clips.length})
            </button>
            {clips.length > 25 && (
              <button
                onClick={async () => {
                  if (window.confirm(`Clean oldest clips to free storage? (Keeps latest 25 clips & protects active scheduled queues)`)) {
                    try {
                      const res = await api.clearOldClips(25);
                      showNotice(`Purged ${res.deleted_count} oldest clips (${res.freed_mb} MB freed)!`);
                      onRefreshClips();
                    } catch (e: any) {
                      showNotice(`Error cleaning clips: ${e.message}`);
                    }
                  }
                }}
                className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-all flex items-center gap-1 cursor-pointer"
                title="Purge oldest clips from storage (keeps active queues safe)"
              >
                <Trash2 className="w-3 h-3" />
                <span>Clean Oldest</span>
              </button>
            )}
            {clips.some((c) => c.source_file?.includes('Beat')) && (
              <button
                onClick={() => setClipFilter('Beat')}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${
                  clipFilter === 'Beat'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50'
                    : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                MrBeast Athlete ({clips.filter((c) => c.source_file?.includes('Beat')).length})
              </button>
            )}
            {clips.some((c) => c.source_file?.includes('zurNfKQB5Cw')) && (
              <button
                onClick={() => setClipFilter('zurNfKQB5Cw')}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${
                  clipFilter === 'zurNfKQB5Cw'
                    ? 'bg-red-500/20 text-red-300 border border-red-500/50'
                    : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                Joe Rogan ({clips.filter((c) => c.source_file?.includes('zurNfKQB5Cw')).length})
              </button>
            )}
            {clips.some((c) => c.source_file?.includes('sample_podcast')) && (
              <button
                onClick={() => setClipFilter('sample_podcast')}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${
                  clipFilter === 'sample_podcast'
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/50'
                    : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                Sample ({clips.filter((c) => c.source_file?.includes('sample_podcast')).length})
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {clips
            .filter((c) => clipFilter === 'all' || (c.source_file && c.source_file.includes(clipFilter)))
            .map((c) => (
              <div
                key={c.id}
                onClick={() => setSelectedClip(c)}
                className={`cursor-pointer rounded-xl overflow-hidden bg-slate-950 border transition-all ${
                  selectedClip?.id === c.id
                    ? 'border-cyan-400 shadow-cyan-sm scale-[1.02]'
                    : 'border-slate-800 hover:border-cyan-500/50 opacity-80 hover:opacity-100'
                }`}
              >
                <div className="relative aspect-[9/16] bg-slate-900 flex items-center justify-center">
                  {c.thumb_url ? (
                    <img src={c.thumb_url} alt={c.title} className="w-full h-full object-cover" />
                  ) : (
                    <Film className="w-6 h-6 text-cyan-500/40" />
                  )}
                  <div className="absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded bg-slate-950/80 text-[9px] font-mono font-bold text-cyan-300">
                    {c.total_score}
                  </div>
                </div>
                <div className="p-2">
                  <div className="text-[11px] font-bold text-slate-200 truncate">{c.title}</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">{c.duration}s</div>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};
