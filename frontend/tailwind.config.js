/** @type {import('tailwindcss').Config} */
// 企业控制台风格：中性灰底 + 单一品牌蓝，小圆角、弱阴影
const brand = {
  50: '#e8f3ff',
  100: '#bedaff',
  200: '#94bfff',
  300: '#6aa1ff',
  400: '#4080ff',
  500: '#165dff',
  600: '#165dff',
  700: '#0e42d2',
  800: '#072ca6',
  900: '#031a79',
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
          50: '#f7f8fa',
          100: '#f2f3f5',
          200: '#e5e6eb',
          300: '#c9cdd4',
          400: '#a9aeb8',
          500: '#86909c',
          600: '#4e5969',
          700: '#4e5969',
          800: '#272e3b',
          900: '#1d2129',
        },
        stone: {
          50: '#f7f8fa',
          100: '#f2f3f5',
          200: '#e5e6eb',
          300: '#c9cdd4',
          400: '#a9aeb8',
          500: '#86909c',
          600: '#4e5969',
          700: '#4e5969',
          800: '#1d2129',
          900: '#1d2129',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
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
        'lg': '4px',
        'xl': '6px',
        '2xl': '6px',
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
