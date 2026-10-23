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
  return civilizationColors[id as keyof typeof civilizationColors] ?? '#51627a';
}
