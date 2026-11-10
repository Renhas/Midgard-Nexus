export function captureQuickState(source) {
  return {
    status: source.status,
    rating: source.rating,
    progress: source.progress,
    isHidden: source.isHidden,
    timesCompleted: source.timesCompleted,
    ownedPlatformIds: [...(source.ownedPlatformIds || [])],
    lastCompletedDate: source.lastCompletedDate,
  };
}

export function restoreQuickState(target, snap) {
  if (!snap) {
    return;
  }
  target.status = snap.status;
  target.rating = snap.rating;
  target.progress = snap.progress;
  target.isHidden = snap.isHidden;
  target.timesCompleted = snap.timesCompleted;
  target.ownedPlatformIds = snap.ownedPlatformIds;
  target.lastCompletedDate = snap.lastCompletedDate;
}

export function applyQuickResult(target, data) {
  if (!data || typeof data !== "object") {
    return;
  }
  if (data.status) {
    target.status = data.status;
  }
  if (data.progress != null) {
    target.progress = Number(data.progress);
  }
  if (data.times_completed != null) {
    target.timesCompleted = Number(data.times_completed);
  }
  if (Object.prototype.hasOwnProperty.call(data, "last_completed_date")) {
    target.lastCompletedDate = data.last_completed_date || "";
  }
  if (Array.isArray(data.owned_platform_ids)) {
    target.ownedPlatformIds = data.owned_platform_ids.map(Number);
  }
}
