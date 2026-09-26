import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#0a0e17",
        panel: "#111827",
        border: "#1f2937",
        accent: "#3b82f6",
        profit: "#10b981",
        loss: "#ef4444",
      },
    },
  },
  plugins: [],
};
export default config;
