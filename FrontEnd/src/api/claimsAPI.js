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

export async function anchorDocumentToBlockchain(docId) {
  const res = await fetch(
    `http://localhost:8000/documents/${docId}/anchor`,
    {
      method: "POST",
    }
  );

  if (!res.ok) {
    throw new Error("Failed to anchor document");
  }

  return res.json();
}

export async function verifyDocumentOnChain(docId) {
  const res = await fetch(
    `http://localhost:8000/documents/${docId}/verify-onchain`
  );

  if (!res.ok) {
    throw new Error("Verification failed");
  }

  return res.json();
}
