export const DAY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  A: { bg: 'bg-violet-500/15', text: 'text-violet-400', border: 'border-violet-500/30' },
  B: { bg: 'bg-blue-500/15', text: 'text-blue-400', border: 'border-blue-500/30' },
  C: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  D: { bg: 'bg-orange-500/15', text: 'text-orange-400', border: 'border-orange-500/30' },
  E: { bg: 'bg-pink-500/15', text: 'text-pink-400', border: 'border-pink-500/30' },
  F: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30' },
  G: { bg: 'bg-cyan-500/15', text: 'text-cyan-400', border: 'border-cyan-500/30' },
  None: { bg: 'bg-zinc-500/15', text: 'text-zinc-400', border: 'border-zinc-500/30' },
};

export function getDayColor(day: string) {
  return DAY_COLORS[day] || DAY_COLORS.None;
}
