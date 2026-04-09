import { useState } from "react";
import UploadDropzone from "../components/UploadDropzone.jsx";
import { useNavigate } from "react-router-dom";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [docId, setDocId] = useState(null);

  const [ingesting, setIngesting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const [error, setError] = useState(null);

  const navigate = useNavigate();

  // ---------- STEP 1: INGEST ----------
  const handleIngest = async () => {
    if (!file) return;

    setIngesting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(
        "http://localhost:8000/api/ingest-document",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!res.ok) throw new Error("Ingestion failed");

      const data = await res.json();

      setDocId(data.doc_id); // store doc_id for next step

    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setIngesting(false);
    }
  };

  // ---------- STEP 2: ANALYZE ----------
  const handleAnalyze = async () => {
    if (!docId) return;

    setAnalyzing(true);
    setError(null);

    try {
      const company = file.name.replace(/\.pdf$/i, "");

      const res = await fetch(
        `http://localhost:8000/documents/upload?company=${company}&doc_id=${docId}`,
        { method: "POST" }
      );

      if (!res.ok) throw new Error("Analysis failed");

      const data = await res.json();
      console.log(data);
      

      navigate(`/documents/${data.document_id}`);

    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* HEADER */}
      <div>
        <h1 className="text-2xl font-bold">Upload PDF</h1>
        <p className="text-sm text-zinc-500">
          Upload a sustainability/ESG report to analyze greenwashing risk.
        </p>
      </div>

      {/* FILE INPUT */}
      <UploadDropzone onFile={(f) => {
        setFile(f);
        setDocId(null); // reset if new file selected
      }} />

      {/* FILE CARD */}
      {file && (
        <div className="rounded-2xl border bg-white p-4 shadow-sm">
          <div className="text-sm text-zinc-500">Selected File</div>
          <div className="mt-1 font-semibold">{file.name}</div>

          {/* STEP 1 BUTTON */}
          <button
            disabled={ingesting}
            onClick={handleIngest}
            className="mt-3 mr-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {ingesting ? "Ingesting..." : "Upload & Ingest"}
          </button>

          {/* STEP 2 BUTTON */}
          <button
            disabled={!docId || analyzing}
            onClick={handleAnalyze}
            className="mt-3 rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
          >
            {analyzing ? "Analyzing..." : "Run Analysis"}
          </button>

          {/* STATUS */}
          {docId && (
            <div className="mt-2 text-xs text-green-600">
              ✅ Document ingested. Ready for analysis.
            </div>
          )}
        </div>
      )}

      {/* ERROR */}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}