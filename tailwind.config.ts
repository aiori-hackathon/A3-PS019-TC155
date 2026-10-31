import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: { extend: { colors: { ink: "#090B12", panel: "#10131D", raised: "#171B27", violet: "#9B83E8", muted: "#A1A8B8", line: "#292E3B" }, fontFamily: { sans: ["Arial", "sans-serif"], mono: ["ui-monospace", "monospace"] } } },
  plugins: []
};
export default config;
