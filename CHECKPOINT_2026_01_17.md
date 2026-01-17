# finLine Development Checkpoint

**Date:** 2026-01-17
**Session:** Backend Complete, Ready for Frontend

---

## Project Overview

**finLine** is a simplified rewrite of finForge - an LBO (Leveraged Buyout) financial modeling platform. The goal was to address pain points from finForge by simplifying the architecture while keeping full LBO functionality.

### Key Simplifications from finForge
- User responsible for complete data (no edge case handling)
- Simple growth percentages instead of complex revenue drivers
- Total working capital instead of DSO/DIO/DPO modeling
- snake_case everywhere (no mixed conventions)
- SQLite instead of JSON files
- Simpler data format: `[{year, value}, ...]` arrays

---

## Current State: Backend Complete ✅

### Phases Completed

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Done | Foundation (SQLite, Config, FastAPI, Auth) |
| Phase 2 | ✅ Done | Core API (CRUD, PATCH, Bulk updates, Cases) |
| Phase 3 | ✅ Done | LBO Engine (IRR, MOIC, Debt schedules, Cash flows) |
| Phase 4 | ✅ Done | AI Features (Chat, Document Extraction, Insights) |
| Phase 5 | ✅ Done | Export & Payments (Excel, Stripe) |
| Phase 6 | 🔲 Next | Frontend (Next.js) |
| Phase 7 | 🔲 Todo | Testing & Polish |

### API Endpoints (28 total)

```
Authentication (4):
  POST   /api/auth/register
  POST   /api/auth/login
  GET    /api/auth/me
  POST   /api/auth/refresh

Projects (10):
  GET    /api/projects
  POST   /api/projects
  GET    /api/projects/{id}
  PATCH  /api/projects/{id}
  DELETE /api/projects/{id}
  PATCH  /api/projects/{id}/bulk
  POST   /api/projects/{id}/cases/{case_id}
  DELETE /api/projects/{id}/cases/{case_id}
  POST   /api/projects/{id}/analyze
  POST   /api/projects/{id}/analyze/all
  POST   /api/projects/{id}/export

Chat (2):
  POST   /api/projects/{id}/chat
  POST   /api/projects/{id}/chat/apply

Extraction (3):
  POST   /api/projects/{id}/extract
  GET    /api/projects/{id}/extractions/{eid}
  POST   /api/projects/{id}/extractions/{eid}/merge

Insights (2):
  POST   /api/projects/{id}/insights
  GET    /api/projects/{id}/insights/quick

Payments (4):
  POST   /api/payments/create-checkout
  GET    /api/payments/subscription
  POST   /api/payments/portal
  POST   /api/payments/webhook
```

---

## File Structure

```
/Users/jadesip/finLine/
├── IMPLEMENTATION_PLAN.md      # Full implementation roadmap
├── CHECKPOINT_2026_01_17.md    # This file
├── backend/
│   ├── .venv/                  # Python virtual environment
│   ├── requirements.txt        # Dependencies
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings (Pydantic)
│   ├── database.py             # SQLite operations
│   ├── api/
│   │   ├── auth.py             # JWT authentication
│   │   ├── projects.py         # Project CRUD + analyze + export
│   │   ├── chat.py             # Natural language chat
│   │   ├── extraction.py       # Document extraction API
│   │   ├── insights.py         # Perplexity insights
│   │   └── payments.py         # Stripe integration
│   ├── engine/
│   │   ├── models.py           # FinFigs, DebtTranche, DealParameters
│   │   ├── extractor.py        # JSON → analysis objects
│   │   ├── sources_uses.py     # Entry equity calculation
│   │   ├── cash_flow.py        # FCF, CFADS projections
│   │   ├── debt.py             # Debt schedule tracker
│   │   ├── returns.py          # IRR, MOIC calculations
│   │   └── lbo.py              # Main orchestrator
│   ├── services/
│   │   ├── excel.py            # Excel export
│   │   └── extraction/         # Document extraction service
│   │       ├── models.py
│   │       ├── file_handler.py
│   │       ├── image_optimizer.py
│   │       ├── prompts.py
│   │       └── extractor.py
│   └── models/
│       └── schemas.py          # Pydantic request/response models
├── frontend/                   # Next.js (stub - needs implementation)
└── data/
    └── finline.db              # SQLite database
```

---

## Key Technical Details

### Data Format
Financial data uses simple array format:
```json
{
  "cases": {
    "base_case": {
      "financials": {
        "income_statement": {
          "revenue": [
            {"year": "2024", "value": 100},
            {"year": "2025", "value": 120}
          ],
          "ebitda": [
            {"year": "2024", "value": 25},
            {"year": "2025", "value": 30}
          ]
        }
      },
      "deal_parameters": {
        "entry_valuation": {"method": "multiple", "multiple": 8.0},
        "exit_valuation": {"method": "multiple", "multiple": 9.0},
        "capital_structure": {
          "tranches": [
            {
              "name": "Senior Debt",
              "amount": 100,
              "interest_rate": 0.06,
              "tranche_type": "term_loan",
              "amortization_rate": 0.10
            }
          ]
        }
      }
    }
  }
}
```

### LBO Analysis Verified Working
Test with sample data produces realistic results:
- Entry: $200M @ 8x, $100M debt → $105M equity
- Exit: $468M @ 9x, $57M cash → $515M proceeds
- Returns: **4.91x MOIC, 37.5% IRR**

### Environment Variables Needed
```bash
# Required
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...  # For chat and extraction

# Optional
PERPLEXITY_API_KEY=pplx-...  # For insights (falls back to mock)
STRIPE_SECRET_KEY=sk_...     # For payments
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Running the Backend
```bash
cd /Users/jadesip/finLine/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

---

## Bugs Fixed During This Session

1. **Debt not extracted**: Extractor expected `original_size` but API sends `amount`. Fixed to support both.

2. **Exit EBITDA = 0**: Cash flow projected to 2029 but financial data ended 2028. Fixed to use last year with non-zero EBITDA.

3. **Revenue format**: `_extract_standard_metric` didn't handle simple list format `[{year, value}]`. Fixed to support lists.

---

## Next Steps (Phase 6: Frontend)

The frontend at `/Users/jadesip/finLine/frontend/` has stubs but needs full implementation:

1. **Setup**: Next.js 14, React 18, TypeScript, Tailwind CSS
2. **Pages to build**:
   - Landing page
   - Dashboard (project list)
   - Project page (main modeling interface)
   - Settings page
3. **Components needed**:
   - Financial table (editable grid)
   - Deal parameters form
   - Debt tranche editor
   - Results view (IRR/MOIC, charts)
   - Chat panel
4. **State management**: React Query recommended for API state

---

## Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Implementation Plan | `/finLine/IMPLEMENTATION_PLAN.md` | Full roadmap |
| finForge CLAUDE.md | `/finForge/CLAUDE.md` | Original project rules |
| finForge Schema | `/finForge/backend/dataStruct/Financial_Project_Schema_v7.json` | Reference schema |

---

## Commands for Quick Testing

```bash
# Start server
cd /Users/jadesip/finLine/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d "username=test@example.com&password=testpass123" | python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))")

# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test LBO","company_name":"TestCo","currency":"USD","unit":"millions"}'

# Run analysis
curl -X POST http://localhost:8000/api/projects/{id}/analyze \
  -H "Authorization: Bearer $TOKEN"
```

---

*This checkpoint was created to preserve context for resuming development.*
