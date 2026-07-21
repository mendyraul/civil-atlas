type StatusBadgeProps = {
  label: string;
  tone: string;
};

export function StatusBadge({ label, tone }: StatusBadgeProps) {
  return <span className={`rounded-full px-2.5 py-1 text-xs ${tone}`}>{label}</span>;
}
