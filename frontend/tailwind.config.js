/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#edf5f2',
          100: '#dcece7',
          200: '#c1ddd5',
          300: '#9cc5ba',
          400: '#6ea79a',
          500: '#3f8278',
          600: '#2f6f68',
          700: '#24564f',
          800: '#1d4742',
          900: '#163833',
        },
      },
      fontFamily: {
        sans: [
          'Inter var',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'PingFang SC',
          'Hiragino Sans GB',
          'Microsoft YaHei',
          'sans-serif',
        ],
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'DEFAULT': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      },
      borderRadius: {
        'lg': '0.5rem',
        'xl': '0.75rem',
        '2xl': '1rem',
      },
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
      },
      maxWidth: {
        '8xl': '88rem',
      }
    },
  },
  plugins: [],
}
