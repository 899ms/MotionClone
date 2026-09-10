export function stateAt(track, time) {
  const keys = track.keyframes;
  if (time <= keys[0].t) return keys[0];
  if (time >= keys.at(-1).t) return keys.at(-1);
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1], b = keys[i];
    if (time > b.t) continue;
    let p = (time - a.t) / Math.max(0.00001, b.t - a.t);
    if (track.easing === 'smooth') p = p * p * (3 - 2 * p);
    if (track.easing === 'out') p = 1 - (1 - p) ** 3;
    if (track.easing === 'step') p = 0;
    return Object.fromEntries(Object.keys(a).map(k => [k, a[k] + (b[k] - a[k]) * p]));
  }
  return keys.at(-1);
}
