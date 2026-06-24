import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        surface: "var(--surface)",
        foreground: "var(--foreground)",
        muted: "var(--muted)",
        border: "var(--border)",
        accent: "var(--accent)",
        "accent-hover": "var(--accent-hover)",
        warning: "var(--warning)",
        success: "var(--success)",
        danger: "var(--danger)",
      },
      boxShadow: {
        ink: "4px 4px 0 var(--border)",
        "ink-sm": "2px 2px 0 var(--border)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Arial", "sans-serif"],
        display: ["var(--font-display)", "Arial Black", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
