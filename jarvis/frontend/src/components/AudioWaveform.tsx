import React from 'react';
import { motion } from 'framer-motion';

interface AudioWaveformProps {
  micLevel?: number;
  isActive?: boolean;
  barsCount?: number;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({
  micLevel = 0,
  isActive = false,
  barsCount = 28
}) => {
  return (
    <div className="flex items-center justify-center gap-[3px] h-12 px-4 py-2 bg-slate-950/60 rounded-xl border border-cyan-500/20 backdrop-blur-md">
      {[...Array(barsCount)].map((_, i) => {
        // Compute pseudo-spectrum curve centered in the middle
        const distanceCenter = Math.abs(i - barsCount / 2) / (barsCount / 2);
        const factor = Math.cos(distanceCenter * Math.PI * 0.45);
        const dynamicHeight = isActive
          ? Math.max(4, Math.min(42, (micLevel * 45 + Math.random() * 12) * factor))
          : 4;

        return (
          <motion.div
            key={i}
            animate={{ height: dynamicHeight }}
            transition={{ type: 'spring', stiffness: 350, damping: 25 }}
            className="w-1 rounded-full transition-colors duration-150"
            style={{
              background: isActive
                ? `linear-gradient(to top, #00f2fe, #4facfe)`
                : 'rgba(100, 116, 139, 0.4)',
              boxShadow: isActive ? '0 0 6px rgba(0, 242, 254, 0.5)' : 'none'
            }}
          />
        );
      })}
    </div>
  );
};

