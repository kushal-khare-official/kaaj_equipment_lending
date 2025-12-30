# Lender Matching Platform

A lender matching platform for equipment finance that evaluates loan applications against multiple lender credit boxes. The system collects borrower/application data, normalizes lender policies into rules, and returns eligibility matches with transparent reasoning.

## 🚀 Live Demo

**Production App:** [https://kaaj-equipment-lending.vercel.app](https://kaaj-equipment-lending.vercel.app)

**Demo Video:** [Watch on Google Drive](https://drive.google.com/file/d/1I19PeOapKlM3OW6SQWp1B_zuQ4hK3Of7/view?usp=sharing)

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Local Development Setup](#local-development-setup)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)

---

## Architecture Overview

### System Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React SPA     │────▶│   FastAPI       │────▶│   SQLite/       │
│   (Frontend)    │     │   (Backend)     │     │   PostgreSQL    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Mock Vendors   │
                        │  (Credit/KYC)   │
                        └─────────────────┘
```

### Backend Stack
- **Framework:** FastAPI with SQLAlchemy ORM
- **Database:** PostgreSQL (production) / SQLite (development)
- **Migrations:** Alembic
- **Language:** Python 3.10+

### Frontend Stack
- **Framework:** React 19 + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router v7

### Key Domain Concepts

| Concept | Description |
|---------|-------------|
| **Application** | Loan request with business, guarantor, equipment, and loan details |
| **Lender** | Financial institution with one or more lending programs |
| **LenderProgram** | Specific lending product with eligibility criteria |
| **LenderCriteria** | Typed rules (range checks, in/not_in lists, boolean flags) |
| **MatchRun** | Evaluation instance with results per lender program |
| **MatchResult** | Per-program eligibility, fit score, and rejection reasons |

### Matching Flow

1. Application submitted via merchant form
2. System triggers parallel vendor checks (credit, KYC, KYB)
3. Feature derivation computes derived fields (equipment age, industry flags)
4. Matching engine evaluates all lender programs
5. Results aggregated with fit scores and per-criterion reasoning

---

## Local Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed sample lender data
python -m scripts.seed_lenders

# Start development server
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000

### Hatchet Workflow Worker (Optional)

The platform uses [Hatchet](https://hatchet.run) for workflow orchestration. To run workflows asynchronously:

```bash
# Navigate to backend directory
cd backend

# Ensure virtual environment is activated
source venv/bin/activate

# Start the Hatchet worker
python -m app.workflows.worker
```

**Environment Variables** (add to `.env`):
```env
HATCHET_CLIENT_TOKEN=your-token      # Optional for local dev
HATCHET_HOST_PORT=localhost:7070     # Default Hatchet server
HATCHET_TLS_ENABLED=false            # Set to true for production
```

The worker registers two workflows:
- **ApplicationWorkflow**: Full application processing (verification, risk assessment, matching)
- **MatchWorkflow**: Standalone lender program matching

> **Note**: The worker is optional for development. Workflows can also run synchronously within the API server.

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at: http://localhost:5173

### Environment Configuration

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=sqlite:///./dev.db
APP_NAME=Lender Matching Platform
```

For PostgreSQL (production):
```env
DATABASE_URL=postgresql://user:password@localhost:5432/lender_platform
```

---

## API Documentation

Base URL: `http://localhost:8000`

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Health Check

```
GET /health
```

**Response:**
```json
{"status": "ok"}
```

---

### Applications

#### List Applications

```
GET /applications
```

**Response:** `ApplicationOut[]`

#### Create Application

```
POST /applications
```

**Request Body:**
```json
{
  "merchant_email": "merchant@example.com",
  "guarantors": [
    {"is_primary": true, "fico": 720}
  ],
  "equipment": [
    {"type": "Truck", "year": 2020, "mileage": 50000, "titled": true, "private_party": false}
  ],
  "loan_request": {"amount": 75000}
}
```

**Response:** `ApplicationOut` with auto-triggered match results

#### Get Application

```
GET /applications/{application_id}
```

**Response:** `ApplicationOut`

---

### Lenders

#### List Lenders

```
GET /lenders
```

**Response:** `LenderOut[]`

#### Create Lender

```
POST /lenders
```

**Request Body:**
```json
{
  "name": "Premier Finance",
  "programs": [
    {
      "name": "Standard Equipment",
      "description": "Equipment financing for established businesses",
      "criteria": [
        {"field_key": "fico", "operator": "gte", "data_type": "int", "operand_int": 680},
        {"field_key": "loan_amount", "operator": "lte", "data_type": "int", "operand_int": 250000}
      ]
    }
  ]
}
```

**Response:** `LenderOut`

#### Get Lender

```
GET /lenders/{lender_id}
```

**Response:** `LenderOut`

#### Update Lender

```
PATCH /lenders/{lender_id}
```

**Request Body:**
```json
{
  "name": "Updated Lender Name",
  "programs": [...]
}
```

**Response:** `LenderOut`

#### Delete Lender

```
DELETE /lenders/{lender_id}
```

**Response:** `204 No Content`

---

### Matching

#### Run Match

Manually trigger matching for an application.

```
POST /match/{application_id}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "completed",
  "check_results": {...},
  "results": [
    {
      "lender_program_id": "uuid",
      "lender_name": "Premier Finance",
      "program_name": "Standard Equipment",
      "eligible": true,
      "fit_score": 85,
      "reasons": "All criteria passed",
      "criterion_results": [...]
    }
  ]
}
```

#### Get Latest Match

```
GET /match/latest/{application_id}
```

**Response:** `MatchRunOut`

#### List Match History

```
GET /match/application/{application_id}
```

**Response:** `MatchRunOut[]`

---

### Documents

#### Request Document

```
POST /documents/applications/{application_id}/request
```

**Headers:** `X-User-Role: underwriter`

**Request Body:**
```json
{
  "type": "bank_statement"
}
```

**Response:** `DocumentRequestOut`

#### Upload Document

```
POST /documents/requests/{request_id}/upload
```

**Request Body:**
```json
{
  "url": "https://storage.example.com/doc.pdf",
  "status": "uploaded",
  "metadata_json": {}
}
```

**Response:** `DocumentRequestOut`

#### List Documents

```
GET /documents/applications/{application_id}
```

**Response:** `DocumentRequestOut[]`

---

### Audit

#### List Audit Logs

```
GET /audit
```

**Response:** `AuditLogOut[]` (last 200 entries)

---

### Mock Vendors

Development endpoints that simulate third-party integrations.

```
GET /mock-vendors/credit-check      # Simulated credit report
GET /mock-vendors/kyc-check         # Know Your Customer check
GET /mock-vendors/kyb-check         # Know Your Business check
GET /mock-vendors/business-prefill  # Business data prefill
```

---

## Project Structure

```
lender_matching_platform/
├── backend/
│   ├── app/
│   │   ├── api/routers/        # REST endpoints
│   │   │   ├── applications.py
│   │   │   ├── lenders.py
│   │   │   ├── match.py
│   │   │   ├── documents.py
│   │   │   ├── audit.py
│   │   │   └── mock_vendors.py
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── application.py
│   │   │   └── lender.py
│   │   ├── schemas/            # Pydantic DTOs
│   │   ├── services/           # Business logic
│   │   │   ├── matching.py     # Rule evaluation
│   │   │   └── rules.py        # Criteria engine
│   │   ├── workflows/          # Match workflow orchestration
│   │   └── shared/             # Enums and types
│   ├── alembic/                # Database migrations
│   ├── scripts/                # Utilities (seed_lenders.py)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/              # React components
│   │   │   ├── Borrower.tsx    # Application form
│   │   │   └── Underwriter.tsx # Admin console
│   │   ├── api.ts              # API client
│   │   └── AppRouter.tsx       # Route definitions
│   ├── package.json
│   └── vite.config.ts
├── docs/                       # UML diagrams
├── CLAUDE.md                   # AI assistant instructions
├── DESIGN.md                   # Feature requirements
└── IMPLEMENTATION.md           # Technical decisions
```

---

## Criteria Operators

The rule engine supports these operators for lender criteria:

| Operator | Description | Data Types |
|----------|-------------|------------|
| `gte` | Greater than or equal | int, decimal |
| `lte` | Less than or equal | int, decimal |
| `eq` | Equals | int, decimal, string, boolean |
| `in` | Value in list | string |
| `not_in` | Value not in list | string |
| `contains` | String contains | string |

**Example Criteria:**
```json
{"field_key": "fico", "operator": "gte", "data_type": "int", "operand_int": 650}
{"field_key": "state", "operator": "not_in", "data_type": "string", "operand_list": ["CA", "NY"]}
{"field_key": "equipment_type", "operator": "in", "data_type": "string", "operand_list": ["truck", "trailer"]}
```

---

## Frontend Routes

| Route | Description |
|-------|-------------|
| `/apply` | Merchant application form |
| `/applications` | Applications list (underwriter view) |
| `/lenders` | Lender policy management |

---

---

## Test Data for Mock APIs

The mock vendor APIs support test scenarios through specific patterns in input data. Use these test values to demonstrate pass/fail scenarios across all workflow steps.

### Credit Check (Personal Credit / FICO Score)

Test SSN patterns trigger different credit scenarios:

| SSN Pattern | Scenario | FICO Score | Status | Use Case |
|------------|----------|------------|--------|----------|
| `111-11-1111` | Excellent credit | 785 | ✅ Pass | Prime borrower, best rates |
| `222-22-2222` | Good credit | 725 | ✅ Pass | Standard approval |
| `333-33-3333` | Fair credit | 670 | ⚠️ Pass with conditions | Near-prime, higher rates |
| `444-44-4444` | Poor credit | 620 | ❌ Likely decline | Subprime territory |
| `555-55-5555` | Bad credit | 540 | ❌ Decline | Bankruptcy history |
| `666-66-6666` | No credit history | N/A | ❌ Fail | Cannot evaluate |
| `777-77-7777` | High utilization | 680 | ⚠️ Review | 95% credit utilization |
| `888-88-8888` | Recent delinquencies | 650 | ⚠️ Review | Recent late payments |
| `999-99-9999` | API failure | N/A | ❌ Error | Service unavailable |
| Default | Good credit | 720 | ✅ Pass | Standard scenario |

### KYC Check (Identity Verification)

Test SSN patterns trigger different KYC scenarios:

| SSN Pattern | Scenario | Verified | Status | Use Case |
|------------|----------|----------|--------|----------|
| `111-11-1111` | Verified | ✅ Yes | ✅ Pass | Clean identity |
| `222-22-2222` | Verified | ✅ Yes | ✅ Pass | Standard verification |
| `333-33-3333` | Address mismatch | ❌ No | ⚠️ Review | Address verification failed |
| `444-44-4444` | Identity failed | ❌ No | ❌ Fail | Cannot verify identity |
| `555-55-5555` | Watchlist hit | ❌ No | ⚠️ Review | OFAC sanctions list match |
| `666-66-6666` | High fraud score | ❌ No | ⚠️ Review | Fraud score 75/100 |
| `999-99-9999` | API failure | N/A | ❌ Error | Service unavailable |
| Default | Verified | ✅ Yes | ✅ Pass | Clean verification |

### KYB Check (Business Verification & PayNet Score)

Test business name keywords trigger different KYB scenarios:

| Business Name Contains | Scenario | PayNet Score | Status | Use Case |
|------------------------|----------|--------------|--------|----------|
| `EXCELLENT` | Excellent credit | 865 | ✅ Pass | 12+ years, A+ rating |
| `GOOD` | Good credit | 775 | ✅ Pass | 7 years, A rating |
| `FAIR` | Fair credit | 670 | ⚠️ Pass | 4 years, B rating |
| `POOR` | Poor credit | 580 | ⚠️ Review | Delinquent accounts |
| `STARTUP` | New business | N/A | ⚠️ Review | < 2 years, no credit history |
| `INACTIVE` | Inactive business | N/A | ❌ Fail | Business not active |
| `UNVERIFIED` | TIN failed | N/A | ❌ Fail | Cannot verify TIN |
| `FAIL` | API failure | N/A | ❌ Error | Service unavailable |
| Default | Good business | 785 | ✅ Pass | 5 years, active |

### Bank Statement Analysis

Test document URL keywords trigger different analysis scenarios:

| URL Contains | Scenario | Cash Flow Grade | Status | Use Case |
|-------------|----------|-----------------|--------|----------|
| `excellent` | Strong cash flow | A+ | ✅ Pass | $250K avg balance, $5.4M revenue |
| `good` | Good cash flow | A | ✅ Pass | $125K avg balance, $2.6M revenue |
| `fair` | Acceptable cash flow | B | ⚠️ Pass | $45K avg balance, 1 overdraft |
| `poor` | Weak cash flow | C | ⚠️ Review | $15K avg balance, negative days |
| `nsf` | Multiple NSF fees | D | ⚠️ Review | 7 NSF fees, 12 overdrafts |
| `mismatch` | Name mismatch | N/A | ⚠️ Review | Account name doesn't match |
| `tampered` | Tampering detected | N/A | ❌ Fail | Document fraud indicators |
| Default | Good cash flow | A | ✅ Pass | $75K avg balance, $1.5M revenue |

### Sample Test Scenarios

#### Scenario 1: Perfect Application (All Pass)
```
Business Name: EXCELLENT TRUCKING INC
Guarantor SSN: 111-11-1111
Bank Statement URL: https://example.com/statements/excellent_2024.pdf
Expected Result: All checks pass, auto-approved, lowest rates
```

#### Scenario 2: Marginal Application (Needs Review)
```
Business Name: FAIR LOGISTICS LLC
Guarantor SSN: 333-33-3333
Bank Statement URL: https://example.com/statements/fair_2024.pdf
Expected Result: Manual review required, document requests triggered
```

#### Scenario 3: High-Risk Application (Likely Decline)
```
Business Name: POOR TRANSPORT CO
Guarantor SSN: 555-55-5555
Bank Statement URL: https://example.com/statements/nsf_2024.pdf
Expected Result: Multiple red flags, manual review, likely rejection
```

#### Scenario 4: Startup Application (Special Handling)
```
Business Name: STARTUP DELIVERY STARTUP
Guarantor SSN: 222-22-2222
Bank Statement URL: https://example.com/statements/good_2024.pdf
Expected Result: No business credit history, relies on personal credit
```

#### Scenario 5: Mixed Signals (Complex Review)
```
Business Name: GOOD HAULING INC
Guarantor SSN: 777-77-7777 (high utilization)
Bank Statement URL: https://example.com/statements/fair_2024.pdf
Expected Result: Good business, concerning personal credit, manual review
```

### Testing Workflow Steps

1. **Step 1-2 (Business Details)**: Use business name patterns to control KYB results
2. **Step 3 (Guarantor Info)**: Use SSN patterns to control credit check and KYC results
3. **Step 4 (Equipment Info)**: No checks run (feature derivation only)
4. **Step 5 (Loan Details)**: Bank verification runs (always passes in mock)
5. **Step 6 (Documents)**: Use URL patterns to control bank statement analysis
6. **Step 7 (Review)**: Final lender matching based on accumulated results

---

## License

Proprietary - All rights reserved.
