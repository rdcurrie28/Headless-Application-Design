import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const target = env.API_TARGET || "http://localhost:8000";
  const headers = env.API_KEY ? { "X-API-Key": env.API_KEY } : undefined;

  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        "/v1": { target, changeOrigin: true, headers },
        "/readyz": { target, changeOrigin: true },
      },
    },
  };
});
