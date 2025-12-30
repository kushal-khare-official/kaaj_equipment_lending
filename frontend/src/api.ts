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

// =============================================================================
// Workflow API
// =============================================================================

export type WorkflowStep =
  | "business_search"
  | "business_details"
  | "guarantor_info"
  | "equipment_info"
  | "loan_details"
  | "documents"
  | "review"
  | "submitted"

export type CheckResult = {
  check_type: string
  status: "pending" | "running" | "completed" | "failed" | "needs_review" | "skipped"
  vendor?: string
  verified?: boolean
  score?: number
  risk_level?: "low" | "medium" | "high" | "critical"
  flags: string[]
  error?: string
  duration_ms?: number
}

export type WorkflowResult = {
  match_run_id: string
  step: string
  status: string
  checks: Record<string, CheckResult>
  derived_features: Record<string, unknown>
  risk_assessment?: {
    overall_risk?: string
    risk_flags: string[]
  }
  validation_errors: string[]
  warnings: string[]
  match_results_count: number
}

export type WorkflowHistoryItem = {
  match_run_id: string
  step?: string
  status: string
  created_at?: string
  risk_level?: string
  flags_count: number
  match_results_count: number
}

export type StepInfo = {
  step: string
  checks: string[]
  description: string
}

/**
 * Trigger workflow at a specific step of the application form.
 * This runs verification checks appropriate for that step.
 */
export async function triggerWorkflow(
  applicationId: string,
  step: WorkflowStep,
  runInBackground = false
): Promise<WorkflowResult> {
  const res = await fetch(`${API_BASE}/workflow/${applicationId}/trigger`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ step, run_in_background: runInBackground }),
  })
  if (!res.ok) throw new Error("failed to trigger workflow")
  return res.json()
}

/**
 * Get the latest workflow result for an application.
 */
export async function getLatestWorkflowResult(applicationId: string): Promise<WorkflowResult> {
  const res = await fetch(`${API_BASE}/workflow/${applicationId}/latest`)
  if (!res.ok) throw new Error("failed to get workflow result")
  return res.json()
}

/**
 * Get workflow execution history for an application.
 */
export async function getWorkflowHistory(applicationId: string): Promise<{ history: WorkflowHistoryItem[] }> {
  const res = await fetch(`${API_BASE}/workflow/${applicationId}/history`)
  if (!res.ok) throw new Error("failed to get workflow history")
  return res.json()
}

/**
 * Get information about workflow steps and their checks.
 */
export async function getWorkflowSteps(): Promise<{ steps: StepInfo[] }> {
  const res = await fetch(`${API_BASE}/workflow/steps`)
  if (!res.ok) throw new Error("failed to get workflow steps")
  return res.json()
}

/**
 * Retry a specific failed check.
 */
export async function retryCheck(applicationId: string, checkType: string): Promise<CheckResult> {
  const res = await fetch(`${API_BASE}/workflow/${applicationId}/retry/${checkType}`, {
    method: "POST",
  })
  if (!res.ok) throw new Error("failed to retry check")
  return res.json()
}

/**
 * Get a specific workflow run result by match_run_id.
 */
export async function getWorkflowRun(applicationId: string, matchRunId: string): Promise<WorkflowResult> {
  const res = await fetch(`${API_BASE}/workflow/${applicationId}/run/${matchRunId}`)
  if (!res.ok) throw new Error("failed to get workflow run")
  return res.json()
}

/**
 * Review status for an application.
 */
export type ReviewStatus = {
  application_id: string
  review_status: "pending" | "auto_approved" | "pending_manual_review" | "manually_approved" | "manually_rejected"
  requires_manual_review: boolean
  reviewed_by?: string
  reviewed_at?: string
}

/**
 * Get the review status of an application.
 */
export async function getReviewStatus(applicationId: string): Promise<ReviewStatus> {
  const res = await fetch(`${API_BASE}/workflow/${applicationId}/review-status`)
  if (!res.ok) throw new Error("failed to get review status")
  return res.json()
}

/**
 * Perform manual review on an application.
 */
export async function manualReview(
  applicationId: string,
  action: "approve" | "reject",
  reviewer = "underwriter"
): Promise<ReviewStatus> {
  const res = await fetch(`${API_BASE}/workflow/${applicationId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, reviewer }),
  })
  if (!res.ok) throw new Error("failed to perform manual review")
  return res.json()
}

/**
 * Rerun the complete workflow for an application.
 */
export async function rerunWorkflow(applicationId: string): Promise<WorkflowResult> {
  const res = await fetch(`${API_BASE}/workflow/${applicationId}/rerun`, {
    method: "POST",
    headers: { "X-Role": "underwriter" },
  })
  if (!res.ok) throw new Error("failed to rerun workflow")
  return res.json()
}

/**
 * Manually match an application to a lender program.
 */
export async function manualMatch(
  applicationId: string,
  lenderProgramId: string,
  termMonths?: number,
  interestRate?: number
): Promise<{
  success: boolean
  application_id: string
  lender_program_id: string
  lender_name: string
  program_name: string
  term_months: number
  interest_rate: number
}> {
  const res = await fetch(`${API_BASE}/workflow/${applicationId}/manual-match`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Role": "underwriter" },
    body: JSON.stringify({
      lender_program_id: lenderProgramId,
      term_months: termMonths,
      interest_rate: interestRate,
    }),
  })
  if (!res.ok) throw new Error("failed to manual match")
  return res.json()
}

