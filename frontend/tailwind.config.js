/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        deepBlue: "#1E3A8A",
        skyBlue: "#38BDF8",
      },
    },
  },
  plugins: [],
}
