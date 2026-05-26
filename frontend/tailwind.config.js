/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        noc: {
          bg: "#0B0F19",
          card: "#151D30",
          cardLight: "#1F2B48",
          border: "#202E4E",
          text: "#F3F4F6",
          textMuted: "#9CA3AF",
          primary: "#6366F1",
          primaryHover: "#4F46E5",
          accent: "#06B6D4",
          success: "#10B981",
          warning: "#F59E0B",
          danger: "#EF4444",
          offline: "#6B7280",
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'glass-hover': '0 8px 32px 0 rgba(99, 102, 241, 0.15)',
      }
    },
  },
  plugins: [],
}
