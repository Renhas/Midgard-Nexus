export function cropCoverFile(file) {
  const targetRatio = 2 / 3;
  return new Promise((resolve, reject) => {
    const image = new Image();
    const url = URL.createObjectURL(file);
    image.onload = () => {
      URL.revokeObjectURL(url);
      const srcW = image.naturalWidth;
      const srcH = image.naturalHeight;
      const srcRatio = srcW / srcH;
      if (Math.abs(srcRatio - targetRatio) < 0.01) {
        resolve({ file, cropped: false, srcW, srcH, outW: srcW, outH: srcH });
        return;
      }
      let sx = 0;
      let sy = 0;
      let sw = srcW;
      let sh = srcH;
      if (srcRatio > targetRatio) {
        sw = srcH * targetRatio;
        sx = (srcW - sw) / 2;
      } else {
        sh = srcW / targetRatio;
        sy = (srcH - sh) / 2;
      }
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(sw));
      canvas.height = Math.max(1, Math.round(sh));
      canvas.getContext("2d").drawImage(
        image, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height
      );
      canvas.toBlob((blob) => {
        if (!blob) {
          reject(new Error("cover"));
          return;
        }
        const next = new File([blob], file.name.replace(/\.\w+$/, ".jpg"), {
          type: "image/jpeg",
        });
        resolve({
          file: next,
          cropped: true,
          srcW,
          srcH,
          outW: canvas.width,
          outH: canvas.height,
        });
      }, "image/jpeg", 0.92);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("cover"));
    };
    image.src = url;
  });
}
