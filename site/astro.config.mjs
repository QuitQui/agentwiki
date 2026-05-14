import { defineConfig } from 'astro/config'

export default defineConfig({
  output: 'static',
  vite: {
    build: {
      rollupOptions: {
        // Pagefind assets are generated after astro build, not resolvable at build time
        external: ['/pagefind/pagefind-ui.js'],
      },
    },
  },
})
