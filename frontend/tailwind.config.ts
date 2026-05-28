import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f7f8fb",
        foreground: "#1d2433",
        panel: "#ffffff",
        muted: "#667085",
        border: "#d9dee8",
        primary: "#2563eb",
        accent: "#0f766e",
        warning: "#b45309"
      },
      boxShadow: {
        soft: "0 10px 30px rgba(29, 36, 51, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
