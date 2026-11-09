import { resolve } from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@lib": resolve(__dirname, "src/static/js/lib"),
      "@vor": resolve(
        __dirname,
        "src/apps/vor_archives/static/vor_archives/js"
      ),
    },
  },
  test: {
    environment: "jsdom",
    include: [
      "src/tests/frontend/**/*.{test,spec}.{js,mjs,ts}",
      "src/apps/*/tests/frontend/**/*.{test,spec}.{js,mjs,ts}",
    ],
    setupFiles: [resolve(__dirname, "vitest.setup.js")],
  },
});
