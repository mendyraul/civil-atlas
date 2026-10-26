export const civilizationColors = {
  'roman-empire': '#942d30',
  'han-dynasty': '#d4ae50',
  'parthian-empire': '#498578',
  'kingdom-of-kush': '#ba8058',
  'aksumite-kingdom': '#5a8dad',
  'maya-civilization': '#2f7d4c',
  'satavahana-dynasty': '#92719e',
  'kushan-empire': '#b23a48',
} as const;

export function civilizationColor(id: keyof typeof civilizationColors | string) {
  const known = civilizationColors[id as keyof typeof civilizationColors];
  if (known) return known;
  // Stable colors keep new polities distinguishable while scrubbing or comparing dates.
  const hash = [...id].reduce((value, char) => ((value * 31) + char.charCodeAt(0)) >>> 0, 0);
  return `hsl(${hash % 360}, 38%, 48%)`;
}
