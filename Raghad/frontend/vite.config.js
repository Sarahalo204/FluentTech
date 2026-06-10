import vite from 'vite';
import react from '@vitejs/plugin-react';

const { defineConfig } = vite;

export default defineConfig({
  plugins: [react()],
});
