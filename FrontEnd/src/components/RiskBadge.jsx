export default function RiskBadge({ level }) {
  const map = {
    LOW: "bg-emerald-100 text-emerald-700 border-emerald-200",
    MEDIUM: "bg-amber-100 text-amber-700 border-amber-200",
    HIGH: "bg-red-100 text-red-700 border-red-200",
    PROCESSING: "bg-zinc-100 text-zinc-700 border-zinc-200",
  };

  const cls = map[level] || map.PROCESSING;

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${cls}`}
    >
      <span className="h-2 w-2 rounded-full bg-current opacity-70" />
      {level}
    </span>
  );
}
