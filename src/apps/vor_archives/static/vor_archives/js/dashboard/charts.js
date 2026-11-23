import { Chart } from "@lib/chart";
import { MIN_CLOUD_SIZE_PX, MAX_CLOUD_SIZE_PX, formatDashPercent, hasNonZeroItems } from "@vor/dashboard/pure/metrics";

export { MIN_CLOUD_SIZE_PX as MIN_SIZE_PX, MAX_CLOUD_SIZE_PX as MAX_SIZE_PX, formatDashPercent };

export const DASH_CHART_COLORS = [
  "#A78BFA",
  "#60A5FA",
  "#34D399",
  "#F87171",
  "#FB923C",
  "#818CF8",
  "#FBBF24",
  "#22D3EE",
  "#F472B6",
  "#94A3B8",
  "#C084FC",
  "#38BDF8",
];

const BASE_TOOLTIP = {
  backgroundColor: "#1A233A",
  titleColor: "#E2E8F0",
  bodyColor: "#E2E8F0",
  borderColor: "rgba(167,139,250,0.3)",
  borderWidth: 1,
};

const AXIS_TICKS = {
  color: "#94A3B8",
  font: { size: 11 },
};

const GRID_STYLE = {
  color: "rgba(255,255,255,0.06)",
};

export const centerTextPlugin = {
  id: "centerText",
  afterDraw(chart, args, opts) {
    if (!opts?.text) return;
    const { ctx, chartArea } = chart;
    if (!chartArea) return;
    const cx = (chartArea.left + chartArea.right) / 2;
    const cy = (chartArea.top + chartArea.bottom) / 2;
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "bold 28px sans-serif";
    ctx.fillStyle = "#E2E8F0";
    ctx.fillText(opts.text, cx, cy - 8);
    if (opts.label) {
      ctx.font = "12px sans-serif";
      ctx.fillStyle = "#94A3B8";
      ctx.fillText(opts.label, cx, cy + 16);
    }
    ctx.restore();
  },
};

export function readJsonScript(id) {
  const el = document.getElementById(id);
  if (!el) return {};
  try {
    return JSON.parse(el.textContent);
  } catch {
    return {};
  }
}

export function chartPalette(count) {
  return Array.from({ length: count }, (_, idx) => DASH_CHART_COLORS[idx % DASH_CHART_COLORS.length]);
}

export function destroyChart(chart) {
  if (!chart) return;
  try {
    chart.stop?.();
    chart.destroy?.();
  } catch (error) {
    console.error("[dashboard] chart destroy failed", error);
  }
}

export function destroyChartMap(chartMap) {
  for (const key of Object.keys(chartMap)) {
    destroyChart(chartMap[key]);
    delete chartMap[key];
  }
}

export function renderDoughnutChart(canvas, items, { centerText = null } = {}) {
  if (!canvas || !Chart) return null;
  Chart.getChart(canvas)?.destroy();
  if (!hasNonZeroItems(items)) return null;

  return new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: items.map((item) => item.label),
      datasets: [
        {
          data: items.map((item) => item.count),
          backgroundColor: chartPalette(items.length),
          borderColor: "#1A233A",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 12, color: "#E2E8F0" },
        },
        centerText: centerText ? { text: centerText.value, label: centerText.label } : undefined,
      },
    },
    plugins: [centerTextPlugin],
  });
}

export function upsertBarChart(existingChart, canvas, items, { horizontal = false, suggestedMax = undefined } = {}) {
  if (!canvas || !Chart) return null;
  if (!hasNonZeroItems(items)) {
    destroyChart(existingChart);
    Chart.getChart(canvas)?.destroy();
    return null;
  }
  const labels = items.map((item) => item.label);
  const data = items.map((item) => item.count);
  const backgroundColor = chartPalette(items.length);

  if (existingChart) {
    existingChart.data.labels = labels;
    existingChart.data.datasets[0].data = data;
    existingChart.data.datasets[0].backgroundColor = backgroundColor;
    existingChart.update();
    return existingChart;
  }

  Chart.getChart(canvas)?.destroy();
  const valueAxis = {
    beginAtZero: true,
    suggestedMax,
    ticks: { ...AXIS_TICKS, precision: 0 },
    grid: GRID_STYLE,
    border: { display: false },
  };
  const categoryAxis = {
    beginAtZero: horizontal,
    ticks: AXIS_TICKS,
    grid: { display: false },
    border: { display: false },
  };

  return new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor,
          borderRadius: 4,
          borderSkipped: false,
          barThickness: "flex",
          maxBarThickness: 96,
        },
      ],
    },
    options: {
      indexAxis: horizontal ? "y" : "x",
      responsive: true,
      maintainAspectRatio: false,
      scales: horizontal ? { x: valueAxis, y: categoryAxis } : { x: categoryAxis, y: valueAxis },
      plugins: {
        legend: { display: false },
        tooltip: BASE_TOOLTIP,
      },
    },
  });
}

export function upsertWordCloudChart(existingChart, canvas, items) {
  if (!canvas || !Chart) return null;
  const labels = items.map((item) => item.label);
  const data = items.map((item) => item.size);
  const counts = items.map((item) => item.count);
  const color = DASH_CHART_COLORS[0];

  if (existingChart) {
    existingChart.data.labels = labels;
    existingChart.data.datasets[0].data = data;
    existingChart.data.datasets[0].color = color;
    existingChart.data.datasets[0].counts = counts;
    existingChart.update();
    return existingChart;
  }

  Chart.getChart(canvas)?.destroy();
  return new Chart(canvas, {
    type: "wordCloud",
    data: {
      labels,
      datasets: [
        {
          label: "",
          data,
          color,
          counts,
          minRotation: 0,
          maxRotation: 0,
          padding: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        title: { display: false },
        tooltip: {
          ...BASE_TOOLTIP,
          callbacks: {
            label: (ctx) => `${ctx.dataset.counts?.[ctx.dataIndex] ?? ""}`,
          },
        },
      },
    },
  });
}
