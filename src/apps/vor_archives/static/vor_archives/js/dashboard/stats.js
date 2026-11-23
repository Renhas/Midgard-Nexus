import { destroyChartMap, readJsonScript, renderDoughnutChart, upsertBarChart } from "@vor/dashboard/charts";
import {
  buildBarRatingItems,
  buildPieChoiceItems,
  buildPieTypeItems,
  buildSpentItems,
  calcAverageRating,
  formatMetricNumber,
  hasNonZeroItems,
  sumByRow,
} from "@vor/dashboard/pure/metrics";

export function createDashStatsComponent() {
  const pieCharts = Object.create(null);
  const barCharts = Object.create(null);

  return {
    workTypes: ["book", "film", "game"],
    statusMatrix: {},
    ageMatrix: {},
    ratingMatrix: {},
    spent: {},
    typeMeta: {},
    statusChoices: {},
    ageChoices: {},
    ratingChoices: {},

    init() {
      const data = readJsonScript("dash-stats-opts");
      this.statusMatrix = data.status_matrix || {};
      this.ageMatrix = data.age_matrix || {};
      this.ratingMatrix = data.rating_matrix || {};
      this.spent = data.spent || {};
      this.typeMeta = data.type_meta || {};
      this.statusChoices = data.status_choices || {};
      this.ageChoices = data.age_choices || {};
      this.ratingChoices = data.rating_choices || {};

      this.$nextTick(() => {
        this.renderPieTypes();
        this.renderPieStatus();
        this.renderPieAge();
        this.renderPieRating();
        this.renderBarRating();
      });

      this.$watch("pieStatusItems", () => this.$nextTick(() => this.renderPieStatus()));
      this.$watch("pieAgeItems", () => this.$nextTick(() => this.renderPieAge()));
      this.$watch("pieRatingItems", () => this.$nextTick(() => this.renderPieRating()));
    },

    get worksTotalCount() {
      return Object.keys(this.typeMeta).reduce((sum, type) => sum + sumByRow(type, this.statusMatrix), 0);
    },

    get averageRating() {
      return calcAverageRating(this.workTypes, this.ratingMatrix);
    },

    get spentProgressItems() {
      return buildSpentItems(this.spent, this.typeMeta);
    },

    get pieTypesItems() {
      return buildPieTypeItems(this.typeMeta, this.statusMatrix);
    },

    get pieStatusItems() {
      return buildPieChoiceItems(this.workTypes, this.statusChoices, this.statusMatrix);
    },

    get pieAgeItems() {
      return buildPieChoiceItems(this.workTypes, this.ageChoices, this.ageMatrix);
    },

    get pieRatingItems() {
      return buildPieChoiceItems(this.workTypes, this.ratingChoices, this.ratingMatrix);
    },

    get barRatingItems() {
      return buildBarRatingItems(this.typeMeta, this.ratingMatrix);
    },

    get hasPieTypesData() {
      return hasNonZeroItems(this.pieTypesItems);
    },

    get hasPieStatusData() {
      return hasNonZeroItems(this.pieStatusItems);
    },

    get hasPieAgeData() {
      return hasNonZeroItems(this.pieAgeItems);
    },

    get hasPieRatingData() {
      return hasNonZeroItems(this.pieRatingItems);
    },

    get hasBarRatingData() {
      return hasNonZeroItems(this.barRatingItems);
    },

    toggleType(type) {
      const index = this.workTypes.indexOf(type);
      if (index > -1) {
        this.workTypes.splice(index, 1);
      } else {
        this.workTypes.push(type);
      }
    },

    formatNumber: formatMetricNumber,

    renderPieTypes() {
      pieCharts.types = renderDoughnutChart(this.$refs.pieTypes, this.pieTypesItems, {
        centerText: { value: this.worksTotalCount, label: "всего" },
      });
    },

    renderPieStatus() {
      pieCharts.statuses = renderDoughnutChart(this.$refs.pieStatus, this.pieStatusItems);
    },

    renderPieAge() {
      pieCharts.age = renderDoughnutChart(this.$refs.pieAge, this.pieAgeItems);
    },

    renderPieRating() {
      pieCharts.rating = renderDoughnutChart(this.$refs.pieRating, this.pieRatingItems, {
        centerText: { value: this.averageRating, label: "среднее" },
      });
    },

    renderBarRating() {
      barCharts.rating = upsertBarChart(barCharts.rating, this.$refs.barRating, this.barRatingItems, {
        suggestedMax: 10,
      });
    },

    destroy() {
      destroyChartMap(pieCharts);
      destroyChartMap(barCharts);
    },
  };
}
