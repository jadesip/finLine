# finLine

A simplified LBO financial modeling platform.

## Overview

finLine is a focused financial modeling tool for LBO analysis with:
- Simple data input (user provides EBITDA directly)
- Chat-assisted editing for bulk updates
- Full debt tranche flexibility
- Multiple case scenarios

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed technical documentation.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Database | SQLite (JSON column) |
| Backend | Python + FastAPI |
| Frontend | Next.js + React |
| Auth | JWT + bcrypt |
| Chat LLM | Gemini Flash (abstracted) |
| Payments | Stripe |

## Naming Convention

**snake_case everywhere** - database, API, TypeScript, Python. No exceptions.

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
finLine/
├── backend/           # FastAPI backend
│   ├── api/          # API endpoints
│   ├── models/       # Pydantic + DB models
│   ├── engine/       # LBO calculations
│   └── services/     # LLM, extraction, export
├── frontend/         # Next.js frontend
│   └── src/
│       ├── app/      # Pages (5 total)
│       ├── components/
│       ├── lib/      # API client
│       └── types/    # TypeScript types
└── data/             # SQLite database
```

## Development

This project was rebuilt from finForge with lessons learned:
- Simplified schema (no revenue drivers, no DSO/DIO/DPO)
- Fewer endpoints (~10 vs 20+)
- Fewer pages (5 vs 24+)
- Single naming convention (snake_case)
- SQLite instead of JSON files
