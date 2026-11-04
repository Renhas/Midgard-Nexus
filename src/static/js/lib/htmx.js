// Vendor UMD wrapper. HTMX 1.9 ships without ESM, so we re-export the
// global installed by base.html. This is the only place allowed to read
// window.htmx; everything else imports from here.
const htmx = window.htmx;
export default htmx;
export { htmx };
