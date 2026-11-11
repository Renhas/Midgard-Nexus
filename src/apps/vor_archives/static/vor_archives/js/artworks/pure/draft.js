export function serializeDraft(source) {
  return JSON.stringify({
    title: source.title,
    description: source.description,
    releaseDate: source.releaseDate,
    ageRating: source.ageRating,
    externalLink: source.externalLink,
    pages: source.pages,
    durationMinutes: source.durationMinutes,
    episodeCount: source.episodeCount,
    authors: source.authors,
    genres: source.genres,
    tags: source.tags,
    platforms: source.platforms,
    relations: source.relations,
    coverPreview: source.coverPreview,
    coverCleared: source.coverCleared,
    coverName: source.coverFile?.name || "",
  });
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
