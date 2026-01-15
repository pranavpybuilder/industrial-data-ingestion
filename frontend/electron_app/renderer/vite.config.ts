import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      pages: path.resolve(__dirname, "src/pages"),
      components: path.resolve(__dirname, "src/components"),
      services: path.resolve(__dirname, "src/services"),
      state: path.resolve(__dirname, "src/state"),
      styles: path.resolve(__dirname, "src/styles"),
      app: path.resolve(__dirname, "src/app"),
      assets: path.resolve(__dirname, "src/assets"), // ✅ THIS LINE
    },
  },

  server: {
    hmr: {
      overlay: false,
    },
  },
});