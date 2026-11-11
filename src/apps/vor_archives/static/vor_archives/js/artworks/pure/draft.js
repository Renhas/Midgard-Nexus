export function serializeDraft(payload) {
  return JSON.stringify(payload || {});
}

export function parseDraft(json) {
  if (typeof json !== "string" || !json) {
    return {};
  }
  try {
    return JSON.parse(json);
  } catch (error) {
    return {};
  }
}

export function dirtyChanges(before, after, labels, hasCoverChange) {
  const changes = [];
  Object.keys(labels).forEach((key) => {
    if (JSON.stringify(before[key] ?? "") !== JSON.stringify(after[key] ?? "")) {
      changes.push(labels[key]);
    }
  });
  if (hasCoverChange) {
    changes.push("Обложка");
  }
  return changes;
}
