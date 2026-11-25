import { cpSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'copy-game-assets',
      apply: 'build',
      closeBundle() {
        cpSync(new URL('./sprites/', import.meta.url), new URL('./dist/sprites/', import.meta.url), { recursive: true });
        cpSync(new URL('./jogar_local.html', import.meta.url), new URL('./dist/jogar_local.html', import.meta.url));
        cpSync(new URL('./brasalume.html', import.meta.url), new URL('./dist/brasalume.html', import.meta.url));
      },
    },
  ],
  publicDir: false,
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src/', import.meta.url)),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
