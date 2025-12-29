# Lender Matching Platform

A lender matching platform for equipment finance that evaluates loan applications against multiple lender credit boxes. The system collects borrower/application data, normalizes lender policies into rules, and returns eligibility matches with transparent reasoning.

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

## License

Proprietary - All rights reserved.
