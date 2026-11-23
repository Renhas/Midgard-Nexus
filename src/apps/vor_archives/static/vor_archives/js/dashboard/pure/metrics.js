export const MIN_CLOUD_SIZE_PX = 12;
export const MAX_CLOUD_SIZE_PX = 48;

export function sumByCol(workTypes, col, matrix) {
  return workTypes.reduce((sum, type) => sum + (matrix[type]?.[col] || 0), 0);
}

export function sumByRow(row, matrix) {
  const rowData = matrix[row] || {};
  return Object.values(rowData).reduce((sum, val) => sum + val, 0);
}

export function sumByRowWithCount(row, matrix) {
  const rowData = matrix[row] || {};
  return Object.entries(rowData).reduce(
    (res, [rating, count]) => {
      if (rating === "") return res;
      res.sum += Number(rating) * count;
      res.count += count;
      return res;
    },
    { sum: 0, count: 0 },
  );
}

export function formatAverage(sum, count) {
  return count ? (sum / count).toFixed(1) : "0.0";
}

export function formatMetricNumber(value) {
  return Number(value || 0)
    .toFixed(1)
    .toLocaleString("ru-RU");
}

export function calcAverageRating(workTypes, ratingMatrix) {
  if (!workTypes.length) return "0.0";
  const totals = workTypes.reduce(
    (res, type) => {
      const row = sumByRowWithCount(type, ratingMatrix);
      res.sum += row.sum;
      res.count += row.count;
      return res;
    },
    { sum: 0, count: 0 },
  );
  return formatAverage(totals.sum, totals.count);
}

export function buildPieTypeItems(typeMeta, statusMatrix) {
  return Object.keys(typeMeta).map((type) => ({
    label: typeMeta[type].label,
    count: sumByRow(type, statusMatrix),
  }));
}

export function buildPieChoiceItems(workTypes, choices, matrix) {
  if (!workTypes.length) return [];
  return Object.keys(choices).map((key) => ({
    label: choices[key].label,
    count: sumByCol(workTypes, key, matrix),
  }));
}

export function buildBarRatingItems(typeMeta, ratingMatrix) {
  return Object.keys(typeMeta).map((type) => {
    const { sum, count } = sumByRowWithCount(type, ratingMatrix);
    return {
      label: typeMeta[type].label,
      count: formatAverage(sum, count),
    };
  });
}

export function buildSpentItems(spent, typeMeta) {
  return Object.entries(spent).map(([key, value]) => ({
    key,
    count: value,
    unit: typeMeta[key]?.unit || "",
    icon: typeMeta[key]?.icon || "",
  }));
}

export function calcAttrTotals(attrs) {
  return Object.fromEntries(
    Object.entries(attrs).map(([key, items]) => [key, (items || []).reduce((sum, item) => sum + (item.count || 0), 0)]),
  );
}

export function calcAttrShare(count, total) {
  return total ? Number(((count / total) * 100).toFixed(1)) : 0;
}

export function formatDashPercent(value) {
  const num = Number(value || 0);
  return `${num}%`;
}

export function buildHistItems(items, topN) {
  return (items || []).slice(0, topN).map((item) => ({
    label: item.name,
    count: item.count,
  }));
}

export function buildCloudItems(items, minPx = MIN_CLOUD_SIZE_PX, maxPx = MAX_CLOUD_SIZE_PX) {
  if (!items?.length) return [];
  const counts = items.map((item) => item.count);
  const min = Math.min(...counts);
  const max = Math.max(...counts);

  return items.map((item) => ({
    label: item.name,
    count: item.count,
    size: min === max ? (minPx + maxPx) / 2 : minPx + ((item.count - min) / (max - min)) * (maxPx - minPx),
  }));
}

export function hasNonZeroItems(items) {
  return Array.isArray(items) && items.some((item) => Number(item?.count) > 0);
}
