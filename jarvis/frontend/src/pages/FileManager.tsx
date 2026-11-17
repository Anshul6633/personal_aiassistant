import React, { useState, useEffect } from 'react';
import {
  FolderOpen,
  Film,
  HardDrive,
  ExternalLink,
  Sparkles,
  RefreshCw,
  Folder,
  Play,
  FileVideo,
  CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';

interface FileManagerProps {
  onSelectVideoForClipping: (path: string) => void;
}

export const FileManager: React.FC<FileManagerProps> = ({ onSelectVideoForClipping }) => {
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [notice, setNotice] = useState<string | null>(null);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const data = await api.browseLocalVideos();
      setFiles(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleOpenFolder = async (path: string) => {
    try {
      await api.openInExplorer(path);
      setNotice(`Opened in File Explorer: ${path}`);
      setTimeout(() => setNotice(null), 3000);
    } catch (e: any) {
      setNotice(`Error opening folder: ${e.message}`);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-cyan-400" />
            Local Video & Media Storage Manager
          </h1>
          <p className="text-xs font-mono text-cyan-400/80">
            Windows Directory Scanner • C: Videos • D: High-Capacity Storage (242 GB Free)
          </p>
        </div>

        <button
          onClick={fetchFiles}
          disabled={loading}
          className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-cyan-500/30 text-cyan-300 text-xs font-mono hover:bg-slate-800 cursor-pointer transition-colors flex items-center gap-1.5 self-start"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Files ({files.length})</span>
        </button>
      </div>

      {notice && (
        <div className="p-3 rounded-xl bg-cyan-950/80 border border-cyan-400 text-xs font-mono text-cyan-300 flex items-center gap-2 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{notice}</span>
        </div>
      )}

      {/* Quick Access Folders */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
        {[
          { name: 'Generated Reels', path: 'jarvis/output/reels', desc: 'Finished 9:16 vertical clips' },
          { name: 'Thumbnails', path: 'jarvis/output/thumbnails', desc: 'Clip preview images' },
          { name: 'Audio Demuxed', path: 'jarvis/output/audio', desc: '16kHz Whisper audio cache' },
          { name: 'Test Samples', path: 'jarvis/tests', desc: 'Sample podcasts and clips' }
        ].map((f, i) => (
          <button
            key={i}
            onClick={() => handleOpenFolder(f.path)}
            className="p-3.5 rounded-xl bg-slate-950/80 border border-cyan-500/20 hover:border-cyan-400 text-left transition-all cursor-pointer group shadow-sm"
          >
            <div className="flex items-center justify-between text-cyan-400 mb-1">
              <span className="font-bold flex items-center gap-1.5">
                <Folder className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                {f.name}
              </span>
              <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100" />
            </div>
            <div className="text-[10px] text-slate-400 truncate">{f.desc}</div>
          </button>
        ))}
      </div>

      {/* Discovered Videos Table */}
      <div className="rounded-2xl bg-slate-950/80 border border-cyan-500/25 overflow-hidden shadow-cyan-sm">
        <div className="px-5 py-3 border-b border-cyan-500/15 bg-slate-900/60 flex items-center justify-between text-xs font-mono">
          <span className="text-slate-200 font-bold flex items-center gap-2">
            <FileVideo className="w-4 h-4 text-cyan-400" />
            DISCOVERED LOCAL MEDIA FILES ({files.length})
          </span>
          <span className="text-slate-400">Supported: .MP4, .MOV, .MKV, .WAV</span>
        </div>

        {files.length === 0 ? (
          <div className="p-8 text-center text-slate-500 font-mono text-xs">
            No video files found in default locations. Place video files in C:\Users\Anshul\Videos or jarvis/tests/.
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {files.map((file, idx) => (
              <div
                key={idx}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-900/40 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center shrink-0">
                    <Film className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-200">{file.name}</div>
                    <div className="text-[10px] font-mono text-slate-400 truncate max-w-md">
                      {file.path}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 text-xs font-mono shrink-0">
                  <span className="text-slate-300 font-bold">{file.size_mb} MB</span>

                  <button
                    onClick={() => onSelectVideoForClipping(file.path)}
                    className="px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 font-bold text-[11px] cursor-pointer flex items-center gap-1.5 transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Send to Clipping Engine</span>
                  </button>

                  <button
                    onClick={() => handleOpenFolder(file.path)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 cursor-pointer transition-colors"
                    title="Open in Windows Explorer"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
