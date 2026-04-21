import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import RiskBadge from "../components/RiskBadge.jsx";
import { getDocuments } from "../api/claimsAPI.js";

export default function Dashboard() {
  const [docs, setDocs] = useState([]);
  console.log(docs);
  
  useEffect(() => {
    getDocuments().then(setDocs);
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-zinc-500">
            Uploaded documents and greenwashing risk scores
          </p>
        </div>

        <Link
          to="/upload"
          className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-800"
        >
          Upload PDF
        </Link>
      </div>

      <div className="rounded-2xl border bg-white shadow-sm overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left text-zinc-500 border-b">
            <tr>
              <th className="py-3 px-4">File</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Score</th>
              <th className="py-3 px-4">Risk</th>
              <th className="py-3 px-4"></th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id} className="border-b last:border-b-0">
                <td className="py-3 px-4 font-medium">{d.company}</td>
                <td className="py-3 px-4 text-zinc-600">{d.status}</td>
                <td className="py-3 px-4 font-semibold">
                  {d.score ?? "—"}
                </td>
                <td className="py-3 px-4">
                  <RiskBadge level={d.riskLevel} />
                </td>
                <td className="py-3 px-4">
                  <Link
                    to={`/documents/${d.id}`}
                    className="text-zinc-900 font-semibold hover:underline"
                  >
                    View →
                  </Link>
                </td>
              </tr>
            ))}

            {docs.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-zinc-500">
                  No documents uploaded.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
