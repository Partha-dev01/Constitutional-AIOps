/* ESLint config for the Vite + React + TypeScript frontend.
 * Matches the installed toolchain (eslint 8, @typescript-eslint 6,
 * react-hooks, react-refresh). Type-aware rules are intentionally NOT enabled
 * yet (no parserOptions.project) to keep lint fast while the backlog is
 * ratcheted down; unused vars / hooks rules are the high-signal ones. */
module.exports = {
  root: true,
  env: { browser: true, es2020: true, node: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: [
    'dist',
    'node_modules',
    'e2e',
    'playwright-report',
    'test-results',
    '.eslintrc.cjs',
    '*.config.ts',
    '*.config.js',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
  },
}
