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
        canvas: '#090D16',
        surface: {
          1: '#0F172A',
          2: '#1E293B',
          3: '#334155',
        },
        brand: {
          cyan: '#06B6D4',
          indigo: '#6366F1',
          blue: '#3B82F6',
        },
        status: {
          success: '#10B981',
          warning: '#F59E0B',
          danger: '#EF4444',
          info: '#0EA5E9',
        },
        category: {
          technical: '#3B82F6',
          gap: '#EC4899',
          behavioral: '#10B981',
          culture: '#8B5CF6',
          situational: '#F59E0B',
        },
        text: {
          primary: '#F8FAFC',
          secondary: '#94A3B8',
          muted: '#64748B',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
