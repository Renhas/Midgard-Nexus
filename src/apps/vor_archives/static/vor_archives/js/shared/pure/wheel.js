export function wheelDirection(deltaY) {
  return deltaY < 0 ? 1 : deltaY > 0 ? -1 : 0;
}
