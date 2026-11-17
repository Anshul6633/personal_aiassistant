/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        jarvis: {
          dark: '#050811',
          panel: '#0a101f',
          card: '#0f172a',
          cyan: '#00f2fe',
          blue: '#4facfe',
          neon: '#00ffff',
          gold: '#fbbf24',
          alert: '#ef4444',
          success: '#10b981',
          border: 'rgba(0, 242, 254, 0.2)',
          glow: 'rgba(0, 242, 254, 0.35)',
        }
      },
      boxShadow: {
        'cyan-glow': '0 0 25px -5px rgba(0, 242, 254, 0.5)',
        'cyan-sm': '0 0 10px rgba(0, 242, 254, 0.3)',
        'blue-glow': '0 0 30px -5px rgba(79, 172, 254, 0.6)',
        'gold-glow': '0 0 20px rgba(251, 191, 36, 0.4)',
      },
      animation: {
        'spin-slow': 'spin 12s linear infinite',
        'spin-reverse': 'spin-reverse 15s linear infinite',
        'pulse-glow': 'pulseGlow 2.5s ease-in-out infinite',
        'radar': 'radar 3s linear infinite',
      },
      keyframes: {
        'spin-reverse': {
          from: { transform: 'rotate(360deg)' },
          to: { transform: 'rotate(0deg)' }
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0.9', transform: 'scale(1.05)' },
        },
        radar: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        }
      }
    },
  },
  plugins: [],
}
