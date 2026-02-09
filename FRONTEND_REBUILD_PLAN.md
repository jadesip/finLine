# finLine Frontend Rebuild Plan

**Status:** Phase 5 UI Complete - Business Logic Pending
**Last Updated:** 2026-02-09

## Overview

Rebuild the finLine frontend to match the finForge wizard flow, UI/UX, and functionality. This document covers the complete 10-step wizard: Dashboard → Type → Name → Upload → Company → Financials → Insights → Forecast → Deal → Capital → Results.

---

## Current State

### Completed ✅

**Phase 1: Foundation Setup**
- ✅ shadcn/ui component library installed and configured
- ✅ Wizard context provider for state management
- ✅ Wizard layout with sidebar navigation
- ✅ Dashboard updated to link to wizard

**Phase 2: Core Wizard Flow (Steps 1-3)**
- ✅ Project type selection page (LBO enabled, others disabled)
- ✅ Project name page with create
- ✅ Document upload page with extraction progress
- ✅ Extraction API integration

**Phase 3: Data Review Pages (Steps 4-5)**
- ✅ Company info page with metadata editing
- ✅ Financials review page with editable table
- ✅ Validation checkbox tracking

**Phase 4: Business Intelligence (Step 6)**
- ✅ Insights page with 5 tabs
- ✅ Overview, Business Model, Management, Strategy & SWOT, Risk Analysis
- ✅ Connected to Perplexity/LangChain backend

**Phase 5: LBO Pages UI (Steps 7-10)**
- ✅ Forecast page (navigation bridge)
- ✅ Deal Assumptions page
  - MonthYearPicker for entry/exit dates
  - MultipleInput (shows "7.0x" format)
  - PercentageInput (shows "2%" format, no spinners)
  - Entry/Exit Valuation Multiples tables
  - Case selector
- ✅ Capital Structure page
  - Debt tranches list with add/remove
  - Tranche configuration (type, size, rates, PIK, fees, amortization, maturity, seniority)
  - Blue info bar
  - Reference rate curve (SOFR) toggle
  - Other Assumptions (tax rate, minimum cash)
  - Sources & Uses with balance check
- ✅ Results page
  - Executive Summary table
  - Sources & Uses cards
  - Returns Waterfall (collapsible)
  - Forecast & Cash Flows table
  - Credit Ratios table

### Pending 🔄

**Phase 5B: Business Logic**
- 🔄 Connect Forecast page to actual project financials
- 🔄 Connect Deal Assumptions to project data (save entry/exit, load EBITDA for multiples)
- 🔄 Connect Capital Structure to project (save tranches, calculate actual sources & uses)
- 🔄 Connect Results page to `/api/projects/{id}/analyze` (display real IRR, MOIC, cash flows)

---

## Architecture Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| UI Components | shadcn/ui + Radix | Industry standard, accessible, matches finForge |
| State Management | React Context + hooks | Simpler than Zustand, sufficient for wizard flow |
| Styling | Tailwind CSS | Already in use, consistent with finForge |
| Icons | Lucide React | Already installed, matches finForge |
| Forms | Native + controlled inputs | Keep simple, no heavy form library needed |

---

## Wizard Steps (10 total)

| # | Step ID | Page | Route | Status |
|---|---------|------|-------|--------|
| 1 | type | Project Type | `/project-wizard/type` | ✅ Complete |
| 2 | name | Project Name | `/project-wizard/name` | ✅ Complete |
| 3 | upload | Document Upload | `/project-wizard/upload` | ✅ Complete |
| 4 | company | Company Info | `/project-wizard/company` | ✅ Complete |
| 5 | financials | Financials Review | `/project-wizard/financials` | ✅ Complete |
| 6 | insights | Business Intelligence | `/project-wizard/insights` | ✅ Complete |
| 7 | forecast | Forecast Builder | `/project-wizard/forecast` | ✅ UI (logic pending) |
| 8 | deal_assumptions | Deal Assumptions | `/project-wizard/deal-assumptions` | ✅ UI (logic pending) |
| 9 | capital_structure | Capital Structure | `/project-wizard/capital-structure` | ✅ UI (logic pending) |
| 10 | results | Results Dashboard | `/project-wizard/results` | ✅ UI (logic pending) |

---

## File Structure

```
frontend/src/
├── app/
│   ├── page.tsx                          # Landing
│   ├── login/page.tsx                    # Auth
│   ├── dashboard/page.tsx                # Project list
│   ├── project/[id]/page.tsx             # Direct project editor
│   ├── project-wizard/
│   │   ├── layout.tsx                    # Wizard layout wrapper
│   │   ├── type/page.tsx                 # Step 1
│   │   ├── name/page.tsx                 # Step 2
│   │   ├── upload/page.tsx               # Step 3
│   │   ├── company/page.tsx              # Step 4
│   │   ├── financials/page.tsx           # Step 5
│   │   ├── insights/page.tsx             # Step 6
│   │   ├── forecast/page.tsx             # Step 7
│   │   ├── deal-assumptions/page.tsx     # Step 8
│   │   ├── capital-structure/page.tsx    # Step 9
│   │   └── results/page.tsx              # Step 10
│   └── settings/page.tsx
├── components/
│   ├── ui/                               # shadcn components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── label.tsx
│   │   ├── select.tsx
│   │   ├── checkbox.tsx
│   │   ├── tabs.tsx
│   │   ├── badge.tsx
│   │   ├── alert.tsx
│   │   ├── progress.tsx
│   │   └── separator.tsx
│   ├── layout/
│   │   ├── wizard-layout.tsx
│   │   ├── wizard-sidebar.tsx
│   │   └── wizard-header.tsx
│   ├── common/
│   │   └── file-upload.tsx
│   └── debug/
│       └── project-json-viewer.tsx       # Debug component for development
├── contexts/
│   └── wizard-context.tsx                # Wizard state management
├── lib/
│   ├── api.ts                            # API client with auth
│   └── utils.ts                          # cn() helper, etc.
└── types/
    ├── index.ts
    ├── project.ts
    ├── wizard.ts                         # Step definitions
    ├── extraction.ts
    └── insights.ts
```

---

## Custom Components

### PercentageInput
Shows value with % suffix (e.g., "5%"), no number spinners.
```tsx
// Usage
<PercentageInput
  value={fee_percentage}
  onChange={(val) => handle_change("fee_percentage", val)}
  placeholder="2.0"
/>
```

### NumberInput
Plain number input without browser spinners.
```tsx
// Usage
<NumberInput
  value={size}
  onChange={(val) => handle_change("size", val)}
  placeholder="100"
/>
```

### MultipleInput
Shows value with x suffix (e.g., "7.0x").
```tsx
// Usage
<MultipleInput
  id="entry-multiple"
  value={entry_multiple}
  onChange={(val) => handle_change("multiple", val)}
  placeholder="7.0"
/>
```

### MonthYearPicker
Date picker for month/year selection (deal dates).
```tsx
// Usage
<MonthYearPicker
  id="entry-date"
  value={deal_data.entry.date}
  onChange={(value) => handle_entry_change("date", value)}
/>
```

---

## Implementation Details

### Extraction Flow

```
1. User selects file → upload_and_extract(project_id, file)
   ↓
2. POST /api/projects/{id}/extract
   - Returns { extraction_id, status: 'pending' }
   ↓
3. Poll GET /api/projects/{id}/extractions/{extraction_id}
   - Every 1s for first 30 polls
   - Every 2s for next 30 polls
   - Every 3s after that
   ↓
4. Status updates shown to user:
   - progress: 0-10%   → "Uploading file..."
   - progress: 10-40%  → "Analyzing document structure..."
   - progress: 40-70%  → "Extracting financial data..."
   - progress: 70-90%  → "Processing business information..."
   - progress: 90-100% → "Finalizing extraction..."
   ↓
5. On status: 'completed':
   POST /api/projects/{id}/extractions/{extraction_id}/apply
   ↓
6. Navigate to /project-wizard/company
```

### State Sync Pattern

```typescript
// In wizard context
const update_field = async (path: string, value: any) => {
  // Optimistic update
  set_project_data(prev => set_nested_value(prev, path, value));

  // Sync to backend
  try {
    await api.update_project(project_id, path, value);
  } catch (error) {
    // Rollback on failure
    await load_project(project_id);
    throw error;
  }
};
```

---

## Next Steps (Business Logic)

### 1. Forecast Page Logic
- Load financials from `project_data.cases.base_case.financials`
- Display historical years (from extraction)
- Enable growth rate editing for forecast years
- Calculate projections and save to project

### 2. Deal Assumptions Logic
- Load EBITDA from financials for valuation multiples
- Save entry/exit dates, multiples, fees to `deal_parameters`
- Calculate purchase price from EBITDA × multiple
- Persist on blur/change

### 3. Capital Structure Logic
- Save debt tranches to `deal_parameters.capital_structure.tranches`
- Calculate sources from actual debt sizes
- Calculate uses from purchase price + fees
- Show equity plug automatically
- Persist tranche changes

### 4. Results Page Logic
- Call `POST /api/projects/{id}/analyze` on page load
- Display actual IRR, MOIC from analysis response
- Display actual sources & uses
- Display actual cash flows and credit ratios
- Handle analysis errors gracefully

---

## Success Criteria

1. **User can complete full wizard flow:**
   - Create LBO project from dashboard
   - Upload PDF/image document
   - Review extracted company info
   - Review and validate extracted financials
   - View AI-generated business intelligence
   - Configure forecast assumptions
   - Set deal entry/exit parameters
   - Configure debt structure
   - View calculated LBO returns

2. **UI matches finForge look and feel:**
   - Same card styles, spacing, colors
   - Same form layouts and interactions
   - Same progress indicators

3. **Data integrity:**
   - All data persists to backend
   - User edits save immediately
   - Analysis results reflect actual inputs

4. **Error handling:**
   - Graceful extraction failures
   - Analysis error display
   - Network error recovery
