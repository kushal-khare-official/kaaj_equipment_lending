# Hatchet Workflow Conversion - Complete

## Overview

Workflows have been converted to Hatchet SDK v0.40+ format. This document provides a reference for the converted workflows.

---

## File Structure

```
workflows/
├── __init__.py              # Package exports
├── hatchet_client.py        # Hatchet client singleton
├── application_workflow.py  # Main application processing workflow
├── match_flow.py            # Standalone lender matching workflow
├── worker.py                # Worker entry point
└── HATCHET_CONVERSION.md    # This documentation
```

---

## Workflows

### 1. ApplicationWorkflow

**Event Trigger**: `application:process`

**Purpose**: Process loan applications through verification, risk assessment, and lender matching.

**DAG Structure**:
```
validate → verify → analyze_docs → derive → assess ─┬─► match ────────┬─► persist
                                                    └─► request_docs ──┘
```

**Steps**:

| Step | Timeout | Retries | Parents | Description |
|------|---------|---------|---------|-------------|
| `validate` | 5s | 0 | - | Validate required fields per application step |
| `verify` | 60s | 3 | validate | Run KYC/KYB/Credit checks in parallel |
| `analyze_docs` | 120s | 2 | verify | AI document analysis (DOCUMENTS step only) |
| `derive` | 10s | 1 | analyze_docs | Calculate derived features |
| `assess` | 5s | 0 | derive | Calculate overall risk level |
| `request_docs` | 10s | 1 | assess | Auto-request documents based on failures |
| `match` | 30s | 2 | assess | Match against lender programs (REVIEW step) |
| `persist` | 10s | 3 | match, request_docs | Save results to database |

**Input Schema**:
```python
{
    "application_id": str,  # UUID as string
    "step": str,            # ApplicationStep.value
    "run_matching": bool    # True only for REVIEW step
}
```

**Usage**:
```python
from app.workflows import run_application_workflow, run_workflow_sync

# Async
match_run = await run_application_workflow(application, step, db)

# Sync
match_run = run_workflow_sync(application, step, db)
```

---

### 2. MatchWorkflow

**Event Trigger**: `match:run`

**Purpose**: Match applications against lender programs.

**DAG Structure**:
```
derive_features → evaluate_programs → aggregate
```

**Steps**:

| Step | Timeout | Retries | Parents | Description |
|------|---------|---------|---------|-------------|
| `derive_features` | 10s | 1 | - | Derive features from application data |
| `evaluate_programs` | 30s | 2 | derive_features | Evaluate each lender program |
| `aggregate` | 5s | 0 | evaluate_programs | Sort and persist match results |

**Input Schema**:
```python
{
    "application_id": str,       # UUID as string
    "check_results": dict | None # Optional external check results
}
```

**Usage**:
```python
from app.workflows import run_match_workflow, run_match_workflow_async

# Sync (backward compatible)
match_run = run_match_workflow(app, programs, check_results)

# Async via Hatchet
result = await run_match_workflow_async(application_id, check_results)
```

---

## Running the Worker

Start the Hatchet worker to process workflows:

```bash
# From backend directory
cd backend

# Run worker
python -m app.workflows.worker
```

The worker will:
1. Connect to Hatchet server (configured via environment variables)
2. Register `ApplicationWorkflow` and `MatchWorkflow`
3. Listen for workflow events and execute steps

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HATCHET_CLIENT_TOKEN` | No | None | API token for Hatchet |
| `HATCHET_HOST_PORT` | No | localhost:7070 | Hatchet server address |
| `HATCHET_TLS_ENABLED` | No | false | Enable TLS |

---

## Key Patterns

### Database Session Handling

Each step creates its own database session to avoid long-lived connections:

```python
def get_db_session() -> Session:
    return SessionLocal()

@hatchet.step(...)
async def my_step(self, context: Context) -> Dict[str, Any]:
    db = get_db_session()
    try:
        # ... work with db
    finally:
        db.close()
```

### Accessing Parent Step Output

```python
@hatchet.step(parents=["validate"])
async def verify(self, context: Context) -> Dict[str, Any]:
    validate_output = context.step_output("validate")
    # Use validate_output...
```

### Workflow Input

```python
@hatchet.step(...)
async def validate(self, context: Context) -> Dict[str, Any]:
    input_data = context.workflow_input()
    application_id = UUID(input_data["application_id"])
    # ...
```

---

## Triggering Workflows

### Via Event

```python
await hatchet.event.push("application:process", {
    "application_id": str(app.id),
    "step": "review",
    "run_matching": True,
})
```

### Direct Run

```python
# Async (waits for completion)
result = await hatchet.workflows.ApplicationWorkflow.run(input_data)

# Spawn (returns immediately)
handle = await hatchet.workflows.ApplicationWorkflow.spawn(input_data)
result = await handle.result()
```

---

## Testing

### Unit Testing Steps

```python
import pytest
from app.workflows.application_workflow import ApplicationWorkflow

@pytest.fixture
def mock_context():
    class MockContext:
        def workflow_input(self):
            return {"application_id": "...", "step": "review", "run_matching": True}
        def step_output(self, name):
            return {"status": "passed", "application_data": {...}}
    return MockContext()

async def test_validate_step(mock_context):
    workflow = ApplicationWorkflow()
    result = await workflow.validate(mock_context)
    assert result["status"] == "passed"
```

### Integration Testing

```python
async def test_full_workflow():
    result = await hatchet.workflows.ApplicationWorkflow.run({
        "application_id": str(test_app.id),
        "step": "review",
        "run_matching": True,
    })
    assert result["persist"]["status"] == "completed"
```

---

## Migration Notes

### From Previous Implementation

The workflows maintain backward compatibility:

1. `run_match_workflow(app, programs, check_results)` - Works as before
2. `run_workflow_sync(application, step, db)` - Works as before

New async functions are available for better Hatchet integration:

1. `run_application_workflow(application, step, db)` - Async via Hatchet
2. `run_match_workflow_async(application_id, check_results)` - Async via Hatchet

### API Changes

- Step methods are now `async def` instead of `def`
- `context.step_output()` instead of direct variable access
- All data passed between steps must be JSON-serializable
