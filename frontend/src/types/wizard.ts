/**
 * Wizard step definitions
 */
export type WizardStepId =
  | "type"
  | "name"
  | "upload"
  | "company"
  | "financials"
  | "insights"
  | "forecast"
  | "deal_assumptions"
  | "capital_structure"
  | "results";

export interface WizardStep {
  id: WizardStepId;
  title: string;
  description: string;
  path: string;
}

export const WIZARD_STEPS: WizardStep[] = [
  {
    id: "type",
    title: "Project Type",
    description: "Select the type of analysis",
    path: "/project-wizard/type",
  },
  {
    id: "name",
    title: "Project Name",
    description: "Name your project",
    path: "/project-wizard/name",
  },
  {
    id: "upload",
    title: "Upload",
    description: "Upload financial documents",
    path: "/project-wizard/upload",
  },
  {
    id: "company",
    title: "Company Info",
    description: "Review company details",
    path: "/project-wizard/company",
  },
  {
    id: "financials",
    title: "Financials",
    description: "Review financial data",
    path: "/project-wizard/financials",
  },
  {
    id: "insights",
    title: "Insights",
    description: "Business intelligence",
    path: "/project-wizard/insights",
  },
  {
    id: "forecast",
    title: "Forecast",
    description: "Financial projections",
    path: "/project-wizard/forecast",
  },
  {
    id: "deal_assumptions",
    title: "Deal",
    description: "Entry and exit parameters",
    path: "/project-wizard/deal-assumptions",
  },
  {
    id: "capital_structure",
    title: "Capital",
    description: "Debt and equity structure",
    path: "/project-wizard/capital-structure",
  },
  {
    id: "results",
    title: "Results",
    description: "Transaction dashboard",
    path: "/project-wizard/results",
  },
];

/**
 * Project types available for selection
 */
export type ProjectType = "lbo" | "corporate_financing" | "business_plan" | "public_equity";

export interface ProjectTypeOption {
  id: ProjectType;
  title: string;
  description: string;
  enabled: boolean;
}

export const PROJECT_TYPES: ProjectTypeOption[] = [
  {
    id: "lbo",
    title: "Leveraged Buyout",
    description: "Analyze private equity transactions with debt financing",
    enabled: true,
  },
  {
    id: "corporate_financing",
    title: "Corporate Financing",
    description: "Model debt and equity financing structures",
    enabled: false,
  },
  {
    id: "business_plan",
    title: "Business Plan",
    description: "Create comprehensive financial projections",
    enabled: false,
  },
  {
    id: "public_equity",
    title: "Public Equity",
    description: "Analyze public market investments",
    enabled: false,
  },
];

/**
 * Extraction status
 */
export type ExtractionStatus =
  | "idle"
  | "uploading"
  | "extracting"
  | "completed"
  | "failed";

/**
 * Validation state for financials
 */
export interface FinancialsValidation {
  [metric_key: string]: {
    [year: string]: boolean;
  };
}
