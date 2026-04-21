import React from "react";

function formatTime(ts) {
  const date = new Date(Number(ts) * 1000);
  return date.toLocaleString();
}

export default function VersionTimeline({ versions }) {
  if (!versions || versions.length === 0) {
    return (
      <div className="text-sm text-zinc-500">No versions found</div>
    );
  }

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="text-lg font-semibold mb-4">
        Version History
      </div>

      <div className="relative border-l-2 border-zinc-200 ml-3">
        {versions.map((v, index) => (
          <div key={index} className="mb-6 ml-4">
            
            {/* Dot */}
            <div className="absolute w-3 h-3 bg-blue-500 rounded-full -left-1.5 mt-2"></div>

            {/* Content */}
            <div className="bg-zinc-50 rounded-lg p-3 border">
              <div className="flex justify-between items-center">
                <span className="font-medium text-blue-600">
                  Version {index + 1}
                </span>
                <span className="text-xs text-zinc-500">
                  {formatTime(v.timestamp)}
                </span>
              </div>

              <div className="mt-2 text-xs text-zinc-600 break-all">
                Hash: {v.hash}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}