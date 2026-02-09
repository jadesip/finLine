# finLine Architecture

> A simplified financial modeling platform - rebuilt from finForge learnings

**Status:** Phase 8 UI Complete - Business Logic Pending
**Last Updated:** 2026-02-09

---

## Overview

finLine is a focused LBO/financial modeling tool with:
- **Simple data input** - user provides financials, we don't guess
- **Chat-assisted editing** - natural language updates to the model
- **Clean architecture** - SQLite, minimal endpoints, snake_case everywhere
- **10-step wizard flow** - guided project creation and analysis

---

## 1. Data Schema

### Design Principles
- **KEEP full deal parameters** - entry/exit valuation, fees, all the LBO mechanics
- **KEEP full debt tranche flexibility** - all fields (PIK, amortization, seniority, etc.)
- **KEEP EBITDA dual entry** - sourced vs calculated (EBIT + D&A)
- **REMOVE revenue driver formulas** - just use growth percentages
- **REMOVE DSO/DIO/DPO** - just total working capital
- **REMOVE P&L case detection** - no A1.1-B2.5 complexity
- **REMOVE COGS/OpEx breakdown** - user provides EBITDA directly

### What We're Simplifying (vs finForge v7)

| Keep | Remove |
|------|--------|
| Deal parameters (full) | Revenue driverFormula |
| Debt tranches (full) | DSO/DIO/DPO days calculations |
| Entry/exit valuation | P&L case detection (A1.1-B2.5) |
| Reference rate curves | COGS, Operating expenses |
| EBITDA sourced/calculated | Complex margin value_type |
| Revenue, EBIT, D&A | Multiple income statement lines |
| Total working capital | Balance sheet breakdown |
| CAPEX | da_present_in_pl flag |

### Value Types (Simplified)

| Type | Keep? | Usage |
|------|-------|-------|
| `hardcode` | YES | Direct values entered by user |
| `formula` | YES | EBITDA = EBIT + D&A calculation |
| `growthFormula` | YES | Revenue growth: prev_year * (1 + growth_rate) |
| `driverFormula` | NO | Complex revenue drivers - removed |
| `margin` | NO | Can be shown as display, not stored |
| `days` | NO | DSO/DIO/DPO - removed |

### Schema Structure

```json
{
  "meta": {
    "user_id": "uuid",
    "project_id": "uuid",
    "version": "1.0",
    "name": "Project Name",
    "company_name": "Acme Corp",
    "currency": "USD",
    "unit": "millions",
    "frequency": "annual",
    "financial_year_end": "December",
    "last_historical_period": "2025",
    "created_date": "2026-01-17T00:00:00Z",
    "last_modified": "2026-01-17T00:00:00Z"
  },

  "cases": {
    "base_case": { /* case structure below */ },
    "upside_case": { /* ... */ },
    "downside_case": { /* ... */ }
  }
}
```

### Case Structure

```json
{
  "case_desc": "Base case assumptions",

  "deal_parameters": {
    "deal_date": "2026-06-30",
    "exit_date": "2031-06-30",
    "tax_rate": 0.25,
    "minimum_cash": 5.0,
    "entry_fee_percentage": 2.0,
    "exit_fee_percentage": 2.0,

    "entry_valuation": {
      "method": "multiple",
      "metric": "EBITDA",
      "multiple": 8.0
    },

    "exit_valuation": {
      "method": "multiple",
      "metric": "EBITDA",
      "multiple": 8.0
    },

    "capital_structure": {
      "tranches": [
        {
          "tranche_id": "senior_1",
          "label": "Senior Term Loan",
          "type": "Loan",
          "currency": "USD",
          "original_size": 200.0,
          "maturity": "2033-06-30",
          "oid": 0.0,
          "interest_margin": 0.04,
          "cash_interest_rate": null,
          "pik_interest_rate": 0.0,
          "financing_fees": 0.01,
          "undrawn_fee": null,
          "seniority": 1,
          "repayment_seniority": 1,
          "amortization": "10/10/10/10/10/50",
          "percentage_drawn_at_deal_date": 1.0
        }
      ],
      "reference_rate_curve": {
        "label": "SOFR",
        "currency": "USD",
        "points": [
          { "period": "2026", "rate": 0.045 },
          { "period": "2027", "rate": 0.04 }
        ]
      }
    }
  },

  "financials": {
    "income_statement": {
      "revenue": { "2024": 100.0, "2025": 110.0 },
      "ebitda": { "2024": 20.0, "2025": 22.0 },
      "ebit": { "2024": 15.0, "2025": 16.5 },
      "d_and_a": { "2024": 5.0, "2025": 5.5 }
    },
    "cash_flow_statement": {
      "capex": { "2024": 8.0, "2025": 8.8 },
      "working_capital": { "2024": 15.0, "2025": 16.5 }
    }
  }
}
```

---

## 2. API Design

### Endpoints (28 total)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login, get JWT |
| POST | `/api/auth/refresh` | Refresh token |
| GET | `/api/auth/me` | Get current user |
| GET | `/api/projects` | List user's projects |
| POST | `/api/projects` | Create new project |
| GET | `/api/projects/{id}` | Get project data |
| PATCH | `/api/projects/{id}` | Update project (partial) |
| DELETE | `/api/projects/{id}` | Delete project |
| POST | `/api/projects/{id}/analyze` | Run LBO analysis |
| POST | `/api/projects/{id}/extract` | Extract from document |
| POST | `/api/projects/{id}/chat` | Chat interface for updates |
| POST | `/api/projects/{id}/export` | Export to Excel |
| GET | `/api/projects/{id}/insights` | Get AI insights |

### Key Design Decisions

**Single update endpoint**: `PATCH /api/projects/{id}` handles all updates.

```json
// Request body - partial update
{
  "path": "cases.base_case.financials.revenue.2026",
  "value": 150.0
}

// Or bulk update
{
  "updates": [
    { "path": "cases.base_case.financials.revenue.2026", "value": 150.0 },
    { "path": "cases.base_case.financials.revenue.2027", "value": 165.0 }
  ]
}
```

**Chat endpoint**: Natural language → structured updates

```json
// Request
{
  "message": "Set CAPEX to 10M for all years from 2026 to 2030",
  "context": {
    "current_case": "base_case"
  }
}

// Response (if clear)
{
  "understood": true,
  "changes": [
    { "path": "cases.base_case.financials.capex.2026", "old": 11.7, "new": 10.0 }
  ],
  "message": "Updated CAPEX to 10M for years 2026-2030 in base case.",
  "applied": true
}
```

---

## 3. Page Structure

### Wizard Flow (10 Steps)

| Step | Route | Purpose |
|------|-------|---------|
| 1 | `/project-wizard/type` | Select project type (LBO, etc.) |
| 2 | `/project-wizard/name` | Enter project name |
| 3 | `/project-wizard/upload` | Upload documents for extraction |
| 4 | `/project-wizard/company` | Review company metadata |
| 5 | `/project-wizard/financials` | Review/edit extracted financials |
| 6 | `/project-wizard/insights` | Business intelligence (5 tabs) |
| 7 | `/project-wizard/forecast` | Financial projections |
| 8 | `/project-wizard/deal-assumptions` | Entry/exit parameters |
| 9 | `/project-wizard/capital-structure` | Debt tranches, sources & uses |
| 10 | `/project-wizard/results` | LBO results dashboard |

### Other Pages

| Page | Route | Purpose |
|------|-------|---------|
| **Landing** | `/` | Marketing page, login/signup CTAs |
| **Dashboard** | `/dashboard` | Project list, create new |
| **Settings** | `/settings` | Account, billing (Stripe) |

### Results Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Header: Project Name | Case Selector | Export | Analyze   │
├─────────────────────────────────────────────────────────────┤
│  Executive Summary                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ IRR: 25.3%  │  MOIC: 2.5x  │  Entry: 7.0x  │ Exit: 6.0x│
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Sources & Uses (side by side)                              │
├─────────────────────────────────────────────────────────────┤
│  Returns Waterfall (collapsible Entry/Exit details)         │
├─────────────────────────────────────────────────────────────┤
│  Forecast & Cash Flows Table                                │
├─────────────────────────────────────────────────────────────┤
│  Credit Ratios Table                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Folder Structure

```
finLine/
├── README.md
├── ARCHITECTURE.md
├── IMPLEMENTATION_PLAN.md
├── FRONTEND_REBUILD_PLAN.md
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── config.py            # Settings, env vars
│   ├── database.py          # SQLite connection
│   ├── main.py              # FastAPI app entry
│   │
│   ├── api/
│   │   ├── auth.py          # Auth endpoints
│   │   ├── projects.py      # Project CRUD
│   │   ├── analysis.py      # LBO analysis
│   │   ├── extraction.py    # Document extraction
│   │   └── chat.py          # Chat interface
│   │
│   ├── engine/
│   │   ├── lbo.py           # LBO calculations
│   │   ├── debt.py          # Debt schedules
│   │   └── returns.py       # IRR, MOIC
│   │
│   ├── services/
│   │   ├── llm.py           # LLM abstraction
│   │   ├── extraction/      # Document extraction module
│   │   │   ├── extractor.py           # Main orchestrator (hybrid text+image)
│   │   │   ├── file_handler.py        # PDF/image processing
│   │   │   ├── text_extractor.py      # PyMuPDF text extraction
│   │   │   ├── image_optimizer.py     # Image optimization
│   │   │   ├── prompts.py             # Extraction prompts
│   │   │   └── langchain_business_insights.py
│   │   └── excel.py         # Excel export
│   │
│   └── tests/
│       ├── test_auth.py
│       ├── test_projects.py
│       └── test_engine.py
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx              # Landing
│       │   ├── dashboard/page.tsx
│       │   ├── project-wizard/
│       │   │   ├── layout.tsx        # Wizard wrapper
│       │   │   ├── type/page.tsx
│       │   │   ├── name/page.tsx
│       │   │   ├── upload/page.tsx
│       │   │   ├── company/page.tsx
│       │   │   ├── financials/page.tsx
│       │   │   ├── insights/page.tsx
│       │   │   ├── forecast/page.tsx
│       │   │   ├── deal-assumptions/page.tsx
│       │   │   ├── capital-structure/page.tsx
│       │   │   └── results/page.tsx
│       │   └── settings/page.tsx
│       │
│       ├── components/
│       │   ├── ui/              # shadcn/ui components
│       │   ├── layout/          # Wizard layout, sidebar
│       │   └── debug/           # JSON viewer for development
│       │
│       ├── contexts/
│       │   └── wizard-context.tsx
│       │
│       ├── lib/
│       │   ├── api.ts           # API client
│       │   └── utils.ts         # Helpers
│       │
│       └── types/
│           ├── index.ts
│           ├── wizard.ts        # Wizard step definitions
│           └── project.ts
│
└── data/
    └── finline.db               # SQLite database file
```

---

## 5. Document Extraction Architecture

### Hybrid Text+Image Extraction

finLine uses hybrid extraction for accurate financial data parsing:

```
PDF Upload
    │
    ▼
┌─────────────────────┐
│  FileHandler        │
│  - Convert to images│
│  - Extract text     │ ← PyMuPDF text extraction
│  - Analyze doc type │
└────────┬────────────┘
         │
         ▼
    ┌────────────┐
    │ Has text?  │
    └────┬───────┘
         │
    Yes ─┴── No
    │         │
    ▼         ▼
┌────────────┐  ┌────────────┐
│ Hybrid     │  │ Image-only │
│ Prompt     │  │ Prompt     │
│ (text+img) │  │            │
└────────────┘  └────────────┘
         │
         ▼
┌─────────────────────┐
│  Vision LLM (GPT-4o)│
│  - Metadata extract │
│  - Financial data   │
│  - Business insights│
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Normalize          │
│  - D&A deduplication│
│  - EBIT mapping     │ ← income_from_operations → ebit
└─────────────────────┘
```

**Why Hybrid Extraction?**

Image-only extraction caused the LLM to visually misinterpret numbers like "282,836" as "282.836" (European decimal format). By extracting actual text from PDFs using PyMuPDF and including it in the prompt, the LLM correctly parses comma-separated thousands.

**EBIT Normalization**

LLMs sometimes extract EBIT under different field names. The extractor normalizes these:
- `income_from_operations` → `ebit`
- `operating_income` → `ebit`
- `operating_profit` → `ebit`
- `operating_earnings` → `ebit`

---

## 6. Technical Specifications

### SQLite Schema

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    last_login TEXT
);

-- Projects table
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    data JSON NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Extractions table
CREATE TABLE extractions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL,
    source_files JSON,
    extracted_data JSON,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### Environment Variables

```bash
# Backend
DATABASE_URL=sqlite:///./data/finline.db
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM Configuration
LLM_PROVIDER=openai          # openai, claude, gemini
LLM_MODEL=gpt-4o
LLM_API_KEY=your-api-key

# Stripe
STRIPE_SECRET_KEY=your-stripe-key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 7. Key Simplifications Summary

| Aspect | finForge | finLine |
|--------|----------|---------|
| Schema | 780 lines, 16 types | ~100 lines, 3 types |
| Endpoints | 20+ | 28 (well-organized) |
| Wizard Steps | 15 steps | 10 steps |
| Pages | 24+ | 12 |
| State Management | Zustand stores | React Context |
| Revenue Modeling | Driver formulas | Growth % |
| Working Capital | DSO/DIO/DPO | Total only |
| P&L Detection | 8 case types | None (user provides) |
| Naming | Mixed case | snake_case everywhere |
| Data Storage | JSON files + locking | SQLite with ACID |
