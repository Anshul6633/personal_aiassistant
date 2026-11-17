import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Mic,
  MicOff,
  Cpu,
  Database,
  BatteryCharging,
  Battery,
  Radio,
  RefreshCw,
  Menu,
  Smartphone,
  Copy,
  Check,
  X,
  QrCode,
  Globe,
  Wifi,
  Play,
  Square,
  ExternalLink,
  Loader2
} from 'lucide-react';
import { JarvisState, api, TunnelStatus } from '../services/api';

interface NavbarProps {
  state: JarvisState | null;
  onEmergencyStop: () => void;
  onResetEmergency: () => void;
  onToggleMic: (active: boolean) => void;
  onToggleMobileMenu?: () => void;
  mobileUrl?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  state,
  onEmergencyStop,
  onResetEmergency,
  onToggleMic,
  onToggleMobileMenu,
  mobileUrl
}) => {
  const [showQrModal, setShowQrModal] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'public' | 'lan'>('public');
  const [tunnelStatus, setTunnelStatus] = useState<TunnelStatus | null>(null);
  const [isTunnelLoading, setIsTunnelLoading] = useState(false);

  const isError = state?.status === 'ERROR';
  const cpuPercent = state?.metrics?.cpu_percent ?? 0;
  const ramPercent = state?.metrics?.ram_percent ?? 0;
  const battery = state?.metrics?.battery_percent;
  const isPlugged = state?.metrics?.is_plugged;
  const micActive = state?.mic_active ?? false;

  const refreshTunnel = async () => {
    try {
      const ts = await api.getTunnelStatus();
      setTunnelStatus(ts);
    } catch (e) {
      console.warn('Failed to fetch tunnel status:', e);
    }
  };

  useEffect(() => {
    if (showQrModal) {
      refreshTunnel();
    }
  }, [showQrModal]);

  const handleStartTunnel = async () => {
    setIsTunnelLoading(true);
    try {
      const ts = await api.startTunnel();
      setTunnelStatus(ts);
    } catch (e) {
      console.error('Failed to start tunnel:', e);
    } finally {
      setIsTunnelLoading(false);
    }
  };

  const handleStopTunnel = async () => {
    setIsTunnelLoading(true);
    try {
      const ts = await api.stopTunnel();
      setTunnelStatus(ts);
    } catch (e) {
      console.error('Failed to stop tunnel:', e);
    } finally {
      setIsTunnelLoading(false);
    }
  };

  const localLanUrl = tunnelStatus?.lan_url || mobileUrl || `http://${window.location.hostname}:8000`;
  const publicLiveUrl = tunnelStatus?.public_url || null;
  const isTunnelActive = tunnelStatus?.is_active && publicLiveUrl !== null;

  const displayedUrl = activeTab === 'public' && isTunnelActive ? publicLiveUrl : localLanUrl;
  const qrCodeImg = `https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(displayedUrl)}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(displayedUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      <header className="h-16 px-4 md:px-6 bg-slate-950/80 backdrop-blur-xl border-b border-cyan-500/20 flex items-center justify-between select-none z-20">
        {/* Left: Mobile Hamburger & System Status */}
        <div className="flex items-center gap-3 md:gap-4">
          {onToggleMobileMenu && (
            <button
              onClick={onToggleMobileMenu}
              className="md:hidden p-2 rounded-lg text-slate-300 hover:text-white bg-slate-900 border border-slate-800 active:scale-95 transition-transform"
              aria-label="Open mobile navigation"
            >
              <Menu className="w-5 h-5 text-cyan-400" />
            </button>
          )}

          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isError ? 'bg-red-400' : 'bg-cyan-400'
              }`} />
              <span className={`relative inline-flex rounded-full h-3 w-3 ${
                isError ? 'bg-red-500' : 'bg-cyan-500'
              }`} />
            </span>
            <span className="font-mono text-xs uppercase tracking-wider text-cyan-300 truncate max-w-[120px] sm:max-w-[180px] md:max-w-none">
              {state?.status_message || 'SYSTEMS NOMINAL'}
            </span>
          </div>

          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-md bg-slate-900 border border-cyan-500/30 text-xs font-mono text-slate-300">
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
            <span>CORE:</span>
            <span className="text-cyan-300 font-bold">{state?.active_model || 'qwen2.5:1.5b'}</span>
          </div>
        </div>

        {/* Center: Live Hardware Telemetry */}
        <div className="hidden md:flex items-center gap-6 font-mono text-xs text-slate-300">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>CPU</span>
            <span className="font-bold text-cyan-300">{cpuPercent}%</span>
          </div>

          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-400" />
            <span>RAM</span>
            <span className="font-bold text-blue-300">{ramPercent}%</span>
          </div>

          {battery !== undefined && battery !== null && (
            <div className="flex items-center gap-1.5">
              {isPlugged ? (
                <BatteryCharging className="w-4 h-4 text-emerald-400" />
              ) : (
                <Battery className="w-4 h-4 text-yellow-400" />
              )}
              <span className="font-bold text-slate-200">{battery}%</span>
            </div>
          )}
        </div>

        {/* Right: Phone Connect & Controls */}
        <div className="flex items-center gap-2 md:gap-3">
          {/* Mobile Phone Link / QR Trigger Button */}
          <button
            onClick={() => setShowQrModal(true)}
            className="px-2.5 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-xs font-mono flex items-center gap-1.5 cursor-pointer transition-all active:scale-95"
            title="Connect Mobile Phone"
          >
            <Smartphone className="w-4 h-4 text-cyan-400" />
            <span className="hidden sm:inline">PHONE LINK</span>
          </button>

          {/* Mic Toggle Button */}
          <button
            onClick={() => onToggleMic(!micActive)}
            className={`px-2.5 md:px-3 py-1.5 rounded-lg flex items-center gap-1.5 md:gap-2 text-xs font-medium cursor-pointer transition-all ${
              micActive
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500 shadow-cyan-sm'
                : 'bg-slate-900 text-slate-400 border border-slate-700 hover:text-slate-200'
            }`}
          >
            {micActive ? <Mic className="w-4 h-4 text-cyan-400 animate-pulse" /> : <MicOff className="w-4 h-4" />}
            <span className="hidden sm:inline">{micActive ? 'LISTENING' : 'MIC MUTED'}</span>
          </button>

          {/* Emergency Stop / Reset Button */}
          {isError ? (
            <button
              onClick={onResetEmergency}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg cursor-pointer transition-transform active:scale-95"
            >
              <RefreshCw className="w-4 h-4" />
              <span className="hidden sm:inline">RESET</span>
            </button>
          ) : (
            <button
              onClick={onEmergencyStop}
              className="px-3 py-1.5 rounded-lg bg-red-600/90 hover:bg-red-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-red-900/40 border border-red-400/50 cursor-pointer transition-transform active:scale-95"
            >
              <ShieldAlert className="w-4 h-4" />
              <span className="hidden sm:inline">STOP</span>
            </button>
          )}
        </div>
      </header>

      {/* Mobile QR & Remote Connection Modal */}
      {showQrModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="relative w-full max-w-md rounded-2xl bg-slate-900 border border-cyan-500/30 p-6 shadow-2xl shadow-cyan-500/10">
            <button
              onClick={() => setShowQrModal(false)}
              className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2.5 mb-3 text-cyan-300">
              <Smartphone className="w-6 h-6 text-cyan-400" />
              <h3 className="font-bold text-base tracking-wide">Connect Mobile Phone</h3>
            </div>

            {/* Connection Mode Tabs */}
            <div className="flex items-center gap-2 p-1 bg-slate-950 rounded-xl border border-slate-800 mb-4">
              <button
                onClick={() => setActiveTab('public')}
                className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-mono font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                  activeTab === 'public'
                    ? 'bg-cyan-500 text-slate-950 shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Globe className="w-3.5 h-3.5" />
                <span>Worldwide Public (HTTPS)</span>
              </button>
              <button
                onClick={() => setActiveTab('lan')}
                className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-mono font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                  activeTab === 'lan'
                    ? 'bg-cyan-500 text-slate-950 shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Wifi className="w-3.5 h-3.5" />
                <span>Local Wi-Fi (LAN)</span>
              </button>
            </div>

            {/* Public Tunnel Control Card */}
            {activeTab === 'public' && (
              <div className="mb-4 p-3 rounded-xl bg-slate-950 border border-cyan-500/20">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${isTunnelActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
                    <span className="text-xs font-mono text-slate-300">
                      Tunnel: <strong className={isTunnelActive ? 'text-emerald-400' : 'text-slate-400'}>{isTunnelActive ? 'LIVE ONLINE' : 'STOPPED'}</strong>
                    </span>
                  </div>
                  <button
                    onClick={isTunnelActive ? handleStopTunnel : handleStartTunnel}
                    disabled={isTunnelLoading}
                    className={`px-3 py-1 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 cursor-pointer transition-all ${
                      isTunnelActive
                        ? 'bg-red-500/20 text-red-300 border border-red-500/40 hover:bg-red-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30'
                    }`}
                  >
                    {isTunnelLoading ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : isTunnelActive ? (
                      <Square className="w-3.5 h-3.5" />
                    ) : (
                      <Play className="w-3.5 h-3.5" />
                    )}
                    <span>{isTunnelActive ? 'Stop Tunnel' : 'Start Live HTTPS'}</span>
                  </button>
                </div>
                <p className="text-[11px] text-slate-400 leading-snug">
                  {isTunnelActive
                    ? 'Secure worldwide HTTPS endpoint active. Control JARVIS from cellular 4G/5G anywhere on earth!'
                    : 'Click "Start Live HTTPS" to create a public link accessible from anywhere outside your house.'}
                </p>
              </div>
            )}

            {/* QR Code Container */}
            <div className="flex justify-center mb-4 p-3 bg-white rounded-xl shadow-inner">
              <img
                src={qrCodeImg}
                alt="JARVIS Mobile QR Code"
                className="w-44 h-44 rounded-lg object-contain"
              />
            </div>

            {/* URL Box with Copy Button */}
            <div className="flex items-center gap-2 p-2 rounded-xl bg-slate-950 border border-slate-700 mb-4">
              <span className="text-xs font-mono text-cyan-300 truncate flex-1 px-1">
                {displayedUrl}
              </span>
              <button
                onClick={handleCopy}
                className="px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-all active:scale-95 cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>

            <div className="text-[11px] font-mono text-slate-400 bg-slate-950/50 p-2.5 rounded-lg border border-slate-800 flex items-start gap-2">
              <span className="text-cyan-400 font-bold">INFO:</span>
              <span>
                {activeTab === 'public'
                  ? 'Works on cellular phone networks (4G/5G) with full voice Siri control and Autopilot.'
                  : 'Works on the same home Wi-Fi network with ultra-low latency sub-50ms controls.'}
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
