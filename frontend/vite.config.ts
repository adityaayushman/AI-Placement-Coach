/// <reference types="vitest" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
    // Lazy-loaded chart pages can take several seconds to import under jsdom on slow CI.
    testTimeout: 30_000,
  },
});
