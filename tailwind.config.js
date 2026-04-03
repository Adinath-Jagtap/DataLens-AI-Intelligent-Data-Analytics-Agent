/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Syne'", "sans-serif"],
        body: ["'DM Sans'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      colors: {
        brand: {
          50:  "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          800: "#075985",
          900: "#0c4a6e",
        },
        surface: {
          0:   "#0a0f1a",
          1:   "#0f1726",
          2:   "#141f33",
          3:   "#1a2740",
          4:   "#1f304d",
        },
        accent: {
          cyan:   "#22d3ee",
          violet: "#a78bfa",
          amber:  "#fbbf24",
          green:  "#34d399",
          coral:  "#fb7185",
        }
      },
      animation: {
        "fade-up":    "fadeUp 0.5s ease forwards",
        "fade-in":    "fadeIn 0.4s ease forwards",
        "pulse-slow": "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
        "spin-slow":  "spin 8s linear infinite",
        "shimmer":    "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeUp:   { from: { opacity: 0, transform: "translateY(16px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        fadeIn:   { from: { opacity: 0 }, to: { opacity: 1 } },
        shimmer:  { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
      },
      backdropBlur: { xs: "2px" },
    },
  },
  plugins: [],
};
