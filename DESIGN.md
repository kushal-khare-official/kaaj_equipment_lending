# App Design Document — Lender Matching Platform

## 1. Problem Statement
Small businesses and brokers need to quickly determine which equipment finance lenders fit a given loan request, based on nuanced credit boxes that vary by lender. Manual review of PDFs is slow, error-prone, and hard to update. We need a system that normalizes lender policies, collects borrower/app data, and returns eligibility and best-fit matches with transparent reasoning, while remaining easy to extend as new lender PDFs arrive.

## 2. Target Users
- Brokers and loan officers submitting equipment finance deals.
- Credit/ops analysts maintaining lender policies and rules.
- Internal product team members reviewing matches and debugging decisions.

## 3. User Journey (High-Level)
Merchant
1) Fills a loan application; system pre-fills wherever possible via third-party data vendors (business/identity/vehicle verification) to reduce manual entry.  
2) Third-party checks (credit, KYC/KYB, business prefill) are initiated in parallel as guarantor/business info is entered/verified; validation runs and derived features are computed (equipment age/mileage, industry flags).  
3) Waits while the underwriting workflow runs; sees status updates.  
4) If additional documents are requested, uploads them.  
5) If approved, reviews terms and signs digitally; if rejected, sees reasons.

Underwriter
1) Views applications, match reasoning, and status.  
2) Requests additional documents and re-runs the workflow after documents arrive.  
3) Views lender policies and adds/edits criteria for all lenders.  
4) Can trigger re-evaluation when policies change.

## 4. Features
- Loan application form (business, guarantor, business credit, equipment, request).
- Lender policy registry with normalized criteria (FICO/PayNet, TIB, loan amounts, equipment types/age/mileage, geography, industry exclusions, collateral type).
- Dynamic criteria engine: typed rules per data element (int/decimal range, in/not_in lists, string contains, boolean checks) to let lenders add new data points and rules without code changes.
- Matching engine: eligibility, best tier/program selection, fit score, reasons for ineligibility.
- Results display: matched/unmatched lenders with per-criterion pass/fail and narrative.
- CRUD for applications; view details and latest match result.
- Lender policy viewer/editor (CRUD) with versioning/effective dating and audit trail.
- Add new lender via manual policy configuration (no PDF upload; underwriter enters criteria directly).
- Persistence in Postgres; API via FastAPI.
- Workflow orchestration with Hatchet: parallel lender eval + retries.
- PDF ingestion helper: metadata capture + manual mapping flow; auto-parse stub.
- Role-based access (broker vs. policy admin).
- Scenario testing/sandbox for “what-if” adjustments.
- Batch uploads and webhooks for status callbacks.
- Scoring explainability view and export (CSV/PDF).
- Audit trail (compliance): all actions, manual/automated, on loan application data and policy changes.
- README/DECISIONS docs; tests for matching logic and critical flows.
- Auth:
  - Merchant: pre-authenticated link via email (no credentials); link-scoped to application/session.
  - Underwriter/admin: ID/password login to back-office portal.

## 5. UI/UX Overview (aligned to journeys)
- Screens:
  - Merchant-facing application form with prefill indicators (third-party data fetched) and manual overrides; pre-auth link entry.
  - Application status/detail: shows submitted data, derived features, underwriting status (Processing/Pending/Approved/Declined), requested documents list, upload area, and audit trail of actions/requests.
  - Match results: per-lender pass/fail by criterion, fit score, best program/tier, and reasons.
  - Offer/terms review + digital signing step for approved applications.
  - Underwriter console: login page; application workbench with doc request controls, re-run workflow trigger, and match reasoning.
  - Lender policies list + policy detail/editor (programs, criteria, effective dates, version history, audit trail).
  - Add new lender: manual policy config form (no PDF upload; underwriter enters criteria directly).
- Components:
  - Form sections: Borrower/Business, Guarantor (primary emphasized), Business Credit, Equipment, Loan Request, Documents.
  - Prefill badges and validation alerts for missing/required data.
  - Document request list and upload widget with status tags.
  - Policy criteria table and inline rule editor with version notes.
  - Match result cards with pass/fail chips, fit score badge, rejection reasons list.
  - Audit trail timeline for application/policy actions.
- Navigation flow:
  - Merchant: Magic/pre-auth link → Create Application (prefill) → Review/Submit (parallel checks running) → Status/Docs → Results → Terms & eSign.
  - Underwriter: Login → Applications list → Application workbench (request docs, re-run) → Results → Record decision; Lenders list → Policy detail/edit/add → Save → Re-run match on an application.

## 6. Constraints / Edge Cases
- Multiple guarantors: default to primary guarantor for personal criteria unless a lender explicitly requires multiple; allow override per lender rule.
- Equipment-specific rules: age, mileage bands, collateral class (class 8 truck vs. light duty), titled vs. non-titled, soft collateral.
- Geography bans (e.g., state exclusions like CA) and industry exclusions (e.g., cannabis).
- Startups vs. established businesses (TIB thresholds; startup programs).
- Missing data: must fail validation early with actionable messages.
- Policy changes over time: need effective dating or versioning (stub in v1, plan in v2).
- Private-party sales vs. dealer; CDL requirements; homeownership requirements.
- Parallel third-party checks: trigger credit/KYC/KYB/business prefill as soon as identifiers are entered; handle partial results/timeouts gracefully and surface status to user.

## 9. Application State Flows
- Processing → Approved → Completed (signed)
- Processing → Pending (additional documents) → Approved → Completed (signed)
- Processing → Pending (additional documents) → Approved → Closed (terms rejected by merchant)
- Processing → Pending (additional documents) → Declined (no lender match or manual decline)
## 8. Data to Collect (from PDF lender guidelines)
- Business profile: legal name, EIN, state, industry/NAICS, physical location (flag “no physical location”), years in business (TIB), annual sales/revenue (Apex corp-only ≥$3MM), number of trucks/units (Falcon trucking requires ≥5 trucks), comparable commercial credit history (percent of request paid down: Apex 50–75%, Falcon ≥70%).
- Guarantors: personal FICO (Stearns tiered 700–725, Apex 640–700, Advantage+ ≥680/700 for startups, Falcon ≥680/700 for trucking), homeownership (Citizens Tier 1), CDL status/years (Citizens + trucking deals), prior bankruptcies (Stearns none <7y, Falcon ≥15y), judgments/foreclosures/repos/collections (Advantage+ no recent), secondary income sources (Advantage+ optional), PG percentage of ownership (Citizens ≥10% must PG).
- Business credit: PayNet score (Stearns tiered 665–700, Apex 640–660+, Falcon ≥660), trade lines/payment activity (Stearns 3+ contracts $10k in last 12 months), revolving utilization and unsecured debt totals (Stearns thresholds $30k/$50k), comparable business borrowing lines (Apex %, Falcon 70%).
- Financials: last 3 months bank statements (Apex over thresholds, Advantage+ optional, Citizens Tier 1), 2 years tax returns or accountant-prepared financials (Apex A/B, corp-only), P&L/leverage/cash-flow indicators (Apex corp-only), personal financial statements (Advantage+ start-ups).
- Loan request: amount (caps: Advantage+ ≤$75k, Apex up to $500k, Falcon app-only limits by industry), term (24–60 months common), down payment/security deposit (Advantage+ 10% + extra 10% for startups), deferred payment option (Apex 90-day for A credit), soft cost percent (Apex max 25%), commission points (Apex per amount band).
- Collateral/equipment: type/class (class 8 truck/trailer, dump, medium/light duty, construction heavy/medium/light, soft collateral), year model bands (Citizens tables; Falcon class 8 ≤10 years old, reefer <7 years), mileage bands (Citizens mileage tiers), age adders (Falcon +0.5% per 15 years), titled vs. non-titled, private-party sale (Falcon +1.0%), reefer hours, dealer vs. private party (Citizens requires title/inspection), equipment condition/overhauls (Citizens notes), maximum mileage (Advantage+ none, Citizens limits).
- Geography & exclusions: state bans (Citizens excludes CA), foreign country not allowed (Stearns), industry exclusions (Stearns list: gaming, hazmat, weapons, etc.; cannabis undesired per Citizens note), restaurant/tanning/beauty exclusions, non-essential use.
- Documentation & process: signed credit app (Apex), equipment quote/invoice, inspections (Citizens private-party DOT + 3rd party; Lemon Squad acceptable), GPS required for some tiers (Citizens), DocuSign acceptance (Advantage+ yes), ACH preference (Citizens), insurance proof with lender as loss payee (Citizens).
## 7. Open Questions
- Guarantor evaluation: default to primary guarantor for personal criteria unless a lender explicitly requires multiple guarantors to meet mins; allow per-lender override.
- Fit score weighting: prioritize lender-required floors first (FICO/PayNet/TIB), then collateral alignment (age/mileage/class), geography/industry exclusions, then financial depth/comparables; allow configurable weights per lender/program.
- Audit/document storage: audit trail required in MVP for all actions on applications/policies/match runs; document storage optional but keep hooks.
- Deployment: backend on Heroku; frontend on Vercel.

## 10. Integrations & Third-Party Checks
- Credit: pull soft credit for guarantors (e.g., TransUnion/Experian partner API) on guarantor entry.
- KYC/KYB: identity and business verification (e.g., Alloy/Persona/Trulioo); trigger as data is keyed.
- Business prefill: firmographics and address (e.g., Clearbit/ZoomInfo/Google Places); VIN/equipment lookup if needed.
- Bank/financials (optional hook): Plaid or statement upload parsing for cash-flow checks.
- Document signing: eSign provider stub (e.g., DocuSign/HelloSign) for approval stage.
- Webhooks/callbacks: surface third-party status into application timeline and audit trail.

## 11. Data Modeling & Diagrams
- DB models (high level): Application, Guarantor (primary flag), BusinessCredit, Equipment, LoanRequest, Lender, LenderProgram, LenderCriteria, PolicyVersion, MatchRun, MatchResult (per-criterion detail), DocumentRequest, DocumentUpload, AuditLog, User (role: broker/underwriter/admin).
- Provide UML/class diagram (to be generated) showing relationships: Application 1-to-many Guarantor, Equipment, DocumentRequest/Upload; Lender 1-to-many Program 1-to-many Criteria; MatchRun → MatchResult; PolicyVersion links to Lender/Program; AuditLog references actor/entity.

