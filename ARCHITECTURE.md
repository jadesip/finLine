# finLine Architecture

> A simplified financial modeling platform - rebuilt from finForge learnings

---

## Overview

finLine is a focused LBO/financial modeling tool with:
- **Simple data input** - user provides financials, we don't guess
- **Chat-assisted editing** - natural language updates to the model
- **Clean architecture** - SQLite, minimal endpoints, snake_case everywhere

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
        },
        {
          "tranche_id": "rcf_1",
          "label": "Revolving Credit Facility",
          "type": "RCF",
          "currency": "USD",
          "original_size": 50.0,
          "maturity": "2031-06-30",
          "interest_margin": 0.035,
          "undrawn_fee": 0.005,
          "seniority": 1,
          "percentage_drawn_at_deal_date": 0.0
        },
        {
          "tranche_id": "mezz_1",
          "label": "Mezzanine Notes",
          "type": "Junior Notes",
          "currency": "USD",
          "original_size": 75.0,
          "maturity": "2034-06-30",
          "cash_interest_rate": 0.06,
          "pik_interest_rate": 0.04,
          "seniority": 2,
          "repayment_seniority": 2,
          "amortization": "",
          "percentage_drawn_at_deal_date": 1.0
        }
      ],
      "reference_rate_curve": {
        "label": "SOFR",
        "currency": "USD",
        "points": [
          { "period": "2026", "rate": 0.045 },
          { "period": "2027", "rate": 0.04 },
          { "period": "2028", "rate": 0.035 }
        ]
      }
    },

    "equity_injection": null
  },

  "financials": {
    "income_statement": {
      "revenue": {
        "2023": { "value_type": "hardcode", "value": 100.0 },
        "2024": { "value_type": "hardcode", "value": 110.0 },
        "2025": { "value_type": "hardcode", "value": 121.0 },
        "2026": { "value_type": "growthFormula", "growth_rate": 0.10 },
        "2027": { "value_type": "growthFormula", "growth_rate": 0.10 }
      },

      "ebitda": [
        {
          "origin": "sourced",
          "primary_use": 1,
          "user_desc": "From financial statements",
          "data": {
            "2023": { "value_type": "hardcode", "value": 20.0 },
            "2024": { "value_type": "hardcode", "value": 22.0 },
            "2025": { "value_type": "hardcode", "value": 24.2 }
          }
        }
      ],

      "ebit": [
        {
          "data": {
            "2023": { "value_type": "hardcode", "value": 15.0 },
            "2024": { "value_type": "hardcode", "value": 16.5 },
            "2025": { "value_type": "hardcode", "value": 18.2 }
          }
        }
      ],

      "d_and_a": [
        {
          "data": {
            "2023": { "value_type": "hardcode", "value": 5.0 },
            "2024": { "value_type": "hardcode", "value": 5.5 },
            "2025": { "value_type": "hardcode", "value": 6.0 }
          }
        }
      ]
    },

    "cash_flow_statement": {
      "capex": {
        "2023": { "value_type": "hardcode", "value": 8.0 },
        "2024": { "value_type": "hardcode", "value": 8.8 },
        "2025": { "value_type": "hardcode", "value": 9.7 }
      },

      "working_capital": {
        "2023": { "value_type": "hardcode", "value": 15.0 },
        "2024": { "value_type": "hardcode", "value": 16.5 },
        "2025": { "value_type": "hardcode", "value": 18.2 }
      }
    }
  }
}
```

### EBITDA Dual Entry (Preserved)

When EBITDA is not directly available but EBIT and D&A are:

```json
"ebitda": [
  {
    "origin": "calculated",
    "primary_use": 1,
    "user_desc": "EBITDA = EBIT + D&A",
    "data": {
      "2023": { "value_type": "formula", "expression": "ebit + d_and_a" },
      "2024": { "value_type": "formula", "expression": "ebit + d_and_a" }
    }
  }
]
```

The engine will:
1. Check if EBITDA is provided (sourced)
2. If not, check if EBIT and D&A are provided
3. If yes, auto-calculate EBITDA = EBIT + D&A
4. Store as "calculated" origin

### Validation Rules

**Sanity checks only:**
- Revenue must be non-negative
- EBITDA margin reasonable (-50% to +80%)
- Interest rates 0-100%
- Exit date after deal date
- At least one debt tranche OR equity-only deal

**NOT validating:**
- Whether all years have data (user's responsibility)
- P&L consistency (no COGS/OpEx to check against)
- Complex business rules

---

## 2. API Design

### Endpoints (7 total)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login, get JWT |
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
    { "path": "cases.base_case.financials.capex.2026", "old": 11.7, "new": 10.0 },
    { "path": "cases.base_case.financials.capex.2027", "old": 12.9, "new": 10.0 },
    ...
  ],
  "message": "Updated CAPEX to 10M for years 2026-2030 in base case.",
  "applied": true
}

// Response (if ambiguous)
{
  "understood": false,
  "clarification_needed": "Which case would you like to update? (base_case, upside_case, downside_case)",
  "applied": false
}
```

---

## 3. Page Structure

### Pages (5 total)

| Page | Route | Purpose |
|------|-------|---------|
| **Landing** | `/` | Marketing page, login/signup CTAs |
| **Dashboard** | `/dashboard` | Project list, create new |
| **Project** | `/project/{id}` | Main modeling interface |
| **Settings** | `/settings` | Account, billing (Stripe) |
| **Insights** | `/project/{id}/insights` | AI-generated analysis |

### Project Page Layout

The main project page is a **single-page interface** with tabs/sections:

```
┌─────────────────────────────────────────────────────────────┐
│  Header: Project Name | Case Selector | Export | Analyze   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Chat Box (collapsible right panel)                 │   │
│  │  "Set CAPEX to 5% of revenue for all years"        │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Tabs: [ Financials | Deal | Debt | Results ]              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Financial Table (editable)                         │   │
│  │                                                     │   │
│  │  Metric      │ 2024  │ 2025  │ 2026E │ 2027E │ ... │   │
│  │  ──────────────────────────────────────────────────│   │
│  │  Revenue     │ 121.0 │ 133.1 │ 146.4 │ 161.0 │     │   │
│  │  Growth %    │  10%  │  10%  │  10%  │  10%  │     │   │
│  │  EBITDA      │  24.2 │  26.6 │  29.3 │  32.2 │     │   │
│  │  Margin %    │  20%  │  20%  │  20%  │  20%  │     │   │
│  │  D&A         │   6.0 │   6.6 │   7.3 │   8.0 │     │   │
│  │  CAPEX       │   9.7 │  10.6 │  11.7 │  12.9 │     │   │
│  │  Working Cap │  18.2 │  20.0 │  22.0 │  24.2 │     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### No Wizard

Project creation is simple:
1. Click "New Project" on Dashboard
2. Modal: Enter project name, upload files (optional)
3. If files uploaded → extraction runs → lands on Project page with data
4. If no files → lands on empty Project page → user fills in data

---

## 4. Folder Structure

```
finLine/
├── README.md
├── ARCHITECTURE.md          # This file
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── config.py            # Settings, env vars
│   ├── database.py          # SQLite connection
│   ├── main.py              # FastAPI app entry
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # Auth endpoints
│   │   ├── projects.py      # Project CRUD
│   │   ├── analysis.py      # LBO analysis
│   │   ├── extraction.py    # Document extraction
│   │   └── chat.py          # Chat interface
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # User model
│   │   ├── project.py       # Project model
│   │   └── schemas.py       # Pydantic schemas
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── lbo.py           # LBO calculations (simplified)
│   │   ├── debt.py          # Debt schedules
│   │   └── returns.py       # IRR, MOIC
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm.py           # LLM abstraction (Gemini/Claude/etc)
│   │   ├── extraction.py    # Document extraction logic
│   │   ├── insights.py      # Perplexity integration
│   │   └── excel.py         # Excel export
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_auth.py
│       ├── test_projects.py
│       └── test_engine.py
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   │
│   ├── public/
│   │   └── ...
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx       # Root layout
│       │   ├── page.tsx         # Landing page
│       │   ├── dashboard/
│       │   │   └── page.tsx     # Project list
│       │   ├── project/
│       │   │   └── [id]/
│       │   │       └── page.tsx # Main project interface
│       │   ├── settings/
│       │   │   └── page.tsx     # Account & billing
│       │   └── login/
│       │       └── page.tsx     # Auth page
│       │
│       ├── components/
│       │   ├── ui/              # Radix UI components (copy from finForge)
│       │   ├── layout/
│       │   │   ├── header.tsx
│       │   │   ├── sidebar.tsx
│       │   │   └── footer.tsx
│       │   ├── project/
│       │   │   ├── financial_table.tsx
│       │   │   ├── deal_form.tsx
│       │   │   ├── debt_config.tsx
│       │   │   ├── results_view.tsx
│       │   │   └── chat_panel.tsx
│       │   └── common/
│       │       ├── loading.tsx
│       │       └── error.tsx
│       │
│       ├── lib/
│       │   ├── api.ts           # API client
│       │   ├── auth.ts          # Auth utilities
│       │   └── utils.ts         # Helpers
│       │
│       └── types/
│           └── index.ts         # TypeScript types (snake_case)
│
└── data/
    └── finline.db               # SQLite database file
```

---

## 5. Migration Plan

### What to Port from finForge

| Component | Source | Action |
|-----------|--------|--------|
| **LBO Engine** | `/backend/finbackend/analysis/` | Simplify & port |
| **Debt Calculations** | `/backend/finbackend/models/financial_structures.py` | Port DebtTranche logic |
| **Auth System** | `/backend/api/auth.py` | Port JWT + bcrypt |
| **Document Extraction** | `/backend/api/main.py` (extract endpoints) | Port & simplify |
| **Perplexity Integration** | `/backend/finbackend/` | Port as-is |
| **UI Components** | `/frontend/firebase2/src/components/ui/` | Copy Radix components |
| **Design Tokens** | `/frontend/firebase2/tailwind.config.ts` | Copy color palette |
| **Landing Page** | `/frontend/firebase2/src/components/landing/` | Adapt |

### What NOT to Port

- Revenue driver formula system
- P&L case detection (A1.1-B3 cases)
- DSO/DIO/DPO working capital modeling
- Complex schema validation (780 lines → ~100 lines)
- Wizard flow (15 steps)
- Multiple Zustand stores
- Event log / undo-redo system (v2 feature)

### Migration Sequence

**Phase 1: Foundation (Week 1)**
1. Set up project structure
2. SQLite database with basic tables
3. Auth system (port from finForge)
4. Basic API scaffolding

**Phase 2: Core Features (Week 2-3)**
1. Project CRUD
2. Financial data model
3. Simple LBO calculations
4. Basic frontend with financial table

**Phase 3: AI Features (Week 4)**
1. Document extraction
2. Chat interface
3. Insights (Perplexity)

**Phase 4: Polish (Week 5)**
1. Excel export
2. Stripe integration
3. UI refinement
4. Testing

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
    data JSON NOT NULL,  -- Full project data as JSON
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Extractions table (for tracking document processing)
CREATE TABLE extractions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL,  -- pending, processing, completed, failed
    source_files JSON,     -- List of uploaded file names
    extracted_data JSON,   -- Raw extraction result
    created_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Indexes
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_extractions_project ON extractions(project_id);
```

### Environment Variables

```bash
# Backend
DATABASE_URL=sqlite:///./data/finline.db
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM Configuration
LLM_PROVIDER=gemini          # gemini, claude, openai
LLM_MODEL=gemini-2.0-flash
LLM_API_KEY=your-api-key

# Perplexity (for insights)
PERPLEXITY_API_KEY=your-api-key

# Stripe
STRIPE_SECRET_KEY=your-stripe-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API Response Format

All API responses follow this structure:

```json
// Success
{
    "success": true,
    "data": { ... }
}

// Error
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Revenue cannot be negative",
        "field": "cases.base_case.financials.revenue.2026"
    }
}
```

---

## 7. Chat Interface Specification

### Supported Commands (Natural Language)

The chat understands patterns like:

**Setting Values:**
- "Set CAPEX to 10M for 2026"
- "Set all CAPEX values to 10M"
- "Set revenue to 100, 110, 120, 130, 140 for years 2026-2030"

**Growth/Percentages:**
- "Increase CAPEX by 5% each year"
- "Set revenue growth to 8% for all forecast years"
- "Apply 20% EBITDA margin across all years"

**Formulas:**
- "Set CAPEX to 5% of revenue for each year"
- "Set D&A to 3% of revenue"

**Bulk Operations:**
- "Copy base case to upside case"
- "Increase all upside case revenues by 10%"

**Image Upload:**
- User uploads screenshot of Excel → extract numbers → apply to model

### Chat Architecture

```
User Input
    │
    ▼
┌─────────────────┐
│  Parse Intent   │  ← LLM (Gemini Flash)
│  Extract Params │
└────────┬────────┘
         │
         ▼
    ┌────────────┐
    │ Ambiguous? │
    └────┬───────┘
         │
    No ──┴── Yes
    │         │
    ▼         ▼
┌────────┐  ┌───────────────┐
│ Apply  │  │ Ask for       │
│ Update │  │ Clarification │
└────────┘  └───────────────┘
```

---

## 8. Key Simplifications Summary

| Aspect | finForge | finLine |
|--------|----------|---------|
| Schema | 780 lines, 16 types | ~100 lines, 3 types |
| Endpoints | 20+ | 7-10 |
| Pages | 24+ | 5 |
| State Management | Zustand stores | React Query only |
| Revenue Modeling | Driver formulas | Growth % |
| Working Capital | DSO/DIO/DPO | Total only |
| P&L Detection | 8 case types | None (user provides) |
| Naming | Mixed case | snake_case everywhere |
| Data Storage | JSON files + locking | SQLite with ACID |
| Wizard | 15 steps | None (modal + direct edit) |

---

## Next Steps

1. **Review this architecture** - any changes needed?
2. **Set up project skeleton** - folder structure, configs
3. **Implement auth** - port from finForge
4. **Build database layer** - SQLite + models
5. **Create basic API** - CRUD for projects
6. **Build frontend shell** - pages, routing, UI components
7. **Implement features** - financial table, chat, analysis

Ready to start coding when you approve this architecture.
