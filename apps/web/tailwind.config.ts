import type { Config } from 'tailwindcss'
import animate from 'tailwindcss-animate'

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          base: '#1c1611',
          raised: '#261d15',
          deep: '#15110c',
          border: '#352616',
        },
        'text-primary': '#f3e9cf',
        accent: {
          saffron: '#d4924a',
          madder: '#8b3a1f',
          warning: '#f3a86e',
          critical: '#fca5a5',
        },
      },
      fontFamily: {
        serif: ['var(--font-serif)', 'Georgia', 'serif'],
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      backgroundImage: {
        'gradient-strip':
          'linear-gradient(90deg, #8b3a1f 0%, #d4924a 55%, #f3e9cf 100%)',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.96)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
      },
      animation: {
        shimmer: 'shimmer 2s linear infinite',
        'fade-in': 'fade-in 180ms ease-out',
        'slide-up': 'slide-up 160ms ease-out',
        'scale-in': 'scale-in 180ms ease-out',
      },
      transitionDuration: {
        '100': '100ms',
        '120': '120ms',
        '140': '140ms',
        '160': '160ms',
        '180': '180ms',
        '220': '220ms',
      },
    },
  },
  plugins: [animate],
}

export default config
