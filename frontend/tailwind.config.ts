import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Government-appropriate primary colors
        'gov-navy': {
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          300: '#9fb3c8',
          400: '#829ab1',
          500: '#627d98',
          600: '#486581',
          700: '#334e68',
          800: '#243b53',
          900: '#1e3a5f', // Primary navy
          950: '#102a43',
        },
        'gov-slate': {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155', // Secondary slate
          800: '#1e293b',
          900: '#0f172a',
        },
        // AI Category colors (professional)
        'ai-blue': {
          light: '#dbeafe',
          DEFAULT: '#3b82f6',
          dark: '#1e40af',
        },
        'ai-teal': {
          light: '#ccfbf1',
          DEFAULT: '#0891b2',
          dark: '#155e75',
        },
        'ai-indigo': {
          light: '#e0e7ff',
          DEFAULT: '#6366f1',
          dark: '#4338ca',
        },
        // Status colors
        'status-success': {
          light: '#d1fae5',
          DEFAULT: '#047857',
          dark: '#065f46',
        },
        'status-warning': {
          light: '#fef3c7',
          DEFAULT: '#d97706',
          dark: '#92400e',
        },
        'status-error': {
          light: '#fee2e2',
          DEFAULT: '#dc2626',
          dark: '#991b1b',
        },
      },
    },
  },
  plugins: [typography],
} satisfies Config;
