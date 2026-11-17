import React from 'react';
import {
  Home,
  Mic,
  Monitor,
  Film,
  Camera,
  PlaySquare,
  Scissors,
  TrendingUp,
  FolderOpen,
  Brain,
  Settings,
  Sparkles,
  Smartphone,
  X,
  Wifi
} from 'lucide-react';

export type SectionType =
  | 'home'
  | 'talk'
  | 'desktop'
  | 'mobile'
  | 'studio'
  | 'reels'
  | 'shorts'
  | 'editor'
  | 'youtube'
  | 'instagram'
  | 'research'
  | 'files'
  | 'memory'
  | 'settings';

interface SidebarProps {
  activeSection: SectionType;
  onSelectSection: (section: SectionType) => void;
  clipsCount?: number;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
  mobileUrl?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeSection,
  onSelectSection,
  clipsCount = 0,
  isMobileOpen = false,
  onCloseMobile,
  mobileUrl
}) => {
  const navItems = [
    { id: 'home', label: 'Home HUD', icon: Home },
    { id: 'mobile', label: 'Mobile Remote Hub', icon: Smartphone, highlight: true },
    { id: 'talk', label: 'Talk to JARVIS', icon: Mic },
    { id: 'desktop', label: 'Desktop Control', icon: Monitor },
    { id: 'studio', label: 'Content Studio', icon: Film, badge: clipsCount },
    { id: 'reels', label: 'Reels Factory', icon: Camera },
    { id: 'shorts', label: 'Shorts Factory', icon: PlaySquare },
    { id: 'editor', label: 'Video Editor', icon: Scissors },
    { id: 'youtube', label: 'YouTube Manager', icon: PlaySquare },
    { id: 'instagram', label: 'Instagram Manager', icon: Camera },
    { id: 'research', label: 'Viral Research', icon: TrendingUp },
    { id: 'files', label: 'File Manager', icon: FolderOpen },
    { id: 'memory', label: 'Memory Bank', icon: Brain },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const handleSelect = (id: SectionType) => {
    onSelectSection(id);
    if (onCloseMobile) onCloseMobile();
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-slate-950/95 backdrop-blur-2xl border-r border-cyan-500/20 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-cyan-500/20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-cyan-sm">
            <Sparkles className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <div className="text-lg font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-300">
              J.A.R.V.I.S
            </div>
            <div className="text-[10px] tracking-wider font-mono text-cyan-400/70">
              MARK VII AUTONOMOUS CORE
            </div>
          </div>
        </div>

        {/* Mobile close button */}
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Nav list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;

          return (
            <button
              key={item.id}
              onClick={() => handleSelect(item.id as SectionType)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                isActive
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-cyan-sm'
                  : item.highlight
                  ? 'text-cyan-300 hover:text-white hover:bg-cyan-500/10 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : item.highlight ? 'text-cyan-300' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.highlight && !isActive && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/30 text-cyan-200 font-bold">
                  PHONE
                </span>
              )}
              {item.badge !== undefined && item.badge > 0 && (
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer Info with Phone LAN link */}
      <div className="p-4 border-t border-cyan-500/20 bg-slate-950/60 text-[11px] font-mono text-slate-400">
        <div className="flex justify-between items-center text-xs mb-1.5">
          <span className="text-cyan-400 flex items-center gap-1.5">
            <Wifi className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            PHONE LINK
          </span>
          <span className="text-emerald-400 font-bold">LAN ACTIVE</span>
        </div>
        {mobileUrl ? (
          <div className="truncate text-[10px] text-cyan-300/80 bg-slate-900/80 px-2 py-1 rounded border border-cyan-500/20">
            {mobileUrl}
          </div>
        ) : (
          <div className="text-slate-400 text-[10px]">Zero Paid APIs • Ollama Core</div>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden md:flex flex-col w-64 h-screen z-30 select-none">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
            onClick={onCloseMobile}
          />
          <div className="relative w-72 max-w-[85vw] h-full shadow-2xl z-10 animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
