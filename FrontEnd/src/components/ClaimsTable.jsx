import RiskBadge from "./RiskBadge.jsx";
import { useMemo, useState,useEffect } from "react";

export default function ClaimsTable({ claims = [] }) {
  
  const [q, setQ] = useState("");
  const [level, setLevel] = useState("ALL");
 


  const filtered = useMemo(() => {
    return claims.filter((c) => {
      const okQ =
        !q ||
        c.text.toLowerCase().includes(q.toLowerCase()) ||
        c.reason.toLowerCase().includes(q.toLowerCase());
      const okLevel = level === "ALL" ? true : c.riskLevel === level;
      return okQ && okLevel;
    });
  }, [claims, q, level]);

  return (
    <div className="rounded-2xl border bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="font-semibold">Flagged Claims</div>
          <div className="text-xs text-zinc-500">
            Filter suspicious claims and view reasons
          </div>
        </div>

        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search claims..."
            className="rounded-xl border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-zinc-200"
          />
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="rounded-xl border px-3 py-2 text-sm outline-none"
          >
            <option value="ALL">All Risk</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
      </div>

      <div className="mt-4 overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left text-zinc-500">
            <tr className="border-b">
              <th className="py-2 pr-4">Risk</th>
              
              <th className="py-2 pr-4">Claim</th>
              <th className="py-2 pr-4">Confidence</th>
              <th className="py-2 pr-4">Rule Score</th>
              <th className="py-2 pr-4">Type</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr key={c.id} className="border-b last:border-b-0">
                <td className="py-3 pr-4">
                  <RiskBadge level={c.riskLevel} />
                </td>
                <td className="py-3 pr-4 max-w-[520px]">
                  <div className="line-clamp-3">{c.text}</div>
                </td>
                <td className="py-3 pr-4 text-zinc-600">{c.mlConfidence}</td>
                <td className="py-3 pr-4 text-zinc-600">{c.ruleScore}</td>
                <td className="py-3 pr-4 text-zinc-600">{c.type}</td>
              </tr>
            ))}

            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-zinc-500">
                  No claims found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
