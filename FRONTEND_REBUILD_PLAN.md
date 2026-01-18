# finLine Frontend Rebuild Plan

## Overview

Rebuild the finLine frontend to match the finForge wizard flow, UI/UX, and functionality. This plan covers the first phase of the wizard: Dashboard → Project Type → Name → Upload → Company Info → Financials Review → Business Intelligence.

---

## Current State Assessment

### What Exists in finLine

**Backend (Ready to Use):**
- ✅ Authentication API (`/api/auth/*`)
- ✅ Projects CRUD API (`/api/projects/*`)
- ✅ Document extraction API (`/api/projects/{id}/extract`) - Full vision LLM extraction
- ✅ LBO Analysis engine (`/api/projects/{id}/analyze`)
- ⚠️ Insights API (`/api/projects/{id}/insights`) - Needs enhancement for rich structure

**Frontend (Needs Rebuild):**
- ❌ No wizard flow
- ❌ No project type selection
- ❌ No upload UI (backend exists but unreachable)
- ❌ No proper component library
- ❌ Manual financials entry only (no extraction integration)
- ❌ No business intelligence UI

### What We're Building

```
Dashboard
    ↓
Project Type Selection (LBO, Corporate Financing, Business Plan, Public Equity)
    ↓
Project Name
    ↓
Document Upload (PDF/Image → AI Extraction)
    ↓
Company Info & Metadata Review (extracted data, editable)
    ↓
Financials Review (extracted data, editable, with validation checkboxes)
    ↓
Business Intelligence Review (Perplexity-powered, 5 tabs)
    ↓
[Future phases: Deal assumptions, Debt config, Analysis, Results...]
```

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

## Implementation Phases

### Phase 1: Foundation Setup

**1.1 Install shadcn/ui and setup component library**

```bash
# Already have Radix installed, need to add shadcn CLI and configure
npx shadcn@latest init
```

**Components to create in `/frontend/src/components/ui/`:**
- `button.tsx` - Primary, secondary, ghost, destructive variants
- `card.tsx` - Card, CardHeader, CardTitle, CardContent, CardFooter
- `input.tsx` - Text input with label support
- `label.tsx` - Form labels
- `select.tsx` - Dropdown select (Radix-based)
- `checkbox.tsx` - Checkboxes with Radix
- `tabs.tsx` - Tab navigation (Radix-based)
- `badge.tsx` - Status badges (Under Development, risk levels)
- `alert.tsx` - Success/error/info alerts
- `progress.tsx` - Progress bar for extraction
- `skeleton.tsx` - Loading skeletons
- `separator.tsx` - Visual dividers

**1.2 Create shared layout components**

```
/frontend/src/components/
├── ui/                    # shadcn components
├── layout/
│   ├── wizard-layout.tsx  # Wrapper with sidebar for wizard pages
│   ├── wizard-sidebar.tsx # Step navigation sidebar
│   └── wizard-header.tsx  # Page header with step indicator
└── common/
    ├── file-upload.tsx    # Drag & drop upload component
    └── editable-table.tsx # Financial data table with inline editing
```

**1.3 Create wizard state context**

```typescript
// /frontend/src/contexts/wizard-context.tsx
interface WizardState {
  project_id: string | null;
  project_data: ProjectData | null;
  current_step: WizardStep;
  visited_steps: string[];
  extraction_id: string | null;
  extraction_status: 'idle' | 'uploading' | 'extracting' | 'completed' | 'failed';
  extraction_progress: number;
  is_loading: boolean;
  error: string | null;
}

interface WizardActions {
  create_project: (type: string, name: string) => Promise<string>;
  load_project: (project_id: string) => Promise<void>;
  update_field: (path: string, value: any) => Promise<void>;
  upload_and_extract: (file: File) => Promise<void>;
  mark_step_visited: (step_id: string) => void;
  go_to_step: (step_id: string) => void;
  reset: () => void;
}
```

---

### Phase 2: Wizard Pages (Frontend)

**2.1 Dashboard Update** (`/dashboard/page.tsx`)

Current: Simple project list with "New Project" modal
Target: Same list but "New Project" → navigates to `/project-wizard/type`

Changes:
- Remove inline project creation modal
- "New Project" button → `router.push('/project-wizard/type')`
- Keep existing project list and navigation

**2.2 Project Type Selection** (`/project-wizard/type/page.tsx`)

UI from finForge screenshot:
- 2x2 grid of project type cards
- Each card: Icon + Title + Description + Badge (if under development)
- Only "Leveraged Buyout" is clickable (others show "Under Development")
- "Create Project" button at bottom (disabled until selection)

```tsx
const PROJECT_TYPES = [
  {
    id: 'lbo',
    title: 'Leveraged Buyout',
    description: 'Analyze private equity transactions with debt financing',
    icon: FileText,
    enabled: true,
  },
  {
    id: 'corporate_financing',
    title: 'Corporate Financing',
    description: 'Model debt and equity financing structures',
    icon: Building2,
    enabled: false,
  },
  {
    id: 'business_plan',
    title: 'Business Plan',
    description: 'Create comprehensive financial projections',
    icon: FileSpreadsheet,
    enabled: false,
  },
  {
    id: 'public_equity',
    title: 'Public Equity',
    description: 'Analyze public market investments',
    icon: TrendingUp,
    enabled: false,
  },
];
```

**2.3 Project Name** (`/project-wizard/name/page.tsx`)

Simple page:
- Text input for project name
- Optional: Company name input
- "Continue" button → creates project via API, navigates to upload

**2.4 Document Upload** (`/project-wizard/upload/page.tsx`)

UI from finForge screenshot:
- Centered card with dashed border drop zone
- Upload icon + "Click to upload or drag and drop" text
- "PDF, PNG, JPG, JPEG (max 50MB)" subtitle
- "Select File" button
- Progress indicator during extraction (animated)
- Status messages: "Uploading...", "Analyzing document...", "Extracting financials...", "Complete!"

Implementation:
```tsx
// States
const [file, set_file] = useState<File | null>(null);
const [status, set_status] = useState<'idle' | 'uploading' | 'extracting' | 'complete' | 'error'>('idle');
const [progress, set_progress] = useState(0);
const [error, set_error] = useState<string | null>(null);

// Flow
1. User drops/selects file
2. Call POST /api/projects/{id}/extract with file
3. Poll GET /api/projects/{id}/extractions/{extraction_id} every 1-3s
4. Show progress updates
5. On complete, call POST /api/projects/{id}/extractions/{extraction_id}/merge
6. Navigate to company info page
```

**2.5 Company Info** (`/project-wizard/company/page.tsx`)

UI from finForge screenshot - two sections in one page:

**Section 1: Success Banner**
- Green alert: "Data extracted successfully! Review and edit as needed."

**Section 2: Company Details Form**
- Company Name (text input, required, editable pencil icon)
- Country of Headquarters (dropdown)
- Currency (dropdown: USD, EUR, GBP, etc.)
- Unit Scale (dropdown: millions, thousands, billions)
- Reporting Frequency (dropdown: annually, quarterly)
- Fiscal Year End (dropdown: January-December)
- Last Historical Period (month dropdown + year dropdown)
- Forecast Horizon (dropdown: 1-10 years)

All fields pre-populated from extraction, user can edit. Changes save on blur.

**2.6 Financials Review** (`/project-wizard/financials/page.tsx`)

UI from finForge screenshot:

**Header:**
- "Review Financial Data"
- "Click any value to edit - changes save automatically"
- "Click the checkbox next to each field to validate the extracted data"

**Key Financials Table:**
- Header row: Metric | 2022A | 2023A | 2024A (years from extraction)
- Rows: Revenue, COGS, Operating Expenses, D&A, EBIT, Capex, Working Capital
- Each cell: value + checkbox
- Editable on click
- Counter: "X / Y validated"

**Other Financials (Collapsible):**
- Additional metrics: Profit Before Tax, Tax, Net Income
- Same format with checkboxes

Implementation notes:
- Years come from `meta.last_historical_period` and periods available
- "A" suffix for Actuals, "E" for Estimates (if forecasted)
- Validation checkboxes track user review state
- Auto-save on cell blur

**2.7 Business Intelligence** (`/project-wizard/insights/page.tsx`)

UI from finForge screenshot - 5 tabs:

**Tab Bar:**
```
[Overview] [Business Model] [Management] [Strategy & SWOT] [Risk Analysis (badge)]
```

**Tab 1: Overview**
- Business Overview card (description + confidence badge)
- Industry Context card (market characteristics, growth trends, regulatory factors, competitive dynamics)
- Recent Events list (with date, event type badges, impact indicator)

**Tab 2: Business Model**
- Revenue Model card (products/services, revenue streams, customer segments, geographic markets, business segments)
- Cost Structure card (fixed costs, variable costs, key cost drivers, operating leverage)
- Capital Requirements card (capex types, capital intensity, key assets, investment focus)

**Tab 3: Management**
- Grid of management team cards
- Each card: Name, Position, Tenure, Career summary
- Optional LinkedIn link

**Tab 4: Strategy & SWOT**
- Business Strategy section
- SWOT Grid (2x2: Strengths/Weaknesses/Opportunities/Threats)
- Color coded quadrants

**Tab 5: Risk Analysis**
- Overall Risk Assessment badge (Low/Medium/High/Critical)
- Individual risk cards for each risk type:
  - Revenue Concentration
  - Liquidity Concerns
  - Related Party Transactions
  - Governance Issues
  - Strategic Inconsistencies
  - Financial Red Flags
  - Operational Risks
  - Market Risks
- Each card shows flag status (green check or red warning)
- Badge in tab shows count of flagged risks

---

### Phase 3: Backend Enhancements

**3.1 Enhanced Insights API**

Update `/backend/api/insights.py` to return the rich finForge structure:

```python
@router.get("/{project_id}/insights")
async def get_full_insights(project_id: str, current_user: CurrentUser):
    """
    Returns complete InsightsData structure:
    - business_insights (description, revenue_model, cost_structure, capital_requirements, management_team)
    - strategic_analysis (strategy, swot_analysis, industry_context, recent_events, risk_analysis)
    """
```

**3.2 Create Insights Extractor Service**

New file: `/backend/services/insights/extractor.py`

```python
class InsightsExtractor:
    """
    Extracts business intelligence using Perplexity API.

    Performs two calls:
    1. Business insights (description, revenue model, costs, management)
    2. Strategic analysis (strategy, SWOT, industry, risks)
    """

    async def extract_insights(self, company_name: str, industry: str, context: str) -> InsightsData:
        # Call Perplexity with structured prompts
        # Parse response into InsightsData schema
        pass
```

**3.3 Insights Data Models**

New file: `/backend/models/insights.py`

```python
class BusinessDescription(BaseModel):
    summary: str
    source_pages: list[int] = []
    confidence: Literal["high", "medium", "low"] = "medium"

class RevenueModel(BaseModel):
    key_products_services: list[str] = []
    revenue_streams: list[str] = []
    customer_segments: list[str] = []
    geographic_markets: list[str] = []
    business_segments: list[BusinessSegment] = []

# ... full schema matching finForge types/insights.ts
```

---

### Phase 4: API Client Updates

**4.1 Add extraction methods to `/frontend/src/lib/api.ts`**

```typescript
// Document extraction
async upload_and_extract(project_id: string, file: File): Promise<ExtractionResponse>
async get_extraction_status(project_id: string, extraction_id: string): Promise<ExtractionStatus>
async merge_extraction(project_id: string, extraction_id: string, strategy: string): Promise<void>

// Insights
async get_insights(project_id: string): Promise<InsightsData | null>
async get_quick_insights(project_id: string): Promise<InsightsSummary>
```

**4.2 Add TypeScript types**

```typescript
// /frontend/src/types/extraction.ts
interface ExtractionResponse {
  extraction_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  result?: ExtractionResult;
}

// /frontend/src/types/insights.ts
// Copy from finForge types/insights.ts (already well-structured)
```

---

## File Structure (Final)

```
frontend/src/
├── app/
│   ├── page.tsx                          # Landing (existing)
│   ├── login/page.tsx                    # Auth (existing)
│   ├── dashboard/page.tsx                # Updated - links to wizard
│   ├── project/[id]/page.tsx             # Existing project editor
│   ├── project-wizard/
│   │   ├── layout.tsx                    # Wizard layout wrapper
│   │   ├── type/page.tsx                 # Step 1: Project type
│   │   ├── name/page.tsx                 # Step 2: Project name
│   │   ├── upload/page.tsx               # Step 3: Document upload
│   │   ├── company/page.tsx              # Step 4: Company info
│   │   ├── financials/page.tsx           # Step 5: Financials review
│   │   └── insights/page.tsx             # Step 6: Business intelligence
│   └── settings/page.tsx                 # Existing
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
│   └── common/
│       ├── file-upload.tsx
│       └── financial-table.tsx
├── contexts/
│   └── wizard-context.tsx
├── lib/
│   ├── api.ts                            # Updated with extraction/insights
│   └── utils.ts                          # cn() helper, etc.
└── types/
    ├── index.ts                          # Re-exports
    ├── project.ts                        # Existing
    ├── extraction.ts                     # New
    └── insights.ts                       # New (from finForge)
```

---

## Implementation Order

### Week 1: Foundation
1. ✅ Setup shadcn/ui components (button, card, input, label, select, badge, alert)
2. ✅ Create wizard context provider
3. ✅ Create wizard layout with sidebar
4. ✅ Update dashboard to link to wizard

### Week 2: Core Wizard Flow
5. ✅ Project type selection page
6. ✅ Project name page
7. ✅ Document upload page with progress
8. ✅ Add extraction API methods to frontend

### Week 3: Data Review Pages
9. ✅ Company info page
10. ✅ Financials review page with editable table
11. ✅ Add checkbox validation tracking

### Week 4: Business Intelligence
12. ✅ Enhance backend insights API
13. ✅ Create insights extractor service
14. ✅ Build insights page with 5 tabs
15. ✅ Connect to Perplexity API

### Week 5: Polish & Testing
16. ✅ Error handling throughout
17. ✅ Loading states and skeletons
18. ✅ Mobile responsiveness
19. ✅ End-to-end testing

---

## Key Implementation Notes

### Extraction Flow Detail

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
   - Max 300 polls (5 min timeout)
   ↓
4. Status updates shown to user:
   - progress: 0-10%   → "Uploading file..."
   - progress: 10-40%  → "Analyzing document structure..."
   - progress: 40-70%  → "Extracting financial data..."
   - progress: 70-90%  → "Processing business information..."
   - progress: 90-100% → "Finalizing extraction..."
   ↓
5. On status: 'completed':
   POST /api/projects/{id}/extractions/{extraction_id}/merge
   - strategy: 'overlay' (keep existing, add extracted)
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

### Validation Checkboxes

```typescript
// Store validation state in project data
interface FinancialsValidation {
  [metric_key: string]: {
    [year: string]: boolean;
  };
}

// Example:
// validation.revenue["2024"] = true (user validated 2024 revenue)
```

---

## Dependencies to Add

```json
{
  "dependencies": {
    "class-variance-authority": "^0.7.0",  // For shadcn button variants
    "clsx": "^2.1.0",                       // Already have
    "tailwind-merge": "^2.2.0"              // Already have
  }
}
```

---

## Questions Resolved

| Question | Answer |
|----------|--------|
| Backend scope | Enhance insights API to match finForge structure |
| UI components | Full shadcn/ui component library |
| State management | React Context + hooks |
| Scope | Phase 1: Dashboard → Insights (6 wizard steps) |

---

## Success Criteria

1. **User can complete full Phase 1 flow:**
   - Create LBO project from dashboard
   - Upload PDF/image document
   - Review extracted company info
   - Review and validate extracted financials
   - View AI-generated business intelligence

2. **UI matches finForge look and feel:**
   - Same card styles, spacing, colors
   - Same form layouts and interactions
   - Same progress indicators

3. **Data integrity:**
   - All extracted data persists to backend
   - User edits save immediately
   - Validation state tracked

4. **Error handling:**
   - Graceful extraction failures
   - Retry mechanisms
   - Clear error messages
