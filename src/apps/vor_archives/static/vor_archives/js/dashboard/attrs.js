import {
  destroyChartMap,
  formatDashPercent,
  readJsonScript,
  upsertBarChart,
  upsertWordCloudChart,
} from "@vor/dashboard/charts";
import {
  buildCloudItems,
  buildHistItems,
  calcAttrShare,
  calcAttrTotals,
  hasNonZeroItems,
} from "@vor/dashboard/pure/metrics";

export function createDashAttrsComponent() {
  const barCharts = Object.create(null);
  const cloudCharts = Object.create(null);

  return {
    attrView: "cloud",
    attrs: {},
    attrTotals: {},
    histTopN: 12,

    init() {
      const data = readJsonScript("dash-attrs-opts");
      this.attrs = data.attrs || {};
      this.histTopN = data.histTopN || 12;
      this.attrTotals = calcAttrTotals(this.attrs);

      this.$nextTick(() => this._renderActiveView());
      this.$watch("attrView", () => this._renderActiveView());
      this.$watch("attrs", () => {
        this.attrTotals = calcAttrTotals(this.attrs);
        this._renderActiveView();
      });
    },

    getItems(attrKey) {
      return this.attrs[attrKey] || [];
    },

    hasItems(attrKey) {
      return hasNonZeroItems(this.getItems(attrKey));
    },

    calcAttrShare(count, attrKey) {
      return calcAttrShare(count, this.attrTotals[attrKey] || 0);
    },

    formatPercent: formatDashPercent,

    setAttrView(view) {
      if (view !== this.attrView) {
        this.attrView = view;
      }
    },

    _renderActiveView() {
      if (this.attrView === "bar") {
        this.$nextTick(() => {
          for (const key of Object.keys(this.attrs)) {
            const items = buildHistItems(this.attrs[key], this.histTopN);
            barCharts[key] = upsertBarChart(barCharts[key], this.$refs[`bar-${key}`], items, {
              horizontal: true,
            });
          }
        });
      } else if (this.attrView === "cloud") {
        this.$nextTick(() => {
          for (const key of Object.keys(this.attrs)) {
            const items = buildCloudItems(this.attrs[key]);
            cloudCharts[key] = upsertWordCloudChart(cloudCharts[key], this.$refs[`cloud-${key}`], items);
          }
        });
      }
    },

    destroy() {
      destroyChartMap(barCharts);
      destroyChartMap(cloudCharts);
    },
  };
}
