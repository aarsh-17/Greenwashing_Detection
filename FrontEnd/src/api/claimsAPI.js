const API = "http://localhost:8000";

export async function getDocuments() {
  const res = await fetch(`${API}/documents`);
  if (!res.ok) {
    throw new Error("Failed to fetch documents");
  }
  return await res.json();
}

export async function getDocumentDetails(docId) {
  const res = await fetch(`${API}/documents/${docId}`);
  if (!res.ok) {
    throw new Error("Failed to fetch document");
  }
  return await res.json();
}

export async function getDocumentClaims(docId) {
  const res = await fetch(`${API}/documents/${docId}/claims`);
  if (!res.ok) {
    throw new Error("Failed to fetch claims");
  }
  return await res.json();
}

export async function anchorDocumentToBlockchain(data) {
  const res = await fetch("http://localhost:3000/store", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  if (!res.ok) {
    throw new Error("Failed to anchor document");
  }

  return res.json();
}

export async function verifyDocumentOnChain(data) {
  const res = await fetch("http://localhost:3000/verify", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  if (!res.ok) {
    throw new Error("Verification failed");
  }

  return res.json();
}

export async function getDocumentVersions(docId) {
  const res = await fetch(`http://localhost:3000/versions/${docId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch versions");
  }

  return res.json();
}