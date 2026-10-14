/** @type {import('tailwindcss').Config} */
const brand = {
  50: '#e8f0eb',
  100: '#d5e3dc',
  200: '#b7cec4',
  300: '#8eb4a5',
  400: '#6a9584',
  500: '#2f5b4e',
  600: '#2f5b4e',
  700: '#234239',
  800: '#234239',
  900: '#1d302b',
}

export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: brand,
        blue: brand,
        // 历史代码中的 teal 焦点环统一收敛到品牌色
        teal: brand,
        gray: {
          50: '#faf9f6',
          100: '#f3f0eb',
          200: '#e1ddd5',
          300: '#c8c1b7',
          400: '#a9a39a',
          500: '#8b867c',
          600: '#5f5b53',
          700: '#4a4741',
          800: '#34332f',
          900: '#252522',
        },
        stone: {
          50: '#faf9f6',
          100: '#f3f0eb',
          200: '#e1ddd5',
          300: '#c8c1b7',
          400: '#a9a39a',
          500: '#8b867c',
          600: '#5f5b53',
          700: '#4a4741',
          800: '#34332f',
          900: '#252522',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI Variable"',
          '"Avenir Next"',
          '"PingFang SC"',
          '"Hiragino Sans GB"',
          '"Microsoft YaHei"',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
        ],
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgb(0 0 0 / 0.04)',
        'DEFAULT': '0 1px 3px 0 rgb(0 0 0 / 0.06)',
        'md': '0 4px 10px 0 rgb(0 0 0 / 0.06)',
        'lg': '0 8px 24px 0 rgb(0 0 0 / 0.10)',
      },
      borderRadius: {
        'lg': '6px',
        'xl': '8px',
        '2xl': '12px',
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
