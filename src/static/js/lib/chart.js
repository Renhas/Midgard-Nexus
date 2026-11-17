// Vendor UMD wrapper. Chart.js 4.4 and chartjs-chart-wordcloud 4.4 are
// loaded as UMD in base.html; wordcloud registers itself as a Chart
// plugin, so re-exporting Chart is enough. Only this file may read
// window.Chart; everything else imports from here.
const Chart = window.Chart;
export default Chart;
export { Chart };
