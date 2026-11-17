import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig } from "vitest/config";

function loadAliases(configPath) {
  const jsconfig = JSON.parse(readFileSync(configPath, "utf8"));
  return Object.fromEntries(
    Object.entries(jsconfig.compilerOptions.paths).map(([alias, [target]]) => [
      alias.replace(/\/\*$/, ""),
      resolve(__dirname, target.replace(/\/\*$/, "")),
    ]),
  );
}

export default defineConfig({
  resolve: {
    alias: loadAliases(resolve(__dirname, "jsconfig.json")),
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
