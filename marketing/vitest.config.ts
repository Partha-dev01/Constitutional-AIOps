import { defineConfig } from 'vitest/config'

// The marketing site is otherwise static, but the smart pre-warm intent logic
// (src/lib/prewarm.ts) is cost-sensitive -- it decides when to spend a box wake
// -- so its pure decision functions are unit tested. A node environment is
// enough: the tested functions take an explicit state object and touch no DOM.
export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
