# finLine Implementation Plan

> Migration from finForge to a simplified, maintainable financial modeling platform

**Last Updated:** 2026-01-17

---

## Project Overview

### What We're Doing

Recreating the finForge LBO financial modeling platform with a **simplified architecture** that addresses the pain points discovered during finForge development:

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

### What We're Keeping

- ✅ Full LBO engine (IRR, MOIC, debt schedules, cash flows)
- ✅ Full deal parameters (entry/exit valuation, fees, tax)
- ✅ Full debt tranche flexibility (PIK, amortization, seniority, revolver)
- ✅ EBITDA dual entry (sourced vs calculated from EBIT + D&A)
- ✅ Multiple case scenarios (base, upside, downside)
- ✅ Document extraction with AI
- ✅ Auth system (JWT + bcrypt)
- ✅ Chat interface for natural language updates
- ✅ Excel export
- ✅ Perplexity insights integration

---

## Progress Tracker

### Phase 1: Foundation ✅ COMPLETE

| Task | Status | Notes |
|------|--------|-------|
| Project structure setup | ✅ Done | Created `/Users/jadesip/finLine` |
| SQLite database | ✅ Done | `database.py` with users, projects, extractions tables |
| Configuration | ✅ Done | `config.py` with Pydantic settings |
| FastAPI app entry | ✅ Done | `main.py` with lifespan, CORS, routers |
| Auth system | ✅ Done | `api/auth.py` - JWT + bcrypt, register/login/me |
| Pydantic schemas | ✅ Done | `models/schemas.py` - all snake_case |
| Virtual environment | ✅ Done | `.venv` with all dependencies |

### Phase 2: Core API ✅ COMPLETE

| Task | Status | Notes |
|------|--------|-------|
| Project CRUD | ✅ Done | `api/projects.py` - list, create, get, update, delete |
| Single PATCH endpoint | ✅ Done | Dot-notation path updates |
| Bulk update endpoint | ✅ Done | Multiple updates in one request |
| Case management | ✅ Done | Add/delete cases |
| Empty project template | ✅ Done | Proper schema structure on creation |

### Phase 3: LBO Engine ✅ COMPLETE

| Task | Status | Notes |
|------|--------|-------|
| Data models | ✅ Done | `engine/models.py` - FinFigs, DebtTranche, DealParameters |
| Project extractor | ✅ Done | `engine/extractor.py` - JSON to analysis objects |
| Sources & Uses | ✅ Done | `engine/sources_uses.py` - entry equity calculation |
| Cash flow engine | ✅ Done | `engine/cash_flow.py` - FCF, CFADS projections |
| Debt schedule tracker | ✅ Done | `engine/debt.py` - waterfall, PIK, revolver plug |
| Returns calculator | ✅ Done | `engine/returns.py` - IRR, MOIC |
| Main orchestrator | ✅ Done | `engine/lbo.py` - `run_lbo_analysis()` |
| Analyze API endpoint | ✅ Done | `POST /api/projects/{id}/analyze` |
| Tested with sample data | ✅ Done | 3.21x MOIC, 26.3% IRR confirmed |

### Phase 4: AI Features ✅ COMPLETE

| Task | Status | Notes |
|------|--------|-------|
| LLM abstraction layer | ✅ Done | `config.py` - OpenAI/Claude/Gemini provider switch |
| Chat endpoint | ✅ Done | `api/chat.py` - POST /chat, POST /chat/apply |
| Chat intent parsing | ✅ Done | LLM parses natural language → structured updates |
| Document extraction | ✅ Done | `api/extraction.py` + `services/extraction/` |
| PDF/Image processing | ✅ Done | PyMuPDF, Pillow, vision LLM |
| Perplexity insights | ✅ Done | `api/insights.py` - POST /insights, GET /insights/quick |

### Phase 5: Export & Payments ✅ COMPLETE

| Task | Status | Notes |
|------|--------|-------|
| Excel export | ✅ Done | `services/excel.py` + `POST /export` endpoint |
| Stripe integration | ✅ Done | `api/payments.py` - checkout, subscription, portal |
| Payment webhooks | ✅ Done | Handles checkout, subscription updates, cancellation |

### Phase 6: Frontend 🔲 NOT STARTED

| Task | Status | Notes |
|------|--------|-------|
| Next.js setup | 🔲 Todo | Package.json, configs exist but pages are stubs |
| Landing page | 🔲 Todo | Marketing, login/signup CTAs |
| Dashboard | 🔲 Todo | Project list, create new |
| Project page | 🔲 Todo | Main modeling interface |
| Financial table | 🔲 Todo | Editable grid component |
| Deal parameters form | 🔲 Todo | Entry/exit valuation, fees |
| Debt configuration | 🔲 Todo | Tranche editor |
| Results view | 🔲 Todo | IRR/MOIC display, charts |
| Chat panel | 🔲 Todo | Right-side collapsible |
| Settings page | 🔲 Todo | Account, billing |

### Phase 7: Testing & Polish 🔲 NOT STARTED

| Task | Status | Notes |
|------|--------|-------|
| Backend unit tests | 🔲 Todo | pytest for API and engine |
| Frontend tests | 🔲 Todo | Jest/Vitest |
| E2E tests | 🔲 Todo | Playwright |
| Error handling | 🔲 Todo | Comprehensive error messages |
| Loading states | 🔲 Todo | Skeleton loaders |
| Mobile responsiveness | 🔲 Todo | Tailwind responsive |

---

## Detailed Implementation Steps

### Backend (Remaining)

#### 1. Chat Interface
```
/backend/api/chat.py
- POST /api/projects/{id}/chat
- Parse user message with LLM
- Extract intent: set_value, growth_formula, bulk_update, etc.
- Return structured changes or clarification request
- Apply changes if confirmed
```

#### 2. Document Extraction
```
/backend/api/extraction.py
- POST /api/projects/{id}/extract (multipart form)
- Accept PDF, images (PNG, JPG)
- Process with vision LLM
- Extract financial tables
- Return structured data for review
- POST /api/projects/{id}/extractions/{id}/merge
```

#### 3. Excel Export
```
/backend/services/excel.py
- Generate Excel workbook with openpyxl
- Sheets: Summary, Financials, Debt Schedule, Returns
- Include formulas for recalculation
```

#### 4. Stripe Integration
```
/backend/api/payments.py
- POST /api/payments/create-checkout
- POST /api/payments/webhook
- GET /api/payments/subscription
- Manage subscription tiers
```

### Frontend (Full Build)

#### 1. Setup & Configuration
```
/frontend/
- Update package.json with all dependencies
- Configure Tailwind properly
- Set up API client with React Query
- Add auth context/provider
```

#### 2. Layout Components
```
/frontend/src/components/layout/
- Header (logo, nav, user menu)
- Sidebar (project navigation)
- Footer
```

#### 3. Landing Page
```
/frontend/src/app/page.tsx
- Hero section
- Feature highlights
- Pricing
- CTA buttons
```

#### 4. Dashboard
```
/frontend/src/app/dashboard/page.tsx
- Project list (cards or table)
- Create project modal
- Search/filter
```

#### 5. Project Page
```
/frontend/src/app/project/[id]/page.tsx
- Tab navigation (Financials, Deal, Debt, Results)
- Financial table component (editable)
- Deal parameters form
- Debt tranche editor
- Results display (IRR, MOIC, charts)
- Chat panel (collapsible right side)
```

#### 6. Settings Page
```
/frontend/src/app/settings/page.tsx
- Account info
- Change password
- Subscription management (Stripe)
- Delete account
```

---

## File Inventory

### Backend Files (Created)

| File | Purpose |
|------|---------|
| `config.py` | Settings with Pydantic |
| `database.py` | SQLite connection + operations |
| `main.py` | FastAPI app entry |
| `api/__init__.py` | Router exports |
| `api/auth.py` | Auth endpoints |
| `api/projects.py` | Project CRUD + analyze |
| `models/__init__.py` | Model exports |
| `models/schemas.py` | Pydantic request/response |
| `engine/__init__.py` | Engine exports |
| `engine/models.py` | FinFigs, DebtTranche, DealParameters |
| `engine/extractor.py` | JSON → analysis objects |
| `engine/sources_uses.py` | Sources & Uses calculation |
| `engine/cash_flow.py` | Cash flow projections |
| `engine/debt.py` | Debt schedule tracker |
| `engine/returns.py` | IRR/MOIC calculations |
| `engine/lbo.py` | Main analysis orchestrator |
| `services/__init__.py` | Service exports |
| `services/llm.py` | LLM abstraction (stub) |
| `requirements.txt` | Dependencies |

### Backend Files (Still Needed)

| File | Purpose |
|------|---------|
| `api/chat.py` | Chat interface endpoint |
| `api/extraction.py` | Document extraction endpoint |
| `api/payments.py` | Stripe endpoints |
| `services/extraction.py` | Document processing logic |
| `services/excel.py` | Excel export logic |
| `services/insights.py` | Perplexity integration |
| `tests/` | Unit tests |

### Frontend Files (Stubs Exist, Need Implementation)

| File | Purpose |
|------|---------|
| `src/app/page.tsx` | Landing page |
| `src/app/layout.tsx` | Root layout |
| `src/app/login/page.tsx` | Auth page |
| `src/app/dashboard/page.tsx` | Project list |
| `src/app/project/[id]/page.tsx` | Main interface |
| `src/app/settings/page.tsx` | Account settings |
| `src/lib/api.ts` | API client |
| `src/lib/utils.ts` | Utilities |
| `src/types/index.ts` | TypeScript types |

---

## API Endpoints Summary

### Implemented ✅

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/health` | ✅ |
| POST | `/api/auth/register` | ✅ |
| POST | `/api/auth/login` | ✅ |
| POST | `/api/auth/refresh` | ✅ |
| GET | `/api/auth/me` | ✅ |
| GET | `/api/projects` | ✅ |
| POST | `/api/projects` | ✅ |
| GET | `/api/projects/{id}` | ✅ |
| PATCH | `/api/projects/{id}` | ✅ |
| PATCH | `/api/projects/{id}/bulk` | ✅ |
| DELETE | `/api/projects/{id}` | ✅ |
| POST | `/api/projects/{id}/cases/{case_id}` | ✅ |
| DELETE | `/api/projects/{id}/cases/{case_id}` | ✅ |
| POST | `/api/projects/{id}/analyze` | ✅ |
| POST | `/api/projects/{id}/analyze/all` | ✅ |

### Not Yet Implemented 🔲

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/projects/{id}/chat` | Chat interface |
| POST | `/api/projects/{id}/extract` | Start extraction |
| GET | `/api/projects/{id}/extractions/{eid}` | Get extraction status |
| POST | `/api/projects/{id}/extractions/{eid}/merge` | Merge extracted data |
| POST | `/api/projects/{id}/export` | Excel export |
| GET | `/api/projects/{id}/insights` | AI insights |
| POST | `/api/payments/create-checkout` | Stripe checkout |
| POST | `/api/payments/webhook` | Stripe webhook |
| GET | `/api/payments/subscription` | Get subscription |

---

## Testing Checklist

### Backend Tests Needed

- [ ] Auth: registration, login, token refresh, protected routes
- [ ] Projects: CRUD, ownership checks, case management
- [ ] Updates: dot-notation paths, bulk updates
- [ ] Engine: sources/uses, cash flows, debt schedules, returns
- [ ] Chat: intent parsing, update application
- [ ] Extraction: file upload, processing, merge

### Manual Testing Done

- [x] Health endpoint
- [x] User registration
- [x] User login
- [x] Token authentication
- [x] Project creation
- [x] Project listing
- [x] Single field update (PATCH)
- [x] Bulk update
- [x] Case management (add/delete)
- [x] LBO analysis with sample data (3.21x MOIC, 26.3% IRR)

---

## Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Architecture | `/finLine/ARCHITECTURE.md` | Full technical spec |
| Original Requirements | `/finForge/REWRITE_REQUIREMENTS.md` | User feedback & decisions |
| finForge LBO Engine | `/finForge/backend/finbackend/financial_analysis/` | Source for porting |
| finForge Schema | `/finForge/backend/dataStruct/Financial_Project_Schema_v7.json` | Reference |

---

## Next Steps (Priority Order)

1. **Chat Interface** - Natural language model updates
2. **Document Extraction** - Port from finForge
3. **Frontend Build** - Full React implementation
4. **Excel Export** - Analysis output
5. **Stripe Integration** - Payments
6. **Testing** - Comprehensive test suite
7. **Deployment** - CI/CD, hosting

---

## Commands Reference

### Start Backend
```bash
cd /Users/jadesip/finLine/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Test API
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=test@example.com&password=TestPass123"

# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My LBO","company_name":"Acme","currency":"USD","unit":"millions"}'

# Run analysis
curl -X POST http://localhost:8000/api/projects/{id}/analyze \
  -H "Authorization: Bearer $TOKEN"
```

---

*This document should be updated as progress is made.*
