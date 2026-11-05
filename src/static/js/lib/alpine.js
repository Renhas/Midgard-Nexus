// Alpine 3.14 cdn build registers itself on window and only emits
// alpine:init when it runs (after our modules). Read lazily via
// getAlpine() to avoid touching window.Alpine at module-eval time.
export const getAlpine = () => window.Alpine;
