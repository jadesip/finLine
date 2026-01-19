# finLine Implementation Plan

> Migration from finForge to a simplified, maintainable financial modeling platform

**Status:** Mid-Implementation (Wizard flow complete, LBO engine & core pages pending)
**Last Updated:** 2026-01-19

---

## Project Overview

### What We Built

A simplified LBO financial modeling platform addressing pain points from finForge:

| Problem in finForge | Solution in finLine |
|---------------------|---------------------|
| Too many edge cases (missing EBITDA, CAPEX) | User responsible for complete data |
| Revenue driver formula complexity | Just use growth percentages |
| DSO/DIO/DPO working capital modeling | Just total working capital |
| P&L format detection (A1.1-B2.5 cases) | No detection - user provides EBITDA |
| Mixed naming conventions (snake_case/camelCase) | snake_case everywhere |
| JSON file storage with concurrency issues | SQLite with ACID transactions |
| Complex multi-step wizard (15 steps) | Simple modal + direct editing |
| Multiple Zustand stores | React Query for state management |

### Features Implemented

- Full LBO engine (IRR, MOIC, debt schedules, cash flows)
- Full deal parameters (entry/exit valuation, fees, tax)
- Full debt tranche flexibility (PIK, amortization, seniority, revolver)
- EBITDA dual entry (sourced vs calculated from EBIT + D&A)
- Multiple case scenarios (base, upside, downside)
- Document extraction with AI (PDF/image processing)
- Auth system (JWT + bcrypt)
- Chat interface for natural language updates
- Excel export with formulas
- Stripe payment integration

---

## Phase Completion

### Phase 1: Foundation ✅

- Project structure setup
- SQLite database with users, projects, extractions tables
- Configuration with Pydantic settings
- FastAPI app with lifespan, CORS, routers
- Auth system - JWT + bcrypt, register/login/me
- Pydantic schemas - all snake_case

### Phase 2: Core API ✅

- Project CRUD - list, create, get, update, delete
- Single PATCH endpoint with dot-notation paths
- Bulk update endpoint
- Case management (add/delete cases)
- Empty project template on creation

### Phase 3: LBO Engine ✅

- Data models - FinFigs, DebtTranche, DealParameters
- Project extractor - JSON to analysis objects
- Sources & Uses calculation
- Cash flow engine - FCF, CFADS projections
- Debt schedule tracker - waterfall, PIK, revolver plug
- Returns calculator - IRR, MOIC
- Main orchestrator - `run_lbo_analysis()`
- Tested: 4.91x MOIC, 37.5% IRR confirmed

### Phase 4: AI Features ✅

- LLM abstraction layer - OpenAI/Claude/Gemini provider switch
- Chat endpoint with intent parsing
- Document extraction - PDF/image processing
  - **Hybrid text+image extraction** (ported from FinForge 2026-01-19)
  - Fixed /1000 bug: LLM misread "282,836" as "282.836" with image-only
  - PyMuPDF text extraction + vision LLM for accurate number parsing
- LangChain integration for business insights extraction
- Perplexity insights integration

### Phase 5: Export & Payments ✅

- Excel export with openpyxl
- Stripe integration - checkout, subscription, portal
- Payment webhooks

### Phase 6: Frontend ✅

- Next.js 14 + React 18 + TypeScript
- Landing page with auth
- Dashboard with project list
- Project page with tabs (Financials, Deal, Debt, Results)
- Editable financial tables
- Debt tranche editor
- Chat panel with apply/cancel
- Settings page (Account, Billing, Security)
- API client with full type definitions

### Phase 7: Testing & Polish ✅

- Backend pytest test suite (30 tests)
  - test_auth.py - registration, login, token validation
  - test_projects.py - CRUD, updates, case management
  - test_analysis.py - LBO calculations, export
- All tests passing
- Error handling throughout
- Type safety with TypeScript

---

## API Endpoints (28 total)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login, get JWT |
| POST | `/api/auth/refresh` | Refresh token |
| GET | `/api/auth/me` | Get current user |
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/{id}` | Get project |
| PATCH | `/api/projects/{id}` | Update field |
| PATCH | `/api/projects/{id}/bulk` | Bulk update |
| DELETE | `/api/projects/{id}` | Delete project |
| POST | `/api/projects/{id}/cases/{case_id}` | Add case |
| DELETE | `/api/projects/{id}/cases/{case_id}` | Delete case |
| POST | `/api/projects/{id}/analyze` | Run analysis |
| POST | `/api/projects/{id}/analyze/all` | Analyze all cases |
| POST | `/api/projects/{id}/chat` | Chat interface |
| POST | `/api/projects/{id}/chat/apply` | Apply chat updates |
| POST | `/api/projects/{id}/export` | Excel export |
| POST | `/api/projects/{id}/extract` | Document extraction |
| GET | `/api/projects/{id}/extractions/{eid}` | Extraction status |
| POST | `/api/projects/{id}/extractions/{eid}/apply` | Apply extraction |
| POST | `/api/projects/{id}/insights` | AI insights |
| GET | `/api/projects/{id}/insights/quick` | Quick insights |
| GET | `/api/payments/subscription` | Get subscription |
| POST | `/api/payments/create-checkout` | Stripe checkout |
| POST | `/api/payments/portal` | Customer portal |
| POST | `/api/payments/webhook` | Stripe webhook |

---

## Commands Reference

### Start Backend
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Run Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+ / FastAPI |
| Database | SQLite with JSON columns |
| Frontend | Next.js 14 / React 18 / TypeScript |
| Styling | Tailwind CSS |
| Auth | JWT + bcrypt |
| LLM | OpenAI / Claude / Gemini (configurable) |
| Payments | Stripe |
| Testing | pytest (backend) |

---

## Remaining Work

The wizard flow (Dashboard → Type → Name → Upload → Company → Financials → Insights) is complete. The following major items remain:

### Phase 8: Core LBO Pages (Priority: High)

| # | Task | Description | Complexity |
|---|------|-------------|------------|
| 1 | **Forecast Builder Page** | Complex financial projections with linked formulas. Must ensure integrity between income statement, balance sheet, and cash flow. Support multiple cases (base, upside, downside). | High |
| 2 | **Transaction Parameters Page** | Deal date, exit date, entry/exit valuation methods, multiples, fees, tax rate. | Medium |
| 3 | **Capital Structure Page** | Debt tranche configuration: term loans, revolvers, mezzanine, PIK, amortization schedules, covenants. | High |
| 4 | **Re-import LBO Engine** | Port and integrate the full LBO calculation engine from FinForge. IRR, MOIC, debt schedules, cash sweeps. | High |
| 5 | **Results/Summary Page** | Returns dashboard, sensitivity tables, charts, key metrics. | Medium |

### Phase 9: Export & Payments (Priority: Medium)

| # | Task | Description |
|---|------|-------------|
| 6 | **Excel Export Template** | Create new Excel template with proper formatting, formulas, and wire extraction data into template. |
| 7 | **Stripe Integration** | Set up payment flows, subscription management, customer portal, webhooks. |

### Phase 10: Infrastructure (Priority: Medium)

| # | Task | Description |
|---|------|-------------|
| 8 | **Data Persistence** | Ensure users can return and find their LBO cases. Session management, auto-save. |
| 9 | **Analytics Page** | Usage metrics, model statistics, user activity tracking. |
| 10 | **Testing** | End-to-end testing at every step. Unit tests, integration tests. |
| 11 | **CI/CD & Docker** | GitHub Actions pipeline, Dockerize frontend and backend, docker-compose for local dev. |

### Phase 11: Deployment (Priority: High)

| # | Task | Description |
|---|------|-------------|
| 12 | **Deployment Options** | Evaluate alternatives to current expensive stack (Vercel + Render). Consider: Railway, Fly.io, self-hosted VPS, Coolify. |
| 13 | **Deploy to finline.app** | Replace current FinForge deployment with finLine. DNS migration, SSL, monitoring. |
| 14 | **Marketing Plan** | Launch strategy, landing page copy, pricing tiers, user acquisition channels. |

### Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 8 (Core LBO) | 3-4 weeks | None |
| Phase 9 (Export/Payments) | 1-2 weeks | Phase 8 |
| Phase 10 (Infrastructure) | 1-2 weeks | Parallel with Phase 9 |
| Phase 11 (Deployment) | 1 week | Phase 8-10 complete |

**Total remaining: ~6-9 weeks**
