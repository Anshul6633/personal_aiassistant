import React, { useState, useEffect, useRef } from 'react';
import {
  Scissors,
  Play,
  Pause,
  RotateCw,
  FlipHorizontal,
  Volume2,
  VolumeX,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  Sparkles,
  Download,
  Upload,
  Mic,
  MicOff,
  Plus,
  Trash2,
  Copy,
  ZoomIn,
  ZoomOut,
  Sliders,
  Film,
  Type,
  Music,
  Split,
  Maximize2,
  CheckCircle2,
  RefreshCw,
  Wand2,
  PanelLeft,
  PanelRight,
  Layers,
  Settings2,
  Smile,
  Palette,
  Smartphone,
  Monitor,
  Square,
  Zap,
  Sun,
  Droplets,
  FastForward,
  Undo2,
  Redo2,
  Activity,
  Magnet,
  BarChart2,
  HelpCircle,
  MapPin,
  Flame,
  AtSign,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Move
} from 'lucide-react';
import {
  ClipItem,
  StudioProject,
  StudioClip,
  StudioTrack,
  api
} from '../services/api';

interface VideoEditorProps {
  clips: ClipItem[];
  onRefreshClips: () => void;
}

export const VideoEditor: React.FC<VideoEditorProps> = ({ clips, onRefreshClips }) => {
  // --- Projects State ---
  const [projects, setProjects] = useState<StudioProject[]>([]);
  const [currentProject, setCurrentProject] = useState<StudioProject | null>(null);
  const currentProjectRef = useRef<StudioProject | null>(null);
  useEffect(() => {
    currentProjectRef.current = currentProject;
  }, [currentProject]);
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'media' | 'audio' | 'text' | 'stickers' | 'effects' | 'transitions'>('media');

  // --- Layout Panes Toggles ---
  const [showLeftPanel, setShowLeftPanel] = useState(true);
  const [showRightInspector, setShowRightInspector] = useState(true);

  // --- Playback & Monitor State ---
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0.0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [showSafeGuides, setShowSafeGuides] = useState(false);
  const [timelineZoom, setTimelineZoom] = useState(30); // Pixels per second
  const [rippleDelete, setRippleDelete] = useState(false);
  const [isFullscreenPreview, setIsFullscreenPreview] = useState(false);

  // --- AI Command Bar State ---
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiWorking, setAiWorking] = useState(false);
  const [aiNotice, setAiNotice] = useState<string | null>(null);
  const [isListeningMic, setIsListeningMic] = useState(false);

  // --- History (Undo/Redo) State ---
  const [undoStack, setUndoStack] = useState<StudioProject[]>([]);
  const [redoStack, setRedoStack] = useState<StudioProject[]>([]);

  // --- CapCut / Instagram Canvas & Snapping State ---
  const [canvasBgMode, setCanvasBgMode] = useState<'blur' | 'black' | 'neon' | 'gradient'>('blur');
  const [snappingEnabled, setSnappingEnabled] = useState(true);

  // --- DaVinci Resolve Inspector Mode ---
  const [activeInspectorTab, setActiveInspectorTab] = useState<'adjust' | 'wheels' | 'scopes'>('adjust');

  // --- Interactive Timeline Drag & Trim Ref ---
  const dragInfoRef = useRef<{
    type: 'move' | 'trim_left' | 'trim_right';
    clipId: string;
    startX: number;
    origStartTime: number;
    origDuration: number;
    origInPoint: number;
    origOutPoint: number;
  } | null>(null);
  const [isTimelineDragging, setIsTimelineDragging] = useState(false);

  // --- Voiceover Recording State ---
  const [isRecordingVoiceover, setIsRecordingVoiceover] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // --- Export Modal State ---
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportRes, setExportRes] = useState('1080p');
  const [exportAspect, setExportAspect] = useState<'16:9' | '9:16' | '1:1' | '4:5'>('16:9');
  const [exportCodec, setExportCodec] = useState('h264');
  const [exportAudioOnly, setExportAudioOnly] = useState(false);
  const [isRendering, setIsRendering] = useState(false);
  const [renderJobId, setRenderJobId] = useState<string | null>(null);
  const [renderProgress, setRenderProgress] = useState(0);
  const [renderDownloadUrl, setRenderDownloadUrl] = useState<string | null>(null);

  // --- References ---
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const timelineScrollRef = useRef<HTMLDivElement | null>(null);
  const previewContainerRef = useRef<HTMLDivElement | null>(null);

  // --- On-Video Direct Manipulation Drag & Transform State ---
  const canvasDragRef = useRef<{
    type: 'move' | 'scale' | 'rotate';
    clipId: string;
    startMouseX: number;
    startMouseY: number;
    origPosX: number;
    origPosY: number;
    origScaleX: number;
    origScaleY: number;
    origRotation: number;
    containerWidth: number;
    containerHeight: number;
    centerPixelX: number;
    centerPixelY: number;
  } | null>(null);
  const [isCanvasDragging, setIsCanvasDragging] = useState(false);
  const [snapGuideX, setSnapGuideX] = useState(false);
  const [snapGuideY, setSnapGuideY] = useState(false);

  // 1. Initial Load of Studio Projects
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const projs = await api.listStudioProjects();
      setProjects(projs);
      if (projs.length > 0) {
        const loaded = await api.getStudioProject(projs[0].id);
        setCurrentProject(loaded);
        setExportAspect(loaded.aspect_ratio || '16:9');
        if (loaded.clips.length > 0) {
          setSelectedClipId(loaded.clips[0].id);
          // If clips exist, jump to the first clip's start time
          setCurrentTime(loaded.clips[0].start_time);
        }
      }
    } catch (e) {
      console.error('Failed to load studio projects:', e);
    }
  };

  // 2. Playhead ticker loop
  useEffect(() => {
    let animId: number;
    let lastStamp = performance.now();

    const loop = (stamp: number) => {
      const delta = (stamp - lastStamp) / 1000;
      lastStamp = stamp;

      if (isPlaying && currentProject) {
        setCurrentTime((prev) => {
          const next = prev + delta * playbackSpeed;
          if (next >= currentProject.duration) {
            setIsPlaying(false);
            return 0;
          }
          return next;
        });
      }
      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [isPlaying, playbackSpeed, currentProject]);

  // Sync HTML5 video tag if active clip is under playhead
  useEffect(() => {
    if (!videoRef.current || !activeVideoClip) return;
    const clipOffset = currentTime - activeVideoClip.start_time;
    const mediaTime = activeVideoClip.in_point + clipOffset * (activeVideoClip.speed || 1.0);
    if (Math.abs(videoRef.current.currentTime - mediaTime) > 0.25) {
      videoRef.current.currentTime = Math.max(0, mediaTime);
    }
    if (isPlaying && videoRef.current.paused) {
      videoRef.current.play().catch(() => {});
    } else if (!isPlaying && !videoRef.current.paused) {
      videoRef.current.pause();
    }
  }, [currentTime, isPlaying]);

  // Determine currently active video clip at playhead
  const activeVideoClip = currentProject?.clips.find(
    (c) =>
      c.source_type === 'video' &&
      currentTime >= c.start_time &&
      currentTime <= c.start_time + c.duration
  );

  // Determine currently active text/subtitle/sticker clips at playhead
  const activeTextClips = currentProject?.clips.filter(
    (c) =>
      (c.source_type === 'text' || c.source_type === 'subtitle' || c.source_type === 'sticker') &&
      currentTime >= c.start_time &&
      currentTime <= c.start_time + c.duration
  );

  const selectedClip = currentProject?.clips.find((c) => c.id === selectedClipId);

  // Auto-Save project state with Undo/Redo history tracking
  const saveProjectState = async (updated: StudioProject, addToHistory: boolean = true) => {
    if (addToHistory && currentProject) {
      setUndoStack((prev) => [...prev.slice(-30), currentProject]);
      setRedoStack([]);
    }
    setCurrentProject(updated);
    try {
      await api.saveStudioProject(updated.id, updated);
    } catch (e) {
      console.error('Failed to save project:', e);
    }
  };

  const handleUndo = () => {
    if (undoStack.length === 0 || !currentProject) return;
    const prev = undoStack[undoStack.length - 1];
    setUndoStack((s) => s.slice(0, -1));
    setRedoStack((s) => [...s, currentProject]);
    setCurrentProject(prev);
    api.saveStudioProject(prev.id, prev).catch(() => {});
    setAiNotice('↩ Undid last action');
  };

  const handleRedo = () => {
    if (redoStack.length === 0 || !currentProject) return;
    const next = redoStack[redoStack.length - 1];
    setRedoStack((s) => s.slice(0, -1));
    setUndoStack((s) => [...s, currentProject]);
    setCurrentProject(next);
    api.saveStudioProject(next.id, next).catch(() => {});
    setAiNotice('↪ Redid last action');
  };

  // Mouse drag handlers for interactive timeline move and trim
  const handleStartTimelineDrag = (
    e: React.MouseEvent,
    type: 'move' | 'trim_left' | 'trim_right',
    clip: StudioClip
  ) => {
    e.stopPropagation();
    e.preventDefault();
    setSelectedClipId(clip.id);
    dragInfoRef.current = {
      type,
      clipId: clip.id,
      startX: e.clientX,
      origStartTime: clip.start_time,
      origDuration: clip.duration,
      origInPoint: clip.in_point,
      origOutPoint: clip.out_point,
    };
    setIsTimelineDragging(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!dragInfoRef.current || !currentProject) return;
      const { type, clipId, startX, origStartTime, origDuration, origInPoint, origOutPoint } = dragInfoRef.current;
      const deltaSec = (e.clientX - startX) / timelineZoom;

      const updatedClips = currentProject.clips.map((c) => {
        if (c.id !== clipId) return c;

        if (type === 'move') {
          let newStart = Math.max(0, origStartTime + deltaSec);
          if (snappingEnabled && Math.abs(newStart - currentTime) < 0.25) {
            newStart = currentTime;
          }
          return { ...c, start_time: Number(newStart.toFixed(2)) };
        } else if (type === 'trim_left') {
          let newStart = origStartTime + deltaSec;
          newStart = Math.max(0, Math.min(newStart, origStartTime + origDuration - 0.2));
          const diff = newStart - origStartTime;
          const newDur = Math.max(0.2, origDuration - diff);
          const newIn = Math.max(0, origInPoint + diff * (c.speed || 1.0));
          return {
            ...c,
            start_time: Number(newStart.toFixed(2)),
            duration: Number(newDur.toFixed(2)),
            in_point: Number(newIn.toFixed(2)),
          };
        } else if (type === 'trim_right') {
          let newDur = Math.max(0.2, origDuration + deltaSec);
          if (snappingEnabled && Math.abs((c.start_time + newDur) - currentTime) < 0.25) {
            newDur = Math.max(0.2, currentTime - c.start_time);
          }
          const newOut = origInPoint + newDur * (c.speed || 1.0);
          return {
            ...c,
            duration: Number(newDur.toFixed(2)),
            out_point: Number(newOut.toFixed(2)),
          };
        }
        return c;
      });

      const maxDur = Math.max(10, ...updatedClips.map((c) => c.start_time + c.duration + 2));
      setCurrentProject({ ...currentProject, clips: updatedClips, duration: maxDur });
    };

    const handleMouseUp = () => {
      if (dragInfoRef.current && currentProject) {
        saveProjectState(currentProject, true);
        dragInfoRef.current = null;
        setIsTimelineDragging(false);
      }
    };

    if (isTimelineDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isTimelineDragging, currentProject, timelineZoom, snappingEnabled, currentTime]);

  // Quick direct adjust helpers for on-screen items (emojis, stickers, subtitles, titles)
  const handleNudgePosition = (clipId: string, deltaX: number, deltaY: number) => {
    const proj = currentProjectRef.current || currentProject;
    if (!proj) return;
    const updatedClips = proj.clips.map((c) => {
      if (c.id !== clipId) return c;
      const curX = c.transform.position_x || 0;
      const curY = c.transform.position_y || 0;
      const newX = Math.max(-0.95, Math.min(0.95, Number((curX + deltaX).toFixed(3))));
      const newY = Math.max(-0.95, Math.min(0.95, Number((curY + deltaY).toFixed(3))));
      return {
        ...c,
        transform: {
          ...c.transform,
          position_x: newX,
          position_y: newY,
        },
      };
    });
    const updated = { ...proj, clips: updatedClips };
    currentProjectRef.current = updated;
    saveProjectState(updated, true);
  };

  const handleSetPosition = (clipId: string, targetX: number, targetY: number) => {
    const proj = currentProjectRef.current || currentProject;
    if (!proj) return;
    const updatedClips = proj.clips.map((c) => {
      if (c.id !== clipId) return c;
      return {
        ...c,
        transform: {
          ...c.transform,
          position_x: Number(targetX.toFixed(3)),
          position_y: Number(targetY.toFixed(3)),
        },
      };
    });
    const updated = { ...proj, clips: updatedClips };
    currentProjectRef.current = updated;
    saveProjectState(updated, true);
  };

  const handleNudgeScale = (clipId: string, deltaScale: number) => {
    const proj = currentProjectRef.current || currentProject;
    if (!proj) return;
    const updatedClips = proj.clips.map((c) => {
      if (c.id !== clipId) return c;
      const curScale = c.transform.scale_x || 1.0;
      const newScale = Math.max(0.2, Math.min(4.0, Number((curScale + deltaScale).toFixed(2))));
      return {
        ...c,
        transform: {
          ...c.transform,
          scale_x: newScale,
          scale_y: newScale,
        },
      };
    });
    const updated = { ...proj, clips: updatedClips };
    currentProjectRef.current = updated;
    saveProjectState(updated, true);
  };

  const handleNudgeRotation = (clipId: string, deltaDeg: number) => {
    const proj = currentProjectRef.current || currentProject;
    if (!proj) return;
    const updatedClips = proj.clips.map((c) => {
      if (c.id !== clipId) return c;
      const curDeg = c.transform.rotation || 0;
      let newDeg = curDeg + deltaDeg;
      if (newDeg > 180) newDeg -= 360;
      if (newDeg < -180) newDeg += 360;
      return {
        ...c,
        transform: {
          ...c.transform,
          rotation: newDeg,
        },
      };
    });
    const updated = { ...proj, clips: updatedClips };
    currentProjectRef.current = updated;
    saveProjectState(updated, true);
  };

  const handleDeleteClipById = (clipId: string) => {
    const proj = currentProjectRef.current || currentProject;
    if (!proj) return;
    const target = proj.clips.find((c) => c.id === clipId);
    if (!target) return;
    const updatedClips = proj.clips.filter((c) => c.id !== clipId);
    const updated = {
      ...proj,
      clips: updatedClips,
      duration: Math.max(10, Math.max(...updatedClips.map((c) => c.start_time + c.duration), 10)),
    };
    if (selectedClipId === clipId) setSelectedClipId(null);
    currentProjectRef.current = updated;
    saveProjectState(updated, true);
    setAiNotice(`Deleted '${target.name}'`);
  };

  // Start on-screen direct drag (move, scale, rotate)
  const handleStartCanvasItemDrag = (
    e: React.MouseEvent | React.TouchEvent,
    clipId: string,
    type: 'move' | 'scale' | 'rotate'
  ) => {
    e.stopPropagation();
    setSelectedClipId(clipId);
    const proj = currentProjectRef.current || currentProject;
    if (!previewContainerRef.current || !proj) return;

    const clip = proj.clips.find((c) => c.id === clipId);
    if (!clip) return;

    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;

    const rect = previewContainerRef.current.getBoundingClientRect();
    const itemPixelCenterX = rect.left + rect.width * (0.5 + ((clip.transform.position_x || 0) * 0.5));
    const itemPixelCenterY = rect.top + rect.height * (0.5 + ((clip.transform.position_y || 0) * 0.5));

    canvasDragRef.current = {
      type,
      clipId,
      startMouseX: clientX,
      startMouseY: clientY,
      origPosX: clip.transform.position_x || 0,
      origPosY: clip.transform.position_y || 0,
      origScaleX: clip.transform.scale_x || 1.0,
      origScaleY: clip.transform.scale_y || 1.0,
      origRotation: clip.transform.rotation || 0,
      containerWidth: rect.width,
      containerHeight: rect.height,
      centerPixelX: itemPixelCenterX,
      centerPixelY: itemPixelCenterY,
    };
    setIsCanvasDragging(true);
  };

  // Global mousemove / mouseup listener for on-screen direct manipulation (Smooth, no teardown)
  useEffect(() => {
    if (!isCanvasDragging) return;

    const handlePointerMove = (e: MouseEvent | TouchEvent) => {
      const proj = currentProjectRef.current;
      if (!canvasDragRef.current || !proj) return;
      const {
        type,
        clipId,
        startMouseX,
        startMouseY,
        origPosX,
        origPosY,
        origScaleX,
        containerWidth,
        containerHeight,
        centerPixelX,
        centerPixelY,
      } = canvasDragRef.current;

      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;

      const dx = clientX - startMouseX;
      const dy = clientY - startMouseY;

      const updatedClips = proj.clips.map((c) => {
        if (c.id !== clipId) return c;

        if (type === 'move') {
          const deltaNormX = dx / (containerWidth * 0.5);
          const deltaNormY = dy / (containerHeight * 0.5);
          let newX = Math.max(-0.95, Math.min(0.95, origPosX + deltaNormX));
          let newY = Math.max(-0.95, Math.min(0.95, origPosY + deltaNormY));

          // Magnetic snapping to center guidelines
          let snappedX = false;
          let snappedY = false;
          if (snappingEnabled) {
            if (Math.abs(newX) < 0.035) {
              newX = 0;
              snappedX = true;
            }
            if (Math.abs(newY) < 0.035) {
              newY = 0;
              snappedY = true;
            } else if (Math.abs(newY - 0.55) < 0.035) {
              newY = 0.55;
              snappedY = true;
            }
          }
          setSnapGuideX(snappedX);
          setSnapGuideY(snappedY);

          return {
            ...c,
            transform: {
              ...c.transform,
              position_x: Number(newX.toFixed(3)),
              position_y: Number(newY.toFixed(3)),
            },
          };
        } else if (type === 'scale') {
          const distDelta = (dx + dy) / 100;
          const newScale = Math.max(0.2, Math.min(4.0, origScaleX + distDelta));
          return {
            ...c,
            transform: {
              ...c.transform,
              scale_x: Number(newScale.toFixed(2)),
              scale_y: Number(newScale.toFixed(2)),
            },
          };
        } else if (type === 'rotate') {
          const rad = Math.atan2(clientY - centerPixelY, clientX - centerPixelX);
          let deg = Math.round(rad * (180 / Math.PI) + 90);
          if (deg > 180) deg -= 360;
          if (deg < -180) deg += 360;
          if (Math.abs(deg) < 4) deg = 0;
          if (Math.abs(deg - 90) < 4) deg = 90;
          if (Math.abs(deg + 90) < 4) deg = -90;
          return {
            ...c,
            transform: {
              ...c.transform,
              rotation: deg,
            },
          };
        }
        return c;
      });

      const updatedProj = { ...proj, clips: updatedClips };
      currentProjectRef.current = updatedProj;
      setCurrentProject(updatedProj);
    };

    const handlePointerUp = () => {
      const finalProj = currentProjectRef.current;
      if (canvasDragRef.current && finalProj) {
        saveProjectState(finalProj, true);
        canvasDragRef.current = null;
        setIsCanvasDragging(false);
        setSnapGuideX(false);
        setSnapGuideY(false);
      }
    };

    window.addEventListener('mousemove', handlePointerMove);
    window.addEventListener('mouseup', handlePointerUp);
    window.addEventListener('touchmove', handlePointerMove, { passive: false });
    window.addEventListener('touchend', handlePointerUp);

    return () => {
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('mouseup', handlePointerUp);
      window.removeEventListener('touchmove', handlePointerMove);
      window.removeEventListener('touchend', handlePointerUp);
    };
  }, [isCanvasDragging, snappingEnabled]);

  // Master Global Pro NLE Keyboard Shortcuts (DaVinci / CapCut / Premiere style)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        setIsPlaying((p) => !p);
      } else if (e.code === 'KeyS' && !e.ctrlKey) {
        e.preventDefault();
        handleSplitClipAtPlayhead();
      } else if (e.code === 'KeyB' && e.ctrlKey) {
        e.preventDefault();
        handleSplitClipAtPlayhead();
      } else if (e.code === 'Delete' || e.code === 'Backspace') {
        e.preventDefault();
        handleDeleteSelectedClip();
      } else if (e.code === 'ArrowUp') {
        if (selectedClip && (selectedClip.source_type === 'sticker' || selectedClip.source_type === 'text' || selectedClip.source_type === 'subtitle')) {
          e.preventDefault();
          handleNudgePosition(selectedClip.id, 0, e.shiftKey ? -0.1 : -0.02);
        }
      } else if (e.code === 'ArrowDown') {
        if (selectedClip && (selectedClip.source_type === 'sticker' || selectedClip.source_type === 'text' || selectedClip.source_type === 'subtitle')) {
          e.preventDefault();
          handleNudgePosition(selectedClip.id, 0, e.shiftKey ? 0.1 : 0.02);
        }
      } else if (e.code === 'ArrowLeft') {
        if (selectedClip && (selectedClip.source_type === 'sticker' || selectedClip.source_type === 'text' || selectedClip.source_type === 'subtitle')) {
          e.preventDefault();
          handleNudgePosition(selectedClip.id, e.shiftKey ? -0.1 : -0.02, 0);
        } else {
          e.preventDefault();
          setCurrentTime((t) => Math.max(0, t - (e.shiftKey ? 1.0 : 0.033)));
        }
      } else if (e.code === 'ArrowRight') {
        if (selectedClip && (selectedClip.source_type === 'sticker' || selectedClip.source_type === 'text' || selectedClip.source_type === 'subtitle')) {
          e.preventDefault();
          handleNudgePosition(selectedClip.id, e.shiftKey ? 0.1 : 0.02, 0);
        } else {
          e.preventDefault();
          setCurrentTime((t) => Math.min(currentProject?.duration || 60, t + (e.shiftKey ? 1.0 : 0.033)));
        }
      } else if (e.code === 'KeyJ') {
        e.preventDefault();
        setPlaybackSpeed((s) => Math.max(0.25, s * 0.5));
      } else if (e.code === 'KeyK') {
        e.preventDefault();
        setIsPlaying(false);
      } else if (e.code === 'KeyL') {
        e.preventDefault();
        setPlaybackSpeed((s) => Math.min(4.0, s * 2.0));
      } else if (e.code === 'KeyZ' && (e.ctrlKey || e.metaKey) && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      } else if ((e.code === 'KeyY' && (e.ctrlKey || e.metaKey)) || (e.code === 'KeyZ' && (e.ctrlKey || e.metaKey) && e.shiftKey)) {
        e.preventDefault();
        handleRedo();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentProject, selectedClipId, currentTime, isPlaying, undoStack, redoStack, selectedClip]);

  // --- Project CRUD Operations ---
  const handleCreateNewProject = async () => {
    const name = prompt('Enter new project name:', 'Cinematic Reel #' + (projects.length + 1));
    if (!name) return;
    try {
      const created = await api.createStudioProject(name, exportAspect);
      setProjects([created, ...projects]);
      setCurrentProject(created);
      setSelectedClipId(null);
      setCurrentTime(0);
    } catch (e: any) {
      alert(`Error creating project: ${e.message}`);
    }
  };

  const handleDuplicateProject = async () => {
    if (!currentProject) return;
    try {
      const dup = await api.duplicateStudioProject(currentProject.id);
      setProjects([dup, ...projects]);
      setCurrentProject(dup);
      setAiNotice(`Duplicated project as '${dup.name}'`);
    } catch (e: any) {
      alert(`Error duplicating: ${e.message}`);
    }
  };

  const handleDeleteProject = async () => {
    if (!currentProject || !confirm(`Delete project '${currentProject.name}'?`)) return;
    try {
      await api.deleteStudioProject(currentProject.id);
      const remaining = projects.filter((p) => p.id !== currentProject.id);
      setProjects(remaining);
      if (remaining.length > 0) {
        const next = await api.getStudioProject(remaining[0].id);
        setCurrentProject(next);
      } else {
        handleCreateNewProject();
      }
    } catch (e: any) {
      alert(`Error deleting project: ${e.message}`);
    }
  };

  // --- Timeline Clip Operations ---
  const handleSplitClipAtPlayhead = async () => {
    if (!currentProject) return;
    const target =
      selectedClip ||
      currentProject.clips.find(
        (c) => currentTime >= c.start_time && currentTime <= c.start_time + c.duration
      );

    if (!target) {
      setAiNotice('Position playhead over a clip to split.');
      return;
    }

    try {
      const res = await api.splitStudioClip(currentProject.id, target.id, currentTime);
      setCurrentProject(res.project);
      setSelectedClipId(res.new_clip.id);
      setAiNotice(`Split clip '${target.name}' at ${currentTime.toFixed(2)}s`);
    } catch (e: any) {
      setAiNotice(`Split notice: ${e.message}`);
    }
  };

  const handleDeleteSelectedClip = () => {
    if (!currentProject || !selectedClipId) return;
    const target = currentProject.clips.find((c) => c.id === selectedClipId);
    if (!target) return;

    let updatedClips = currentProject.clips.filter((c) => c.id !== selectedClipId);

    if (rippleDelete) {
      const deletedTrack = target.track_id;
      const deletedStart = target.start_time;
      const deletedDur = target.duration;
      updatedClips = updatedClips.map((c) => {
        if (c.track_id === deletedTrack && c.start_time >= deletedStart) {
          return { ...c, start_time: Math.max(0, c.start_time - deletedDur) };
        }
        return c;
      });
    }

    const updated = {
      ...currentProject,
      clips: updatedClips,
      duration: Math.max(
        10,
        Math.max(...updatedClips.map((c) => c.start_time + c.duration), 10)
      ),
    };
    setSelectedClipId(null);
    saveProjectState(updated);
    setAiNotice(`Deleted clip '${target.name}'`);
  };

  const handleDuplicateSelectedClip = () => {
    if (!currentProject || !selectedClip) return;
    const clone: StudioClip = {
      ...selectedClip,
      id: Math.random().toString(36).substring(2, 9),
      name: `${selectedClip.name} (Copy)`,
      start_time: selectedClip.start_time + selectedClip.duration + 0.1,
    };
    const updated = {
      ...currentProject,
      clips: [...currentProject.clips, clone],
      duration: Math.max(currentProject.duration, clone.start_time + clone.duration + 2),
    };
    saveProjectState(updated);
    setSelectedClipId(clone.id);
    setCurrentTime(clone.start_time);
    setAiNotice(`Cloned clip '${clone.name}'`);
  };



  // --- AI Voice/Text Video Agent ---
  const handleExecuteAICommand = async (customPrompt?: string) => {
    const cmd = customPrompt || aiPrompt;
    if (!cmd.trim() || !currentProject) return;

    setAiWorking(true);
    setAiNotice(`JARVIS analyzing directive: "${cmd}"...`);

    try {
      const res = await api.executeStudioAIEdit(
        currentProject.id,
        cmd,
        selectedClipId || undefined,
        currentTime
      );
      if (res.project) {
        setCurrentProject(res.project);
        setExportAspect(res.project.aspect_ratio || '16:9');
      }
      setAiNotice(res.message);
      setAiPrompt('');
      if (res.export_triggered && res.export_job_id) {
        setShowExportModal(true);
        startTrackingRender(res.export_job_id);
      }
    } catch (e: any) {
      setAiNotice(`AI execution error: ${e.message}`);
    } finally {
      setAiWorking(false);
    }
  };

  // Voice Input via Web Speech API
  const handleToggleVoiceInput = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Type in the AI bar instead.');
      return;
    }

    if (isListeningMic) {
      setIsListeningMic(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListeningMic(true);
      setAiNotice('Listening for video editing command...');
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setAiPrompt(transcript);
      setIsListeningMic(false);
      handleExecuteAICommand(transcript);
    };

    recognition.onerror = () => {
      setIsListeningMic(false);
    };

    recognition.onend = () => {
      setIsListeningMic(false);
    };

    recognition.start();
  };

  // --- Voiceover Microphone Recording ---
  const handleToggleVoiceover = async () => {
    if (isRecordingVoiceover) {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      setIsRecordingVoiceover(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          const file = new File([audioBlob], `voiceover_${Date.now()}.wav`, { type: 'audio/wav' });

          try {
            const uploadRes = await api.uploadStudioMedia(file);
            if (currentProject) {
              const a1Track =
                currentProject.tracks.find((t) => t.id === 'A1') || currentProject.tracks[0];
              const voClip: StudioClip = {
                id: Math.random().toString(36).substring(2, 9),
                track_id: a1Track.id,
                name: 'Live Voiceover',
                source_type: 'audio',
                source_file: uploadRes.path,
                source_url: uploadRes.url,
                start_time: currentTime,
                duration: 5.0,
                in_point: 0.0,
                out_point: 5.0,
                speed: 1.0,
                volume: 1.2,
                fade_in: 0.2,
                fade_out: 0.2,
                transform: {
                  scale_x: 1,
                  scale_y: 1,
                  position_x: 0,
                  position_y: 0,
                  rotation: 0,
                  flip_h: false,
                  flip_v: false,
                  opacity: 1,
                },
                filters: {
                  brightness: 0,
                  contrast: 1,
                  saturation: 1,
                  temperature: 0,
                  tint: 0,
                  blur: 0,
                  sharpen: 0,
                  vignette: 0,
                },
              };

              const updated = {
                ...currentProject,
                clips: [...currentProject.clips, voClip],
              };
              saveProjectState(updated);
              setAiNotice('Voiceover recorded and placed on Audio Track A1.');
            }
          } catch (e: any) {
            alert(`Voiceover upload failed: ${e.message}`);
          }
          stream.getTracks().forEach((track) => track.stop());
        };

        mediaRecorder.start();
        setIsRecordingVoiceover(true);
        setAiNotice('Recording voiceover live into timeline...');
      } catch (err: any) {
        alert(`Cannot access microphone: ${err.message}`);
      }
    }
  };

  // --- Media Import from Local Files ---
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !currentProject) return;

    try {
      setAiNotice(`Uploading media '${file.name}'...`);
      const res = await api.uploadStudioMedia(file);
      const isAudio = file.type.startsWith('audio');
      const isImg = file.type.startsWith('image');
      const targetTrack = isAudio ? 'A1' : isImg ? 'V2' : 'V1';
      const clipType = isAudio ? 'audio' : isImg ? 'image' : 'video';

      const v1Clips = currentProject.clips.filter((c) => c.track_id === targetTrack);
      const insertTime = v1Clips.length === 0 ? 0.0 : currentTime;

      const newClip: StudioClip = {
        id: Math.random().toString(36).substring(2, 9),
        track_id: targetTrack,
        name: file.name,
        source_type: clipType,
        source_file: res.path,
        source_url: res.url,
        start_time: insertTime,
        duration: isImg ? 5.0 : 15.0,
        in_point: 0.0,
        out_point: isImg ? 5.0 : 15.0,
        speed: 1.0,
        volume: 1.0,
        fade_in: 0.0,
        fade_out: 0.0,
        transform: {
          scale_x: 1,
          scale_y: 1,
          position_x: 0,
          position_y: 0,
          rotation: 0,
          flip_h: false,
          flip_v: false,
          opacity: 1,
        },
        filters: {
          brightness: 0,
          contrast: 1,
          saturation: 1,
          temperature: 0,
          tint: 0,
          blur: 0,
          sharpen: 0,
          vignette: 0,
        },
      };

      const updated = {
        ...currentProject,
        clips: [...currentProject.clips, newClip],
        duration: Math.max(currentProject.duration, insertTime + newClip.duration + 2),
      };
      saveProjectState(updated);
      setSelectedClipId(newClip.id);
      setCurrentTime(newClip.start_time);
      setAiNotice(`Imported '${file.name}' to timeline.`);
    } catch (e: any) {
      alert(`Media upload failed: ${e.message}`);
    }
  };

  // Import Candidate Clip from JARVIS Clipping Engine
  const handleImportClippingCandidate = async (candidate: ClipItem) => {
    if (!currentProject) return;
    try {
      const v1Clips = currentProject.clips.filter((c) => c.track_id === 'V1');
      let insertTime = 0.0;
      if (v1Clips.length > 0) {
        insertTime = Math.round(currentTime * 10) / 10;
      }

      const res = await api.importClippedToStudio(
        currentProject.id,
        candidate.output_path || candidate.source_file,
        candidate.title,
        insertTime
      );
      if (res.project) {
        setCurrentProject(res.project);
        setSelectedClipId(res.clip.id);
        setCurrentTime(res.clip.start_time);
        setAiNotice(`Imported '${candidate.title}' and jumped playhead to ${res.clip.start_time.toFixed(1)}s.`);
      }
    } catch (e: any) {
      alert(`Error importing clip: ${e.message}`);
    }
  };

  // --- Web Audio SFX Synthesizer (Instant Meme & Sound FX) ---
  const playViralSFX = (type: string) => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      if (type === 'vine_boom') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(80, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(18, ctx.currentTime + 1.2);
        gain.gain.setValueAtTime(1.0, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.2);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 1.2);
      } else if (type === 'whoosh') {
        const bufferSize = Math.floor(ctx.sampleRate * 0.4);
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
        const noise = ctx.createBufferSource();
        noise.buffer = buffer;
        const filter = ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(350, ctx.currentTime);
        filter.frequency.exponentialRampToValueAtTime(2600, ctx.currentTime + 0.2);
        filter.frequency.exponentialRampToValueAtTime(250, ctx.currentTime + 0.4);
        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0.8, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.01, ctx.currentTime + 0.4);
        noise.connect(filter);
        filter.connect(gain);
        gain.connect(ctx.destination);
        noise.start();
      } else if (type === 'camera') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(1500, ctx.currentTime);
        gain.gain.setValueAtTime(0.8, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.08);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.08);
      } else if (type === '808_drop') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(130, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(32, ctx.currentTime + 0.9);
        gain.gain.setValueAtTime(1.0, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.9);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.9);
      } else if (type === 'bell') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(1760, ctx.currentTime);
        gain.gain.setValueAtTime(0.7, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.8);
      } else if (type === 'glitch') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(250, ctx.currentTime);
        osc.frequency.setValueAtTime(900, ctx.currentTime + 0.06);
        osc.frequency.setValueAtTime(120, ctx.currentTime + 0.12);
        gain.gain.setValueAtTime(0.6, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.22);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.22);
      } else if (type === 'pop') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(350, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(1200, ctx.currentTime + 0.12);
        gain.gain.setValueAtTime(0.8, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.12);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.12);
      }
    } catch (e) {
      console.warn('Audio synthesis warning:', e);
    }
  };

  // --- Viral SFX Catalog ---
  const viralSFXList = [
    { id: 'vine_boom', title: 'Vine Boom', duration: 1.2, icon: '💥', tag: 'Meme Bass' },
    { id: 'whoosh', title: 'Whoosh Swish', duration: 0.4, icon: '💨', tag: 'Fast Transition' },
    { id: 'camera', title: 'Camera Shutter', duration: 0.1, icon: '📸', tag: 'Photo Click' },
    { id: '808_drop', title: '808 Bass Drop', duration: 0.9, icon: '🔊', tag: 'Sub Drop' },
    { id: 'bell', title: 'Ding Bell', duration: 0.8, icon: '🔔', tag: 'Reward Bell' },
    { id: 'glitch', title: 'Cyber Glitch', duration: 0.2, icon: '⚡', tag: 'Zap Distortion' },
    { id: 'pop', title: 'Bubble Pop', duration: 0.15, icon: '🫧', tag: 'Snappy UI' },
  ];

  const handleAddSFXToTimeline = (sfx: typeof viralSFXList[0]) => {
    if (!currentProject) return;
    const audioTrack = currentProject.tracks.find((t) => t.type === 'audio') || currentProject.tracks[0];
    const sfxClip: StudioClip = {
      id: Math.random().toString(36).substring(2, 9),
      track_id: audioTrack ? audioTrack.id : 'A1',
      name: `SFX: ${sfx.title}`,
      source_type: 'audio',
      start_time: currentTime,
      duration: sfx.duration,
      in_point: 0.0,
      out_point: sfx.duration,
      speed: 1.0,
      volume: 1.0,
      fade_in: 0.0,
      fade_out: 0.0,
      transform: { scale_x: 1, scale_y: 1, position_x: 0, position_y: 0, rotation: 0, flip_h: false, flip_v: false, opacity: 1 },
      filters: { brightness: 0, contrast: 1, saturation: 1, temperature: 0, tint: 0, blur: 0, sharpen: 0, vignette: 0 },
    };
    playViralSFX(sfx.id);
    const updated = {
      ...currentProject,
      clips: [...currentProject.clips, sfxClip],
    };
    saveProjectState(updated);
    setSelectedClipId(sfxClip.id);
    setAiNotice(`Added '${sfx.title}' SFX at ${currentTime.toFixed(1)}s.`);
  };

  // --- Viral Stickers & Emojis Catalog ---
  const viralStickers = [
    { emoji: '🔥', name: 'Fire', label: 'Viral Lit' },
    { emoji: '⚽', name: 'Football', label: 'Golazo' },
    { emoji: '👑', name: 'Crown', label: 'GOAT King' },
    { emoji: '💀', name: 'Skull', label: 'Dead / LOL' },
    { emoji: '⚡', name: 'Lightning', label: 'Speed Shock' },
    { emoji: '🎯', name: 'Target', label: 'Precision' },
    { emoji: '⚠️', name: 'Warning', label: 'Alert' },
    { emoji: '🔔', name: 'Bell', label: 'Subscribe' },
    { emoji: '❤️', name: 'Heart', label: 'Love' },
    { emoji: '💯', name: '100', label: 'Peak Tier' },
    { emoji: '🚀', name: 'Rocket', label: 'Moon' },
    { emoji: '🏆', name: 'Trophy', label: 'Winner' },
  ];

  const handleAddSticker = (stickerEmoji: string, name: string, customText?: string) => {
    if (!currentProject) return;
    const stickerClip: StudioClip = {
      id: Math.random().toString(36).substring(2, 9),
      track_id: 'T1',
      name: `Sticker: ${name}`,
      source_type: 'sticker',
      start_time: currentTime,
      duration: 3.5,
      in_point: 0.0,
      out_point: 3.5,
      speed: 1.0,
      volume: 1.0,
      fade_in: 0.0,
      fade_out: 0.0,
      transform: {
        scale_x: customText ? 1.0 : 1.5,
        scale_y: customText ? 1.0 : 1.5,
        position_x: 0,
        position_y: -0.25,
        rotation: 0,
        flip_h: false,
        flip_v: false,
        opacity: 1,
      },
      filters: {
        brightness: 0,
        contrast: 1,
        saturation: 1,
        temperature: 0,
        tint: 0,
        blur: 0,
        sharpen: 0,
        vignette: 0,
      },
      text_props: {
        text: customText || stickerEmoji,
        font: 'Arial',
        font_size: 72,
        color: '#FFFFFF',
        highlight_color: '#FFFF00',
        outline_color: '#000000',
        outline_width: 0,
        alignment: 'center',
        is_subtitle: false,
        karaoke_mode: false,
        sticker_emoji: stickerEmoji,
        animation: customText ? 'none' : 'bounce',
      },
    };

    const updated = {
      ...currentProject,
      clips: [...currentProject.clips, stickerClip],
    };
    saveProjectState(updated);
    setSelectedClipId(stickerClip.id);
    setAiNotice(`Added sticker ${stickerEmoji} overlay to timeline.`);
  };

  // Helper to determine the target video clip for effects, filters, and transitions
  const getTargetVideoClip = (): StudioClip | null => {
    if (!currentProject) return null;
    const selected = currentProject.clips.find((c) => c.id === selectedClipId && c.source_type === 'video');
    if (selected) return selected;
    if (activeVideoClip) return activeVideoClip;
    return currentProject.clips.find((c) => c.source_type === 'video') || null;
  };

  // --- CapCut Transitions Catalog ---
  const capCutTransitions = [
    { id: 'none', name: 'None / Cut', desc: 'Standard sharp cut without transition', icon: '✂️' },
    { id: 'flash_white', name: 'Flash White', desc: 'Dramatic white frame impact flash', icon: '⚡' },
    { id: 'cross_dissolve', name: 'Cross Dissolve', desc: 'Smooth cinematic blend between shots', icon: '✨' },
    { id: 'zoom_in', name: 'Zoom In Punch', desc: 'Sudden scale punch for impactful beats', icon: '🔍' },
    { id: 'zoom_out', name: 'Zoom Out Reveal', desc: 'Fast pull-back to wide frame', icon: '🔭' },
    { id: 'glitch', name: 'Cyber Glitch', desc: 'Futuristic stutter digital interference', icon: '📺' },
    { id: 'wipe_left', name: 'Wipe Left', desc: 'Horizontal motion push transition', icon: '◀' },
  ];

  const handleApplyTransition = (transId: string) => {
    if (!currentProject) return;
    const targetVideo = getTargetVideoClip();
    if (!targetVideo) {
      setAiNotice('Please add or select a video clip first.');
      return;
    }

    const updatedClips = currentProject.clips.map((c) =>
      c.id === targetVideo.id ? { ...c, filters: { ...c.filters, transition: transId } } : c
    );
    const updated = { ...currentProject, clips: updatedClips };
    currentProjectRef.current = updated;
    saveProjectState(updated, true);
    setSelectedClipId(targetVideo.id);

    if (transId === 'none') {
      setAiNotice(`Removed transition from '${targetVideo.name}'.`);
    } else {
      setAiNotice(`Applied ${transId.replace('_', ' ')} transition to '${targetVideo.name}'.`);
      // Rewind to start of clip and auto-play transition preview
      setCurrentTime(targetVideo.start_time);
      setIsPlaying(true);
      playViralSFX(transId === 'glitch' ? 'glitch' : 'whoosh');
    }
  };

  // --- Dynamic Aspect Ratio Switcher ---
  const handleSetAspectRatio = (ratio: '16:9' | '9:16' | '1:1' | '4:5') => {
    if (!currentProject) return;
    let w = 1920, h = 1080;
    if (ratio === '9:16') { w = 1080; h = 1920; }
    else if (ratio === '1:1') { w = 1080; h = 1080; }
    else if (ratio === '4:5') { w = 1080; h = 1350; }
    const updated = {
      ...currentProject,
      aspect_ratio: ratio,
      width: w,
      height: h
    };
    saveProjectState(updated);
    setExportAspect(ratio);
    setAiNotice(`Timeline aspect ratio updated to ${ratio}`);
  };

  // --- Preset Stock Clips Catalog ---
  const presetStockVideos = [
    {
      id: 'stk_mrbeast',
      title: 'MrBeast Vertical Challenge',
      url: '/output/reels/clip_8207c7fa-4f9_mrbeast.mp4',
      aspect: '9:16',
      duration: 15.0,
      genre: 'Viral Short'
    },
    {
      id: 'stk_cyber',
      title: 'Cyberpunk Neon Action',
      url: '/output/reels/clip_8207c7fa-4f9_cyberpunk.mp4',
      aspect: '9:16',
      duration: 12.0,
      genre: 'High Energy'
    },
    {
      id: 'stk_cinema',
      title: 'Chef Gourmet 35mm',
      url: '/output/reels/clip_5f17a17f-84c_cinematic.mp4',
      aspect: '16:9',
      duration: 20.0,
      genre: 'Cinema 4K'
    },
    {
      id: 'stk_splash',
      title: 'Sin City Subject Splash',
      url: '/output/exports/mrbeast_color_splash.mp4',
      aspect: '9:16',
      duration: 14.0,
      genre: 'Isolation'
    }
  ];

  const handleAddStockVideo = (stock: typeof presetStockVideos[0]) => {
    if (!currentProject) return;
    const vTrack = currentProject.tracks.find((t) => t.type === 'video') || currentProject.tracks[0];
    const newClip: StudioClip = {
      id: Math.random().toString(36).substring(2, 9),
      track_id: vTrack.id,
      name: stock.title,
      source_type: 'video',
      source_url: stock.url,
      start_time: currentTime,
      duration: stock.duration,
      in_point: 0.0,
      out_point: stock.duration,
      speed: 1.0,
      volume: 1.0,
      fade_in: 0.0,
      fade_out: 0.0,
      transform: { scale_x: 1, scale_y: 1, position_x: 0, position_y: 0, rotation: 0, flip_h: false, flip_v: false, opacity: 1 },
      filters: { brightness: 0, contrast: 1, saturation: 1, temperature: 0, tint: 0, blur: 0, sharpen: 0, vignette: 0 },
    };
    const updated = {
      ...currentProject,
      clips: [...currentProject.clips, newClip],
      duration: Math.max(currentProject.duration, currentTime + stock.duration)
    };
    saveProjectState(updated);
    setSelectedClipId(newClip.id);
    setAiNotice(`Added stock clip '${stock.title}' at ${currentTime.toFixed(1)}s.`);
  };

  // --- Trending Royalty-Free Audio Beats ---
  const trendingAudioBeats = [
    { id: 'beat_phonk', title: 'Brazilian Phonk Beat', bpm: 140, genre: 'High Drift', duration: 18.0 },
    { id: 'beat_trap', title: 'Dark Cyber Trap Sub', bpm: 130, genre: 'Heavy 808', duration: 15.0 },
    { id: 'beat_lofi', title: 'Midnight Chill Lo-Fi', bpm: 85, genre: 'Relaxed', duration: 24.0 },
    { id: 'beat_stadium', title: 'Champions Stadium Roar', bpm: 125, genre: 'Crowd Roar', duration: 16.0 },
  ];

  const handleAddMusicBeat = (beat: typeof trendingAudioBeats[0]) => {
    if (!currentProject) return;
    const aTrack = currentProject.tracks.find((t) => t.type === 'audio') || currentProject.tracks[0];
    const newClip: StudioClip = {
      id: Math.random().toString(36).substring(2, 9),
      track_id: aTrack.id,
      name: `Music: ${beat.title}`,
      source_type: 'audio',
      start_time: currentTime,
      duration: beat.duration,
      in_point: 0.0,
      out_point: beat.duration,
      speed: 1.0,
      volume: 0.8,
      fade_in: 0.5,
      fade_out: 0.5,
      transform: { scale_x: 1, scale_y: 1, position_x: 0, position_y: 0, rotation: 0, flip_h: false, flip_v: false, opacity: 1 },
      filters: { brightness: 0, contrast: 1, saturation: 1, temperature: 0, tint: 0, blur: 0, sharpen: 0, vignette: 0 },
    };
    playViralSFX('808_drop');
    const updated = {
      ...currentProject,
      clips: [...currentProject.clips, newClip],
    };
    saveProjectState(updated);
    setSelectedClipId(newClip.id);
    setAiNotice(`Added music beat '${beat.title}' at ${currentTime.toFixed(1)}s.`);
  };

  // --- Subtitle & Text Presets ---
  const subtitlePresets = [
    {
      id: 'mrbeast',
      name: 'MrBeast Bouncing Yellow',
      font: 'Impact',
      color: '#FFFF00',
      highlight: '#00FFFF',
      outline: '#000000',
      outlineWidth: 5,
      bgColor: undefined,
    },
    {
      id: 'hormozi',
      name: 'Alex Hormozi Red Box',
      font: 'Arial Black',
      color: '#FFFFFF',
      highlight: '#FFFF00',
      outline: '#000000',
      outlineWidth: 2,
      bgColor: '#DC2626',
    },
    {
      id: 'tiktok',
      name: 'TikTok Viral Green',
      font: 'Montserrat',
      color: '#22C55E',
      highlight: '#FFFFFF',
      outline: '#000000',
      outlineWidth: 3,
      bgColor: undefined,
    },
    {
      id: 'cyberpunk',
      name: 'Cyberpunk Neon',
      font: 'Impact',
      color: '#00FFFF',
      highlight: '#EC4899',
      outline: '#000000',
      outlineWidth: 4,
      bgColor: undefined,
    },
    {
      id: 'serif',
      name: 'Cinematic Gold Serif',
      font: 'Georgia',
      color: '#F59E0B',
      highlight: '#FDE68A',
      outline: '#000000',
      outlineWidth: 2,
      bgColor: undefined,
    },
    {
      id: 'clean',
      name: 'Clean White Minimal',
      font: 'Helvetica',
      color: '#FFFFFF',
      highlight: '#38BDF8',
      outline: '#000000',
      outlineWidth: 2,
      bgColor: undefined,
    },
  ];

  const handleAddTextOverlay = (presetId = 'mrbeast') => {
    if (!currentProject) return;
    const preset = subtitlePresets.find((p) => p.id === presetId) || subtitlePresets[0];
    const textClip: StudioClip = {
      id: Math.random().toString(36).substring(2, 9),
      track_id: 'T1',
      name: `Title: ${preset.name}`,
      source_type: 'text',
      start_time: currentTime,
      duration: 4.0,
      in_point: 0.0,
      out_point: 4.0,
      speed: 1.0,
      volume: 1.0,
      fade_in: 0.0,
      fade_out: 0.0,
      transform: {
        scale_x: 1,
        scale_y: 1,
        position_x: 0,
        position_y: 0.28,
        rotation: 0,
        flip_h: false,
        flip_v: false,
        opacity: 1,
      },
      filters: {
        brightness: 0,
        contrast: 1,
        saturation: 1,
        temperature: 0,
        tint: 0,
        blur: 0,
        sharpen: 0,
        vignette: 0,
      },
      text_props: {
        text: 'ATTRACT ATTENTION HERE',
        font: preset.font,
        font_size: 56,
        color: preset.color,
        highlight_color: preset.highlight,
        outline_color: preset.outline,
        outline_width: preset.outlineWidth,
        bg_color: preset.bgColor,
        alignment: 'center',
        is_subtitle: true,
        karaoke_mode: true,
      },
    };

    const updated = {
      ...currentProject,
      clips: [...currentProject.clips, textClip],
    };
    saveProjectState(updated);
    setSelectedClipId(textClip.id);
    setAiNotice(`Added ${preset.name} caption overlay.`);
  };

  // --- Instagram & DaVinci Color Grading Presets ---
  const applyColorPreset = (preset: string) => {
    if (!currentProject) return;
    const targetVideo = getTargetVideoClip();
    if (!targetVideo) {
      setAiNotice('Please add or select a video clip first.');
      return;
    }

    let b = 0.0;
    let c = 1.0;
    let s = 1.0;
    let v = 0.0;
    let t = 0;
    let tint = 0;
    let lift = 0.0;
    let gamma = 1.0;
    let gain = 1.0;
    let colorSplash = false;

    if (preset === 'clarendon') {
      b = 0.06;
      c = 1.25;
      s = 1.35;
      v = 0.15;
      tint = -8;
      t = 5;
    } else if (preset === 'juno') {
      b = 0.05;
      c = 1.2;
      s = 1.3;
      t = 28;
      v = 0.1;
      tint = 5;
    } else if (preset === 'valencia') {
      b = 0.08;
      c = 1.08;
      s = 0.9;
      t = 35;
      v = 0.25;
      tint = 10;
    } else if (preset === 'retro_vhs') {
      b = -0.02;
      c = 1.35;
      s = 0.85;
      t = 15;
      tint = -10;
      v = 0.45;
    } else if (preset === 'teal_orange') {
      b = -0.02;
      c = 1.3;
      s = 1.3;
      t = 25;
      tint = -18;
      lift = -0.06;
      gamma = 1.05;
      gain = 1.15;
      v = 0.25;
    } else if (preset === 'cyberpunk') {
      b = 0.05;
      c = 1.35;
      s = 1.6;
      t = -25;
      tint = 30;
      v = 0.2;
    } else if (preset === 'cinematic') {
      b = -0.04;
      c = 1.25;
      s = 0.9;
      v = 0.35;
      t = -5;
    } else if (preset === 'vibrant') {
      b = 0.04;
      c = 1.2;
      s = 1.65;
    } else if (preset === 'noir') {
      s = 0.0;
      c = 1.45;
      b = 0.02;
      v = 0.35;
      lift = -0.05;
      gain = 1.1;
    } else if (preset === 'vintage') {
      b = 0.05;
      c = 1.1;
      s = 1.1;
      t = 25;
      v = 0.2;
    } else if (preset === 'color_splash') {
      c = 1.3;
      s = 1.4;
      v = 0.2;
      colorSplash = true;
    } else if (preset === 'reset' || preset === 'normal') {
      b = 0.0;
      c = 1.0;
      s = 1.0;
      v = 0.0;
      t = 0;
      tint = 0;
      lift = 0.0;
      gamma = 1.0;
      gain = 1.0;
      colorSplash = false;
    }

    const updatedClips = currentProject.clips.map((clip) => {
      if (clip.id === targetVideo.id) {
        return {
          ...clip,
          filters: {
            ...clip.filters,
            brightness: b,
            contrast: c,
            saturation: s,
            vignette: v,
            temperature: t,
            tint: tint,
            lift: lift,
            gamma: gamma,
            gain: gain,
            color_splash: colorSplash,
            preset_name: preset === 'color_splash' ? 'Sin City (Color Splash)' : preset === 'reset' ? undefined : preset,
          },
        };
      }
      return clip;
    });

    const updated = { ...currentProject, clips: updatedClips };
    currentProjectRef.current = updated;
    saveProjectState(updated, true);
    setSelectedClipId(targetVideo.id);
    if (currentTime < targetVideo.start_time || currentTime > targetVideo.start_time + targetVideo.duration) {
      setCurrentTime(targetVideo.start_time);
    }
    setAiNotice(`Applied ${preset.replace('_', ' ').toUpperCase()} color preset to '${targetVideo.name}'.`);
  };

  // --- Export and Render Execution ---
  const handleStartExport = async () => {
    if (!currentProject) return;
    setIsRendering(true);
    setRenderProgress(10);
    setRenderDownloadUrl(null);

    try {
      const res = await api.exportStudioProject(currentProject.id, {
        resolution: exportRes,
        aspect_ratio: exportAspect,
        codec: exportCodec,
        export_audio_only: exportAudioOnly,
      });
      setRenderJobId(res.job_id);
      startTrackingRender(res.job_id);
    } catch (e: any) {
      alert(`Export trigger error: ${e.message}`);
      setIsRendering(false);
    }
  };

  const startTrackingRender = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const job = await api.getStudioJobStatus(jobId);
        if (job) {
          setRenderProgress(job.progress || 20);
          if (job.status === 'completed') {
            clearInterval(interval);
            setIsRendering(false);
            setRenderProgress(100);
            setRenderDownloadUrl(job.output_url);
            setAiNotice(`Project export complete: ${job.output_filename}`);
          } else if (job.status === 'failed') {
            clearInterval(interval);
            setIsRendering(false);
            alert(`Render failed: ${job.error}`);
          }
        }
      } catch (err) {
        clearInterval(interval);
        setIsRendering(false);
      }
    }, 1500);
  };

  // Export Apple FCPXML v1.9 for DaVinci Resolve
  const handleExportDaVinciFCPXML = async () => {
    if (!currentProject) return;
    try {
      const res = await api.exportStudioFcpxml(currentProject.id);
      window.open(res.download_url, '_blank');
      setAiNotice(`FCPXML v1.9 downloaded for DaVinci Resolve!`);
    } catch (e: any) {
      alert(`DaVinci FCPXML export failed: ${e.message}`);
    }
  };

  // Time format helper
  const formatTimecode = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 100);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-950 text-slate-100 font-sans select-none overflow-hidden">
      {/* 1. COMPACT TOP TOOLBAR (Full Width, 48px) */}
      <header className="h-12 border-b border-cyan-500/20 bg-slate-900/95 px-3 flex items-center justify-between gap-3 shrink-0 z-30 backdrop-blur-md">
        {/* Left: Project Selector & Panels Toggle */}
        <div className="flex items-center gap-2">
          {/* Panel Toggles */}
          <button
            onClick={() => setShowLeftPanel(!showLeftPanel)}
            title={showLeftPanel ? 'Hide Media Panel' : 'Show Media Panel'}
            className={`p-1.5 rounded-lg border text-xs cursor-pointer transition-colors ${
              showLeftPanel
                ? 'bg-cyan-500/15 border-cyan-500/40 text-cyan-300'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <PanelLeft className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-1.5 text-cyan-400 font-bold font-mono tracking-wider text-xs uppercase ml-1">
            <Film className="w-4 h-4 text-cyan-400" />
            <span className="hidden sm:inline">STUDIO</span>
          </div>

          <div className="h-4 w-px bg-slate-800 mx-1" />

          {/* Project Switcher */}
          <select
            value={currentProject?.id || ''}
            onChange={async (e) => {
              const loaded = await api.getStudioProject(e.target.value);
              setCurrentProject(loaded);
              setExportAspect(loaded.aspect_ratio || '16:9');
              setSelectedClipId(null);
            }}
            className="bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-1 text-slate-200 font-mono focus:border-cyan-400 outline-none max-w-[150px] truncate"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          <button
            onClick={handleCreateNewProject}
            title="Create New Project"
            className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-cyan-400 cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>

          {/* Undo / Redo */}
          <div className="flex items-center gap-0.5 bg-slate-950 p-0.5 rounded-lg border border-slate-800 ml-1">
            <button
              onClick={handleUndo}
              disabled={undoStack.length === 0}
              title="Undo (Ctrl+Z)"
              className="p-1 rounded text-slate-300 hover:text-cyan-400 hover:bg-slate-800 disabled:opacity-30 disabled:hover:text-slate-500 cursor-pointer transition-colors"
            >
              <Undo2 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleRedo}
              disabled={redoStack.length === 0}
              title="Redo (Ctrl+Y)"
              className="p-1 rounded text-slate-300 hover:text-cyan-400 hover:bg-slate-800 disabled:opacity-30 disabled:hover:text-slate-500 cursor-pointer transition-colors"
            >
              <Redo2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Center: Aspect Ratio & AI Command Bar */}
        <div className="flex-1 max-w-xl flex items-center gap-2">
          {/* Aspect Ratio Pills */}
          <div className="flex items-center rounded-lg bg-slate-950 p-0.5 border border-slate-800 text-[11px] font-mono shrink-0">
            <button
              onClick={() => handleSetAspectRatio('16:9')}
              className={`px-2 py-0.5 rounded-md transition-all ${
                currentProject?.aspect_ratio === '16:9'
                  ? 'bg-cyan-500/20 text-cyan-300 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              16:9
            </button>
            <button
              onClick={() => handleSetAspectRatio('9:16')}
              className={`px-2 py-0.5 rounded-md transition-all ${
                currentProject?.aspect_ratio === '9:16'
                  ? 'bg-cyan-500/20 text-cyan-300 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              9:16 Vertical
            </button>
            <button
              onClick={() => handleSetAspectRatio('1:1')}
              className={`px-2 py-0.5 rounded-md transition-all ${
                currentProject?.aspect_ratio === '1:1'
                  ? 'bg-cyan-500/20 text-cyan-300 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              1:1
            </button>
            <button
              onClick={() => handleSetAspectRatio('4:5')}
              className={`px-2 py-0.5 rounded-md transition-all ${
                currentProject?.aspect_ratio === '4:5'
                  ? 'bg-cyan-500/20 text-cyan-300 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              4:5 Feed
            </button>
          </div>

          {/* JARVIS Natural Language AI Command Bar */}
          <div className="flex-1 relative flex items-center">
            <input
              type="text"
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleExecuteAICommand()}
              placeholder="Ask JARVIS: 'cut from 20s to 45s', 'make cinematic', 'add subtitles'..."
              className="w-full bg-slate-950 border border-cyan-500/30 rounded-xl pl-8 pr-14 py-1 text-xs text-slate-100 placeholder-slate-500 font-mono focus:border-cyan-400 outline-none"
            />
            <Sparkles className="w-3.5 h-3.5 text-cyan-400 absolute left-2.5 pointer-events-none" />

            <div className="absolute right-1 flex items-center gap-0.5">
              <button
                onClick={handleToggleVoiceInput}
                title="Voice Command (Mic)"
                className={`p-1 rounded cursor-pointer transition-colors ${
                  isListeningMic
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'text-slate-400 hover:text-cyan-400 hover:bg-slate-800'
                }`}
              >
                {isListeningMic ? <Mic className="w-3 h-3" /> : <MicOff className="w-3 h-3" />}
              </button>
              <button
                onClick={() => handleExecuteAICommand()}
                disabled={aiWorking}
                title="Execute Command"
                className="p-1 rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 cursor-pointer disabled:opacity-50"
              >
                <Wand2 className={`w-3 h-3 ${aiWorking ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>

        {/* Right: Inspector Toggle, DaVinci & Render */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowRightInspector(!showRightInspector)}
            title={showRightInspector ? 'Hide Inspector' : 'Show Inspector'}
            className={`p-1.5 rounded-lg border text-xs cursor-pointer transition-colors ${
              showRightInspector
                ? 'bg-cyan-500/15 border-cyan-500/40 text-cyan-300'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <PanelRight className="w-4 h-4" />
          </button>

          <button
            onClick={handleExportDaVinciFCPXML}
            title="Export Apple FCPXML to DaVinci Resolve"
            className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-cyan-400 text-xs font-mono flex items-center gap-1.5 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden md:inline">DaVinci XML</span>
          </button>

          <button
            onClick={() => setShowExportModal(true)}
            className="px-3.5 py-1 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase font-mono tracking-wider flex items-center gap-1.5 cursor-pointer shadow-cyan-sm"
          >
            <Film className="w-3.5 h-3.5" />
            <span>Render</span>
          </button>
        </div>
      </header>

      {/* AI Notification Banner */}
      {aiNotice && (
        <div className="bg-cyan-950/90 border-b border-cyan-500/30 px-3 py-1 text-xs font-mono text-cyan-300 flex items-center justify-between shrink-0 z-20">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span>{aiNotice}</span>
          </div>
          <button
            onClick={() => setAiNotice(null)}
            className="text-slate-400 hover:text-slate-200 text-[11px] cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* 2. MAIN COMPOSITION WORKSPACE (Flex-1) */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* A. LEFT SIDEBAR (Collapsible, w-72) */}
        {showLeftPanel && (
          <div className="w-72 border-r border-slate-800 bg-slate-950/95 flex flex-col shrink-0 z-10 animate-fadeIn">
            {/* Tab Navigation (6 Pro Tabs: CapCut / Instagram / DaVinci) */}
            <div className="grid grid-cols-6 border-b border-slate-800 text-[10px] font-mono">
              <button
                onClick={() => setActiveTab('media')}
                className={`py-2 flex flex-col items-center gap-0.5 transition-all ${
                  activeTab === 'media'
                    ? 'border-b-2 border-cyan-400 text-cyan-300 bg-slate-900/50'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Media Library & Ingest"
              >
                <Film className="w-3.5 h-3.5" />
                <span className="truncate">Media</span>
              </button>
              <button
                onClick={() => setActiveTab('audio')}
                className={`py-2 flex flex-col items-center gap-0.5 transition-all ${
                  activeTab === 'audio'
                    ? 'border-b-2 border-cyan-400 text-cyan-300 bg-slate-900/50'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Audio, SFX & Voiceover"
              >
                <Music className="w-3.5 h-3.5" />
                <span className="truncate">Audio</span>
              </button>
              <button
                onClick={() => setActiveTab('text')}
                className={`py-2 flex flex-col items-center gap-0.5 transition-all ${
                  activeTab === 'text'
                    ? 'border-b-2 border-cyan-400 text-cyan-300 bg-slate-900/50'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Viral Text & Subtitles"
              >
                <Type className="w-3.5 h-3.5" />
                <span className="truncate">Text</span>
              </button>
              <button
                onClick={() => setActiveTab('stickers')}
                className={`py-2 flex flex-col items-center gap-0.5 transition-all ${
                  activeTab === 'stickers'
                    ? 'border-b-2 border-cyan-400 text-cyan-300 bg-slate-900/50'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Viral Stickers & Emojis"
              >
                <Smile className="w-3.5 h-3.5" />
                <span className="truncate">Stickers</span>
              </button>
              <button
                onClick={() => setActiveTab('effects')}
                className={`py-2 flex flex-col items-center gap-0.5 transition-all ${
                  activeTab === 'effects'
                    ? 'border-b-2 border-cyan-400 text-cyan-300 bg-slate-900/50'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Instagram Filters & DaVinci LUTs"
              >
                <Sliders className="w-3.5 h-3.5" />
                <span className="truncate">Filters</span>
              </button>
              <button
                onClick={() => setActiveTab('transitions')}
                className={`py-2 flex flex-col items-center gap-0.5 transition-all ${
                  activeTab === 'transitions'
                    ? 'border-b-2 border-cyan-400 text-cyan-300 bg-slate-900/50'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="CapCut Motion Transitions"
              >
                <Layers className="w-3.5 h-3.5" />
                <span className="truncate">Transit</span>
              </button>
            </div>

            {/* Tab Content Panes */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {/* TAB 1: MEDIA LIBRARY */}
              {activeTab === 'media' && (
                <div className="space-y-3">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept="video/*,audio/*,image/*"
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full py-2.5 rounded-xl border border-dashed border-cyan-500/40 bg-cyan-950/20 hover:bg-cyan-950/40 text-cyan-300 text-xs font-mono flex flex-col items-center justify-center gap-1 cursor-pointer transition-all"
                  >
                    <Upload className="w-4 h-4 text-cyan-400" />
                    <span>Upload Local File</span>
                    <span className="text-[9px] text-slate-500">MP4, MOV, MP3, PNG, JPG</span>
                  </button>

                  <div>
                    <div className="flex items-center justify-between text-xs font-bold text-slate-200 uppercase tracking-wider mb-2">
                      <span>Clipped Reels ({clips.length})</span>
                      <button
                        onClick={onRefreshClips}
                        className="text-[10px] text-cyan-400 font-mono hover:underline"
                      >
                        Refresh
                      </button>
                    </div>

                    <div className="space-y-1.5 max-h-[calc(100vh-320px)] overflow-y-auto pr-1">
                      {clips.map((c) => (
                        <div
                          key={c.id}
                          onClick={() => handleImportClippingCandidate(c)}
                          className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/50 cursor-pointer flex items-center gap-2 transition-all group"
                        >
                          <div className="w-10 h-10 rounded-lg bg-slate-950 overflow-hidden relative shrink-0">
                            {c.thumb_url && (
                              <img src={c.thumb_url} alt={c.title} className="w-full h-full object-cover" />
                            )}
                            <div className="absolute bottom-0.5 right-0.5 px-0.5 rounded bg-black/80 text-[7px] font-mono text-cyan-300">
                              {c.duration}s
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-bold text-slate-200 truncate group-hover:text-cyan-300">
                              {c.title}
                            </div>
                            <div className="text-[9px] text-slate-400 font-mono flex items-center gap-1 mt-0.5">
                              <span>Score: {c.total_score}</span>
                              <span>•</span>
                              <span className="text-cyan-400">+ Add</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Preset Demo Stock Assets Tray */}
                  <div className="pt-2 border-t border-slate-800">
                    <div className="flex items-center justify-between text-xs font-bold text-slate-200 uppercase tracking-wider mb-2">
                      <span>Preset Stock Clips (4)</span>
                      <span className="text-[9px] text-cyan-400 font-mono">Instant Insert</span>
                    </div>

                    <div className="space-y-1.5">
                      {presetStockVideos.map((stk) => (
                        <div
                          key={stk.id}
                          className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/50 flex items-center justify-between gap-2 transition-all group"
                        >
                          <div className="min-w-0">
                            <div className="text-xs font-bold text-slate-200 truncate group-hover:text-cyan-300">
                              {stk.title}
                            </div>
                            <div className="text-[9px] text-slate-400 font-mono mt-0.5">
                              {stk.aspect} • {stk.duration}s • {stk.genre}
                            </div>
                          </div>
                          <button
                            onClick={() => handleAddStockVideo(stk)}
                            className="px-2 py-1 rounded bg-cyan-500/20 hover:bg-cyan-500 border border-cyan-400/40 text-cyan-300 hover:text-slate-950 text-[10px] font-mono cursor-pointer transition-all flex items-center gap-0.5 shrink-0"
                          >
                            <Plus className="w-3 h-3" />
                            <span>Add</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: AUDIO, SFX & VOICEOVER */}
              {activeTab === 'audio' && (
                <div className="space-y-3">
                  {/* Mic Voiceover */}
                  <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center justify-between">
                    <span>Voiceover (Mic)</span>
                    {isRecordingVoiceover && (
                      <span className="text-[9px] text-red-400 font-mono animate-pulse">● LIVE</span>
                    )}
                  </div>
                  <button
                    onClick={handleToggleVoiceover}
                    className={`w-full py-2.5 rounded-xl font-bold font-mono text-xs uppercase flex items-center justify-center gap-1.5 cursor-pointer transition-all ${
                      isRecordingVoiceover
                        ? 'bg-red-600 hover:bg-red-500 text-white animate-pulse'
                        : 'bg-slate-900 border border-cyan-500/40 text-cyan-300 hover:bg-slate-800'
                    }`}
                  >
                    <Mic className="w-4 h-4" />
                    <span>{isRecordingVoiceover ? 'STOP RECORDING' : 'RECORD VOICEOVER'}</span>
                  </button>

                  {/* Viral SFX Synthesizer Catalog */}
                  <div className="pt-2 border-t border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-cyan-300 uppercase tracking-wider">
                        Viral Sound Effects (SFX)
                      </span>
                      <span className="text-[9px] font-mono text-slate-500">CapCut / Meme</span>
                    </div>

                    <div className="space-y-1.5">
                      {viralSFXList.map((sfx) => (
                        <div
                          key={sfx.id}
                          className="p-2 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between gap-2 hover:border-slate-700 transition-all"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="text-base">{sfx.icon}</span>
                            <div className="min-w-0">
                              <div className="text-xs font-bold text-slate-200 truncate">{sfx.title}</div>
                              <div className="text-[9px] text-slate-400 font-mono">{sfx.tag} • {sfx.duration}s</div>
                            </div>
                          </div>
                          <div className="flex items-center gap-1 shrink-0">
                            <button
                              onClick={() => playViralSFX(sfx.id)}
                              className="px-2 py-1 rounded bg-slate-800 hover:bg-cyan-500/20 hover:text-cyan-300 text-slate-300 text-[10px] font-mono cursor-pointer transition-colors"
                              title="Preview sound"
                            >
                              Test
                            </button>
                            <button
                              onClick={() => handleAddSFXToTimeline(sfx)}
                              className="px-2 py-1 rounded bg-cyan-500/20 hover:bg-cyan-500 border border-cyan-400/40 text-cyan-300 hover:text-slate-950 text-[10px] font-mono cursor-pointer transition-all flex items-center gap-0.5"
                              title="Add clip to timeline"
                            >
                              <Plus className="w-3 h-3" />
                              <span>Add</span>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Trending Royalty-Free Audio Beats */}
                  <div className="pt-2 border-t border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-cyan-300 uppercase tracking-wider">
                        Trending Audio Tracks
                      </span>
                      <span className="text-[9px] font-mono text-slate-500">Royalty-Free</span>
                    </div>

                    <div className="space-y-1.5">
                      {trendingAudioBeats.map((beat) => (
                        <div
                          key={beat.id}
                          className="p-2 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between gap-2 hover:border-slate-700 transition-all"
                        >
                          <div className="min-w-0">
                            <div className="text-xs font-bold text-slate-200 truncate">{beat.title}</div>
                            <div className="text-[9px] text-slate-400 font-mono">
                              {beat.bpm} BPM • {beat.genre} • {beat.duration}s
                            </div>
                          </div>
                          <button
                            onClick={() => handleAddMusicBeat(beat)}
                            className="px-2 py-1 rounded bg-cyan-500/20 hover:bg-cyan-500 border border-cyan-400/40 text-cyan-300 hover:text-slate-950 text-[10px] font-mono cursor-pointer transition-all flex items-center gap-0.5 shrink-0"
                          >
                            <Plus className="w-3 h-3" />
                            <span>Add</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Auto Dead Air Trim */}
                  <div className="pt-2 border-t border-slate-800 space-y-2">
                    <button
                      onClick={() => handleExecuteAICommand('remove unnecessary silence')}
                      className="w-full py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-400 text-xs font-mono text-slate-200 flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      <Scissors className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Auto-Trim Dead Air</span>
                    </button>
                  </div>
                </div>
              )}

              {/* TAB 3: VIRAL TEXT & SUBTITLES */}
              {activeTab === 'text' && (
                <div className="space-y-3">
                  <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center justify-between">
                    <span>Viral Text Templates</span>
                    <span className="text-[9px] text-cyan-400 font-mono">1-Click</span>
                  </div>
                  <div className="space-y-1.5">
                    {subtitlePresets.map((sp) => (
                      <button
                        key={sp.id}
                        onClick={() => handleAddTextOverlay(sp.id)}
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-400 flex items-center justify-between text-left cursor-pointer transition-all group"
                      >
                        <div>
                          <div className="text-xs font-bold text-slate-200 group-hover:text-cyan-300">
                            {sp.name}
                          </div>
                          <div className="text-[9px] text-slate-400 font-mono mt-0.5">
                            {sp.font} • Outline {sp.outlineWidth}px
                          </div>
                        </div>
                        <Plus className="w-4 h-4 text-cyan-400 shrink-0" />
                      </button>
                    ))}
                  </div>

                  <div className="pt-2 border-t border-slate-800 space-y-2">
                    <button
                      onClick={() => handleExecuteAICommand('generate viral animated karaoke subtitles')}
                      className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-950/40 via-cyan-900/30 to-slate-900 border border-cyan-500/40 hover:border-cyan-400 text-xs font-mono text-cyan-300 flex items-center justify-center gap-1.5 cursor-pointer shadow-cyan-sm transition-all"
                    >
                      <Wand2 className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Generate AI Subtitles</span>
                    </button>
                  </div>
                </div>
              )}

              {/* TAB 4: VIRAL STICKERS & EMOJIS */}
              {activeTab === 'stickers' && (
                <div className="space-y-3">
                  <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center justify-between">
                    <span>Viral Stickers & Emojis</span>
                    <span className="text-[9px] text-cyan-400 font-mono">Instagram / CapCut</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {viralStickers.map((stk) => (
                      <button
                        key={stk.name}
                        onClick={() => handleAddSticker(stk.emoji, stk.name)}
                        className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-400 hover:bg-slate-800/80 flex flex-col items-center justify-center gap-1 cursor-pointer transition-all group"
                        title={`Add ${stk.name} sticker`}
                      >
                        <span className="text-3xl group-hover:scale-125 transition-transform">{stk.emoji}</span>
                        <span className="text-[10px] font-mono text-slate-300 group-hover:text-cyan-300">{stk.label}</span>
                      </button>
                    ))}
                  </div>

                  {/* Instagram Interactive Stories/Reels Cards */}
                  <div className="pt-2 border-t border-slate-800 space-y-2">
                    <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center justify-between">
                      <span>Instagram Interactive Cards</span>
                      <span className="text-[9px] text-pink-400 font-mono">Reels Viral</span>
                    </div>

                    <div className="space-y-1.5">
                      <button
                        onClick={() => handleAddSticker('📊', 'Instagram Poll', '[POLL] Who was better at their prime?')}
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-pink-500/50 flex items-center justify-between text-left cursor-pointer transition-all group"
                      >
                        <div className="flex items-center gap-2">
                          <BarChart2 className="w-4 h-4 text-pink-400" />
                          <div>
                            <div className="text-xs font-bold text-slate-200 group-hover:text-pink-300">Poll Card (CR7 vs Messi)</div>
                            <div className="text-[9px] text-slate-400 font-mono">Interactive voting card</div>
                          </div>
                        </div>
                        <Plus className="w-3.5 h-3.5 text-pink-400" />
                      </button>

                      <button
                        onClick={() => handleAddSticker('❓', 'Question Box', '[QUESTION] Ask @Ghost_300-m3r anything...')}
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-purple-500/50 flex items-center justify-between text-left cursor-pointer transition-all group"
                      >
                        <div className="flex items-center gap-2">
                          <HelpCircle className="w-4 h-4 text-purple-400" />
                          <div>
                            <div className="text-xs font-bold text-slate-200 group-hover:text-purple-300">Question Box</div>
                            <div className="text-[9px] text-slate-400 font-mono">Ask me anything sticker</div>
                          </div>
                        </div>
                        <Plus className="w-3.5 h-3.5 text-purple-400" />
                      </button>

                      <button
                        onClick={() => handleAddSticker('📍', 'Location Tag', '[LOCATION] Santiago Bernabéu 📍')}
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-red-500/50 flex items-center justify-between text-left cursor-pointer transition-all group"
                      >
                        <div className="flex items-center gap-2">
                          <MapPin className="w-4 h-4 text-red-400" />
                          <div>
                            <div className="text-xs font-bold text-slate-200 group-hover:text-red-300">Location Tag</div>
                            <div className="text-[9px] text-slate-400 font-mono">Stadium / City pill</div>
                          </div>
                        </div>
                        <Plus className="w-3.5 h-3.5 text-red-400" />
                      </button>

                      <button
                        onClick={() => handleAddSticker('@', 'Account Mention', '[MENTION] @Ghost_300-m3r')}
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-amber-500/50 flex items-center justify-between text-left cursor-pointer transition-all group"
                      >
                        <div className="flex items-center gap-2">
                          <AtSign className="w-4 h-4 text-amber-400" />
                          <div>
                            <div className="text-xs font-bold text-slate-200 group-hover:text-amber-300">Account Mention</div>
                            <div className="text-[9px] text-slate-400 font-mono">Instagram rainbow gradient pill</div>
                          </div>
                        </div>
                        <Plus className="w-3.5 h-3.5 text-amber-400" />
                      </button>

                      <button
                        onClick={() => handleAddSticker('⏱️', 'Match Countdown', '[COUNTDOWN] Next Match Kickoff in 01:45:00')}
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 flex items-center justify-between text-left cursor-pointer transition-all group"
                      >
                        <div className="flex items-center gap-2">
                          <Zap className="w-4 h-4 text-cyan-400" />
                          <div>
                            <div className="text-xs font-bold text-slate-200 group-hover:text-cyan-300">Kickoff Countdown</div>
                            <div className="text-[9px] text-slate-400 font-mono">Digital match clock card</div>
                          </div>
                        </div>
                        <Plus className="w-3.5 h-3.5 text-cyan-400" />
                      </button>

                      <button
                        onClick={() => handleAddSticker('🔥', 'Emoji Flame Slider', '[SLIDER] Rate this insane goal! 🔥')}
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-orange-500/50 flex items-center justify-between text-left cursor-pointer transition-all group"
                      >
                        <div className="flex items-center gap-2">
                          <Flame className="w-4 h-4 text-orange-400" />
                          <div>
                            <div className="text-xs font-bold text-slate-200 group-hover:text-orange-300">Viral Hype Slider</div>
                            <div className="text-[9px] text-slate-400 font-mono">Interactive flame score</div>
                          </div>
                        </div>
                        <Plus className="w-3.5 h-3.5 text-orange-400" />
                      </button>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-[10px] font-mono text-slate-400">
                    💡 Click any sticker to add it as an overlay layer at the current playhead. Position & scale it freely in the Inspector.
                  </div>
                </div>
              )}

              {/* TAB 5: INSTAGRAM FILTERS & DAVINCI LUTS */}
              {activeTab === 'effects' && (() => {
                const targetVid = getTargetVideoClip();
                const activePreset = targetVid?.filters.preset_name;
                return (
                  <div className="space-y-3">
                    <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center justify-between">
                      <span>Color Grading & Filters</span>
                      <span className="text-[9px] text-cyan-400 font-mono">Real-time</span>
                    </div>

                    {/* Target Video Badge */}
                    <div className="text-[10px] text-cyan-300 font-mono flex items-center justify-between bg-cyan-950/40 p-2 rounded-xl border border-cyan-500/30">
                      <span className="text-slate-400">Target Clip:</span>
                      <span className="font-bold text-cyan-200 truncate max-w-[140px]">{targetVid?.name || 'No video loaded'}</span>
                    </div>

                    {/* Quick Reset Button */}
                    <button
                      onClick={() => applyColorPreset('reset')}
                      className="w-full py-1.5 px-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-cyan-300 text-[11px] font-mono flex items-center justify-center gap-1 cursor-pointer transition-colors"
                    >
                      <RotateCw className="w-3 h-3 text-cyan-400" />
                      <span>Reset Filters (Clean Normal)</span>
                    </button>

                    <div className="text-[10px] text-slate-400 font-mono uppercase font-bold">
                      Instagram Social Presets
                    </div>
                    <div className="grid grid-cols-2 gap-1.5 text-xs font-mono">
                      <button
                        onClick={() => applyColorPreset('clarendon')}
                        className={`p-2 rounded-xl border text-left cursor-pointer transition-all ${
                          activePreset === 'clarendon'
                            ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 ring-1 ring-cyan-400 font-bold'
                            : 'bg-slate-900 border-slate-800 hover:border-cyan-400 text-slate-200'
                        }`}
                      >
                        <div className="font-bold text-cyan-300">Clarendon</div>
                        <div className="text-[9px] text-slate-400 mt-0.5">Punchy contrast & blues</div>
                      </button>
                      <button
                        onClick={() => applyColorPreset('juno')}
                        className={`p-2 rounded-xl border text-left cursor-pointer transition-all ${
                          activePreset === 'juno'
                            ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 ring-1 ring-cyan-400 font-bold'
                            : 'bg-slate-900 border-slate-800 hover:border-cyan-400 text-slate-200'
                        }`}
                      >
                        <div className="font-bold text-cyan-300">Juno</div>
                        <div className="text-[9px] text-slate-400 mt-0.5">Warm glow highlights</div>
                      </button>
                      <button
                        onClick={() => applyColorPreset('valencia')}
                        className={`p-2 rounded-xl border text-left cursor-pointer transition-all ${
                          activePreset === 'valencia'
                            ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 ring-1 ring-cyan-400 font-bold'
                            : 'bg-slate-900 border-slate-800 hover:border-cyan-400 text-slate-200'
                        }`}
                      >
                        <div className="font-bold text-cyan-300">Valencia</div>
                        <div className="text-[9px] text-slate-400 mt-0.5">Warm vintage fade</div>
                      </button>
                      <button
                        onClick={() => applyColorPreset('retro_vhs')}
                        className={`p-2 rounded-xl border text-left cursor-pointer transition-all ${
                          activePreset === 'retro_vhs'
                            ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 ring-1 ring-cyan-400 font-bold'
                            : 'bg-slate-900 border-slate-800 hover:border-cyan-400 text-slate-200'
                        }`}
                      >
                        <div className="font-bold text-cyan-300">Retro VHS 90s</div>
                        <div className="text-[9px] text-slate-400 mt-0.5">Tape vignette & tint</div>
                      </button>
                    </div>

                    <div className="pt-2 border-t border-slate-800 space-y-2">
                      <div className="text-[10px] text-slate-400 font-mono uppercase font-bold">
                        DaVinci Resolve Cinema Grades
                      </div>
                      <div className="grid grid-cols-2 gap-1.5 text-xs font-mono">
                        <button
                          onClick={() => applyColorPreset('teal_orange')}
                          className={`p-2 rounded-xl border text-left cursor-pointer transition-all ${
                            activePreset === 'teal_orange'
                              ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 ring-1 ring-cyan-400 font-bold'
                              : 'bg-slate-900 border-slate-800 hover:border-cyan-400 text-slate-200'
                          }`}
                        >
                          <div className="font-bold text-cyan-300">Teal & Orange</div>
                          <div className="text-[9px] text-slate-400 mt-0.5">Hollywood Blockbuster</div>
                        </button>
                        <button
                          onClick={() => applyColorPreset('noir')}
                          className={`p-2 rounded-xl border text-left cursor-pointer transition-all ${
                            activePreset === 'noir'
                              ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 ring-1 ring-cyan-400 font-bold'
                              : 'bg-slate-900 border-slate-800 hover:border-cyan-400 text-slate-200'
                          }`}
                        >
                          <div className="font-bold text-cyan-300">Noir B&W</div>
                          <div className="text-[9px] text-slate-400 mt-0.5">Crisp Monochrome</div>
                        </button>
                        <button
                          onClick={() => applyColorPreset('vibrant')}
                          className={`p-2 rounded-xl border text-left cursor-pointer transition-all ${
                            activePreset === 'vibrant'
                              ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 ring-1 ring-cyan-400 font-bold'
                              : 'bg-slate-900 border-slate-800 hover:border-cyan-400 text-slate-200'
                          }`}
                        >
                          <div className="font-bold text-cyan-300">Vibrant Pop</div>
                          <div className="text-[9px] text-slate-400 mt-0.5">+165% Saturation</div>
                        </button>
                        <button
                          onClick={() => applyColorPreset('cyberpunk')}
                          className={`p-2 rounded-xl border text-left cursor-pointer transition-all ${
                            activePreset === 'cyberpunk'
                              ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 ring-1 ring-cyan-400 font-bold'
                              : 'bg-slate-900 border-slate-800 hover:border-cyan-400 text-slate-200'
                          }`}
                        >
                          <div className="font-bold text-cyan-300">Cyberpunk</div>
                          <div className="text-[9px] text-slate-400 mt-0.5">Neon magenta & cyan</div>
                        </button>
                        <button
                          onClick={() => applyColorPreset('color_splash')}
                          className={`col-span-2 p-2 rounded-xl border text-left cursor-pointer transition-all ${
                            activePreset?.includes('Color Splash')
                              ? 'bg-red-950/60 border-red-400 text-red-200 ring-1 ring-red-400 font-bold'
                              : 'bg-gradient-to-r from-red-950/40 via-slate-900 to-slate-900 border border-red-500/40 hover:border-red-400 text-slate-200'
                          }`}
                        >
                          <div className="font-bold text-red-400 flex items-center justify-between">
                            <span>Sin City (Color Splash)</span>
                            <span className="text-[9px] px-1 rounded bg-red-500/20 text-red-300">ISOLATION</span>
                          </div>
                          <div className="text-[9px] text-slate-300 mt-0.5">
                            Character colorful • Entire background black & white
                          </div>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* TAB 6: CAPCUT TRANSITIONS */}
              {activeTab === 'transitions' && (() => {
                const targetVid = getTargetVideoClip();
                const activeTrans = targetVid?.filters.transition || 'none';
                return (
                  <div className="space-y-3">
                    <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center justify-between">
                      <span>CapCut Motion Transitions</span>
                      <span className="text-[9px] text-cyan-400 font-mono">Dynamic</span>
                    </div>

                    {/* Target Video Badge */}
                    <div className="text-[10px] text-cyan-300 font-mono flex items-center justify-between bg-cyan-950/40 p-2 rounded-xl border border-cyan-500/30">
                      <span className="text-slate-400">Target Clip:</span>
                      <span className="font-bold text-cyan-200 truncate max-w-[140px]">{targetVid?.name || 'No video loaded'}</span>
                    </div>

                    <div className="space-y-1.5">
                      {capCutTransitions.map((tr) => (
                        <button
                          key={tr.id}
                          onClick={() => handleApplyTransition(tr.id)}
                          className={`w-full p-2.5 rounded-xl border flex items-center justify-between text-left cursor-pointer transition-all group ${
                            activeTrans === tr.id
                              ? 'bg-cyan-950/50 border-cyan-400 text-cyan-300 ring-1 ring-cyan-400/50 shadow-cyan-sm font-bold'
                              : 'bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-200'
                          }`}
                        >
                          <div className="flex items-center gap-2.5">
                            <span className="text-xl">{tr.icon}</span>
                            <div>
                              <div className="text-xs font-bold group-hover:text-cyan-300 flex items-center gap-1.5">
                                <span>{tr.name}</span>
                                {activeTrans === tr.id && (
                                  <span className="px-1 py-0.2 rounded bg-cyan-400/20 text-cyan-300 text-[8px] font-mono">ACTIVE</span>
                                )}
                              </div>
                              <div className="text-[9px] text-slate-400 font-mono">{tr.desc}</div>
                            </div>
                          </div>
                          <span className="text-[10px] text-cyan-400 font-mono font-bold">
                            {activeTrans === tr.id ? '✓ Live' : 'Apply'}
                          </span>
                        </button>
                      ))}
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-[10px] font-mono text-slate-400">
                      💡 Click any transition to apply it instantly to the video, auto-rewind, and preview the motion live.
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* B. CENTER HERO STAGE (Massive, Adaptive Video Preview Monitor) */}
        <div className="flex-1 flex flex-col bg-slate-950 items-center justify-center p-3 relative overflow-hidden">
          {/* Top Quick Bar: Aspect Ratio Switcher (Reels 9:16 / YouTube 16:9 / 1:1 / 4:5), Safe Guides, Speed Ramp */}
          <div className="mb-2 flex items-center gap-2 bg-slate-900/90 px-3 py-1.5 rounded-2xl border border-slate-800 text-xs font-mono shadow-xl backdrop-blur-sm z-10">
            {/* Aspect Ratio Switcher */}
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
              <button
                onClick={() => handleSetAspectRatio('9:16')}
                className={`px-2 py-0.5 rounded-lg flex items-center gap-1 text-[11px] font-bold transition-all ${
                  currentProject?.aspect_ratio === '9:16'
                    ? 'bg-cyan-500 text-slate-950 shadow-cyan-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="9:16 Instagram Reels / YouTube Shorts / TikTok"
              >
                <Smartphone className="w-3 h-3" />
                <span>9:16</span>
              </button>
              <button
                onClick={() => handleSetAspectRatio('16:9')}
                className={`px-2 py-0.5 rounded-lg flex items-center gap-1 text-[11px] font-bold transition-all ${
                  currentProject?.aspect_ratio === '16:9'
                    ? 'bg-cyan-500 text-slate-950 shadow-cyan-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="16:9 YouTube Landscape"
              >
                <Monitor className="w-3 h-3" />
                <span>16:9</span>
              </button>
              <button
                onClick={() => handleSetAspectRatio('1:1')}
                className={`px-2 py-0.5 rounded-lg flex items-center gap-1 text-[11px] font-bold transition-all ${
                  currentProject?.aspect_ratio === '1:1'
                    ? 'bg-cyan-500 text-slate-950 shadow-cyan-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="1:1 Instagram Square Post"
              >
                <Square className="w-3 h-3" />
                <span>1:1</span>
              </button>
              <button
                onClick={() => handleSetAspectRatio('4:5')}
                className={`px-2 py-0.5 rounded-lg flex items-center gap-1 text-[11px] font-bold transition-all ${
                  currentProject?.aspect_ratio === '4:5'
                    ? 'bg-cyan-500 text-slate-950 shadow-cyan-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="4:5 Instagram Portrait Feed (1080x1350)"
              >
                <Smartphone className="w-3 h-3" />
                <span>4:5</span>
              </button>
            </div>

            <div className="h-4 w-px bg-slate-800" />

            {/* Quick Speed Ramping Preset Pills */}
            <div className="flex items-center gap-1 text-[10px]">
              <span className="text-slate-500 hidden sm:inline">Speed:</span>
              {[0.25, 0.5, 1.0, 1.5, 2.0, 4.0].map((spd) => (
                <button
                  key={spd}
                  onClick={() => {
                    if (selectedClip && currentProject) {
                      const updated = currentProject.clips.map((c) =>
                        c.id === selectedClip.id ? { ...c, speed: spd } : c
                      );
                      saveProjectState({ ...currentProject, clips: updated });
                    }
                  }}
                  className={`px-1.5 py-0.5 rounded transition-all ${
                    selectedClip?.speed === spd
                      ? 'bg-cyan-500/20 border border-cyan-400 text-cyan-300 font-bold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                  title={`Set selected clip to ${spd}x speed`}
                >
                  {spd}x
                </button>
              ))}
            </div>

            <div className="h-4 w-px bg-slate-800" />

            {/* CapCut Canvas Background Selector */}
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-[10px]">
              <span className="text-slate-500 pl-1">BG:</span>
              {(['blur', 'black', 'neon'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setCanvasBgMode(mode)}
                  className={`px-1.5 py-0.5 rounded capitalize transition-all ${
                    canvasBgMode === mode
                      ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-400/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  title={`Canvas background mode: ${mode}`}
                >
                  {mode === 'blur' ? 'Blur Mirror' : mode}
                </button>
              ))}
            </div>

            <div className="h-4 w-px bg-slate-800" />

            {/* Magnet Snapping Toggle */}
            <button
              onClick={() => setSnappingEnabled(!snappingEnabled)}
              className={`px-2 py-0.5 rounded-lg flex items-center gap-1 cursor-pointer transition-all ${
                snappingEnabled
                  ? 'bg-cyan-500/20 border border-cyan-400 text-cyan-300 font-bold'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
              title="Toggle Timeline Magnetic Snapping (N)"
            >
              <Magnet className="w-3 h-3" />
              <span>Snap</span>
            </button>

            <div className="h-4 w-px bg-slate-800" />

            {/* Quick Blade Split */}
            <button
              onClick={handleSplitClipAtPlayhead}
              className="px-2 py-0.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-cyan-300 flex items-center gap-1 cursor-pointer transition-colors"
              title="Split clip at playhead (S)"
            >
              <Scissors className="w-3 h-3 text-cyan-400" />
              <span>Split (S)</span>
            </button>
          </div>

          {/* Aspect Ratio Viewport Container (Auto-scales to full height) */}
          <div
            ref={previewContainerRef}
            className={`relative rounded-2xl overflow-hidden bg-black shadow-2xl border border-cyan-500/30 flex items-center justify-center transition-all select-none ${
              currentProject?.aspect_ratio === '9:16'
                ? 'h-full max-h-[calc(100vh-360px)] min-h-[360px] aspect-[9/16] max-w-[440px]'
                : currentProject?.aspect_ratio === '1:1'
                ? 'h-full max-h-[calc(100vh-360px)] min-h-[360px] aspect-square'
                : currentProject?.aspect_ratio === '4:5'
                ? 'h-full max-h-[calc(100vh-360px)] min-h-[360px] aspect-[4/5] max-w-[460px]'
                : 'w-full max-w-[920px] max-h-[calc(100vh-360px)] aspect-video'
            }`}
          >
            {/* Magnetic Center Alignment Visual Snapping Guides */}
            {snapGuideX && (
              <div className="absolute inset-y-0 left-1/2 w-0.5 -ml-px bg-cyan-400 z-40 pointer-events-none shadow-[0_0_8px_rgba(34,211,238,0.85)] animate-pulse" />
            )}
            {snapGuideY && (
              <div className="absolute inset-x-0 top-1/2 h-0.5 -mt-px bg-cyan-400 z-40 pointer-events-none shadow-[0_0_8px_rgba(34,211,238,0.85)] animate-pulse" />
            )}
            {/* CapCut Canvas Background Fill (Mirror Blur / OLED / Neon) */}
            {activeVideoClip?.source_url && canvasBgMode === 'blur' && (
              <video
                src={activeVideoClip.source_url}
                playsInline
                muted
                className="absolute inset-0 w-full h-full object-cover filter blur-3xl scale-125 opacity-55 pointer-events-none"
              />
            )}
            {canvasBgMode === 'neon' && (
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-950/60 via-slate-950 to-purple-950/60 pointer-events-none" />
            )}

            {/* Active Video Player with Real-time CSS Filters, Transitions and Transforms */}
            {activeVideoClip?.source_url ? (() => {
              const f = activeVideoClip.filters;
              const isColorSplash = !!f.color_splash;

              // Transition Dynamics (0 to 0.55s from start of clip)
              const transTime = currentTime - activeVideoClip.start_time;
              const transDur = 0.55;
              const hasTrans = !!f.transition && f.transition !== 'none';
              const isTransActive = hasTrans && transTime >= 0 && transTime <= transDur;
              const transProgress = isTransActive ? Math.min(1.0, Math.max(0.0, transTime / transDur)) : 1.0;
              const remaining = 1.0 - transProgress;

              let transScale = 1.0;
              let transTranslateX = 0;
              if (isTransActive) {
                if (f.transition === 'zoom_in') {
                  transScale = 1.0 + remaining * 0.55;
                } else if (f.transition === 'zoom_out') {
                  transScale = 1.0 - remaining * 0.35;
                } else if (f.transition === 'glitch') {
                  const jitter = Math.sin(transTime * 80) * remaining;
                  transTranslateX = jitter * 16;
                }
              }

              // Color Filters with high-precision nullish checks
              const baseContrast = isColorSplash ? 1.25 : ((f.contrast ?? 1.0) * (f.gamma ?? 1.0));
              const baseBrightness = 1 + (f.brightness ?? 0) + (f.lift ?? 0);
              const baseSaturation = isColorSplash ? 1.75 : ((f.saturation ?? 1.0) * (f.gain ?? 1.0));
              const blurPx = (f.blur ?? 0) + (isTransActive && f.transition === 'zoom_in' ? remaining * 3 : 0);

              const tempVal = f.temperature ?? 0;
              const tintVal = f.tint ?? 0;
              let colorShift = '';
              if (tempVal > 0) {
                colorShift += ` sepia(${Math.min(0.7, tempVal / 60)}) hue-rotate(-10deg)`;
              } else if (tempVal < 0) {
                colorShift += ` hue-rotate(${tempVal * 1.2}deg)`;
              }
              if (tintVal !== 0) {
                colorShift += ` hue-rotate(${tintVal * 1.5}deg)`;
              }

              let glitchFilter = '';
              if (isTransActive && f.transition === 'glitch') {
                const gDisplace = (Math.sin(transTime * 70) * remaining * 8).toFixed(1);
                glitchFilter = ` drop-shadow(${gDisplace}px 0 #00ffff) drop-shadow(-${gDisplace}px 0 #ff007f)`;
              }

              return (
                <>
                  <video
                    ref={videoRef}
                    key={activeVideoClip.id}
                    src={activeVideoClip.source_url}
                    playsInline
                    muted={false}
                    className="w-full h-full object-contain pointer-events-none transition-transform relative z-10"
                    style={{
                      filter: `
                        contrast(${baseContrast.toFixed(2)})
                        brightness(${baseBrightness.toFixed(2)})
                        saturate(${baseSaturation.toFixed(2)})
                        ${blurPx > 0 ? `blur(${blurPx.toFixed(1)}px)` : ''}
                        ${colorShift}
                        ${glitchFilter}
                      `,
                      transform: `
                        scale(${(activeVideoClip.transform.scale_x ?? 1.0) * transScale}, ${(activeVideoClip.transform.scale_y ?? 1.0) * transScale})
                        translate(${transTranslateX}px, 0px)
                        rotate(${activeVideoClip.transform.rotation ?? 0}deg)
                        ${activeVideoClip.transform.flip_h ? 'scaleX(-1)' : ''}
                        ${activeVideoClip.transform.flip_v ? 'scaleY(-1)' : ''}
                      `,
                      opacity: activeVideoClip.transform.opacity ?? 1.0,
                    }}
                  />

                  {/* Real-time Cinematic Vignette Overlay */}
                  {(f?.vignette || 0) > 0 && (
                    <div
                      className="absolute inset-0 pointer-events-none z-10 transition-opacity"
                      style={{
                        background: `radial-gradient(circle at center, transparent 40%, rgba(0,0,0,${((f.vignette || 0) * 0.95).toFixed(2)}) 100%)`,
                      }}
                    />
                  )}

                  {/* Transition: White Flash */}
                  {isTransActive && f.transition === 'flash_white' && (
                    <div
                      className="absolute inset-0 bg-white pointer-events-none z-30 transition-opacity"
                      style={{ opacity: Math.pow(remaining, 1.4) }}
                    />
                  )}

                  {/* Transition: Cross Dissolve */}
                  {isTransActive && f.transition === 'cross_dissolve' && (
                    <div
                      className="absolute inset-0 bg-black pointer-events-none z-25 transition-opacity"
                      style={{ opacity: remaining }}
                    />
                  )}

                  {/* Transition: Cyber Glitch Overlays */}
                  {isTransActive && f.transition === 'glitch' && (
                    <div
                      className="absolute inset-0 pointer-events-none z-25 mix-blend-screen"
                      style={{
                        opacity: remaining,
                        background: 'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0, 255, 255, 0.25) 4px, transparent 6px)',
                      }}
                    >
                      <div className="absolute inset-0 bg-purple-500/20 mix-blend-color-dodge animate-pulse" />
                    </div>
                  )}

                  {/* Transition: Wipe Left */}
                  {isTransActive && f.transition === 'wipe_left' && (
                    <>
                      <div
                        className="absolute inset-y-0 w-1 bg-cyan-400 z-30 pointer-events-none shadow-[0_0_12px_rgba(34,211,238,0.9)]"
                        style={{ left: `${transProgress * 100}%` }}
                      />
                      <div
                        className="absolute inset-y-0 right-0 bg-black z-25 pointer-events-none"
                        style={{ width: `${remaining * 100}%` }}
                      />
                    </>
                  )}

                  {/* Active Transition Real-time On-Screen Indicator */}
                  {isTransActive && f.transition && (
                    <div className="absolute top-3 right-3 z-40 px-2 py-0.5 rounded-lg bg-black/85 border border-cyan-400/80 text-cyan-300 font-mono font-bold text-[9px] flex items-center gap-1 shadow-lg backdrop-blur-sm animate-pulse">
                      <Zap className="w-2.5 h-2.5 text-cyan-400" />
                      <span>TRANSITION: {f.transition.replace('_', ' ').toUpperCase()}</span>
                      <span>({Math.round(transProgress * 100)}%)</span>
                    </div>
                  )}

                  {/* Real-time Color Splash Subject Isolation Overlay */}
                  {f?.color_splash && (
                    <>
                      <div
                        className="absolute inset-0 pointer-events-none z-10"
                        style={{
                          backdropFilter: 'grayscale(100%) contrast(1.3) brightness(0.95)',
                          WebkitBackdropFilter: 'grayscale(100%) contrast(1.3) brightness(0.95)',
                          maskImage: `radial-gradient(ellipse ${((f.color_splash_radius || 0.32) * 100).toFixed(0)}% ${((f.color_splash_radius || 0.32) * 115).toFixed(0)}% at ${((f.color_splash_x ?? 0.56) * 100).toFixed(0)}% ${((f.color_splash_y ?? 0.58) * 100).toFixed(0)}%, transparent 20%, rgba(0,0,0,0.4) 40%, rgba(0,0,0,0.85) 65%, black 85%)`,
                          WebkitMaskImage: `radial-gradient(ellipse ${((f.color_splash_radius || 0.32) * 100).toFixed(0)}% ${((f.color_splash_radius || 0.32) * 115).toFixed(0)}% at ${((f.color_splash_x ?? 0.56) * 100).toFixed(0)}% ${((f.color_splash_y ?? 0.58) * 100).toFixed(0)}%, transparent 20%, rgba(0,0,0,0.4) 40%, rgba(0,0,0,0.85) 65%, black 85%)`,
                        }}
                      />

                      <div
                        className="absolute pointer-events-none z-10 border border-red-500/35 rounded-full animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.2)]"
                        style={{
                          left: `${((f.color_splash_x ?? 0.56) * 100 - (f.color_splash_radius || 0.32) * 100).toFixed(1)}%`,
                          top: `${((f.color_splash_y ?? 0.58) * 100 - (f.color_splash_radius || 0.32) * 115).toFixed(1)}%`,
                          width: `${((f.color_splash_radius || 0.32) * 200).toFixed(1)}%`,
                          height: `${((f.color_splash_radius || 0.32) * 230).toFixed(1)}%`,
                        }}
                      />

                      <div className="absolute top-3 left-3 z-20 px-2 py-0.5 rounded-lg bg-black/85 border border-red-500/70 text-red-300 font-mono font-bold text-[9px] flex items-center gap-1 shadow-lg backdrop-blur-sm">
                        <Sparkles className="w-2.5 h-2.5 text-red-400 animate-pulse" />
                        <span>COLOR SPLASH: CHARACTER COLORFUL • REST B&W</span>
                      </div>
                    </>
                  )}
                </>
              );
            })() : (
              <div className="flex flex-col items-center justify-center text-slate-500 font-mono text-xs gap-3 p-4 text-center">
                <Film className="w-10 h-10 opacity-40 text-cyan-400" />
                <div>
                  <span className="text-slate-200 block font-bold text-sm">
                    No media at playhead {formatTimecode(currentTime)}
                  </span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    Timeline playhead is on empty space
                  </span>
                </div>

                {/* Helpful jump buttons to clip */}
                {currentProject?.clips.some((c) => c.source_type === 'video' && c.source_url) && (
                  <div className="flex flex-wrap items-center justify-center gap-2 mt-1">
                    {selectedClip?.source_url && (
                      <button
                        onClick={() => setCurrentTime(selectedClip.start_time)}
                        className="px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400 text-cyan-300 text-xs font-mono cursor-pointer transition-all"
                      >
                        Jump to Selected ({formatTimecode(selectedClip.start_time)})
                      </button>
                    )}
                    {(() => {
                      const firstVideo = currentProject.clips.find(
                        (c) => c.source_type === 'video' && c.source_url
                      );
                      if (firstVideo && firstVideo.id !== selectedClip?.id) {
                        return (
                          <button
                            onClick={() => setCurrentTime(firstVideo.start_time)}
                            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 text-xs font-mono cursor-pointer transition-all"
                          >
                            Jump to '{firstVideo.name.slice(0, 18)}' ({formatTimecode(firstVideo.start_time)})
                          </button>
                        );
                      }
                      return null;
                    })()}
                  </div>
                )}
              </div>
            )}

            {/* Safe-Area Guides Overlay (Instagram Reels / TikTok 9:16 & 4:5) */}
            {showSafeGuides && (currentProject?.aspect_ratio === '9:16' || currentProject?.aspect_ratio === '4:5') && (
              <div className="absolute inset-0 pointer-events-none border border-dashed border-cyan-400/50 m-6 flex flex-col justify-between p-2 z-20">
                <div className="text-[9px] font-mono text-cyan-400/90 bg-slate-950/80 px-1.5 py-0.5 rounded self-start backdrop-blur-sm">
                  Header Safe Zone (Username & Audio Title)
                </div>
                <div className="text-[9px] font-mono text-cyan-400/90 bg-slate-950/80 px-1.5 py-0.5 rounded self-end backdrop-blur-sm">
                  Side Buttons (Like, Share, Comment)
                </div>
                <div className="text-[9px] font-mono text-cyan-400/90 bg-slate-950/80 px-1.5 py-0.5 rounded self-start backdrop-blur-sm">
                  Caption & Description Safe Zone
                </div>
              </div>
            )}

            {/* Real-time Subtitle, Text & Sticker Overlay Preview */}
            {activeTextClips && activeTextClips.length > 0 && (
              <div className="absolute inset-0 pointer-events-none z-30">
                {activeTextClips.map((tc) => {
                  const tp = tc.text_props;
                  const isSticker = tc.source_type === 'sticker';
                  const isSel = selectedClipId === tc.id;
                  return (
                    <div
                      key={tc.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedClipId(tc.id);
                      }}
                      onMouseDown={(e) => handleStartCanvasItemDrag(e, tc.id, 'move')}
                      onTouchStart={(e) => handleStartCanvasItemDrag(e, tc.id, 'move')}
                      className={`absolute pointer-events-auto select-none transition-shadow ${
                        isSel
                          ? 'ring-2 ring-cyan-400 ring-offset-2 ring-offset-black/60 rounded-xl cursor-grab active:cursor-grabbing shadow-[0_0_20px_rgba(34,211,238,0.5)]'
                          : 'hover:ring-1 hover:ring-cyan-400/50 cursor-pointer'
                      }`}
                      style={{
                        left: `${50 + ((tc.transform.position_x || 0) * 50)}%`,
                        top: `${50 + ((tc.transform.position_y || 0) * 50)}%`,
                        transform: `translate(-50%, -50%) rotate(${tc.transform.rotation || 0}deg) scale(${tc.transform.scale_x || 1.0}, ${tc.transform.scale_y || 1.0})`,
                        opacity: tc.transform.opacity ?? 1.0,
                      }}
                    >
                      {/* Direct Bounding Box Controls & Floating Position HUD when Selected */}
                      {isSel && (
                        <>
                          {/* Floating Quick Position & Adjustment HUD on the element */}
                          <div
                            className={`absolute left-1/2 -translate-x-1/2 flex items-center gap-1.5 bg-slate-950/95 border border-cyan-400/80 shadow-[0_10px_25px_rgba(0,0,0,0.85)] rounded-xl p-1 z-50 backdrop-blur-md whitespace-nowrap select-none pointer-events-auto ${
                              (tc.transform.position_y || 0) < -0.3 ? '-bottom-12' : '-top-12'
                            }`}
                            onClick={(e) => e.stopPropagation()}
                            onMouseDown={(e) => e.stopPropagation()}
                          >
                            {/* 4-Way D-Pad Arrows */}
                            <div className="flex items-center gap-0.5 bg-slate-900/90 rounded-lg p-0.5 border border-slate-800">
                              <button
                                onClick={() => handleNudgePosition(tc.id, -0.05, 0)}
                                className="p-1 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer transition-colors"
                                title="Nudge Left 5% (ArrowLeft)"
                              >
                                <ArrowLeft className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => handleNudgePosition(tc.id, 0, -0.05)}
                                className="p-1 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer transition-colors"
                                title="Nudge Up 5% (ArrowUp)"
                              >
                                <ArrowUp className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => handleNudgePosition(tc.id, 0, 0.05)}
                                className="p-1 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer transition-colors"
                                title="Nudge Down 5% (ArrowDown)"
                              >
                                <ArrowDown className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => handleNudgePosition(tc.id, 0.05, 0)}
                                className="p-1 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer transition-colors"
                                title="Nudge Right 5% (ArrowRight)"
                              >
                                <ArrowRight className="w-3.5 h-3.5" />
                              </button>
                            </div>

                            <div className="h-4 w-px bg-slate-800" />

                            {/* Quick Position Snap Pills: Center, Top, Bottom */}
                            <div className="flex items-center gap-0.5 bg-slate-900/90 rounded-lg p-0.5 border border-slate-800">
                              <button
                                onClick={() => handleSetPosition(tc.id, 0, 0)}
                                className="px-1.5 py-0.5 text-[9px] font-mono rounded hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 cursor-pointer"
                                title="Center on screen (0, 0)"
                              >
                                Center
                              </button>
                              <button
                                onClick={() => handleSetPosition(tc.id, 0, -0.65)}
                                className="px-1.5 py-0.5 text-[9px] font-mono rounded hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 cursor-pointer"
                                title="Snap to Top Header"
                              >
                                Top
                              </button>
                              <button
                                onClick={() => handleSetPosition(tc.id, 0, 0.55)}
                                className="px-1.5 py-0.5 text-[9px] font-mono rounded hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 cursor-pointer"
                                title="Snap to Bottom Subtitle"
                              >
                                Bottom
                              </button>
                            </div>

                            <div className="h-4 w-px bg-slate-800" />

                            {/* Scale - / + */}
                            <div className="flex items-center gap-0.5 bg-slate-900/90 rounded-lg p-0.5 border border-slate-800">
                              <button
                                onClick={() => handleNudgeScale(tc.id, -0.15)}
                                className="px-1.5 py-0.5 text-[10px] font-bold hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer"
                                title="Scale Smaller (-15%)"
                              >
                                −
                              </button>
                              <button
                                onClick={() => handleNudgeScale(tc.id, 0.15)}
                                className="px-1.5 py-0.5 text-[10px] font-bold hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer"
                                title="Scale Bigger (+15%)"
                              >
                                +
                              </button>
                            </div>

                            <div className="h-4 w-px bg-slate-800" />

                            {/* Delete */}
                            <button
                              onClick={() => handleDeleteClipById(tc.id)}
                              className="p-1 hover:bg-red-500/20 text-slate-400 hover:text-red-400 rounded cursor-pointer transition-colors"
                              title="Delete item (Del)"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>

                          {/* Corner Scale Handle: Top-Left */}
                          <div
                            onMouseDown={(e) => handleStartCanvasItemDrag(e, tc.id, 'scale')}
                            onTouchStart={(e) => handleStartCanvasItemDrag(e, tc.id, 'scale')}
                            className="absolute -top-2 -left-2 w-3.5 h-3.5 bg-cyan-400 hover:bg-white border-2 border-slate-950 rounded-full cursor-nwse-resize z-40 shadow-lg"
                            title="Drag to scale"
                          />
                          {/* Corner Scale Handle: Top-Right */}
                          <div
                            onMouseDown={(e) => handleStartCanvasItemDrag(e, tc.id, 'scale')}
                            onTouchStart={(e) => handleStartCanvasItemDrag(e, tc.id, 'scale')}
                            className="absolute -top-2 -right-2 w-3.5 h-3.5 bg-cyan-400 hover:bg-white border-2 border-slate-950 rounded-full cursor-nesw-resize z-40 shadow-lg"
                            title="Drag to scale"
                          />
                          {/* Corner Scale Handle: Bottom-Left */}
                          <div
                            onMouseDown={(e) => handleStartCanvasItemDrag(e, tc.id, 'scale')}
                            onTouchStart={(e) => handleStartCanvasItemDrag(e, tc.id, 'scale')}
                            className="absolute -bottom-2 -left-2 w-3.5 h-3.5 bg-cyan-400 hover:bg-white border-2 border-slate-950 rounded-full cursor-nesw-resize z-40 shadow-lg"
                            title="Drag to scale"
                          />
                          {/* Corner Scale Handle: Bottom-Right */}
                          <div
                            onMouseDown={(e) => handleStartCanvasItemDrag(e, tc.id, 'scale')}
                            onTouchStart={(e) => handleStartCanvasItemDrag(e, tc.id, 'scale')}
                            className="absolute -bottom-2 -right-2 w-3.5 h-3.5 bg-cyan-400 hover:bg-white border-2 border-slate-950 rounded-full cursor-nwse-resize z-40 shadow-lg"
                            title="Drag to scale"
                          />
                          {/* Top Rotation Stem & Handle */}
                          <div className="absolute -top-7 left-1/2 -translate-x-1/2 flex flex-col items-center pointer-events-auto">
                            <div
                              onMouseDown={(e) => handleStartCanvasItemDrag(e, tc.id, 'rotate')}
                              onTouchStart={(e) => handleStartCanvasItemDrag(e, tc.id, 'rotate')}
                              className="w-4 h-4 bg-cyan-400 hover:bg-white border-2 border-slate-950 rounded-full cursor-grab active:cursor-grabbing shadow-lg flex items-center justify-center text-[8px] text-slate-950 font-bold"
                              title="Drag to rotate"
                            >
                              ↻
                            </div>
                            <div className="w-0.5 h-3 bg-cyan-400" />
                          </div>
                          {/* Real-time Position & Action Overlay Badge */}
                          <div className="absolute -bottom-7 left-1/2 -translate-x-1/2 bg-slate-950/95 text-cyan-300 border border-cyan-400/40 px-2 py-0.5 rounded-full text-[8px] font-mono whitespace-nowrap shadow-xl flex items-center gap-1.5 pointer-events-none z-40">
                            <span>X: {Math.round((tc.transform.position_x || 0) * 100)}%</span>
                            <span>•</span>
                            <span>Y: {Math.round((tc.transform.position_y || 0) * 100)}%</span>
                          </div>
                        </>
                      )}
                      {isSticker && tp?.text?.startsWith('[POLL]') ? (
                        <div className="bg-slate-900/90 backdrop-blur-md border border-white/20 rounded-2xl p-3 shadow-2xl min-w-[210px] text-center">
                          <div className="text-xs font-bold text-white mb-2">{tp.text.replace('[POLL]', '').trim()}</div>
                          <div className="space-y-1.5">
                            <div className="relative overflow-hidden rounded-xl bg-slate-800 p-2 text-[11px] font-bold text-white flex justify-between">
                              <div className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-500 to-blue-500 opacity-60 w-[58%]" />
                              <span className="relative z-10">⚽ CR7</span>
                              <span className="relative z-10 font-mono">58%</span>
                            </div>
                            <div className="relative overflow-hidden rounded-xl bg-slate-800 p-2 text-[11px] font-bold text-white flex justify-between">
                              <div className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-500 to-pink-500 opacity-60 w-[42%]" />
                              <span className="relative z-10">🐐 Messi</span>
                              <span className="relative z-10 font-mono">42%</span>
                            </div>
                          </div>
                        </div>
                      ) : isSticker && tp?.text?.startsWith('[QUESTION]') ? (
                        <div className="bg-white rounded-2xl p-3 shadow-2xl min-w-[200px] text-center text-slate-900">
                          <div className="bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-xl py-1 px-2 text-[11px] font-bold mb-2">
                            Ask me a question
                          </div>
                          <div className="text-xs font-medium text-slate-600 bg-slate-100 rounded-lg p-2">
                            {tp.text.replace('[QUESTION]', '').trim() || 'Type question here...'}
                          </div>
                        </div>
                      ) : isSticker && tp?.text?.startsWith('[LOCATION]') ? (
                        <div className="bg-black/75 backdrop-blur-md border border-white/20 text-white px-3 py-1.5 rounded-full shadow-xl flex items-center gap-1.5 text-xs font-bold">
                          <MapPin className="w-3.5 h-3.5 text-red-500 fill-current" />
                          <span>{tp.text.replace('[LOCATION]', '').trim()}</span>
                        </div>
                      ) : isSticker && tp?.text?.startsWith('[MENTION]') ? (
                        <div className="bg-gradient-to-r from-purple-600 via-pink-500 to-amber-500 text-white px-3 py-1 rounded-full shadow-xl flex items-center gap-1 text-xs font-bold">
                          <AtSign className="w-3.5 h-3.5" />
                          <span>{tp.text.replace('[MENTION]', '').trim()}</span>
                        </div>
                      ) : isSticker && tp?.text?.startsWith('[COUNTDOWN]') ? (
                        <div className="bg-slate-900/90 backdrop-blur-md border border-cyan-400/40 rounded-2xl p-3 shadow-2xl text-center min-w-[190px]">
                          <div className="text-[10px] text-cyan-300 font-bold uppercase tracking-wider mb-1">
                            {tp.text.replace('[COUNTDOWN]', '').trim() || 'Kickoff Countdown'}
                          </div>
                          <div className="flex items-center justify-center gap-1.5 font-mono text-lg font-bold text-white">
                            <span className="bg-slate-800 px-1.5 py-0.5 rounded">01</span>:
                            <span className="bg-slate-800 px-1.5 py-0.5 rounded">45</span>:
                            <span className="bg-slate-800 px-1.5 py-0.5 rounded text-cyan-400">00</span>
                          </div>
                        </div>
                      ) : isSticker && tp?.text?.startsWith('[SLIDER]') ? (
                        <div className="bg-slate-900/90 backdrop-blur-md border border-white/20 rounded-2xl p-2.5 shadow-2xl text-center min-w-[190px]">
                          <div className="text-[10px] text-white font-bold mb-1.5">{tp.text.replace('[SLIDER]', '').trim()}</div>
                          <div className="relative flex items-center justify-center">
                            <div className="w-full h-2 bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 rounded-full" />
                            <div className="absolute text-xl -top-3 left-[75%] filter drop-shadow">🔥</div>
                          </div>
                        </div>
                      ) : isSticker ? (
                        <div
                          className={`text-5xl drop-shadow-[0_4px_12px_rgba(0,0,0,0.85)] filter ${
                            tp?.animation === 'bounce'
                              ? 'animate-bounce'
                              : tp?.animation === 'pulse'
                              ? 'animate-pulse'
                              : ''
                          }`}
                        >
                          {tp?.sticker_emoji || tp?.text || '🔥'}
                        </div>
                      ) : (
                        <div
                          className="font-bold uppercase tracking-wide drop-shadow-2xl px-3 py-1.5 rounded-lg whitespace-pre-wrap text-center"
                          style={{
                            fontFamily: tp?.font || 'Impact',
                            fontSize: `${(tp?.font_size || 56) * 0.42}px`,
                            color: tp?.color || '#FFFFFF',
                            backgroundColor: tp?.bg_color || 'transparent',
                            textShadow: (tp?.outline_width || 0) > 0
                              ? `-2px -2px 0 ${tp?.outline_color || '#000'}, 2px -2px 0 ${tp?.outline_color || '#000'}, -2px 2px 0 ${tp?.outline_color || '#000'}, 2px 2px 0 ${tp?.outline_color || '#000'}`
                              : '0 2px 8px rgba(0,0,0,0.9)',
                          }}
                        >
                          {tp?.text || tc.name}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Dedicated On-Screen Position Adjustment Dock for Selected Emoji/Text */}
          {selectedClip && (selectedClip.source_type === 'sticker' || selectedClip.source_type === 'text' || selectedClip.source_type === 'subtitle') && (
            <div className="mt-2 flex flex-wrap items-center justify-between gap-2 bg-slate-950/95 border border-cyan-500/50 px-3 py-1.5 rounded-2xl text-xs font-mono shadow-[0_0_20px_rgba(34,211,238,0.2)] backdrop-blur-md shrink-0">
              <div className="flex items-center gap-1.5 text-cyan-300 font-bold">
                <Move className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                <span>Adjust {selectedClip.source_type === 'sticker' ? 'Emoji' : 'Text'} Position:</span>
              </div>

              {/* Directional Nudge Arrows */}
              <div className="flex items-center gap-1 bg-slate-900 px-1.5 py-0.5 rounded-lg border border-slate-800">
                <button
                  onClick={() => handleNudgePosition(selectedClip.id, -0.05, 0)}
                  className="p-1 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer transition-colors"
                  title="Move Left 5% (ArrowLeft)"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => handleNudgePosition(selectedClip.id, 0, -0.05)}
                  className="p-1 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer transition-colors"
                  title="Move Up 5% (ArrowUp)"
                >
                  <ArrowUp className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => handleNudgePosition(selectedClip.id, 0, 0.05)}
                  className="p-1 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer transition-colors"
                  title="Move Down 5% (ArrowDown)"
                >
                  <ArrowDown className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => handleNudgePosition(selectedClip.id, 0.05, 0)}
                  className="p-1 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer transition-colors"
                  title="Move Right 5% (ArrowRight)"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Quick Presets */}
              <div className="flex items-center gap-1">
                <button
                  onClick={() => handleSetPosition(selectedClip.id, 0, -0.65)}
                  className="px-2 py-0.5 rounded bg-slate-900 hover:bg-cyan-500/20 border border-slate-800 hover:border-cyan-400 text-[10px] text-slate-300 hover:text-cyan-300 cursor-pointer"
                  title="Snap to Top Header"
                >
                  Top
                </button>
                <button
                  onClick={() => handleSetPosition(selectedClip.id, 0, 0)}
                  className="px-2 py-0.5 rounded bg-slate-900 hover:bg-cyan-500/20 border border-slate-800 hover:border-cyan-400 text-[10px] text-slate-300 hover:text-cyan-300 cursor-pointer"
                  title="Snap to Dead Center"
                >
                  Center
                </button>
                <button
                  onClick={() => handleSetPosition(selectedClip.id, 0, 0.55)}
                  className="px-2 py-0.5 rounded bg-slate-900 hover:bg-cyan-500/20 border border-slate-800 hover:border-cyan-400 text-[10px] text-slate-300 hover:text-cyan-300 cursor-pointer"
                  title="Snap to Bottom Subtitles"
                >
                  Bottom
                </button>
              </div>

              {/* Scale Nudge */}
              <div className="flex items-center gap-1 bg-slate-900 px-1.5 py-0.5 rounded-lg border border-slate-800">
                <button
                  onClick={() => handleNudgeScale(selectedClip.id, -0.15)}
                  className="px-1.5 py-0.5 text-[11px] font-bold hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer"
                  title="Scale Smaller (-15%)"
                >
                  −
                </button>
                <span className="text-[10px] text-cyan-400 font-mono">{(selectedClip.transform.scale_x || 1.0).toFixed(1)}x</span>
                <button
                  onClick={() => handleNudgeScale(selectedClip.id, 0.15)}
                  className="px-1.5 py-0.5 text-[11px] font-bold hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 rounded cursor-pointer"
                  title="Scale Bigger (+15%)"
                >
                  +
                </button>
              </div>

              {/* Live Coordinates */}
              <div className="text-[10px] text-slate-400 font-mono">
                X: <span className="text-cyan-400 font-bold">{Math.round((selectedClip.transform.position_x || 0) * 100)}%</span> • Y: <span className="text-cyan-400 font-bold">{Math.round((selectedClip.transform.position_y || 0) * 100)}%</span>
              </div>
            </div>
          )}

          {/* Transport Controls Bar (Sleek Floating Pill) */}
          <div className="mt-2.5 flex items-center gap-3 bg-slate-900/90 px-4 py-1.5 rounded-2xl border border-slate-800 text-xs font-mono shadow-xl backdrop-blur-sm shrink-0">
            {/* Step -1f */}
            <button
              onClick={() => setCurrentTime((t) => Math.max(0, t - 0.033))}
              title="Step -1 frame (ArrowLeft)"
              className="p-1 rounded hover:bg-slate-800 text-slate-300 hover:text-cyan-400 cursor-pointer"
            >
              -1f
            </button>

            {/* Play / Pause Toggle */}
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              title="Play/Pause (Space)"
              className="p-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 cursor-pointer shadow-cyan-sm transition-all"
            >
              {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
            </button>

            {/* Step +1f */}
            <button
              onClick={() => setCurrentTime((t) => Math.min(currentProject?.duration || 60, t + 0.033))}
              title="Step +1 frame (ArrowRight)"
              className="p-1 rounded hover:bg-slate-800 text-slate-300 hover:text-cyan-400 cursor-pointer"
            >
              +1f
            </button>

            {/* Timecode display */}
            <div className="text-cyan-300 font-bold px-2">
              {formatTimecode(currentTime)} / {formatTimecode(currentProject?.duration || 0)}
            </div>

            {/* Playback speed selector */}
            <select
              value={playbackSpeed}
              onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
              className="bg-slate-950 border border-slate-700 text-[11px] rounded px-1.5 py-0.5 text-slate-300 outline-none"
            >
              <option value="0.5">0.5x</option>
              <option value="1.0">1.0x</option>
              <option value="1.5">1.5x</option>
              <option value="2.0">2.0x</option>
            </select>

            {/* Safe guides toggle */}
            <button
              onClick={() => setShowSafeGuides(!showSafeGuides)}
              title="Toggle Safe Area Guides"
              className={`p-1.5 rounded-lg transition-colors ${
                showSafeGuides ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* C. RIGHT INSPECTOR (Collapsible, w-72) */}
        {showRightInspector && (
          <div className="w-72 border-l border-slate-800 bg-slate-950/95 flex flex-col shrink-0 overflow-y-auto p-3 space-y-3 z-10 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                {selectedClip ? 'Clip Inspector' : 'Project Properties'}
              </span>
              {selectedClip && (
                <span className="text-[10px] font-mono text-cyan-400 uppercase">
                  {selectedClip.source_type}
                </span>
              )}
            </div>

            {selectedClip ? (
              <div className="space-y-3 text-xs font-mono">
                {/* Name */}
                <div>
                  <label className="text-[10px] text-slate-400 block mb-0.5">Clip Name</label>
                  <input
                    type="text"
                    value={selectedClip.name}
                    onChange={(e) => {
                      const updated = currentProject!.clips.map((c) =>
                        c.id === selectedClip.id ? { ...c, name: e.target.value } : c
                      );
                      saveProjectState({ ...currentProject!, clips: updated });
                    }}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-200 outline-none focus:border-cyan-400"
                  />
                </div>

                {/* Timing */}
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-slate-400 block">Start (s)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={selectedClip.start_time}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        const updated = currentProject!.clips.map((c) =>
                          c.id === selectedClip.id ? { ...c, start_time: val } : c
                        );
                        saveProjectState({ ...currentProject!, clips: updated });
                      }}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400 block">Duration (s)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={selectedClip.duration}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0.5;
                        const updated = currentProject!.clips.map((c) =>
                          c.id === selectedClip.id
                            ? { ...c, duration: val, out_point: c.in_point + val * (c.speed || 1) }
                            : c
                        );
                        saveProjectState({ ...currentProject!, clips: updated });
                      }}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
                    />
                  </div>
                </div>

                {/* Playhead jump and snap tools */}
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => setCurrentTime(selectedClip.start_time)}
                    className="flex-1 py-1 px-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-[10px] text-cyan-300 flex items-center justify-center gap-1 cursor-pointer transition-colors"
                  >
                    <span>Jump Playhead Here</span>
                  </button>
                  {selectedClip.start_time > 0 && (
                    <button
                      onClick={() => {
                        const updated = currentProject!.clips.map((c) =>
                          c.id === selectedClip.id ? { ...c, start_time: 0.0 } : c
                        );
                        saveProjectState({ ...currentProject!, clips: updated });
                        setCurrentTime(0.0);
                      }}
                      className="py-1 px-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-[10px] text-slate-300 hover:text-cyan-300 cursor-pointer"
                      title="Snap clip to start of timeline (0.0s)"
                    >
                      Snap 0s
                    </button>
                  )}
                </div>

                {/* Speed */}
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-0.5">
                    <span>Speed Ramp</span>
                    <span>{selectedClip.speed || 1}x</span>
                  </div>
                  <input
                    type="range"
                    min="0.25"
                    max="4.0"
                    step="0.25"
                    value={selectedClip.speed || 1}
                    onChange={(e) => {
                      const spd = parseFloat(e.target.value);
                      const updated = currentProject!.clips.map((c) =>
                        c.id === selectedClip.id ? { ...c, speed: spd } : c
                      );
                      saveProjectState({ ...currentProject!, clips: updated });
                    }}
                    className="w-full accent-cyan-400 h-1 bg-slate-800 rounded-lg cursor-pointer"
                  />
                </div>

                {/* Volume */}
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-0.5">
                    <span>Volume</span>
                    <span>{Math.round((selectedClip.volume || 1) * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max="2.0"
                    step="0.05"
                    value={selectedClip.volume || 1}
                    onChange={(e) => {
                      const vol = parseFloat(e.target.value);
                      const updated = currentProject!.clips.map((c) =>
                        c.id === selectedClip.id ? { ...c, volume: vol } : c
                      );
                      saveProjectState({ ...currentProject!, clips: updated });
                    }}
                    className="w-full accent-cyan-400 h-1 bg-slate-800 rounded-lg cursor-pointer"
                  />
                </div>

                {/* Transform */}
                <div className="pt-2 border-t border-slate-800 space-y-1.5">
                  <span className="text-[10px] text-slate-400 block font-bold">Orientation</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        const updated = currentProject!.clips.map((c) =>
                          c.id === selectedClip.id
                            ? { ...c, transform: { ...c.transform, flip_h: !c.transform.flip_h } }
                            : c
                        );
                        saveProjectState({ ...currentProject!, clips: updated });
                      }}
                      className={`flex-1 py-1 rounded border text-[11px] flex items-center justify-center gap-1 ${
                        selectedClip.transform.flip_h
                          ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300'
                          : 'bg-slate-900 border-slate-700 text-slate-300'
                      }`}
                    >
                      <FlipHorizontal className="w-3 h-3" />
                      <span>Flip H</span>
                    </button>
                    <button
                      onClick={() => {
                        const updated = currentProject!.clips.map((c) =>
                          c.id === selectedClip.id
                            ? { ...c, transform: { ...c.transform, flip_v: !c.transform.flip_v } }
                            : c
                        );
                        saveProjectState({ ...currentProject!, clips: updated });
                      }}
                      className={`flex-1 py-1 rounded border text-[11px] flex items-center justify-center gap-1 ${
                        selectedClip.transform.flip_v
                          ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300'
                          : 'bg-slate-900 border-slate-700 text-slate-300'
                      }`}
                    >
                      <RotateCw className="w-3 h-3" />
                      <span>Flip V</span>
                    </button>
                  </div>
                </div>

                {/* CapCut Motion Transition for Video Clip */}
                {selectedClip.source_type === 'video' && (
                  <div className="pt-2 border-t border-slate-800 space-y-1.5">
                    <div className="flex items-center justify-between text-slate-200 font-bold">
                      <span className="text-[11px] text-cyan-300 uppercase flex items-center gap-1">
                        <Zap className="w-3 h-3 text-cyan-400" />
                        <span>Motion Transition</span>
                      </span>
                      {selectedClip.filters.transition && selectedClip.filters.transition !== 'none' && (
                        <span className="text-[9px] text-cyan-400 font-mono">
                          ⚡ {selectedClip.filters.transition.replace('_', ' ')}
                        </span>
                      )}
                    </div>
                    <select
                      value={selectedClip.filters.transition || 'none'}
                      onChange={(e) => handleApplyTransition(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-200 outline-none focus:border-cyan-400 text-xs font-mono cursor-pointer"
                    >
                      {capCutTransitions.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.icon} {t.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* DaVinci Resolve 3-Way Color Wheels & Grading (When Video Clip) */}
                {selectedClip.source_type === 'video' && (
                  <div className="pt-2 border-t border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-slate-200 font-bold">
                      <span className="text-[11px] text-cyan-300 uppercase flex items-center gap-1">
                        <Palette className="w-3 h-3 text-cyan-400" />
                        <span>Color Grading (DaVinci / Social)</span>
                      </span>
                      {selectedClip.filters.preset_name && (
                        <span className="text-[9px] text-cyan-400 font-mono truncate max-w-[100px]">
                          {selectedClip.filters.preset_name}
                        </span>
                      )}
                    </div>

                    {/* DaVinci Mode Selector Tabs */}
                    <div className="flex rounded-lg bg-slate-900 p-0.5 border border-slate-800 text-[10px]">
                      <button
                        onClick={() => setActiveInspectorTab('adjust')}
                        className={`flex-1 py-1 rounded text-center transition-all ${
                          activeInspectorTab === 'adjust'
                            ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-400/40'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        Sliders
                      </button>
                      <button
                        onClick={() => setActiveInspectorTab('wheels')}
                        className={`flex-1 py-1 rounded text-center transition-all ${
                          activeInspectorTab === 'wheels'
                            ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-400/40'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        3-Way Wheels
                      </button>
                      <button
                        onClick={() => setActiveInspectorTab('scopes')}
                        className={`flex-1 py-1 rounded text-center transition-all ${
                          activeInspectorTab === 'scopes'
                            ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-400/40'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        Scopes
                      </button>
                    </div>

                    {/* SUB-VIEW 1: SLIDERS & PRESETS */}
                    {activeInspectorTab === 'adjust' && (
                      <div className="space-y-2">
                        {/* Quick 1-Click Color Presets */}
                        <div className="flex flex-wrap gap-1 bg-slate-900/60 p-1.5 rounded-lg border border-slate-800">
                          {[
                            { id: 'clarendon', name: 'Clarendon' },
                            { id: 'juno', name: 'Juno' },
                            { id: 'valencia', name: 'Valencia' },
                            { id: 'teal_orange', name: 'Teal/Orange' },
                            { id: 'noir', name: 'Noir' },
                            { id: 'cyberpunk', name: 'Cyber' },
                            { id: 'retro_vhs', name: 'VHS' },
                          ].map((p) => (
                            <button
                              key={p.id}
                              onClick={() => applyColorPreset(p.id)}
                              className={`px-1.5 py-0.5 rounded text-[9px] font-mono border transition-all cursor-pointer ${
                                selectedClip.filters.preset_name?.toLowerCase().includes(p.name.toLowerCase())
                                  ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold'
                                  : 'bg-slate-950 border-slate-700 text-slate-300 hover:border-slate-500'
                              }`}
                            >
                              {p.name}
                            </button>
                          ))}
                        </div>

                        {/* Temperature & Tint */}
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-0.5">
                            <div className="flex justify-between text-[10px] text-slate-300">
                              <span>Warmth</span>
                              <span className="font-mono text-amber-400">{selectedClip.filters.temperature || 0}</span>
                            </div>
                            <input
                              type="range"
                              min="-100"
                              max="100"
                              step="5"
                              value={selectedClip.filters.temperature || 0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id
                                    ? { ...c, filters: { ...c.filters, temperature: val } }
                                    : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-full h-1 accent-amber-400 bg-slate-800 rounded-lg cursor-pointer"
                            />
                          </div>
                          <div className="space-y-0.5">
                            <div className="flex justify-between text-[10px] text-slate-300">
                              <span>Tint</span>
                              <span className="font-mono text-emerald-400">{selectedClip.filters.tint || 0}</span>
                            </div>
                            <input
                              type="range"
                              min="-100"
                              max="100"
                              step="5"
                              value={selectedClip.filters.tint || 0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id
                                    ? { ...c, filters: { ...c.filters, tint: val } }
                                    : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-full h-1 accent-emerald-400 bg-slate-800 rounded-lg cursor-pointer"
                            />
                          </div>
                        </div>

                        {/* Contrast & Saturation */}
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-0.5">
                            <div className="flex justify-between text-[10px] text-slate-300">
                              <span>Contrast</span>
                              <span className="font-mono text-cyan-400">{(((selectedClip.filters.contrast ?? 1.0)) * 100).toFixed(0)}%</span>
                            </div>
                            <input
                              type="range"
                              min="0.5"
                              max="2.5"
                              step="0.05"
                              value={selectedClip.filters.contrast ?? 1.0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id
                                    ? { ...c, filters: { ...c.filters, contrast: val } }
                                    : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-full h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                            />
                          </div>
                          <div className="space-y-0.5">
                            <div className="flex justify-between text-[10px] text-slate-300">
                              <span>Saturation</span>
                              <span className="font-mono text-cyan-400">{(((selectedClip.filters.saturation ?? 1.0)) * 100).toFixed(0)}%</span>
                            </div>
                            <input
                              type="range"
                              min="0.0"
                              max="3.0"
                              step="0.05"
                              value={selectedClip.filters.saturation ?? 1.0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id
                                    ? { ...c, filters: { ...c.filters, saturation: val } }
                                    : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-full h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                            />
                          </div>
                        </div>

                        {/* Brightness & Vignette */}
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-0.5">
                            <div className="flex justify-between text-[10px] text-slate-300">
                              <span>Brightness</span>
                              <span className="font-mono text-cyan-400">{((selectedClip.filters.brightness || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <input
                              type="range"
                              min="-0.5"
                              max="0.5"
                              step="0.02"
                              value={selectedClip.filters.brightness || 0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id
                                    ? { ...c, filters: { ...c.filters, brightness: val } }
                                    : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-full h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                            />
                          </div>
                          <div className="space-y-0.5">
                            <div className="flex justify-between text-[10px] text-slate-300">
                              <span>Vignette</span>
                              <span className="font-mono text-cyan-400">{((selectedClip.filters.vignette || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <input
                              type="range"
                              min="0.0"
                              max="1.0"
                              step="0.05"
                              value={selectedClip.filters.vignette || 0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id
                                    ? { ...c, filters: { ...c.filters, vignette: val } }
                                    : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-full h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                            />
                          </div>
                        </div>

                        {/* Blur & Quick Reset */}
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-0.5">
                            <div className="flex justify-between text-[10px] text-slate-300">
                              <span>Blur ({selectedClip.filters.blur || 0}px)</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max="15"
                              step="0.5"
                              value={selectedClip.filters.blur || 0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id
                                    ? { ...c, filters: { ...c.filters, blur: val } }
                                    : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-full h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                            />
                          </div>
                          <div className="space-y-0.5">
                            <div className="flex justify-between text-[10px] text-slate-300">
                              <span>Quick Grade Reset</span>
                            </div>
                            <button
                              onClick={() => {
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id
                                    ? {
                                        ...c,
                                        filters: {
                                          ...c.filters,
                                          brightness: 0,
                                          contrast: 1.0,
                                          saturation: 1.0,
                                          temperature: 0,
                                          tint: 0,
                                          lift: 0,
                                          gamma: 1.0,
                                          gain: 1.0,
                                          vignette: 0,
                                          blur: 0,
                                          color_splash: false,
                                          preset_name: undefined,
                                        },
                                      }
                                    : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                                setAiNotice('Reset color grading to 100% natural.');
                              }}
                              className="w-full py-1 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 hover:text-cyan-300 font-mono transition-colors cursor-pointer"
                            >
                              Reset Natural
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* SUB-VIEW 2: DAVINCI 3-WAY COLOR WHEELS */}
                    {activeInspectorTab === 'wheels' && (
                      <div className="space-y-3 bg-slate-900/60 p-2 rounded-xl border border-slate-800">
                        <div className="grid grid-cols-3 gap-2">
                          {/* LIFT WHEEL */}
                          <div className="flex flex-col items-center gap-1">
                            <span className="text-[10px] font-bold text-slate-300">LIFT (Shadows)</span>
                            <div className="w-16 h-16 rounded-full border-2 border-cyan-500/40 relative flex items-center justify-center bg-[radial-gradient(circle_at_center,_#1e293b_0%,_#0f172a_100%)] shadow-inner">
                              <div className="absolute inset-0.5 rounded-full border border-dashed border-cyan-400/30" />
                              <div
                                className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-cyan-sm transition-transform"
                                style={{
                                  transform: `translate(${(selectedClip.filters.tint || 0) * 0.15}px, ${-(selectedClip.filters.lift || 0) * 20}px)`,
                                }}
                              />
                            </div>
                            <span className="text-[9px] font-mono text-cyan-400">
                              {(selectedClip.filters.lift || 0).toFixed(2)}
                            </span>
                            <input
                              type="range"
                              min="-0.50"
                              max="0.50"
                              step="0.02"
                              value={selectedClip.filters.lift || 0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id ? { ...c, filters: { ...c.filters, lift: val } } : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-16 h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                              title="Master Lift Wheel"
                            />
                          </div>

                          {/* GAMMA WHEEL */}
                          <div className="flex flex-col items-center gap-1">
                            <span className="text-[10px] font-bold text-slate-300">GAMMA (Mids)</span>
                            <div className="w-16 h-16 rounded-full border-2 border-amber-500/40 relative flex items-center justify-center bg-[radial-gradient(circle_at_center,_#1e293b_0%,_#0f172a_100%)] shadow-inner">
                              <div className="absolute inset-0.5 rounded-full border border-dashed border-amber-400/30" />
                              <div
                                className="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-md transition-transform"
                                style={{
                                  transform: `translate(${(selectedClip.filters.temperature || 0) * 0.15}px, ${-(selectedClip.filters.gamma ?? 1.0 - 1.0) * 15}px)`,
                                }}
                              />
                            </div>
                            <span className="text-[9px] font-mono text-amber-400">
                              {(selectedClip.filters.gamma ?? 1.0).toFixed(2)}
                            </span>
                            <input
                              type="range"
                              min="0.50"
                              max="2.00"
                              step="0.05"
                              value={selectedClip.filters.gamma ?? 1.0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id ? { ...c, filters: { ...c.filters, gamma: val } } : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-16 h-1 accent-amber-400 bg-slate-800 rounded-lg cursor-pointer"
                              title="Master Gamma Wheel"
                            />
                          </div>

                          {/* GAIN WHEEL */}
                          <div className="flex flex-col items-center gap-1">
                            <span className="text-[10px] font-bold text-slate-300">GAIN (Highs)</span>
                            <div className="w-16 h-16 rounded-full border-2 border-emerald-500/40 relative flex items-center justify-center bg-[radial-gradient(circle_at_center,_#1e293b_0%,_#0f172a_100%)] shadow-inner">
                              <div className="absolute inset-0.5 rounded-full border border-dashed border-emerald-400/30" />
                              <div
                                className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-md transition-transform"
                                style={{
                                  transform: `translate(0px, ${-(selectedClip.filters.gain ?? 1.0 - 1.0) * 15}px)`,
                                }}
                              />
                            </div>
                            <span className="text-[9px] font-mono text-emerald-400">
                              {(selectedClip.filters.gain ?? 1.0).toFixed(2)}
                            </span>
                            <input
                              type="range"
                              min="0.50"
                              max="2.00"
                              step="0.05"
                              value={selectedClip.filters.gain ?? 1.0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id ? { ...c, filters: { ...c.filters, gain: val } } : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-16 h-1 accent-emerald-400 bg-slate-800 rounded-lg cursor-pointer"
                              title="Master Gain Wheel"
                            />
                          </div>
                        </div>
                      </div>
                    )}

                    {/* SUB-VIEW 3: DAVINCI SCOPES (WAVEFORM & RGB PARADE) */}
                    {activeInspectorTab === 'scopes' && (
                      <div className="space-y-2 bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 font-mono">
                        <div className="flex items-center justify-between text-[10px] text-slate-400">
                          <span className="flex items-center gap-1 text-emerald-400 font-bold">
                            <Activity className="w-3 h-3 text-emerald-400" />
                            <span>Waveform Monitor (0-100 IRE)</span>
                          </span>
                          <span>RGB Parade</span>
                        </div>
                        {/* Oscilloscope SVG */}
                        <div className="h-28 w-full bg-slate-950 rounded-lg border border-slate-800 p-1 relative overflow-hidden flex flex-col justify-between text-[8px] text-slate-600">
                          <div className="border-b border-dashed border-slate-800/80 pb-0.5 flex justify-between">
                            <span>100 IRE (Peak)</span>
                            <span className="text-red-400/80">Clip</span>
                          </div>
                          <div className="border-b border-dashed border-slate-800/80 pb-0.5">
                            <span>75 IRE</span>
                          </div>
                          <div className="border-b border-dashed border-slate-800/80 pb-0.5">
                            <span>50 IRE (Mid)</span>
                          </div>
                          <div className="border-b border-dashed border-slate-800/80 pb-0.5">
                            <span>25 IRE</span>
                          </div>
                          <div className="flex justify-between pt-0.5">
                            <span>0 IRE (Black)</span>
                            <span className="text-cyan-400/80">Floor</span>
                          </div>

                          {/* Dynamic SVG Waveform trace reacting to clip filters */}
                          <svg className="absolute inset-0 w-full h-full pointer-events-none p-1" preserveAspectRatio="none" viewBox="0 0 100 100">
                            {/* Green / Cyan phosphor trace */}
                            <path
                              d={`M 0 ${80 - (selectedClip.filters.lift || 0) * 30} Q 25 ${60 - (selectedClip.filters.gamma ?? 1.0 - 1) * 25}, 50 ${50 - (selectedClip.filters.brightness || 0) * 40} T 100 ${30 - (selectedClip.filters.gain ?? 1.0 - 1) * 30}`}
                              fill="none"
                              stroke="#10b981"
                              strokeWidth="2"
                              className="opacity-80"
                            />
                            {/* Blue secondary trace */}
                            <path
                              d={`M 0 ${85 - (selectedClip.filters.lift || 0) * 20} Q 30 ${65 - (selectedClip.filters.gamma ?? 1.0 - 1) * 20}, 60 ${55 - (selectedClip.filters.brightness || 0) * 35} T 100 ${35 - (selectedClip.filters.gain ?? 1.0 - 1) * 25}`}
                              fill="none"
                              stroke="#06b6d4"
                              strokeWidth="1.5"
                              className="opacity-70"
                            />
                            {/* Red / Warmth trace */}
                            <path
                              d={`M 0 ${78 - (selectedClip.filters.lift || 0) * 25} Q 20 ${58 - (selectedClip.filters.temperature || 0) * 0.2}, 70 ${48 - (selectedClip.filters.brightness || 0) * 35} T 100 ${28 - (selectedClip.filters.gain ?? 1.0 - 1) * 35}`}
                              fill="none"
                              stroke="#f59e0b"
                              strokeWidth="1.5"
                              className="opacity-70"
                            />
                          </svg>
                        </div>
                        <div className="text-[9px] text-slate-500 text-center">
                          Dynamic luminance & color traces reflect live grading adjustments.
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Text & Sticker Properties Inspector */}
                {(selectedClip.source_type === 'text' || selectedClip.source_type === 'subtitle' || selectedClip.source_type === 'sticker') && selectedClip.text_props && (
                  <div className="pt-2 border-t border-slate-800 space-y-2.5">
                    <span className="text-[11px] text-cyan-300 uppercase font-bold block">
                      {selectedClip.source_type === 'sticker' ? 'Sticker Inspector' : 'Text / Caption Inspector'}
                    </span>

                    {/* Text Input */}
                    <div>
                      <label className="text-[10px] text-slate-400 block mb-0.5">
                        {selectedClip.source_type === 'sticker' ? 'Emoji / Sticker' : 'Caption Text'}
                      </label>
                      <input
                        type="text"
                        value={selectedClip.text_props.text}
                        onChange={(e) => {
                          const val = e.target.value;
                          const updated = currentProject!.clips.map((c) =>
                            c.id === selectedClip.id
                              ? {
                                  ...c,
                                  text_props: { ...c.text_props!, text: val, sticker_emoji: c.source_type === 'sticker' ? val : c.text_props!.sticker_emoji }
                                }
                              : c
                          );
                          saveProjectState({ ...currentProject!, clips: updated });
                        }}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-200 outline-none focus:border-cyan-400 font-mono text-xs"
                      />
                    </div>

                    {/* On-Screen Screen Transform & Alignment Controls (Promoted to Top) */}
                    <div className="space-y-2 bg-slate-900/60 p-2.5 rounded-xl border border-cyan-500/30">
                      <div className="flex items-center justify-between text-[11px] font-bold text-slate-200">
                        <span className="text-cyan-300 flex items-center gap-1">
                          <Move className="w-3.5 h-3.5 text-cyan-400" />
                          <span>Screen Position & Alignment</span>
                        </span>
                        <span className="text-[9px] text-slate-500 font-mono">Drag on Video</span>
                      </div>

                      {/* Position X (Horizontal Offset) */}
                      <div className="space-y-0.5">
                        <div className="flex justify-between text-[10px] text-slate-300">
                          <span>Horizontal (X)</span>
                          <span className="font-mono text-cyan-400">
                            {Math.round((selectedClip.transform.position_x || 0) * 100)}%
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => handleNudgePosition(selectedClip.id, -0.05, 0)}
                            className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 hover:border-cyan-400 text-slate-300 hover:text-cyan-300 text-[10px] font-mono cursor-pointer"
                            title="Nudge Left 5%"
                          >
                            -5%
                          </button>
                          <input
                            type="range"
                            min="-0.85"
                            max="0.85"
                            step="0.02"
                            value={selectedClip.transform.position_x || 0}
                            onChange={(e) => {
                              const val = parseFloat(e.target.value);
                              const updated = currentProject!.clips.map((c) =>
                                c.id === selectedClip.id
                                  ? { ...c, transform: { ...c.transform, position_x: val } }
                                  : c
                              );
                              saveProjectState({ ...currentProject!, clips: updated });
                            }}
                            className="w-full h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                          />
                          <button
                            onClick={() => handleNudgePosition(selectedClip.id, 0.05, 0)}
                            className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 hover:border-cyan-400 text-slate-300 hover:text-cyan-300 text-[10px] font-mono cursor-pointer"
                            title="Nudge Right 5%"
                          >
                            +5%
                          </button>
                        </div>
                      </div>

                      {/* Position Y (Vertical Offset) */}
                      <div className="space-y-0.5">
                        <div className="flex justify-between text-[10px] text-slate-300">
                          <span>Vertical (Y)</span>
                          <span className="font-mono text-cyan-400">
                            {Math.round((selectedClip.transform.position_y || 0) * 100)}%
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => handleNudgePosition(selectedClip.id, 0, -0.05)}
                            className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 hover:border-cyan-400 text-slate-300 hover:text-cyan-300 text-[10px] font-mono cursor-pointer"
                            title="Nudge Up 5%"
                          >
                            -5%
                          </button>
                          <input
                            type="range"
                            min="-0.85"
                            max="0.85"
                            step="0.02"
                            value={selectedClip.transform.position_y || 0}
                            onChange={(e) => {
                              const val = parseFloat(e.target.value);
                              const updated = currentProject!.clips.map((c) =>
                                c.id === selectedClip.id
                                  ? { ...c, transform: { ...c.transform, position_y: val } }
                                  : c
                              );
                              saveProjectState({ ...currentProject!, clips: updated });
                            }}
                            className="w-full h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                          />
                          <button
                            onClick={() => handleNudgePosition(selectedClip.id, 0, 0.05)}
                            className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 hover:border-cyan-400 text-slate-300 hover:text-cyan-300 text-[10px] font-mono cursor-pointer"
                            title="Nudge Down 5%"
                          >
                            +5%
                          </button>
                        </div>
                      </div>

                      {/* Scale & Rotation */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="space-y-0.5">
                          <div className="flex justify-between text-[10px] text-slate-300">
                            <span>Scale</span>
                            <span className="font-mono text-cyan-400">{(selectedClip.transform.scale_x || 1.0).toFixed(1)}x</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleNudgeScale(selectedClip.id, -0.15)}
                              className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 hover:text-cyan-300 text-[10px] font-bold cursor-pointer"
                            >
                              −
                            </button>
                            <input
                              type="range"
                              min="0.3"
                              max="3.0"
                              step="0.1"
                              value={selectedClip.transform.scale_x || 1.0}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                const updated = currentProject!.clips.map((c) =>
                                  c.id === selectedClip.id
                                    ? { ...c, transform: { ...c.transform, scale_x: val, scale_y: val } }
                                    : c
                                );
                                saveProjectState({ ...currentProject!, clips: updated });
                              }}
                              className="w-full h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                            />
                            <button
                              onClick={() => handleNudgeScale(selectedClip.id, 0.15)}
                              className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 hover:text-cyan-300 text-[10px] font-bold cursor-pointer"
                            >
                              +
                            </button>
                          </div>
                        </div>

                        <div className="space-y-0.5">
                          <div className="flex justify-between text-[10px] text-slate-300">
                            <span>Rotation</span>
                            <span className="font-mono text-cyan-400">{Math.round(selectedClip.transform.rotation || 0)}°</span>
                          </div>
                          <input
                            type="range"
                            min="-180"
                            max="180"
                            step="5"
                            value={selectedClip.transform.rotation || 0}
                            onChange={(e) => {
                              const val = parseInt(e.target.value);
                              const updated = currentProject!.clips.map((c) =>
                                c.id === selectedClip.id
                                  ? { ...c, transform: { ...c.transform, rotation: val } }
                                  : c
                              );
                              saveProjectState({ ...currentProject!, clips: updated });
                            }}
                            className="w-full h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                          />
                        </div>
                      </div>

                      {/* 1-Click Quick Align Presets */}
                      <div className="space-y-1">
                        <span className="text-[9px] text-slate-400 block font-bold">Quick Screen Presets</span>
                        <div className="grid grid-cols-3 gap-1 text-[9px] font-mono">
                          <button
                            onClick={() => handleSetPosition(selectedClip.id, 0, -0.65)}
                            className="p-1 rounded bg-slate-900 border border-slate-700 hover:border-cyan-400 text-slate-300 cursor-pointer"
                          >
                            Top Header
                          </button>
                          <button
                            onClick={() => handleSetPosition(selectedClip.id, 0, 0)}
                            className="p-1 rounded bg-slate-900 border border-slate-700 hover:border-cyan-400 text-slate-300 cursor-pointer"
                          >
                            Dead Center
                          </button>
                          <button
                            onClick={() => handleSetPosition(selectedClip.id, 0, 0.55)}
                            className="p-1 rounded bg-cyan-950/40 border border-cyan-400/40 text-cyan-300 font-bold cursor-pointer"
                          >
                            Subtitles (Reels)
                          </button>
                        </div>
                      </div>

                      <div className="p-1.5 rounded-lg bg-cyan-950/20 border border-cyan-500/30 text-[9px] text-cyan-300 font-mono">
                        💡 Direct Screen Drag: Click & drag directly on the video monitor to reposition, or use on-screen arrows!
                      </div>
                    </div>

                    {/* Font & Font Size (For text) */}
                    {selectedClip.source_type !== 'sticker' && (
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-0.5">Font</label>
                          <select
                            value={selectedClip.text_props.font}
                            onChange={(e) => {
                              const val = e.target.value;
                              const updated = currentProject!.clips.map((c) =>
                                c.id === selectedClip.id
                                  ? { ...c, text_props: { ...c.text_props!, font: val } }
                                  : c
                              );
                              saveProjectState({ ...currentProject!, clips: updated });
                            }}
                            className="w-full bg-slate-900 border border-slate-700 rounded px-1.5 py-1 text-[11px] text-slate-200 outline-none"
                          >
                            <option value="Impact">Impact (Viral)</option>
                            <option value="Arial Black">Arial Black</option>
                            <option value="Montserrat">Montserrat</option>
                            <option value="Georgia">Georgia Serif</option>
                            <option value="Helvetica">Helvetica Clean</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-0.5">Size ({selectedClip.text_props.font_size}px)</label>
                          <input
                            type="range"
                            min="24"
                            max="120"
                            step="2"
                            value={selectedClip.text_props.font_size}
                            onChange={(e) => {
                              const val = parseInt(e.target.value);
                              const updated = currentProject!.clips.map((c) =>
                                c.id === selectedClip.id
                                  ? { ...c, text_props: { ...c.text_props!, font_size: val } }
                                  : c
                              );
                              saveProjectState({ ...currentProject!, clips: updated });
                            }}
                            className="w-full h-1 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                          />
                        </div>
                      </div>
                    )}

                    {/* Colors */}
                    {selectedClip.source_type !== 'sticker' && (
                      <div className="grid grid-cols-3 gap-1.5">
                        <div>
                          <label className="text-[9px] text-slate-400 block mb-0.5">Color</label>
                          <input
                            type="color"
                            value={selectedClip.text_props.color}
                            onChange={(e) => {
                              const val = e.target.value;
                              const updated = currentProject!.clips.map((c) =>
                                c.id === selectedClip.id
                                  ? { ...c, text_props: { ...c.text_props!, color: val } }
                                  : c
                              );
                              saveProjectState({ ...currentProject!, clips: updated });
                            }}
                            className="w-full h-6 bg-slate-900 border border-slate-700 rounded cursor-pointer"
                          />
                        </div>
                        <div>
                          <label className="text-[9px] text-slate-400 block mb-0.5">Outline</label>
                          <input
                            type="color"
                            value={selectedClip.text_props.outline_color}
                            onChange={(e) => {
                              const val = e.target.value;
                              const updated = currentProject!.clips.map((c) =>
                                c.id === selectedClip.id
                                  ? { ...c, text_props: { ...c.text_props!, outline_color: val } }
                                  : c
                              );
                              saveProjectState({ ...currentProject!, clips: updated });
                            }}
                            className="w-full h-6 bg-slate-900 border border-slate-700 rounded cursor-pointer"
                          />
                        </div>
                        <div>
                          <label className="text-[9px] text-slate-400 block mb-0.5">Box BG</label>
                          <input
                            type="color"
                            value={selectedClip.text_props.bg_color || '#000000'}
                            onChange={(e) => {
                              const val = e.target.value;
                              const updated = currentProject!.clips.map((c) =>
                                c.id === selectedClip.id
                                  ? { ...c, text_props: { ...c.text_props!, bg_color: val } }
                                  : c
                              );
                              saveProjectState({ ...currentProject!, clips: updated });
                            }}
                            className="w-full h-6 bg-slate-900 border border-slate-700 rounded cursor-pointer"
                          />
                        </div>
                      </div>
                    )}

                    {/* Animation Style */}
                    <div>
                      <label className="text-[10px] text-slate-400 block mb-0.5">Animation</label>
                      <div className="grid grid-cols-3 gap-1 text-[10px]">
                        {(['none', 'bounce', 'pulse'] as const).map((anim) => (
                          <button
                            key={anim}
                            onClick={() => {
                              const updated = currentProject!.clips.map((c) =>
                                c.id === selectedClip.id
                                  ? { ...c, text_props: { ...c.text_props!, animation: anim } }
                                  : c
                              );
                              saveProjectState({ ...currentProject!, clips: updated });
                            }}
                            className={`py-1 rounded border capitalize transition-all ${
                              selectedClip.text_props?.animation === anim
                                ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold'
                                : 'bg-slate-900 border-slate-700 text-slate-400'
                            }`}
                          >
                            {anim}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Color Splash (Character in color, rest B&W) */}
                <div className="pt-2 border-t border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-red-300 font-bold">Sin City (Color Splash)</span>
                    <input
                      type="checkbox"
                      checked={!!selectedClip.filters.color_splash}
                      onChange={(e) => {
                        const val = e.target.checked;
                        const updated = currentProject!.clips.map((c) =>
                          c.id === selectedClip.id
                            ? {
                                ...c,
                                filters: {
                                  ...c.filters,
                                  color_splash: val,
                                  contrast: val ? 1.35 : 1.0,
                                  saturation: val ? 1.35 : 1.0,
                                  preset_name: val ? 'Sin City (Color Splash)' : undefined,
                                },
                              }
                            : c
                        );
                        saveProjectState({ ...currentProject!, clips: updated });
                        setAiNotice(
                          val
                            ? 'Enabled Sin City Color Splash: Character colorful, background monochrome.'
                            : 'Disabled Sin City Color Splash.'
                        );
                      }}
                      className="accent-red-500 cursor-pointer w-4 h-4"
                    />
                  </div>
                  <span className="text-[9px] text-slate-500 block leading-tight">
                    Character colorful • entire rest of video black & white
                  </span>

                  {selectedClip.filters.color_splash && (
                    <div className="pt-2 pl-2 space-y-2 border-l border-red-500/30 mt-2 bg-red-950/10 p-2 rounded-lg">
                      <div className="space-y-0.5">
                        <div className="flex justify-between text-[10px] text-slate-300">
                          <span>Focus X Position</span>
                          <span className="font-mono text-red-400">
                            {Math.round(((selectedClip.filters.color_splash_x ?? 0.56) as number) * 100)}%
                          </span>
                        </div>
                        <input
                          type="range"
                          min="0.1"
                          max="0.9"
                          step="0.02"
                          value={selectedClip.filters.color_splash_x ?? 0.56}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value);
                            const updated = currentProject!.clips.map((c) =>
                              c.id === selectedClip.id
                                ? { ...c, filters: { ...c.filters, color_splash_x: val } }
                                : c
                            );
                            saveProjectState({ ...currentProject!, clips: updated });
                          }}
                          className="w-full h-1 accent-red-500 bg-slate-800 rounded-lg cursor-pointer"
                        />
                      </div>

                      <div className="space-y-0.5">
                        <div className="flex justify-between text-[10px] text-slate-300">
                          <span>Focus Y Position</span>
                          <span className="font-mono text-red-400">
                            {Math.round(((selectedClip.filters.color_splash_y ?? 0.58) as number) * 100)}%
                          </span>
                        </div>
                        <input
                          type="range"
                          min="0.1"
                          max="0.9"
                          step="0.02"
                          value={selectedClip.filters.color_splash_y ?? 0.58}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value);
                            const updated = currentProject!.clips.map((c) =>
                              c.id === selectedClip.id
                                ? { ...c, filters: { ...c.filters, color_splash_y: val } }
                                : c
                            );
                            saveProjectState({ ...currentProject!, clips: updated });
                          }}
                          className="w-full h-1 accent-red-500 bg-slate-800 rounded-lg cursor-pointer"
                        />
                      </div>

                      <div className="space-y-0.5">
                        <div className="flex justify-between text-[10px] text-slate-300">
                          <span>Isolation Radius</span>
                          <span className="font-mono text-red-400">
                            {Math.round(((selectedClip.filters.color_splash_radius ?? 0.32) as number) * 100)}%
                          </span>
                        </div>
                        <input
                          type="range"
                          min="0.15"
                          max="0.65"
                          step="0.02"
                          value={selectedClip.filters.color_splash_radius ?? 0.32}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value);
                            const updated = currentProject!.clips.map((c) =>
                              c.id === selectedClip.id
                                ? { ...c, filters: { ...c.filters, color_splash_radius: val } }
                                : c
                            );
                            saveProjectState({ ...currentProject!, clips: updated });
                          }}
                          className="w-full h-1 accent-red-500 bg-slate-800 rounded-lg cursor-pointer"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="pt-2 border-t border-slate-800 space-y-1.5">
                  <button
                    onClick={handleSplitClipAtPlayhead}
                    className="w-full py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <Split className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Split at Playhead (S)</span>
                  </button>
                  <button
                    onClick={handleDuplicateSelectedClip}
                    className="w-full py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <Copy className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Duplicate Clip</span>
                  </button>
                  <button
                    onClick={handleDeleteSelectedClip}
                    className="w-full py-1.5 rounded-lg bg-red-950/40 hover:bg-red-900/60 border border-red-500/30 text-red-300 text-xs flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete Clip</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-slate-500 text-xs font-mono space-y-2">
                <p>Click any clip on the multitrack timeline to inspect and edit its properties.</p>
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1 text-[11px] text-slate-400">
                  <div className="text-slate-300 font-bold mb-1">Hotkeys</div>
                  <div><span className="text-cyan-400">Space:</span> Play/Pause</div>
                  <div><span className="text-cyan-400">S:</span> Split Clip</div>
                  <div><span className="text-cyan-400">Del:</span> Delete Clip</div>
                  <div><span className="text-cyan-400">← / →:</span> Step 1 Frame</div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 3. MULTITRACK TIMELINE (Spacious, Height: 240px) */}
      <div className="h-60 border-t border-cyan-500/20 bg-slate-950 flex flex-col shrink-0 z-20">
        {/* Timeline Header Toolbar */}
        <div className="h-9 border-b border-slate-800 px-3 flex items-center justify-between text-xs font-mono bg-slate-900/80">
          <div className="flex items-center gap-2">
            <button
              onClick={handleSplitClipAtPlayhead}
              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
            >
              <Scissors className="w-3 h-3 text-cyan-400" />
              <span>Split (S)</span>
            </button>
            <button
              onClick={handleDeleteSelectedClip}
              disabled={!selectedClipId}
              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-red-400 flex items-center gap-1 cursor-pointer disabled:opacity-40"
            >
              <Trash2 className="w-3 h-3" />
              <span>Delete</span>
            </button>

            <label className="flex items-center gap-1 text-slate-400 cursor-pointer ml-2">
              <input
                type="checkbox"
                checked={rippleDelete}
                onChange={(e) => setRippleDelete(e.target.checked)}
                className="accent-cyan-400"
              />
              <span className="text-[10px]">Ripple Delete</span>
            </label>
          </div>

          {/* Timeline Zoom Slider */}
          <div className="flex items-center gap-1.5">
            <ZoomOut className="w-3 h-3 text-slate-400" />
            <input
              type="range"
              min="15"
              max="75"
              value={timelineZoom}
              onChange={(e) => setTimelineZoom(parseInt(e.target.value))}
              className="w-20 accent-cyan-400 h-1 bg-slate-800 rounded-lg cursor-pointer"
            />
            <ZoomIn className="w-3 h-3 text-slate-400" />
          </div>
        </div>

        {/* Tracks Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Track Headers (w-44) */}
          <div className="w-44 border-r border-slate-800 bg-slate-900/60 flex flex-col shrink-0">
            {currentProject?.tracks.map((track) => (
              <div
                key={track.id}
                className="h-10 border-b border-slate-800/80 px-2.5 flex items-center justify-between text-xs font-mono"
              >
                <div className="flex items-center gap-1.5 truncate">
                  <span className="text-cyan-400 font-bold text-[10px]">{track.id}</span>
                  <span className="text-slate-300 truncate text-[11px]">{track.name}</span>
                </div>
                <div className="flex items-center gap-1 text-slate-400">
                  <button
                    onClick={() => {
                      const updatedTracks = currentProject.tracks.map((t) =>
                        t.id === track.id ? { ...t, visible: !t.visible } : t
                      );
                      saveProjectState({ ...currentProject, tracks: updatedTracks });
                    }}
                    className="hover:text-cyan-400 p-0.5 cursor-pointer"
                  >
                    {track.visible ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                  </button>
                  <button
                    onClick={() => {
                      const updatedTracks = currentProject.tracks.map((t) =>
                        t.id === track.id ? { ...t, locked: !t.locked } : t
                      );
                      saveProjectState({ ...currentProject, tracks: updatedTracks });
                    }}
                    className="hover:text-cyan-400 p-0.5 cursor-pointer"
                  >
                    {track.locked ? <Lock className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Timeline Grid, Ruler & Playhead */}
          <div
            ref={timelineScrollRef}
            className="flex-1 overflow-x-auto overflow-y-hidden relative bg-slate-950"
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const clickX = e.clientX - rect.left + e.currentTarget.scrollLeft;
              const newTime = Math.max(0, clickX / timelineZoom);
              setCurrentTime(newTime);
            }}
          >
            {/* Draggable Playhead Needle */}
            <div
              className="absolute top-0 bottom-0 w-px bg-cyan-400 z-30 pointer-events-none shadow-cyan-glow"
              style={{ left: `${currentTime * timelineZoom}px` }}
            >
              <div className="w-3 h-3 -ml-1.5 bg-cyan-400 rotate-45 transform origin-center shadow-lg" />
            </div>

            {/* Track Lanes */}
            {currentProject?.tracks.map((track) => {
              const trackClips = currentProject.clips.filter((c) => c.track_id === track.id);
              return (
                <div
                  key={track.id}
                  className="h-10 border-b border-slate-800/60 relative"
                  style={{ width: `${(currentProject.duration || 60) * timelineZoom + 400}px` }}
                >
                  {trackClips.map((clip) => {
                    const isSelected = selectedClipId === clip.id;
                    return (
                      <div
                        key={clip.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedClipId(clip.id);
                          setCurrentTime(clip.start_time);
                        }}
                        onMouseDown={(e) => handleStartTimelineDrag(e, 'move', clip)}
                        className={`absolute top-1 bottom-1 rounded-lg px-2 flex items-center justify-between text-xs font-mono cursor-grab active:cursor-grabbing transition-all border group select-none ${
                          isSelected
                            ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200 shadow-cyan-sm ring-1 ring-cyan-400/50'
                            : clip.source_type === 'video'
                            ? 'bg-blue-900/40 border-blue-500/40 text-blue-200 hover:border-blue-400'
                            : clip.source_type === 'audio'
                            ? 'bg-emerald-900/40 border-emerald-500/40 text-emerald-200 hover:border-emerald-400'
                            : 'bg-purple-900/40 border-purple-500/40 text-purple-200 hover:border-purple-400'
                        }`}
                        style={{
                          left: `${clip.start_time * timelineZoom}px`,
                          width: `${Math.max(24, clip.duration * timelineZoom)}px`,
                        }}
                      >
                        {/* Interactive Left Trim Handle */}
                        {isSelected && (
                          <div
                            onMouseDown={(e) => handleStartTimelineDrag(e, 'trim_left', clip)}
                            className="absolute -left-1.5 top-0 bottom-0 w-3 bg-cyan-400 hover:bg-cyan-300 rounded-l cursor-ew-resize flex items-center justify-center z-20 shadow-md group/handle"
                            title="Drag to trim start (In Point)"
                          >
                            <div className="w-0.5 h-3 bg-slate-950 rounded-full" />
                          </div>
                        )}

                        {/* Audio Waveform visualization if audio clip */}
                        {clip.source_type === 'audio' && (
                          <div className="absolute inset-0 opacity-25 overflow-hidden flex items-center gap-0.5 pointer-events-none px-1">
                            {[40, 70, 30, 90, 60, 80, 45, 100, 30, 85, 50, 75, 40, 95, 60, 30, 80, 70].map((h, i) => (
                              <div
                                key={i}
                                className="w-1 bg-emerald-300 rounded-full"
                                style={{ height: `${h}%` }}
                              />
                            ))}
                          </div>
                        )}

                        <div className="flex items-center gap-1.5 min-w-0 relative z-10 overflow-hidden">
                          <span className="truncate text-[11px] font-bold">{clip.name}</span>
                          {clip.filters?.transition && clip.filters.transition !== 'none' && (
                            <span className="px-1 py-0.2 rounded bg-cyan-400/25 border border-cyan-400/70 text-[8px] font-mono text-cyan-200 shrink-0 font-bold" title={`Transition: ${clip.filters.transition}`}>
                              ⚡ {clip.filters.transition.replace('_', ' ')}
                            </span>
                          )}
                          {clip.filters?.preset_name && (
                            <span className="px-1 py-0.2 rounded bg-purple-400/25 border border-purple-400/70 text-[8px] font-mono text-purple-200 shrink-0 font-bold" title={`Filter: ${clip.filters.preset_name}`}>
                              🎨 {clip.filters.preset_name.replace('Sin City (Color Splash)', 'Splash')}
                            </span>
                          )}
                        </div>
                        <span className="text-[9px] opacity-70 ml-1 shrink-0 relative z-10">
                          {clip.duration.toFixed(1)}s
                        </span>

                        {/* Interactive Right Trim Handle */}
                        {isSelected && (
                          <div
                            onMouseDown={(e) => handleStartTimelineDrag(e, 'trim_right', clip)}
                            className="absolute -right-1.5 top-0 bottom-0 w-3 bg-cyan-400 hover:bg-cyan-300 rounded-r cursor-ew-resize flex items-center justify-center z-20 shadow-md group/handle"
                            title="Drag to trim end (Out Point)"
                          >
                            <div className="w-0.5 h-3 bg-slate-950 rounded-full" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 4. EXPORT & RENDER MODAL */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-cyan-500/30 rounded-2xl p-5 shadow-2xl space-y-4 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <div className="flex items-center gap-2 font-bold font-mono text-cyan-400 uppercase text-xs">
                <Film className="w-4 h-4 text-cyan-400" />
                <span>Export Composition</span>
              </div>
              <button
                onClick={() => setShowExportModal(false)}
                className="text-slate-400 hover:text-slate-200 cursor-pointer text-xs"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div>
                <label className="text-slate-400 block mb-1">Resolution</label>
                <div className="grid grid-cols-4 gap-1.5">
                  {['720p', '1080p', '1440p', '4K'].map((res) => (
                    <button
                      key={res}
                      onClick={() => setExportRes(res)}
                      className={`py-1 rounded border transition-all ${
                        exportRes === res
                          ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold'
                          : 'bg-slate-950 border-slate-800 text-slate-400'
                      }`}
                    >
                      {res}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Aspect Ratio</label>
                <div className="grid grid-cols-4 gap-1.5">
                  {(['16:9', '9:16', '1:1', '4:5'] as const).map((asp) => (
                    <button
                      key={asp}
                      onClick={() => setExportAspect(asp)}
                      className={`py-1 rounded border transition-all ${
                        exportAspect === asp
                          ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold'
                          : 'bg-slate-950 border-slate-800 text-slate-400'
                      }`}
                    >
                      {asp}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Codec</label>
                <div className="grid grid-cols-2 gap-1.5">
                  <button
                    onClick={() => setExportCodec('h264')}
                    className={`py-1 rounded border transition-all ${
                      exportCodec === 'h264'
                        ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold'
                        : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    H.264 (MP4)
                  </button>
                  <button
                    onClick={() => setExportCodec('hevc')}
                    className={`py-1 rounded border transition-all ${
                      exportCodec === 'hevc'
                        ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold'
                        : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    H.265 (HEVC)
                  </button>
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer text-slate-300 pt-1">
                <input
                  type="checkbox"
                  checked={exportAudioOnly}
                  onChange={(e) => setExportAudioOnly(e.target.checked)}
                  className="accent-cyan-400"
                />
                <span>Export Audio Only (.mp3)</span>
              </label>

              {isRendering && (
                <div className="space-y-1 pt-1">
                  <div className="flex justify-between text-[11px] text-cyan-400">
                    <span>Rendering composition...</span>
                    <span>{renderProgress}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
                      style={{ width: `${renderProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {renderDownloadUrl && (
                <div className="p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-emerald-300 text-xs font-bold">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Render Complete!</span>
                  </div>
                  <a
                    href={renderDownloadUrl}
                    download
                    className="px-3 py-1 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center gap-1"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </a>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setShowExportModal(false)}
                className="px-3 py-1.5 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 text-xs font-mono"
              >
                Close
              </button>
              <button
                onClick={handleStartExport}
                disabled={isRendering}
                className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs font-mono uppercase tracking-wider flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRendering ? 'animate-spin' : ''}`} />
                <span>{isRendering ? 'Rendering...' : 'Start Render'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
