/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#070a0f", 900: "#0a0e14", 800: "#11161f", 700: "#1a2230", 600: "#27324a" },
        line: { DEFAULT: "#1f2937" },
        up: "#22c55e",
        down: "#ef4444",
        accent: "#38bdf8",
        amber: "#f59e0b",
        muted: "#8b98ad",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
