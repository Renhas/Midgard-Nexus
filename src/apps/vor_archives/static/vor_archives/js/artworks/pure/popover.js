const DEFAULT_PAD = 8;
const TIP_GAP = 6;

export function computeTipLayout({ chipRect, tipSize, viewportWidth, viewportHeight, pad }) {
  const padValue = pad == null ? DEFAULT_PAD : pad;
  let left = chipRect.right + TIP_GAP;
  if (left + tipSize.width > viewportWidth - padValue) {
    left = Math.max(padValue, chipRect.left - tipSize.width - TIP_GAP);
  }
  const anchorTop = chipRect.top + chipRect.height / 2;
  const tipTop = anchorTop - tipSize.height / 2;
  const tipBottom = anchorTop + tipSize.height / 2;
  let shiftY = 0;
  if (tipBottom > viewportHeight - padValue) {
    shiftY = viewportHeight - padValue - tipBottom;
  }
  if (tipTop + shiftY < padValue) {
    shiftY = padValue - tipTop;
  }
  return { left, top: anchorTop, shiftY };
}

export function computePopupLayout({ popupRect, viewportWidth, viewportHeight, pad }) {
  const padValue = pad == null ? DEFAULT_PAD : pad;
  return {
    flipH: popupRect.right > viewportWidth - padValue,
    flipV: popupRect.bottom > viewportHeight - padValue,
  };
}
