# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a lender matching platform for equipment finance that evaluates loan applications against multiple lender credit boxes. The system collects borrower/application data, normalizes lender policies into rules, and returns eligibility matches with transparent reasoning.

**Key Users:**
- Merchants: Submit loan applications via pre-authenticated links
- Underwriters: Review applications, manage lender policies, request documents, make decisions

## Architecture

### Backend (Python/FastAPI)
- **Framework:** FastAPI with SQLAlchemy ORM and Alembic migrations
- **Database:** PostgreSQL (dev uses SQLite at `backend/dev.db`)
- **Workflow Engine:** Hatchet (planned) for orchestrated parallel lender evaluation
- **Structure:**
  - `app/models/`: SQLAlchemy models (Application, Guarantor, BusinessCredit, Equipment, Lender, LenderProgram, LenderCriteria, MatchRun, DocumentRequest, AuditLog)
  - `app/schemas/`: Pydantic request/response DTOs
  - `app/services/`: Business logic (matching engine, rule evaluation, feature derivation, audit logging)
  - `app/api/routers/`: REST endpoints (applications, lenders, match, documents, audit, storage, mock_vendors)
  - `app/workflows/`: Hatchet workflow DAGs
  - `app/shared/`: Enums and shared types
  - `scripts/`: Utilities like `seed_lenders.py` for sample data

### Frontend (React/TypeScript/Vite)
- **Stack:** React 19 + TypeScript + Vite + Tailwind CSS + React Router
- **Structure:**
  - `src/pages/`: Main views (Borrower application form, Applications list, Underwriter console)
  - `src/AppRouter.tsx`: Route definitions
  - `src/api.ts`: API client functions
- **Routes:**
  - `/apply`: Merchant application form (pre-auth link)
  - `/applications`: Underwriter applications workbench
  - `/lenders`: Lender policies management (view/add/edit)

### Core Domain Concepts
- **Application:** Represents a loan request with business, guarantor, equipment, and loan details
- **Lender/LenderProgram/LenderCriteria:** Normalized lender policies as typed rules (range checks, in/not_in lists, contains, boolean flags)
- **MatchRun/MatchResult:** Evaluation results with per-criterion pass/fail and fit scoring
- **Feature Derivation:** Computes derived fields (equipment age/mileage bands, startup vs established business, geography/industry flags) from raw application data
- **Rule Engine:** Dynamic criteria evaluation supporting multiple data types and operators without code changes

## Common Development Commands

### Backend
```bash
# From repository root
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed sample lender data
python -m scripts.seed_lenders

# Start development server (defaults to http://localhost:8000)
uvicorn app.main:app --reload

# Run tests (when available)
pytest

# Create new migration
alembic revision --autogenerate -m "description"
```

### Frontend
```bash
# From repository root
cd frontend

# Install dependencies
npm install

# Start development server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Database
- **Dev database:** SQLite at `backend/dev.db`
- **Connection string:** Configured via `backend/app/config.py` (reads from `.env` file)
- **Migrations:** Managed by Alembic in `backend/alembic/`

## API Architecture

All API routers are mounted in `backend/app/main.py`:
- `/mock-vendors/*`: Mock third-party vendor responses (credit, KYC, business prefill)
- `/applications/*`: CRUD and submission endpoints
- `/lenders/*`: Lender and program management
- `/match/*`: Trigger and retrieve matching results
- `/documents/*`: Document request/upload handling
- `/audit/*`: Audit trail retrieval
- `/storage/*`: File upload/storage utilities
- `/health`: Health check endpoint

## Key Workflows

### Application Submission Flow
1. Merchant fills application form with pre-filled data from third-party vendors
2. System triggers parallel checks: credit pull, KYC/KYB, business prefill
3. Feature derivation computes derived fields (age/mileage bands, industry flags)
4. Matching engine evaluates against all lender programs in parallel
5. Results aggregated with fit scores and per-criterion reasoning
6. Status set to Processing → Pending (if docs needed) → Approved/Declined

### Lender Matching Logic
- Located in `backend/app/services/matching.py` and `backend/app/services/rules.py`
- Uses LenderCriteria as typed rules (field_key, operator, data_type, operands)
- Evaluates eligibility per program with pass/fail per criterion
- Computes fit score: prioritizes required floors (FICO/PayNet/TIB) > collateral alignment > geo/industry > financials
- Returns ranked match results with rejection reasons

### Policy Management
- Underwriters manually configure lender policies via UI (no PDF upload in MVP)
- Criteria stored with versioning/effective dates in LenderCriteria table
- All policy changes logged in AuditLog
- Re-evaluation can be triggered when policies change

## Testing Strategy

### Backend
- Use pytest for unit and integration tests
- Test rule evaluation logic with fixtures covering edge cases (startups, geography bans, equipment age thresholds)
- Test feature derivation with various application states
- Use SQLite or PostgreSQL in CI

### Frontend
- Use React Testing Library for critical UI flows
- Test form validation and match result rendering
- Mock API responses for isolated component testing

## Important Notes

### Data Model Relationships
- Application has one-to-many: Guarantor (with is_primary flag), Equipment, DocumentRequest
- Application has one-to-one: BusinessCredit, LoanRequest
- Lender → LenderProgram → LenderCriteria (many-to-many hierarchy)
- MatchRun produces many MatchResults (one per lender program)

### Rule System
- LenderCriteria uses typed operators: `gte`, `lte`, `in`, `not_in`, `contains`, `eq`
- Supports int, decimal, string, boolean data types
- New criteria can be added via database inserts without code changes

### Application States
- `processing`: Initial evaluation in progress
- `pending_docs`: Additional documents requested
- `approved`: Matched with at least one lender
- `declined`: No lender match or manual rejection
- `completed`: Terms accepted and signed
- `closed`: Terms rejected by merchant

### Authentication
- Merchants: Pre-authenticated magic links (no credentials)
- Underwriters: ID/password login (stub; plan for SSO)
- Role checking via simple header/env flag

### Third-Party Integrations
- Mock vendor endpoints in `backend/app/api/routers/mock_vendors.py` for local development
- Real integrations (credit, KYC, business prefill, eSign) are stubs with hooks for future implementation
- Parallel third-party checks triggered on data entry with graceful timeout handling

## Design Documentation
- **DESIGN.md**: Full feature requirements, user journeys, edge cases, and data collection details
- **IMPLEMENTATION.md**: Phased implementation plan, tech stack decisions, ERD and workflow diagrams
- **docs/**: UML/class diagrams and workflow visualizations (Mermaid format)

## Deployment
- **Backend:** Heroku with Postgres; use Procfile + Gunicorn/Uvicorn
- **Frontend:** Vercel
- **Migrations:** Run via Alembic release phase on Heroku
