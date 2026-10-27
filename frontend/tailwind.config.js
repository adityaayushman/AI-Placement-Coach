/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "var(--ink)",
        muted: "var(--muted)",
        faint: "var(--faint)",
        line: "var(--line)",
        mauve: "var(--mauve)",
        rose: "var(--rose)",
        sage: "var(--sage)",
        amber: "var(--amber)",
        danger: "var(--danger)",
        ok: "var(--ok)",
      },
      fontFamily: {
        serif: ['"Source Serif 4"', "Georgia", "serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
