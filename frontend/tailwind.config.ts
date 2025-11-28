import type { Config } from "tailwindcss";

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Lora', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        // IFP Primary Colors
        'cream': {
          DEFAULT: '#FCFBE8',
          50: '#FEFDF5',
          100: '#FCFBE8',
          200: '#F9F7D9',
        },
        'charcoal': {
          DEFAULT: '#373737',
          50: '#f5f5f5',
          100: '#e8e8e8',
          200: '#d4d4d4',
          300: '#a3a3a3',
          400: '#737373',
          500: '#555555',
          600: '#454545',
          700: '#373737',
          800: '#2a2a2a',
          900: '#1a1a1a',
        },
        // IFP Accent Colors
        'ifp-purple': {
          light: '#E8D5F0',
          DEFAULT: '#b17ada',
          dark: '#8B5CB8',
        },
        'ifp-orange': {
          light: '#FFE4D4',
          DEFAULT: '#FF9762',
          dark: '#E07840',
        },
        // Status colors
        'status-success': {
          light: '#d1fae5',
          DEFAULT: '#047857',
          dark: '#065f46',
        },
        'status-warning': {
          light: '#FFE4D4',
          DEFAULT: '#FF9762',
          dark: '#E07840',
        },
        'status-error': {
          light: '#fee2e2',
          DEFAULT: '#dc2626',
          dark: '#991b1b',
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
