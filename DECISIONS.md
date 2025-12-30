# Design Decisions

This document captures the key decisions made during the development of the Lender Matching Platform, including which lender requirements were prioritized, simplifications made, and future enhancements.

---

## 1. Lender Requirements Prioritized

### 1.1 Core Credit Criteria (High Priority)

The following requirements were extracted from the 5 lender PDFs and implemented as first-class matching criteria:

| Criterion | Implementation | Rationale |
|-----------|---------------|-----------|
| **FICO Score** | Range operator with min/max thresholds | Universal gating criterion across all lenders; tiered programs (e.g., Stearns 725/710/700, Apex 700/670/640) |
| **PayNet Score** | Range operator with min/max thresholds | Primary business credit indicator; most lenders require 640-700+ |
| **Time in Business (TIB)** | Derived from `incorporation_date` | Distinguishes established vs. startup programs; ranges from 2-10+ years |
| **Loan Amount** | Range operator with caps per program | Critical for app-only vs. full-doc thresholds (e.g., $75K, $100K, $200K caps) |
| **Equipment Age** | Derived from `equipment.year` | Collateral depreciation; Falcon requires Class 8 ≤10 years, Apex A+ ≤5 years |

### 1.2 Eligibility Exclusions (High Priority)

| Criterion | Implementation | Rationale |
|-----------|---------------|-----------|
| **State Exclusions** | `not_in` operator with state list | Citizens excludes CA; Apex excludes CA, NV, ND, VT |
| **Private Party Sales** | Boolean check on `equipment.private_party` | Apex A+ program explicitly prohibits; affects pricing elsewhere |

### 1.3 Secondary Criteria (Medium Priority)

| Criterion | Implementation | Rationale |
|-----------|---------------|-----------|
| **Homeownership** | Boolean flag on guarantor | Citizens Tier 1 requires; differentiates risk tiers |
| **CDL Status** | Boolean flag on guarantor | Citizens startup/trucking programs require 5+ years CDL |
| **Revolving Utilization** | Decimal range (0-50%) | Apex requires 50% available; indicates credit management |
| **Equipment Mileage** | Range operator per equipment | Citizens has 600K mile cap for Class 8 trucks |

### 1.4 Interest Rates & Terms (Medium Priority)

| Feature | Implementation | Rationale |
|---------|---------------|-----------|
| **Term Ranges** | `term_min`, `term_max`, `term_default`, `term_used_equipment` | Lenders offer 24-84 month terms; used equipment gets shorter terms |
| **Interest Rates** | `interest_rate_min`, `interest_rate_max`, `interest_rate_default` | Enables "best rate" calculation; rates vary 5.99%-16.99% |
| **Best Terms Display** | Calculated at match time | Shows borrower the optimal terms across eligible lenders |

---

## 2. Simplifications Made

### 2.1 Data Model Simplifications

| Simplification | What Was Skipped | Why |
|----------------|------------------|-----|
| **Single Primary Guarantor** | Multiple guarantor evaluation | PDFs mention multiple PGs but default to primary; added `is_primary` flag for future extension |
| **Single Equipment Item Focus** | Multi-equipment complex rules | Criteria reference `equipment.0.*`; most deals are single-unit; schema supports multiple |
| **Flat Criteria Structure** | Nested/conditional rules | Some lenders have "if X then Y" logic; implemented as separate programs instead |
| **No Bankruptcy Timeline** | "BK discharged 7/15+ years" rules | Would require bankruptcy date field and timeline calculation; deferred |

### 2.2 Feature Derivation Simplifications

| Simplification | What Was Skipped | Why |
|----------------|------------------|-----|
| **TIB from Incorporation Date** | Verified business registration lookup | Real systems would pull from Secretary of State; we derive from user input |
| **Equipment Age from Year** | VIN decode / actual manufacture date | Model year is sufficient for matching; VIN lookup is a future integration |
| **No Industry Classification** | NAICS-based rules | Lenders exclude industries (gaming, cannabis, hazmat); would need NAICS mapping |

### 2.3 Workflow Simplifications

| Simplification | What Was Skipped | Why |
|----------------|------------------|-----|
| **Mock Vendor APIs** | Real credit bureau / KYB integrations | Enables demo without vendor contracts; patterns match real API structures |
| **Synchronous Matching** | Async Hatchet workflow | Hatchet scaffolded but matching runs synchronously for simplicity |
| **In-Memory Fit Scoring** | Weighted scoring with lender preferences | Simple pass/fail count; real systems would weight by lender priority |

### 2.4 UI/UX Simplifications

| Simplification | What Was Skipped | Why |
|----------------|------------------|-----|
| **Mock Authentication** | OAuth/OIDC integration | Demonstrates protected routes; production would use Auth0/Okta |
| **localStorage Auth** | Secure httpOnly cookies | Acceptable for demo; production needs proper session management |
| **Single-Page Intake** | Multi-step wizard with save/resume | Wizard flow implemented but no partial save; full submit only |

---

## 3. What Would Be Added With More Time

### 3.1 Advanced Matching Logic

| Enhancement | Description | Effort |
|-------------|-------------|--------|
| **Weighted Fit Scoring** | Configurable weights per criterion (FICO 30%, TIB 20%, etc.) | Medium |
| **Program Ranking** | Rank eligible programs by best fit, not just pass/fail | Medium |
| **Conditional Rules** | "If startup, then require 10% extra security deposit" | High |
| **Rate Calculation Engine** | Dynamic rate based on risk factors, equipment age adders | High |
| **Comparable Credit Rules** | "70% of request paid down on existing loans" (Falcon/Apex) | Medium |

### 3.2 Data Model Enhancements

| Enhancement | Description | Effort |
|-------------|-------------|--------|
| **Industry/NAICS Support** | Map business to NAICS; enforce industry exclusions | Medium |
| **Bankruptcy History** | Track BK dates; enforce "discharged 7+ years" rules | Low |
| **Multiple Guarantor Evaluation** | Aggregate scores across PGs; "all must meet min" vs "any" | Medium |
| **Equipment Class Taxonomy** | Class 8 truck vs. light duty vs. construction; affects age/mileage rules | Medium |
| **Policy Versioning** | Effective dates on criteria; historical match replay | High |

### 3.3 Third-Party Integrations

| Integration | Description | Effort |
|-------------|-------------|--------|
| **Real Credit Bureau** | TransUnion/Experian soft pull API | High |
| **PayNet Integration** | Equifax Commercial Credit | High |
| **KYC/KYB Provider** | Alloy, Persona, or Trulioo | Medium |
| **VIN Decode** | NHTSA or commercial VIN API for equipment details | Low |
| **Document OCR** | Extract data from uploaded bank statements, tax returns | High |
| **eSign Integration** | DocuSign/HelloSign for approval workflow | Medium |

### 3.4 Workflow Enhancements

| Enhancement | Description | Effort |
|-------------|-------------|--------|
| **Async Hatchet Workflows** | Parallel lender evaluation with retries | Medium |
| **Document Request Automation** | Auto-request docs based on failed criteria | Medium |
| **Re-Evaluation on Upload** | Re-run matching when new docs are uploaded | Low |
| **Webhook Callbacks** | Notify external systems on status changes | Low |
| **Audit Trail UI** | Timeline view of all application actions | Medium |

### 3.5 Testing & Quality

| Enhancement | Description | Effort |
|-------------|-------------|--------|
| **Unit Tests** | pytest coverage for rules.py, feature_derivation.py | Medium |
| **Integration Tests** | End-to-end workflow tests with mock vendors | Medium |
| **Property-Based Tests** | Hypothesis tests for rule evaluation edge cases | Medium |
| **Load Testing** | Verify matching performance at scale | Low |
| **Scenario Regression Suite** | Golden test cases for each lender program | Medium |

### 3.6 Production Readiness

| Enhancement | Description | Effort |
|-------------|-------------|--------|
| **Real Authentication** | OAuth 2.0 with Auth0/Okta; RBAC | High |
| **Document Storage** | S3 integration with encryption at rest | Medium |
| **Observability** | Structured logging, APM, error tracking | Medium |
| **Rate Limiting** | Protect APIs from abuse | Low |
| **HTTPS/Security Headers** | Production security hardening | Low |

---

## 4. Lender Program Summary

The following 5 lenders with 27 programs were implemented from the PDF documentation:

### Citizens Bank (4 programs)
- Tier 1 - General Program (700+ FICO, 2+ TIB, $75K max, homeowner required)
- Tier 2 - Start-up Program (700+ FICO, CDL required, $50K max)
- Tier 2 - Non-Homeowner Program (700+ FICO, 2+ TIB, $50K max)
- Tier 3 - Full Financials Program ($75K-$1M, full docs required)

### Advantage+ Financing (2 programs)
- Standard Program - Established Business (680+ FICO, 2+ TIB, $75K max)
- Start-Up Program (700+ FICO, <2 TIB, $75K max)

### Apex Commercial Capital (6 programs)
- A Rate Program (700+ FICO, 660+ PayNet, 5+ TIB)
- B Rate Program (670+ FICO, 650+ PayNet, 3+ TIB)
- C Rate Program (640+ FICO, 640+ PayNet, 2+ TIB)
- Medical A Rate Program (700+ FICO, licensed professional)
- A+ Rate Program (720+ FICO, 670+ PayNet, 5+ TIB, premium rates)
- Corp Only Program (no PG, 5+ TIB, $3M+ revenue)

### Falcon Equipment Finance (6 programs)
- A Credit Program (680+ FICO, 660+ PayNet, 3+ TIB)
- B Credit Program (680+ FICO, 660+ PayNet, 3+ TIB)
- C Credit Program (640+ FICO, 620+ PayNet, 3+ TIB)
- D Credit Program (600+ FICO, 580+ PayNet, 3+ TIB)
- E Credit Program (550+ FICO, 3+ TIB)
- Trucking Program (700+ FICO, 680+ PayNet, 5+ TIB, 5+ trucks)

### Stearns Bank (9 programs)
- Tier 1/2/3 Programs (725/710/700+ FICO, 685/675/665+ PayNet)
- Tier 1/2/3 No PayNet Programs (735/720/710+ FICO, higher TIB)
- Corp Only Tier 1/2/3 (700/690/680+ PayNet, no PG)

---

## 5. Key Technical Decisions

### 5.1 Dynamic Criteria Engine

**Decision**: Store criteria as typed rules (`field_key`, `operator`, `data_type`, `value_min/max/values`) rather than hard-coded logic.

**Rationale**: 
- New lender criteria can be added via SQL/admin UI without code changes
- Supports range, in/not_in, boolean, and contains operators
- Enables future policy versioning and A/B testing

### 5.2 Feature Derivation Layer

**Decision**: Separate feature derivation from rule evaluation.

**Rationale**:
- `derive_application_features()` normalizes application data into flat key-value pairs
- Rule engine evaluates against normalized features
- Enables caching, logging, and debugging of derived values
- Makes adding new derived features straightforward

### 5.3 Program-Level Matching

**Decision**: Match at the program level, not lender level.

**Rationale**:
- Lenders have multiple programs with different criteria (e.g., Apex A/B/C rates)
- Borrower may qualify for some programs but not others
- Enables "best program" selection within a lender

### 5.4 Mock Vendor Pattern

**Decision**: Implement mock vendors with deterministic test scenarios (SSN/business name patterns).

**Rationale**:
- Enables reliable demo and testing without external dependencies
- Test scenarios cover pass/fail/edge cases for each vendor type
- Same API contract as real vendors for easy swap-out

---

## 6. Trade-offs Acknowledged

| Trade-off | Decision Made | Alternative Considered |
|-----------|---------------|----------------------|
| **Simplicity vs. Completeness** | Implemented core criteria; deferred edge cases | Full PDF rule extraction |
| **Speed vs. Accuracy** | Synchronous matching; mock vendors | Async workflows; real integrations |
| **Flexibility vs. Performance** | Dynamic criteria engine | Hard-coded lender logic |
| **Demo-ability vs. Security** | Mock auth with localStorage | Real OAuth from start |
| **Single-tenant vs. Multi-tenant** | Single database; no tenant isolation | Per-tenant schemas |

---

## 7. Lessons Learned

1. **PDF Extraction is Hard**: Lender guidelines are inconsistent in format; manual extraction was faster than attempting OCR/parsing.

2. **Criteria Complexity Varies**: Some rules are simple ranges; others are conditional ("if startup AND trucking, then CDL required"). Flat criteria work for 80% of cases.

3. **Test Data is Critical**: Deterministic mock scenarios enabled rapid iteration; random data made debugging difficult.

4. **UI Drives Requirements**: Building the borrower flow revealed missing fields (SSN format, equipment make/model) that weren't in initial spec.

5. **Fit Scoring is Subjective**: "Best" lender depends on rate, term, relationship, and factors not in the data; simple pass/fail is a reasonable MVP.

