/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0a0a0f',
          surface: '#13131a',
          card: '#1a1a24',
          border: '#2a2a38',
          text: '#f0f0f5',
          muted: '#a0a0b0',
        },
        neon: {
          blue: '#00d4ff',
          purple: '#a855f7',
          pink: '#ff10f0',
          cyan: '#00fff9',
          green: '#00ff94',
          orange: '#ff6b35',
        },
        glow: {
          blue: '#3b82f6',
          purple: '#8b5cf6',
          pink: '#ec4899',
          cyan: '#06b6d4',
          green: '#10b981',
          orange: '#f97316',
        },
      },
      textColor: {
        DEFAULT: '#f0f0f5',
      },
      boxShadow: {
        'neon-blue': '0 0 20px rgba(0, 212, 255, 0.5)',
        'neon-purple': '0 0 20px rgba(168, 85, 247, 0.5)',
        'neon-pink': '0 0 20px rgba(255, 16, 240, 0.5)',
        'neon-cyan': '0 0 20px rgba(0, 255, 249, 0.5)',
      },
    },
  },
  plugins: [],
}

