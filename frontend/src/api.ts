const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000"

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

export async function getApplication(applicationId: string) {
  const res = await fetch(`${API_BASE}/applications/${applicationId}`)
  if (!res.ok) throw new Error("failed to load application")
  return res.json()
}

export async function updateApplication(applicationId: string, data: Record<string, unknown>) {
  const res = await fetch(`${API_BASE}/applications/${applicationId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error("failed to update application")
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

export type LenderCriteriaInput = {
  field_key: string
  data_type: string
  operator: string
  value_min?: string
  value_max?: string
  values?: string[]
  pattern?: string
  description?: string
}

export type LenderProgramInput = {
  name: string
  description?: string
  criteria: LenderCriteriaInput[]
}

export type LenderCreateInput = {
  name: string
  programs: LenderProgramInput[]
}

export async function createLender(payload: LenderCreateInput) {
  const res = await fetch(`${API_BASE}/lenders`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Role": "underwriter",
    },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error("failed to create lender")
  return res.json()
}

export async function deleteLender(lenderId: string) {
  const res = await fetch(`${API_BASE}/lenders/${lenderId}`, {
    method: "DELETE",
    headers: {
      "X-Role": "underwriter",
    },
  })
  if (!res.ok) throw new Error("failed to delete lender")
  return
}

export async function updateLender(lenderId: string, payload: Partial<LenderCreateInput>) {
  const res = await fetch(`${API_BASE}/lenders/${lenderId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-Role": "underwriter",
    },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error("failed to update lender")
  return res.json()
}

// Mock Vendor APIs
export async function businessSearch(businessName: string) {
  const res = await fetch(`${API_BASE}/mock/business-search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ business_name: businessName }),
  })
  if (!res.ok) throw new Error("failed to search businesses")
  return res.json()
}

export async function businessPrefill(businessId: string) {
  const res = await fetch(`${API_BASE}/mock/business-prefill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ business_id: businessId }),
  })
  if (!res.ok) throw new Error("failed to fetch business prefill")
  return res.json()
}

export async function kybCheck(businessName: string, tin?: string) {
  const res = await fetch(`${API_BASE}/mock/kyb`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ business_name: businessName, tin }),
  })
  if (!res.ok) throw new Error("failed to run KYB check")
  return res.json()
}

export async function creditCheck(ssn: string, firstName?: string, lastName?: string) {
  const res = await fetch(`${API_BASE}/mock/credit-check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ssn, first_name: firstName, last_name: lastName }),
  })
  if (!res.ok) throw new Error("failed to run credit check")
  return res.json()
}

export async function kycCheck(ssn: string, firstName?: string, lastName?: string, address?: string) {
  const res = await fetch(`${API_BASE}/mock/kyc`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ssn, first_name: firstName, last_name: lastName, address }),
  })
  if (!res.ok) throw new Error("failed to run KYC check")
  return res.json()
}

