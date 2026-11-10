export function displayRating(rating, hover) {
  return hover || rating || 0;
}

export function ratingLabel(value) {
  return value ? String(value) : "—";
}

export function starState(value, star) {
  const fullAt = star * 2;
  if (value >= fullAt) return "is-full";
  if (value === fullAt - 1) return "is-half";
  return "is-empty";
}
