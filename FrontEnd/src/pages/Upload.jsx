import { useState } from "react";
import UploadDropzone from "../components/UploadDropzone.jsx";
import { useNavigate } from "react-router-dom";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const navigate = useNavigate(); // ✅ hook at top level

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      // ✅ derive company name from filename (remove .pdf)
      const company = file.name.replace(/\.pdf$/i, "").trim();

      const res = await fetch(
        `http://localhost:8000/documents/upload?company=${encodeURIComponent(company)}`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!res.ok) {
        throw new Error(`Backend error: ${res.status}`);
      }

      const data = await res.json();

      // ✅ navigate to document details
      navigate(`/documents/${data.document_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Upload PDF</h1>
        <p className="text-sm text-zinc-500">
          Upload a sustainability/ESG report to analyze greenwashing risk.
        </p>
      </div>

      <UploadDropzone onFile={setFile} />

      {file && (
        <div className="rounded-2xl border bg-white p-4 shadow-sm">
          <div className="text-sm text-zinc-500">Selected File</div>
          <div className="mt-1 font-semibold">{file.name}</div>

          <button
            disabled={loading}
            className="mt-3 rounded-xl bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-800 disabled:opacity-60"
            onClick={handleUpload}
          >
            {loading ? "Analyzing..." : "Upload & Analyze"}
          </button>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}
