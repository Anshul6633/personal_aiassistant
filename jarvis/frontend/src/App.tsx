import React, { useState, useEffect } from 'react';
import { Sidebar, SectionType } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { TalkToJarvis } from './pages/TalkToJarvis';
import { DesktopControl } from './pages/DesktopControl';
import { ContentStudio } from './pages/ContentStudio';
import { ReelsFactory } from './pages/ReelsFactory';
import { ShortsFactory } from './pages/ShortsFactory';
import { VideoEditor } from './pages/VideoEditor';
import { YouTubeManager } from './pages/YouTubeManager';
import { InstagramManager } from './pages/InstagramManager';
import { FileManager } from './pages/FileManager';
import { ViralResearch } from './pages/ViralResearch';
import { MemoryViewer } from './pages/MemoryViewer';
import { SettingsPage } from './pages/SettingsPage';
import { MobileRemote } from './pages/MobileRemote';
import { useJarvisWebSocket } from './services/websocket';
import { ClipItem, api } from './services/api';
import {
  Home as HomeIcon,
  Smartphone,
  Mic,
  PlaySquare,
  Menu
} from 'lucide-react';

export const App: React.FC = () => {
  const { state: wsState, isConnected, sendAction } = useJarvisWebSocket();
  const [activeSection, setActiveSection] = useState<SectionType>('home');
  const [clips, setClips] = useState<ClipItem[]>([]);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [mobileUrl, setMobileUrl] = useState<string>('');

  const fetchClips = async () => {
    try {
      const data = await api.getClips();
      setClips(data);
    } catch (e) {
      console.error('Failed to load clips:', e);
    }
  };

  useEffect(() => {
    fetchClips();
    api.getMobileInfo()
      .then(info => {
        if (info && info.mobile_url) {
          setMobileUrl(info.mobile_url);
        }
      })
      .catch(e => console.warn('Could not load mobile info:', e));
  }, []);

  const handleEmergencyStop = () => {
    sendAction('EMERGENCY_STOP');
    api.triggerEmergencyStop();
  };

  const handleResetEmergency = () => {
    api.resetEmergency();
  };

  const handleToggleMic = (active: boolean) => {
    sendAction('TOGGLE_MIC', { active });
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* Futuristic Sidebar HUD (Desktop Persistent + Mobile Drawer) */}
      <Sidebar
        activeSection={activeSection}
        onSelectSection={setActiveSection}
        clipsCount={clips.length}
        isMobileOpen={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
        mobileUrl={mobileUrl}
      />

      {/* Main Workspace Frame */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Telemetry Header */}
        <Navbar
          state={wsState}
          onEmergencyStop={handleEmergencyStop}
          onResetEmergency={handleResetEmergency}
          onToggleMic={handleToggleMic}
          onToggleMobileMenu={() => setIsMobileMenuOpen(true)}
          mobileUrl={mobileUrl}
        />

        {/* Dynamic Section Content View */}
        <main className={`flex-1 ${
          activeSection === 'editor'
            ? 'p-0 overflow-hidden flex flex-col pb-16 md:pb-0'
            : 'overflow-y-auto p-4 sm:p-6 pb-20 md:pb-6'
        }`}>
          {activeSection === 'home' && (
            <Home
              state={wsState}
              clips={clips}
              onNavigate={setActiveSection}
              onRefreshClips={fetchClips}
            />
          )}

          {activeSection === 'mobile' && (
            <MobileRemote
              state={wsState}
              onNavigate={setActiveSection}
            />
          )}

          {activeSection === 'talk' && <TalkToJarvis />}

          {activeSection === 'desktop' && <DesktopControl />}

          {activeSection === 'studio' && (
            <ContentStudio clips={clips} onRefreshClips={fetchClips} />
          )}

          {activeSection === 'reels' && (
            <ReelsFactory clips={clips} onRefreshClips={fetchClips} />
          )}

          {activeSection === 'shorts' && (
            <ShortsFactory clips={clips} onRefreshClips={fetchClips} />
          )}

          {activeSection === 'editor' && (
            <VideoEditor clips={clips} onRefreshClips={fetchClips} />
          )}

          {activeSection === 'youtube' && (
            <YouTubeManager clips={clips} onRefreshClips={fetchClips} />
          )}

          {activeSection === 'instagram' && (
            <InstagramManager clips={clips} onRefreshClips={fetchClips} />
          )}

          {activeSection === 'research' && <ViralResearch />}

          {activeSection === 'files' && (
            <FileManager
              onSelectVideoForClipping={(path) => {
                setActiveSection('studio');
              }}
            />
          )}

          {activeSection === 'memory' && <MemoryViewer />}

          {activeSection === 'settings' && <SettingsPage state={wsState} />}
        </main>

        {/* Sleek Mobile Bottom Navigation Bar (Visible on mobile screens) */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-slate-950/95 backdrop-blur-2xl border-t border-cyan-500/25 z-40 flex items-center justify-around px-2 select-none shadow-2xl">
          <button
            onClick={() => setActiveSection('home')}
            className={`flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition-all ${
              activeSection === 'home'
                ? 'text-cyan-400 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <HomeIcon className="w-5 h-5" />
            <span className="text-[10px] font-mono">Home</span>
          </button>

          <button
            onClick={() => setActiveSection('mobile')}
            className={`flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition-all ${
              activeSection === 'mobile'
                ? 'text-cyan-400 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Smartphone className="w-5 h-5" />
            <span className="text-[10px] font-mono">Remote</span>
          </button>

          <button
            onClick={() => setActiveSection('talk')}
            className={`flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition-all ${
              activeSection === 'talk'
                ? 'text-cyan-400 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Mic className="w-5 h-5" />
            <span className="text-[10px] font-mono">Siri Talk</span>
          </button>

          <button
            onClick={() => setActiveSection('shorts')}
            className={`flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition-all ${
              activeSection === 'shorts'
                ? 'text-cyan-400 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <PlaySquare className="w-5 h-5" />
            <span className="text-[10px] font-mono">Shorts</span>
          </button>

          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="flex flex-col items-center gap-1 py-1 px-3 rounded-xl text-slate-400 hover:text-slate-200"
          >
            <Menu className="w-5 h-5 text-cyan-400" />
            <span className="text-[10px] font-mono">Menu</span>
          </button>
        </nav>
      </div>
    </div>
  );
};

export default App;
