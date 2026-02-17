import { useRef, useState } from "react";

export default function UploadDropzone({ onFile }) {
  const ref = useRef(null);
  const [drag, setDrag] = useState(false);

  function pick() {
    ref.current?.click();
  }

  function handleFiles(files) {
    const f = files?.[0];
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      alert("Only PDF files allowed");
      return;
    }
    onFile?.(f);
  }

  return (
    <div
      className={`rounded-2xl border bg-white p-6 shadow-sm transition ${
        drag ? "border-zinc-900" : "border-zinc-200"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        handleFiles(e.dataTransfer.files);
      }}
    >
      <input
        ref={ref}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      <div className="flex flex-col items-center text-center gap-2">
        <div className="text-lg font-semibold">Upload PDF</div>
        <div className="text-sm text-zinc-500">
          Drag & drop your sustainability report / ESG PDF
        </div>

        <button
          onClick={pick}
          className="mt-2 rounded-xl bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-800"
        >
          Choose File
        </button>

        <div className="text-xs text-zinc-500 mt-2">
          Supported: .pdf • Fast scoring • Explainable results
        </div>
      </div>
    </div>
  );
}
