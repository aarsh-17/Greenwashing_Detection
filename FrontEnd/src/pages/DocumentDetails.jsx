import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ScoreRing from "../components/ScoringRing.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import StatCard from "../components/StatCard.jsx";
import ClaimsTable from "../components/ClaimsTable.jsx";

import { getDocumentDetails, getDocumentClaims } from "../api/claimsAPI.js";

export default function DocumentDetails() {
  const { docId } = useParams();
  const [doc, setDoc] = useState(null);

 

useEffect(() => {
  async function load() {
    const docData = await getDocumentDetails(docId);
    const claimsData = await getDocumentClaims(docId);
    setDoc({ ...docData, claims: claimsData });
  }
  load();
}, [docId]);

  if (!doc) return <div className="text-zinc-500">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="text-sm text-zinc-500">Document</div>
            <div className="text-xl font-bold">{doc.filename}</div>
            <div className="mt-2">
              <RiskBadge level={doc.riskLevel} />
            </div>
          </div>

          <div className="flex items-center gap-5">
            <ScoreRing score={doc.score} />
            <div>
              <div className="text-sm text-zinc-500">Greenwashing Risk</div>
              <div className="text-2xl font-bold">
                {doc.score}/100
              </div>
              <div className="text-sm text-zinc-500 mt-1">
                Flag: <span className="font-semibold">{doc.riskLevel}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Total Claims" value={doc.summary.totalClaims} />
        <StatCard label="ESG Claims" value={doc.summary.esgClaims} />
        <StatCard label="Risky Claims" value={doc.summary.riskyClaims} />
      </div>

      <ClaimsTable claims={doc.claims} />
    </div>
  );
}
