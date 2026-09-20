// Tailwind v4 moved the PostCSS plugin into its own package, and does its own
// vendor prefixing, so autoprefixer is gone. Same config the app uses.
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
}
