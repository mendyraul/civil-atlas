export const civilizationColors = {
  'roman-empire': '#c95a2f',
  'han-dynasty': '#d4a63a',
  'parthian-empire': '#357266',
  'kingdom-of-kush': '#7f4a2b',
  'aksumite-kingdom': '#245c96',
  'maya-civilization': '#2f7d4c',
  'satavahana-dynasty': '#8a4fb4',
} as const;

export function civilizationColor(id: keyof typeof civilizationColors | string) {
  return civilizationColors[id as keyof typeof civilizationColors] ?? '#51627a';
}
