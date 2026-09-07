// @ts-check
// Flat ESLint config for the Vite + React + TypeScript frontend (eslint 10).
// Ports the previous .eslintrc.cjs one-for-one: eslint + typescript-eslint
// recommended, plus the two classic react-hooks rules and the react-refresh
// rule. Type-aware linting is intentionally NOT enabled (no projectService) to
// keep lint fast, exactly as before. The rule SET is unchanged from the eslintrc
// era on purpose, so the 6-warning baseline is preserved across the toolchain
// bump (eslint 8 -> 10, ts-eslint 6 -> 8, react-hooks 4 -> 7, react-refresh
// 0.4 -> 0.5).
import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

export default tseslint.config(
  {
    // Replaces the old ignorePatterns (config-only block == .eslintignore).
    ignores: [
      'dist',
      'node_modules',
      'e2e',
      'playwright-report',
      'test-results',
      '*.config.ts',
      '*.config.js',
      'eslint.config.js',
    ],
  },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser, ...globals.node },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      // Same two hooks rules the old plugin:react-hooks/recommended enabled —
      // NOT react-hooks 7's larger recommended set, to keep the baseline stable.
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' },
      ],
    },
  },
)
