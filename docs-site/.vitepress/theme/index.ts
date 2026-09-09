// Custom theme entry: extends the VitePress default theme and layers the
// Constitutional AIOps brand on top (navy background, blue accent, Inter).
// The product and marketing site are dark-only, so the site is forced dark
// (see appearance: 'force-dark' in ../config.ts); custom.css redefines the
// VitePress design tokens under :root, .dark so the palette holds either way.
import DefaultTheme from 'vitepress/theme'
import './custom.css'

export default DefaultTheme
