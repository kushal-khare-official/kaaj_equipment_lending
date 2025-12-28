const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8100"

export async function health() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error("health check failed")
  return res.json()
}

export async function listLenders() {
  const res = await fetch(`${API_BASE}/lenders`)
  if (!res.ok) throw new Error("failed to load lenders")
  return res.json()
}

export async function createApplication(body: unknown) {
  const res = await fetch(`${API_BASE}/applications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error("failed to create application")
  return res.json()
}

export async function listDocuments(applicationId: string) {
  const res = await fetch(`${API_BASE}/documents/applications/${applicationId}`)
  if (!res.ok) throw new Error("failed to load documents")
  return res.json()
}

export async function latestMatch(applicationId: string) {
  const res = await fetch(`${API_BASE}/match/latest/${applicationId}`)
  if (!res.ok) throw new Error("failed to load match")
  return res.json()
}

export async function listMatchRuns(applicationId: string) {
  const res = await fetch(`${API_BASE}/match/application/${applicationId}`)
  if (!res.ok) throw new Error("failed to load match runs")
  return res.json()
}

export async function listApplications() {
  const res = await fetch(`${API_BASE}/applications`)
  if (!res.ok) throw new Error("failed to load applications")
  return res.json()
}

export async function requestDoc(applicationId: string, type: string) {
  const res = await fetch(`${API_BASE}/documents/applications/${applicationId}/request`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Role": "underwriter",
    },
    body: JSON.stringify({ type }),
  })
  if (!res.ok) throw new Error("failed to request doc")
  return res.json()
}

export async function rerunMatch(applicationId: string) {
  const res = await fetch(`${API_BASE}/match/${applicationId}`, {
    method: "POST",
    headers: { "X-Role": "underwriter" },
  })
  if (!res.ok) throw new Error("failed to rerun match")
  return res.json()
}

export async function updateLenderName(lenderId: string, name: string) {
  const res = await fetch(`${API_BASE}/lenders/${lenderId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-Role": "underwriter",
    },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error("failed to update lender")
  return res.json()
}

