/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#04060c", 900: "#070b14", 800: "#0b111e", 700: "#141c2e", 600: "#1f2a44" },
        line: { DEFAULT: "#1c2740" },
        up: "#34d399",
        down: "#f87171",
        accent: "#22d3ee",
        violet: "#8b5cf6",
        amber: "#fbbf24",
        muted: "#7d8aa5",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        glow: "0 0 18px -2px rgba(34, 211, 238, 0.35)",
        "glow-sm": "0 0 10px -2px rgba(34, 211, 238, 0.25)",
        "glow-up": "0 0 14px -2px rgba(52, 211, 153, 0.35)",
        "glow-down": "0 0 14px -2px rgba(248, 113, 113, 0.35)",
        "glow-amber": "0 0 14px -2px rgba(251, 191, 36, 0.35)",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "pulse-dot": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.45", transform: "scale(0.8)" },
        },
        scanline: {
          from: { transform: "translateY(-100%)" },
          to: { transform: "translateY(100%)" },
        },
        "grid-drift": {
          from: { backgroundPosition: "0 0" },
          to: { backgroundPosition: "48px 48px" },
        },
        shimmer: {
          from: { backgroundPosition: "-200% 0" },
          to: { backgroundPosition: "200% 0" },
        },
        blink: { "0%, 100%": { opacity: "1" }, "50%": { opacity: "0.2" } },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        "fade-in": "fade-in 0.6s ease-out both",
        "pulse-dot": "pulse-dot 1.2s ease-in-out infinite",
        scanline: "scanline 3.5s linear infinite",
        "grid-drift": "grid-drift 6s linear infinite",
        shimmer: "shimmer 2.5s linear infinite",
        blink: "blink 1.1s steps(2) infinite",
      },
    },
  },
  plugins: [],
};
