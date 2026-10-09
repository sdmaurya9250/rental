import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiTarget = env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8787';

  return {
    plugins: [react(), tailwindcss()],
    ssgOptions: {
      includedRoutes: (paths) => paths.filter((path) => [
        '/', '/privacy-policy', '/terms-and-conditions', '/refund-policy', '/contact', '/help', '/404',
      ].includes(path)),
    },
    server: {
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
        '/auth': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  };
});
