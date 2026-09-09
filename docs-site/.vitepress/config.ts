import { defineConfig } from 'vitepress'

// Project site served at https://partha-dev01.github.io/Constitutional-AIOps/
const BASE = '/Constitutional-AIOps/'
const REPO = 'https://github.com/Partha-dev01/Constitutional-AIOps'

export default defineConfig({
  lang: 'en-US',
  title: 'Constitutional AIOps',
  description:
    'Autonomous infrastructure management with a constitutional AI safety layer. Self-host with your own OpenAI-compatible LLM endpoint.',
  base: BASE,
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: false,

  // Product + marketing site are dark-only; force dark and hide the toggle so
  // the docs match. The brand palette lives in .vitepress/theme/custom.css.
  appearance: 'force-dark',

  sitemap: {
    hostname: 'https://partha-dev01.github.io' + BASE,
  },

  head: [
    ['meta', { name: 'theme-color', content: '#050c1c' }],
    // Inter, to match the marketing/app wordmark and body type.
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    [
      'link',
      {
        rel: 'stylesheet',
        href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
      },
    ],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'Constitutional AIOps' }],
    [
      'meta',
      {
        property: 'og:description',
        content:
          'A dual-agent AIOps system with a constitutional safety gate and human approval. Bring your own OpenAI-compatible LLM endpoint.',
      },
    ],
  ],

  themeConfig: {
    nav: [
      { text: 'Guide', link: '/guide/getting-started' },
      { text: 'Features', link: '/features/' },
      { text: 'Self-Host', link: '/guide/self-hosting' },
      { text: 'Architecture', link: '/guide/architecture' },
      {
        text: 'v1.0.0',
        items: [
          { text: 'Releases', link: REPO + '/releases' },
          { text: 'Changelog', link: REPO + '/blob/main/RELEASES.md' },
          { text: 'License (AGPL-3.0)', link: REPO + '/blob/main/LICENSE' },
        ],
      },
    ],

    sidebar: {
      '/features/': [
        {
          text: 'Features',
          items: [{ text: 'All features', link: '/features/' }],
        },
        {
          text: 'Observe',
          items: [
            { text: 'Dashboard', link: '/features/dashboard' },
            { text: 'Generative UI', link: '/features/generative-ui' },
            { text: 'Incidents and RCA', link: '/features/incidents' },
            { text: 'Metrics', link: '/features/metrics' },
            { text: 'Telemetry', link: '/features/telemetry' },
          ],
        },
        {
          text: 'Investigate',
          items: [
            { text: 'Graph Explorer', link: '/features/graph-explorer' },
            { text: 'Console', link: '/features/console' },
            { text: 'Chat and Assistant', link: '/features/chat' },
          ],
        },
        {
          text: 'Operate',
          items: [
            { text: 'Infrastructure', link: '/features/infrastructure' },
            { text: 'MCP tools', link: '/features/mcp' },
            { text: 'Agent Hub', link: '/features/agent-hub' },
            { text: 'Settings', link: '/features/settings' },
          ],
        },
        {
          text: 'Evaluate',
          items: [{ text: 'Benchmark', link: '/features/benchmark' }],
        },
      ],
      '/guide/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Overview', link: '/guide/getting-started' },
            { text: 'Self-Hosting', link: '/guide/self-hosting' },
            { text: 'Bring Your Own Endpoint', link: '/guide/bring-your-own-endpoint' },
            { text: 'Configuration', link: '/guide/configuration' },
          ],
        },
        {
          text: 'Concepts',
          items: [
            { text: 'Architecture', link: '/guide/architecture' },
            { text: 'Constitutional Safety', link: '/guide/safety' },
            { text: 'Benchmarking', link: '/guide/benchmarking' },
          ],
        },
        {
          text: 'Build',
          items: [
            { text: 'Developer Platform', link: '/guide/developer-platform' },
          ],
        },
      ],
    },

    socialLinks: [{ icon: 'github', link: REPO }],
    search: { provider: 'local' },

    editLink: {
      pattern: REPO + '/edit/main/docs-site/:path',
      text: 'Edit this page on GitHub',
    },

    footer: {
      message: 'Released under the AGPL-3.0 License.',
      copyright: 'Copyright © 2026 Partha-dev01',
    },
  },
})
