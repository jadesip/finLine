# finLine Implementation Plan

> Migration from finForge to a simplified, maintainable financial modeling platform

**Status:** Phase 8 UI Complete - Business Logic Pending
**Last Updated:** 2026-02-09

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
| Complex multi-step wizard (15 steps) | 10-step focused wizard |
| Multiple Zustand stores | React Context for state management |

### Features Implemented

- Full LBO engine (IRR, MOIC, debt schedules, cash flows)
- Full deal parameters (entry/exit valuation, fees, tax)
- Full debt tranche flexibility (PIK, amortization, seniority, revolver)
- EBITDA dual entry (sourced vs calculated from EBIT + D&A)
- Multiple case scenarios (base, upside, downside)
- Document extraction with AI (PDF/image processing)
- Auth system (JWT + bcrypt with auto-refresh)
- Chat interface for natural language updates
- Excel export with formulas
- Stripe payment integration
- **10-step wizard flow with full UI**

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
- **EBIT normalization** - maps income_from_operations, operating_income → ebit

### Phase 5: Export & Payments ✅

- Excel export with openpyxl
- Stripe integration - checkout, subscription, portal
- Payment webhooks

### Phase 6: Frontend Foundation ✅

- Next.js 14 + React 18 + TypeScript
- Landing page with auth
- Dashboard with project list
- shadcn/ui component library
- Wizard context for state management
- API client with full type definitions
- JWT auto-refresh mechanism

### Phase 7: Wizard Flow (Steps 1-6) ✅

- **Type Selection** - Project type cards (LBO enabled, others disabled)
- **Name** - Project name input with create
- **Upload** - Drag-drop file upload with extraction progress
- **Company Info** - Metadata review and editing
- **Financials Review** - Editable table with validation checkboxes
- **Business Intelligence** - 5 tabs (Overview, Business Model, Management, Strategy & SWOT, Risk Analysis)

### Phase 8: LBO Wizard Pages (Steps 7-10) ✅ UI COMPLETE

- **Forecast Page** ✅ - Navigation bridge to deal assumptions
- **Deal Assumptions Page** ✅
  - Entry/exit parameters with MonthYearPicker
  - MultipleInput component (shows "7.0x" format)
  - PercentageInput component (shows "2%" format, no spinners)
  - Entry and Exit Valuation Multiples tables
  - Case selector (Base/Upside/Downside)
- **Capital Structure Page** ✅
  - Debt tranches list with add/remove
  - Tranche configuration (type, size, rates, PIK, amortization, maturity, seniority)
  - Blue info bar: "Fill in the various debt tranches of the financing package"
  - Reference rate curve (SOFR) with enable toggle
  - Other Assumptions (tax rate, minimum cash)
  - Sources & Uses summary with balance check
  - Red alert shown only when not balanced
- **Results Page** ✅
  - Executive Summary table (IRR, MOIC, key metrics)
  - Sources & Uses side-by-side cards
  - Returns Waterfall with collapsible entry/exit details
  - Forecast & Cash Flows table
  - Credit Ratios table
  - Case selector

**Note:** All Phase 8 pages are UI-only (hardcoded sample data). Business logic to connect to backend pending.

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

## Wizard Steps (10 total)

| # | Step ID | Page | Status |
|---|---------|------|--------|
| 1 | type | Project Type Selection | ✅ Complete |
| 2 | name | Project Name | ✅ Complete |
| 3 | upload | Document Upload | ✅ Complete |
| 4 | company | Company Info Review | ✅ Complete |
| 5 | financials | Financials Review | ✅ Complete |
| 6 | insights | Business Intelligence | ✅ Complete |
| 7 | forecast | Forecast Builder | ✅ UI Complete (logic pending) |
| 8 | deal_assumptions | Deal Assumptions | ✅ UI Complete (logic pending) |
| 9 | capital_structure | Capital Structure | ✅ UI Complete (logic pending) |
| 10 | results | Results Dashboard | ✅ UI Complete (logic pending) |

---

## Remaining Work

### Phase 8B: Business Logic (Priority: HIGH) 🔄

Connect the UI-only pages to actual data and calculations:

| # | Task | Description | Files |
|---|------|-------------|-------|
| 1 | **Forecast Page Logic** | Load financials from project, enable growth rate editing, calculate projections | `forecast/page.tsx` |
| 2 | **Deal Assumptions Logic** | Save entry/exit dates, multiples, fees to project data. Load EBITDA from financials for valuation multiples tables. | `deal-assumptions/page.tsx` |
| 3 | **Capital Structure Logic** | Save debt tranches to project. Calculate sources & uses from actual deal data. | `capital-structure/page.tsx` |
| 4 | **Results Page Logic** | Call `/api/projects/{id}/analyze`, display actual IRR, MOIC, cash flows. | `results/page.tsx` |
| 5 | **Wizard Navigation** | Ensure step-by-step data persistence and validation | `wizard-context.tsx` |

### Phase 9: Export Refinement (Priority: Medium)

| # | Task | Description |
|---|------|-------------|
| 6 | **Excel Export Template** | Create polished Excel template with proper formatting, formulas, and all LBO outputs |
| 7 | **PDF Report** | Optional: Generate PDF summary report |

### Phase 10: Infrastructure (Priority: Medium)

| # | Task | Description |
|---|------|-------------|
| 8 | **End-to-End Testing** | Full flow testing from upload to results |
| 9 | **Error Handling** | Comprehensive error states and recovery |
| 10 | **CI/CD & Docker** | GitHub Actions pipeline, Docker setup |

### Phase 11: Deployment (Priority: High)

| # | Task | Description |
|---|------|-------------|
| 11 | **Deployment Options** | Evaluate: Railway, Fly.io, self-hosted VPS, Coolify |
| 12 | **Deploy to finline.app** | Production deployment with SSL, monitoring |
| 13 | **Marketing Plan** | Launch strategy, pricing tiers |

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
| Styling | Tailwind CSS + shadcn/ui |
| Auth | JWT + bcrypt (auto-refresh) |
| LLM | OpenAI / Claude / Gemini (configurable) |
| Payments | Stripe |
| Testing | pytest (backend) |

---

## Key Files Reference

### Backend
- `backend/services/extraction/extractor.py` - Document extraction with hybrid text+image, EBIT normalization
- `backend/engine/lbo.py` - LBO calculation engine
- `backend/api/projects.py` - Project CRUD endpoints

### Frontend
- `frontend/src/app/project-wizard/` - All 10 wizard pages
- `frontend/src/contexts/wizard-context.tsx` - Wizard state management
- `frontend/src/types/wizard.ts` - Step definitions and types
- `frontend/src/lib/api.ts` - API client

### Custom Components
- `PercentageInput` - Shows value with % suffix (e.g., "5%"), no spinners
- `NumberInput` - Plain number input, no spinners
- `MultipleInput` - Shows value with x suffix (e.g., "7.0x")
- `MonthYearPicker` - Month/year date picker for deal dates
