import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import packageJson from "./package.json";

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  define: {
    __APP_VERSION__: JSON.stringify(packageJson.version),
  },
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
      "/docs": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
      "/openapi.json": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
      "/version/core": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
    },
  },
});
