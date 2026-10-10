/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1A6B5A',
          dark: '#135043',
          light: '#248671',
        },
        accent: {
          DEFAULT: '#4ECBA0',
          dark: '#3AB58B',
          light: '#72D8B3',
        },
        warning: '#F5A623',
        critical: '#E53E3E',
        background: '#F7FAF9',
        surface: '#FFFFFF',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
