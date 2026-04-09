import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ScoreRing from "../components/ScoringRing.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import StatCard from "../components/StatCard.jsx";
import ClaimsTable from "../components/ClaimsTable.jsx";

import { getDocumentDetails, getDocumentClaims } from "../api/claimsAPI.js";
import { anchorDocumentToBlockchain } from "../api/claimsAPI.js";


export default function DocumentDetails() {
  const { docId } = useParams();
  const [doc, setDoc] = useState(null);
  const [anchoring, setAnchoring] = useState(false);
  const [blockchainTx, setBlockchainTx] = useState(null);
  const [anchorStatus, setAnchorStatus] = useState(null);
    
  async function load() {
      const docData = await getDocumentDetails(docId);
      const claimsData = await getDocumentClaims(docId);
      setDoc({ ...docData, claims: claimsData });
    }
 

  async function handleAnchor() {
    try {
      setAnchoring(true);
      setAnchorStatus(null);

      const res = await anchorDocumentToBlockchain(docId);

      setBlockchainTx(res.blockchain_tx);
      setAnchorStatus("ANCHORED");
    } catch (err) {
      console.error(err);
      setAnchorStatus("ERROR");
    } finally {
      setAnchoring(false);
    }
  }

  async function handleRAG() {
    try {
      const data=await fetch(
        `http://localhost:8000/api/rag/process-rag?doc_id=${docId}`,
        { method: "POST" }
      );
      const res = await data.json();
      console.log(res);
    } catch (err) {
      console.error(err);
    }
  }
  useEffect(() => {
    
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
            <div className="mt-4">
              {!blockchainTx ? (
                <button
                  onClick={handleAnchor}
                  disabled={anchoring}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  {anchoring ? "Anchoring on Blockchain..." : "Anchor to Blockchain"}
                </button>
              ) : (
                <div className="text-sm text-emerald-700 font-medium">
                  ✔ Anchored on Blockchain
                  <div className="mt-1">
                    <a
                      href={`https://amoy.polygonscan.com/tx/${blockchainTx}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 underline"
                    >
                      View on Polygonscan
                    </a>
                  </div>
                </div>
              )}

              {anchorStatus === "ERROR" && (
                <div className="text-sm text-red-600 mt-1">
                  Failed to anchor document
                </div>
              )}
            </div>

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

      <div>
        <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          onClick={handleRAG}>
          Check RAG
        </button>
      </div>

      <ClaimsTable
        claims={doc.claims}
        refresh={load}
        onDelete={(id) =>
          setDoc((prev) => ({
            ...prev,
            claims: prev.claims.filter((c) => c.id !== id),
          }))
        }
      />
    </div>
  );
}
