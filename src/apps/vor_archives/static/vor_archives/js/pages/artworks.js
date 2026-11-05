// Page entry point for /vor/artworks/. Imports are side-effect only:
// each module registers Alpine components and/or event listeners on
// evaluation. Shared base (common.js, events/shell.js) is loaded by
// base_vor.html.
import "../events/list.js";
import "../artworks/store.js";
import "../artworks/row_preview.js";
import "../artworks/overlay.js";
import "../artworks/add.js";
import "../artworks/chip.js";
