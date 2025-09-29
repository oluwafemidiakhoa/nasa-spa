/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Space weather theme colors
        space: {
          50: '#f0f4ff',
          100: '#e0e9ff',
          200: '#c7d4fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        aurora: {
          green: '#00ff80',
          blue: '#0080ff',
          purple: '#8000ff',
          pink: '#ff0080',
        },
        solar: {
          yellow: '#ffff00',
          orange: '#ff8000',
          red: '#ff0000',
        },
        alert: {
          low: '#22c55e',
          moderate: '#eab308',
          high: '#f97316',
          severe: '#ef4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'aurora': 'aurora 8s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        aurora: {
          '0%, 100%': { opacity: '0.3', transform: 'rotate(0deg) scale(1)' },
          '50%': { opacity: '0.8', transform: 'rotate(180deg) scale(1.1)' },
        },
      },
      backgroundImage: {
        'space-gradient': 'linear-gradient(135deg, #000428 0%, #004e92 100%)',
        'aurora-gradient': 'linear-gradient(45deg, #00ff80, #0080ff, #8000ff)',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}