import { defineConfig } from 'vite';

export default defineConfig({
    root: './',
    build: {
        outDir: 'dist',
        assetsDir: 'assets',
        emptyOutDir: true,
        rollupOptions: {
            input: {
                main: './index.html'
            }
        }
    },
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: process.env.VITE_API_URL || 'http://localhost:5001',
                changeOrigin: true,
                ws: true
            }
        }
    }
}); 