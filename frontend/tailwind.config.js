/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: "#020617", // slate-950
          800: "#0f172a", // slate-900
          700: "#1e293b", // slate-800
          600: "#334155", // slate-700
          500: "#475569"  // slate-600
        },
        brand: {
          crimson: "#ef4444",
          sunset: "#f97316",
          gold: "#eab308",
          sky: "#3b82f6"
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
        border: "inset 0 1px 0 0 rgba(255, 255, 255, 0.05)"
      }
    },
  },
  plugins: [],
}
