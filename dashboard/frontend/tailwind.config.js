/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0F0F13",
        card: "#1A1A24",
        "card-hover": "#22223A",
        border: "#2A2A3A",
        accent: "#7C3AED",
        "accent-light": "#8B5CF6",
        "accent-dim": "#4C1D95",
        muted: "#6B7280",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};
