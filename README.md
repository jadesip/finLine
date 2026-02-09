# finLine

A simplified LBO financial modeling platform with AI-powered features.

**Status:** Phase 8 Complete (UI) | Business Logic Pending | [See Implementation Plan](IMPLEMENTATION_PLAN.md)

## Features

- **LBO Analysis Engine** - IRR, MOIC, debt schedules, cash flow projections
- **AI Chat Assistant** - Natural language model updates ("Set EBITDA to 100M for 2024")
- **Document Extraction** - Extract financials from PDFs and images
  - Hybrid text+image extraction for accurate number parsing
  - LangChain-powered business insights
  - EBIT/D&A field normalization
- **10-Step Wizard Flow** - Type → Name → Upload → Company → Financials → Insights → Forecast → Deal → Capital → Results
- **Excel Export** - Full model export with formulas
- **Multiple Cases** - Base, upside, downside scenarios
- **Full Debt Modeling** - Term loans, revolvers, PIK, amortization schedules

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+ / FastAPI |
| Database | SQLite with JSON columns |
| Frontend | Next.js 14 / React 18 / TypeScript |
| Styling | Tailwind CSS + shadcn/ui |
| Auth | JWT + bcrypt (with auto-refresh) |
| LLM | OpenAI / Claude / Gemini (configurable) |
| Payments | Stripe |

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export JWT_SECRET_KEY="your-secret-key"
export LLM_API_KEY="your-openai-key"

# Start server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Project Structure

```
finLine/
├── backend/
│   ├── api/           # FastAPI endpoints (auth, projects, chat, etc.)
│   ├── engine/        # LBO calculation engine
│   ├── services/      # LLM, Excel export, document extraction
│   ├── models/        # Pydantic schemas
│   └── tests/         # pytest test suite
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── project-wizard/  # 10-step wizard flow
│       │   │   ├── type/
│       │   │   ├── name/
│       │   │   ├── upload/
│       │   │   ├── company/
│       │   │   ├── financials/
│       │   │   ├── insights/
│       │   │   ├── forecast/
│       │   │   ├── deal-assumptions/
│       │   │   ├── capital-structure/
│       │   │   └── results/
│       │   └── dashboard/
│       ├── components/  # UI components (shadcn/ui)
│       ├── contexts/    # Wizard state management
│       └── lib/         # API client, utilities
└── data/              # SQLite database (gitignored)
```

## API Endpoints

### Auth
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login, get JWT
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project
- `PATCH /api/projects/{id}` - Update field
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/analyze` - Run LBO analysis
- `POST /api/projects/{id}/export` - Export to Excel
- `POST /api/projects/{id}/chat` - AI chat updates
- `POST /api/projects/{id}/extract` - Document extraction

## Environment Variables

```bash
# Backend
JWT_SECRET_KEY=your-secret-key
LLM_PROVIDER=openai          # openai, claude, gemini
LLM_API_KEY=your-api-key
STRIPE_SECRET_KEY=sk_...     # Optional

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

## Current Status

### Completed
- ✅ Full backend API (28 endpoints)
- ✅ LBO calculation engine
- ✅ Document extraction with hybrid text+image
- ✅ 10-step wizard UI (all pages built)
- ✅ JWT auth with auto-refresh
- ✅ EBIT normalization (handles income_from_operations, operating_income variants)

### In Progress
- 🔄 Business logic for wizard pages (connecting UI to backend)
- 🔄 Forecast builder calculations
- 🔄 Deal assumptions to LBO engine integration

### Pending
- ⏳ Full end-to-end testing
- ⏳ Excel export template refinement
- ⏳ Deployment to production

## License

MIT
