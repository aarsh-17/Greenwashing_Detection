import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ScoreRing from "../components/ScoringRing.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import StatCard from "../components/StatCard.jsx";
import ClaimsTable from "../components/ClaimsTable.jsx";
import VersionTimeline from "../components/VersionTimeline";

import {
  getDocumentDetails,
  getDocumentClaims,
  anchorDocumentToBlockchain,
  verifyDocumentOnChain,
  getDocumentVersions
} from "../api/claimsAPI.js";

export default function DocumentDetails() {
  const { docId } = useParams();

  const [doc, setDoc] = useState(null);
  
  const [versions, setVersions] = useState([]);
  // Anchor states
  const [anchoring, setAnchoring] = useState(false);
  const [blockchainTx, setBlockchainTx] = useState(null);
  const [anchorStatus, setAnchorStatus] = useState(null);

  // Verify states
  const [verifying, setVerifying] = useState(false);
  const [verifyStatus, setVerifyStatus] = useState(null);
  const [verifyData, setVerifyData] = useState(null);

  // ---------- Load Data ----------
  async function load() {
    const docData = await getDocumentDetails(docId);
    const claimsData = await getDocumentClaims(docId);

    setDoc({ ...docData, claims: claimsData });

    // if already anchored, show tx
    if (docData.blockchain_tx) {
      setBlockchainTx(docData.blockchain_tx);
    }
  }
  async function loadVersions() {
    try {
      const res = await getDocumentVersions(docId);
      setVersions(res.versions);
    } catch (err) {
      console.error(err);
    }
  }
  // ---------- Anchor ----------
  async function handleAnchor() {
    try {
      setAnchoring(true);
      setAnchorStatus(null);

      const payload = {
        docId: docId,
        company: doc.company,
        overall_score: doc.score,
        risk_level: doc.riskLevel,
        total_claims: doc.totalClaims
      };

      const res = await anchorDocumentToBlockchain(payload);

      setBlockchainTx(res.txHash);
      setAnchorStatus(`ANCHORED (v${res.version})`);

    } catch (err) {
      console.error(err);
      setAnchorStatus("ERROR");
    } finally {
      setAnchoring(false);
    }
  }

  // ---------- Verify ----------
  async function handleVerify() {
  try {
    setVerifying(true);
    setVerifyStatus(null);

    const payload = {
      docId: docId,
      company: doc.company,
      overall_score: doc.score,
      risk_level: doc.riskLevel,
      total_claims: doc.totalClaims
    };

    const res = await verifyDocumentOnChain(payload);
    console.log("Verification result:", res);

    setVerifyData(res);
    setVerifyStatus(
      res.valid 
        ? `VALID (v${res.currentVersion})`
        : "TAMPERED"
    );

  } catch (err) {
    console.error(err);
    setVerifyStatus("ERROR");
  } finally {
    setVerifying(false);
  }
}

  // ---------- RAG ----------
  async function handleRAG() {
    try {
      const data = await fetch(
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
    loadVersions();
  }, [docId]);

  if (!doc) return <div className="text-zinc-500">Loading...</div>;

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="rounded-2xl border bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          
          {/* LEFT */}
          <div>
            <div className="text-sm text-zinc-500">Document</div>
            <div className="text-xl font-bold">{doc.filename}</div>

            <div className="mt-2">
              <RiskBadge level={doc.riskLevel} />
            </div>
          </div>

          {/* RIGHT */}
          <div className="flex items-center gap-5">

            {/* ACTIONS */}
            <div className="flex flex-col gap-2 mt-4">

              {/* Anchor */}
              {!blockchainTx ? (
                <button
                  onClick={handleAnchor}
                  disabled={anchoring}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  {anchoring ? "Anchoring..." : "Anchor to Blockchain"}
                </button>
              ) : (
                <div className="text-sm text-emerald-700 font-medium">
                  ✔ Anchored
                  <div className="mt-1">
                    <a
                      href={`https://amoy.polygonscan.com/tx/${blockchainTx}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 underline"
                    >
                      View Transaction
                    </a>
                  </div>
                </div>
              )}

              {/* Verify */}
              <button
                onClick={handleVerify}
                disabled={verifying}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {verifying ? "Verifying..." : "Verify on Blockchain"}
              </button>

              {/* Anchor Error */}
              {anchorStatus === "ERROR" && (
                <div className="text-sm text-red-600">
                  Failed to anchor
                </div>
              )}

              {/* Verify Result */}
              {verifyStatus && (
                <div className="text-sm">
                  {verifyStatus === "VALID" && (
                    <div className="text-green-600 font-medium">
                      ✅ Verified (Authentic)
                    </div>
                  )}

                  {verifyStatus === "TAMPERED" && (
                    <div className="text-red-600 font-medium">
                      ❌ Tampered
                    </div>
                  )}

                  {verifyStatus === "NOT_ANCHORED" && (
                    <div className="text-yellow-600">
                      ⚠️ Not anchored
                    </div>
                  )}

                  {verifyStatus === "ERROR" && (
                    <div className="text-red-600">
                      Verification failed
                    </div>
                  )}
                </div>
              )}

              {verifyData && (
                <div className="text-xs text-zinc-600 mt-2">
                  <div>
                    Document ID: <span className="font-medium">{verifyData.docId}</span>
                  </div>
                  <div>
                    Status:{" "}
                    <span className={verifyData.valid ? "text-green-600" : "text-red-600"}>
                      {verifyData.valid ? "VALID (Authentic)" : "TAMPERED"}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* SCORE */}
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

      {/* STATS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Total Claims" value={doc.summary.totalClaims} />
        <StatCard label="ESG Claims" value={doc.summary.esgClaims} />
        <StatCard label="Risky Claims" value={doc.summary.riskyClaims} />
      </div>

      {/* RAG */}
      <VersionTimeline versions={versions} />

      {/* TABLE */}
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