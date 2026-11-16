// Vendor UMD wrapper. @floating-ui/core 1.6.9, @floating-ui/utils 0.2.9,
// and @floating-ui/dom 1.6.13 are loaded as UMD in base.html in that
// order; dom's UMD externals read core and utils from globals, so both
// must already exist. Together they expose the full public API under
// window.FloatingUIDOM. Only this file may read that global; everything
// else imports from here.
export const FloatingUI = window.FloatingUIDOM;
