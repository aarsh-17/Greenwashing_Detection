import RiskBadge from "./RiskBadge.jsx";
import { useMemo, useState, Fragment } from "react";

export default function ClaimsTable({ claims = [], refresh, onDelete }) {
  const [q, setQ] = useState("");
  const [level, setLevel] = useState("ALL");
  const [loadingId, setLoadingId] = useState(null);

  // RAG state
  const [ragResults, setRagResults] = useState({});
  const [openRows, setOpenRows] = useState({});

  // ---------- FILTER ----------
  const filtered = useMemo(() => {
    return claims.filter((c) => {
      const okQ =
        !q || c.text.toLowerCase().includes(q.toLowerCase());

      const okLevel =
        level === "ALL" ? true : c.riskLevel === level;

      return okQ && okLevel;
    });
  }, [claims, q, level]);

  // ---------- DELETE ----------
  const deleteClaim = async (id) => {
    try {
      await fetch(
        `http://localhost:8000/documents/delete-claim/${id}`,
        { method: "DELETE" }
      );
      onDelete?.(id);
    } catch (err) {
      console.error(err);
    }
  };

  // ---------- RUN RAG ----------
  const runRAG = async (claimId) => {
    try {
      setLoadingId(claimId);

      const res = await fetch(
        `http://localhost:8000/api/rag/run-rag-claim?claim_id=${claimId}`,
        { method: "POST" }
      );

      const raw = await res.json();
      const d = raw.data || {};

      // Normalize backend response
      const normalized = {
        label: d.rag_label,
        confidence: d.rag_confidence,
        similarity: d.rag_similarity,
        top_chunks: d.textual_evidence || [],
      };
      console.log(normalized.top_chunks);
      

      setRagResults((prev) => ({
        ...prev,
        [claimId]: normalized,
      }));

      setOpenRows((prev) => ({
        ...prev,
        [claimId]: true,
      }));

      refresh();
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingId(null);
    }
  };

  // ---------- CLOSE PANEL ----------
  const closeRag = (id) => {
    setOpenRows((prev) => ({
      ...prev,
      [id]: false,
    }));
  };

  const applyRAG = async (claimId) => {
  try {
    const res = await fetch(
      `http://localhost:8000/api/rag/apply-rag?claim_id=${claimId}`,
      { method: "POST" }
    );
    const data = await res.json();
    console.log("Apply RAG response:", data);

    refresh(); // reload updated claim
  } catch (err) {
    console.error(err);
  }
};

  // ---------- LABEL COLOR ----------
  const getLabelColor = (label) => {
    switch (label) {
      case "SUPPORTED":
        return "bg-green-600";
      case "UNSUPPORTED":
        return "bg-red-600";
      case "PARTIALLY_SUPPORTED":
        return "bg-yellow-500";
      case "MARKETING_LANGUAGE":
        return "bg-purple-600";
      default:
        return "bg-black";
    }
  };

  return (
    <div className="rounded-2xl border bg-white p-4 shadow-sm">
      {/* HEADER */}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="font-semibold">Flagged Claims</div>
          <div className="text-xs text-zinc-500">
            Filter and manage claims
          </div>
        </div>

        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search claims..."
            className="rounded-xl border px-3 py-2 text-sm outline-none"
          />

          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="rounded-xl border px-3 py-2 text-sm"
          >
            <option value="ALL">All Risk</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
      </div>

      {/* TABLE */}
      <div className="mt-4 overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left text-zinc-500">
            <tr className="border-b">
              <th className="py-2 pr-4">Risk</th>
              <th className="py-2 pr-4">Claim</th>
              <th className="py-2 pr-4">Confidence</th>
              <th className="py-2 pr-4">Actions</th>
            </tr>
          </thead>

          <tbody>
            {filtered.map((c) => {
              const rag = ragResults[c.id];
              const isOpen = openRows[c.id];

              return (
                <Fragment key={c.id}>
                  {/* MAIN ROW */}
                  <tr className="border-b">
                    <td className="py-3 pr-4">
                      <RiskBadge level={c.riskLevel} />
                          {c.rag_applied && (
                            <span className="text-xs text-green-600">
                              ✓ Applied
                            </span>
                          )}
                    </td>

                    <td className="py-3 pr-4 max-w-[520px]">
                      <div className="line-clamp-3">{c.text}</div>
                    </td>

                    <td className="py-3 pr-4 text-zinc-600">
                      {c.mlConfidence}
                    </td>

                    <td className="py-3 pr-4 flex gap-2">
                      <button
                        onClick={() => runRAG(c.id)}
                        disabled={loadingId === c.id}
                        className="px-3 py-1 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                      >
                        {loadingId === c.id ? "Running..." : "Run RAG"}
                      </button>

                      <button
                        onClick={() => deleteClaim(c.id)}
                        className="px-3 py-1 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>

                  {/* RAG PANEL */}
                  {isOpen && rag && (
                    <tr className="bg-zinc-50">
                      <td colSpan={4} className="p-4">
                        <div className="relative rounded-xl border bg-white p-4 shadow-sm">

                          {/* CLOSE */}
                          <button
                            onClick={() => closeRag(c.id)}
                            className="absolute top-2 right-2 text-xs text-zinc-400 hover:text-black"
                          >
                            ✕
                          </button>

                          {/* LABEL + META */}
                          <div className="flex items-center gap-3 mb-3">
                            <span
                              className={`text-xs px-2 py-1 rounded text-white ${getLabelColor(
                                rag.label
                              )}`}
                            >
                              {rag.label}
                            </span>

                            <span className="text-xs text-zinc-500">
                              confidence: {rag.confidence}
                            </span>

                            <span className="text-xs text-zinc-500">
                              similarity: {rag.similarity}
                            </span>
                            <button
                              onClick={() => applyRAG(c.id)}
                              className="mt-2 px-3 py-1 text-xs bg-green-700 text-white rounded-lg hover:bg-green-800"
                            >
                              Apply RAG Decision
                            </button>
                          </div>

                          {/* ALL EVIDENCE */}
                          <div className="space-y-2">
                            {(rag.top_chunks || []).map((chunk, i) => (
                              <div
                                key={i}
                                className="text-xs p-3 rounded-lg bg-zinc-100 border"
                              >
                                <div>{chunk.text}</div>

                                <div className="text-[10px] text-zinc-400 mt-1">
                                  page: {chunk.page} • score:{" "}
                                  {chunk.final_score?.toFixed(2)}
                                </div>
                              </div>
                            ))}
                          </div>

                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}

            {filtered.length === 0 && (
              <tr>
                <td colSpan={4} className="py-8 text-center text-zinc-500">
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