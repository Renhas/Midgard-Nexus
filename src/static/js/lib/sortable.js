// Vendor UMD wrapper. Sortable 1.15 has an ESM build, but we keep the
// UMD file for consistency with the other vendors. Only this file may
// read window.Sortable; everything else imports from here.
const Sortable = window.Sortable;
export default Sortable;
export { Sortable };
