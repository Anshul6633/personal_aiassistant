import React from 'react';
import { motion } from 'framer-motion';

interface ArcReactorProps {
  status?: string;
  micLevel?: number;
  size?: number;
}

export const ArcReactor: React.FC<ArcReactorProps> = ({
  status = 'IDLE',
  micLevel = 0,
  size = 280
}) => {
  // Determine color scheme based on assistant state
  const isError = status === 'ERROR';
  const isEditing = status === 'EDITING' || status === 'PLANNING';
  const isThinking = status === 'THINKING';
  const isSpeaking = status === 'SPEAKING';

  let primaryColor = '#00f2fe';
  let secondaryColor = '#4facfe';
  let glowColor = 'rgba(0, 242, 254, 0.6)';

  if (isError) {
    primaryColor = '#ef4444';
    secondaryColor = '#f87171';
    glowColor = 'rgba(239, 68, 68, 0.7)';
  } else if (isEditing) {
    primaryColor = '#fbbf24';
    secondaryColor = '#f59e0b';
    glowColor = 'rgba(251, 191, 36, 0.7)';
  } else if (isThinking) {
    primaryColor = '#818cf8';
    secondaryColor = '#6366f1';
    glowColor = 'rgba(129, 140, 248, 0.7)';
  } else if (isSpeaking) {
    primaryColor = '#10b981';
    secondaryColor = '#34d399';
    glowColor = 'rgba(16, 185, 129, 0.7)';
  }

  // Energy pulse scaling driven by audio level & activity
  const pulseScale = 1.0 + (micLevel * 0.25) + (isSpeaking ? 0.08 : 0);

  return (
    <div 
      className="relative flex items-center justify-center select-none"
      style={{ width: size, height: size }}
    >
      {/* Outer Glow Halo */}
      <motion.div
        animate={{
          scale: [1, pulseScale, 1],
          opacity: [0.5, 0.85, 0.5],
        }}
        transition={{
          duration: isThinking ? 1.0 : 2.5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute inset-0 rounded-full blur-2xl pointer-events-none"
        style={{ background: glowColor }}
      />

      {/* Outermost Segmented Armor Ring */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
        className="absolute inset-2 rounded-full border border-cyan-500/30"
        style={{
          borderStyle: 'dashed',
          borderColor: primaryColor,
          opacity: 0.4
        }}
      />

      {/* Outer Rotating Gear Ring */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
        className="absolute inset-6 rounded-full border-2"
        style={{
          borderColor: `${primaryColor}40`,
          borderTopColor: primaryColor,
          borderRightColor: secondaryColor,
        }}
      />

      {/* Counter-Rotating Concentric Ring */}
      <motion.div
        animate={{ rotate: -360 }}
        transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
        className="absolute inset-12 rounded-full border-2"
        style={{
          borderColor: `${secondaryColor}30`,
          borderBottomColor: primaryColor,
          borderLeftColor: secondaryColor,
        }}
      />

      {/* 10 Power Core Triangular Copper Filaments (Iron Man Mark II / Arc Reactor) */}
      <div className="absolute inset-16 flex items-center justify-center">
        {[...Array(10)].map((_, i) => (
          <div
            key={i}
            className="absolute w-3 h-10 rounded-sm"
            style={{
              transform: `rotate(${i * 36}deg) translateY(-54px)`,
              background: `linear-gradient(to bottom, ${primaryColor}, transparent)`,
              boxShadow: `0 0 8px ${glowColor}`,
              opacity: 0.75 + (micLevel * 0.25)
            }}
          />
        ))}
      </div>

      {/* Inner Metallic Housing Ring */}
      <div 
        className="absolute inset-20 rounded-full border-2 backdrop-blur-md flex items-center justify-center"
        style={{
          borderColor: primaryColor,
          background: 'radial-gradient(circle, rgba(15,23,42,0.9) 0%, rgba(5,8,17,0.95) 100%)',
          boxShadow: `inset 0 0 20px ${glowColor}, 0 0 15px ${glowColor}`
        }}
      >
        {/* Core Pulsing Crystal Eye */}
        <motion.div
          animate={{
            scale: [0.95, 1.1 + (micLevel * 0.4), 0.95],
            boxShadow: [
              `0 0 15px ${glowColor}`,
              `0 0 35px ${glowColor}`,
              `0 0 15px ${glowColor}`
            ]
          }}
          transition={{
            duration: isSpeaking ? 0.6 : 1.8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="w-16 h-16 rounded-full flex flex-col items-center justify-center"
          style={{
            background: `radial-gradient(circle, #ffffff 10%, ${primaryColor} 60%, ${secondaryColor} 100%)`,
          }}
        >
          <div className="text-[10px] font-black tracking-widest text-slate-950 uppercase">
            J.A.R.V.I.S
          </div>
        </motion.div>
      </div>

      {/* Arc Reactor State Label Badge */}
      <div className="absolute -bottom-6 px-4 py-1 rounded-full bg-slate-900/90 border border-cyan-500/40 text-xs font-mono tracking-wider text-cyan-300 shadow-cyan-sm">
        {status}
      </div>
    </div>
  );
};

