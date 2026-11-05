// Page entry point for /vor/artworks/. Imports are side-effect only:
// each module registers Alpine components and/or event listeners on
// evaluation. Shared base (common.js, events/shell.js) is loaded by
// base_vor.html.
import "@vor/events/list";
import "@vor/artworks/store";
import "@vor/artworks/row_preview";
import "@vor/artworks/overlay";
import "@vor/artworks/add";
import "@vor/artworks/chip";
