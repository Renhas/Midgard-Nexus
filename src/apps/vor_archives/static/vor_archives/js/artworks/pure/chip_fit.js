export function allChipsFit(chipWidths, available, gap) {
  if (available <= 0) {
    return false;
  }
  let sum = 0;
  (chipWidths || []).forEach((width, index) => {
    sum += width + (index ? gap : 0);
  });
  return sum <= available;
}

export function computeVisibleChipCount({ chipWidths, available, gap, moreWidth }) {
  const widths = chipWidths || [];
  const total = widths.length;
  if (available <= 0) {
    return { visibleCount: 0, hiddenCount: total };
  }
  let used = 0;
  let visible = 0;
  for (let index = 0; index < widths.length; index += 1) {
    const next = used + (index ? gap : 0) + widths[index];
    if (next + gap + moreWidth <= available) {
      used = next;
      visible = index + 1;
    } else {
      break;
    }
  }
  return { visibleCount: visible, hiddenCount: total - visible };
}
