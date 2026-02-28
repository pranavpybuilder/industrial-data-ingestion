import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// ─────────────────────────────────────────────────────────────────────────────
// Vite config for Offline Industrial Intelligence — Electron renderer
//
// CRITICAL:
//   base: './'  →  Electron loads via file:// protocol, NOT http://
//                  Using '/' would break all asset paths after NSIS install
// ─────────────────────────────────────────────────────────────────────────────
export default defineConfig({
  plugins: [react()],
  base: "./", // ← MUST be './' — Electron loads via file:// not http://
  build: {
    outDir: "dist",
    emptyOutDir: true,
    assetsDir: "assets",
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          charts: ["recharts"],
        },
      },
    },
  },
  resolve: {
    alias: {
      pages: path.resolve(__dirname, "src/pages"),
      components: path.resolve(__dirname, "src/components"),
      services: path.resolve(__dirname, "src/services"),
      state: path.resolve(__dirname, "src/state"),
      styles: path.resolve(__dirname, "src/styles"),
      app: path.resolve(__dirname, "src/app"),
      assets: path.resolve(__dirname, "src/assets"),
    },
  },
  server: {
    hmr: {
      overlay: false,
    },
  },
});