/**
 * finLine API Client
 *
 * All API calls go through this module.
 * Uses snake_case to match backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================================
// Types (snake_case to match backend)
// ============================================================

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface ProjectListItem {
  id: string;
  name: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectResponse {
  id: string;
  name: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  data: ProjectData;
}

export interface ProjectData {
  meta: ProjectMeta;
  cases: Record<string, CaseData>;
}

export interface ProjectMeta {
  user_id: string;
  project_id: string;
  version: string;
  name: string;
  company_name: string;
  currency: string;
  unit: string;
  frequency: string;
  financial_year_end: string;
  last_historical_period: string;
  created_date: string;
  last_modified: string;
}

export interface CaseData {
  case_desc: string;
  deal_parameters: DealParameters;
  financials: Financials;
}

export interface DealParameters {
  deal_date: string;
  exit_date: string;
  tax_rate: number;
  minimum_cash: number;
  entry_fee_percentage: number;
  exit_fee_percentage: number;
  entry_valuation: Valuation;
  exit_valuation: Valuation;
  capital_structure: CapitalStructure;
  equity_injection: number | null;
}

export interface Valuation {
  method: "multiple" | "hardcode";
  metric?: "EBITDA" | "EBIT" | "Revenue";
  multiple?: number;
  firm_value?: number;
}

export interface CapitalStructure {
  tranches: DebtTranche[];
  reference_rate_curve: ReferenceRateCurve | null;
}

export interface DebtTranche {
  tranche_id: string;
  label: string;
  type: string;
  currency: string;
  original_size: number;
  maturity?: string;
  oid?: number;
  interest_margin?: number;
  cash_interest_rate?: number;
  pik_interest_rate?: number;
  financing_fees?: number;
  undrawn_fee?: number;
  seniority?: number;
  repayment_seniority?: number;
  amortization?: string;
  percentage_drawn_at_deal_date?: number;
}

export interface ReferenceRateCurve {
  label: string;
  currency: string;
  points: Array<{ period: string; rate: number }>;
}

export interface Financials {
  income_statement: IncomeStatement;
  cash_flow_statement: CashFlowStatement;
}

export interface IncomeStatement {
  revenue: Record<string, DataPoint>;
  ebitda: EbitdaEntry[];
  ebit: Array<{ data: Record<string, DataPoint> }>;
  d_and_a: Array<{ data: Record<string, DataPoint> }>;
}

export interface EbitdaEntry {
  origin: "sourced" | "calculated";
  primary_use: 0 | 1;
  user_desc?: string;
  data: Record<string, DataPoint>;
}

export interface CashFlowStatement {
  capex: Record<string, DataPoint>;
  working_capital: Record<string, DataPoint>;
}

export interface DataPoint {
  value_type: "hardcode" | "formula" | "growthFormula";
  value?: number;
  expression?: string;
  growth_rate?: number;
}

// Analysis types
export interface AnalysisResult {
  success: boolean;
  case_id: string;
  summary: {
    moic: number;
    irr: number;
    entry_equity: number;
    exit_proceeds: number;
    total_debt_paydown?: number;
    final_cash?: number;
    final_leverage?: number;
    holding_period?: number;
    currency?: string;
  };
  sources_uses: {
    sources: Record<string, number>;
    uses: Record<string, number>;
    details?: Record<string, number>;
    validation?: { balanced: boolean; imbalance: number };
  };
  debt_schedules: Record<string, {
    type: string;
    starting_balance: number;
    original_size: number;
    balances: Record<string, number>;
    principal_payments: Record<string, { mandatory: number; sweep: number; total: number }>;
    interest_expense: Record<string, number>;
  }>;
  annual_cash_flows: Record<string, {
    ebitda: number;
    capex: number;
    fcf: number;
    cfads: number;
    cash_interest?: number;
  }>;
  returns?: {
    entry_equity: number;
    exit_enterprise_value: number;
    exit_proceeds: number;
    moic: number;
    irr: number;
  };
  leverage_metrics?: Record<string, {
    net_leverage: number;
    gross_leverage: number;
    total_debt: number;
    cash: number;
  }>;
  error?: string;
}

export interface AllCasesAnalysisResult {
  cases: Record<string, AnalysisResult>;
  summary: Record<string, {
    moic: number;
    irr: number;
    entry_equity: number;
    exit_proceeds: number;
  } | { error: string }>;
}

// Chat types
export interface ChatUpdate {
  path: string;
  value: any;
  description: string;
}

export interface ChatResponse {
  response: string;
  updates: ChatUpdate[];
  applied: boolean;
  error?: string;
}

// Subscription types
export interface SubscriptionResponse {
  status: string; // active, cancelled, past_due, none
  plan: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

export interface CheckoutResponse {
  checkout_url: string;
  session_id: string;
}

export interface PortalResponse {
  portal_url: string;
}

// ============================================================
// API Error
// ============================================================

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

// ============================================================
// Helper Functions
// ============================================================

function get_auth_header(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function handle_response<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = "Request failed";
    try {
      const error_data = await response.json();
      detail = error_data.detail || error_data.message || detail;
    } catch {
      // Ignore JSON parse errors
    }
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

// ============================================================
// API Functions
// ============================================================

export const api = {
  // Auth
  async register(email: string, password: string): Promise<UserResponse> {
    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    return handle_response(response);
  },

  async login(email: string, password: string): Promise<Token> {
    const form_data = new URLSearchParams();
    form_data.append("username", email);
    form_data.append("password", password);

    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form_data,
    });
    return handle_response(response);
  },

  async get_me(): Promise<UserResponse> {
    const response = await fetch(`${API_URL}/api/auth/me`, {
      headers: get_auth_header(),
    });
    return handle_response(response);
  },

  // Projects
  async list_projects(): Promise<ProjectListItem[]> {
    const response = await fetch(`${API_URL}/api/projects`, {
      headers: get_auth_header(),
    });
    return handle_response(response);
  },

  async create_project(
    name: string,
    company_name?: string,
    currency?: string,
    unit?: string
  ): Promise<ProjectResponse> {
    const response = await fetch(`${API_URL}/api/projects`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...get_auth_header(),
      },
      body: JSON.stringify({ name, company_name, currency, unit }),
    });
    return handle_response(response);
  },

  async get_project(project_id: string): Promise<ProjectResponse> {
    const response = await fetch(`${API_URL}/api/projects/${project_id}`, {
      headers: get_auth_header(),
    });
    return handle_response(response);
  },

  async update_project(
    project_id: string,
    path: string,
    value: any
  ): Promise<ProjectResponse> {
    const response = await fetch(`${API_URL}/api/projects/${project_id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...get_auth_header(),
      },
      body: JSON.stringify({ path, value }),
    });
    return handle_response(response);
  },

  async bulk_update_project(
    project_id: string,
    updates: Array<{ path: string; value: any }>
  ): Promise<ProjectResponse> {
    const response = await fetch(`${API_URL}/api/projects/${project_id}/bulk`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...get_auth_header(),
      },
      body: JSON.stringify({ updates }),
    });
    return handle_response(response);
  },

  async delete_project(project_id: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/projects/${project_id}`, {
      method: "DELETE",
      headers: get_auth_header(),
    });
    if (!response.ok) {
      throw new ApiError(response.status, "Failed to delete project");
    }
  },

  async add_case(project_id: string, case_id: string): Promise<ProjectResponse> {
    const response = await fetch(
      `${API_URL}/api/projects/${project_id}/cases/${case_id}`,
      {
        method: "POST",
        headers: get_auth_header(),
      }
    );
    return handle_response(response);
  },

  async delete_case(
    project_id: string,
    case_id: string
  ): Promise<ProjectResponse> {
    const response = await fetch(
      `${API_URL}/api/projects/${project_id}/cases/${case_id}`,
      {
        method: "DELETE",
        headers: get_auth_header(),
      }
    );
    return handle_response(response);
  },

  // Analysis
  async analyze(
    project_id: string,
    case_id: string = "base_case"
  ): Promise<AnalysisResult> {
    const response = await fetch(
      `${API_URL}/api/projects/${project_id}/analyze?case_id=${encodeURIComponent(case_id)}`,
      {
        method: "POST",
        headers: get_auth_header(),
      }
    );
    return handle_response(response);
  },

  async analyze_all(project_id: string): Promise<AllCasesAnalysisResult> {
    const response = await fetch(
      `${API_URL}/api/projects/${project_id}/analyze/all`,
      {
        method: "POST",
        headers: get_auth_header(),
      }
    );
    return handle_response(response);
  },

  // Export
  async export_excel(
    project_id: string,
    case_id: string = "base_case"
  ): Promise<Blob> {
    const response = await fetch(
      `${API_URL}/api/projects/${project_id}/export?case_id=${encodeURIComponent(case_id)}`,
      {
        method: "POST",
        headers: get_auth_header(),
      }
    );
    if (!response.ok) {
      let detail = "Export failed";
      try {
        const error_data = await response.json();
        detail = error_data.detail || detail;
      } catch {
        // Ignore
      }
      throw new ApiError(response.status, detail);
    }
    return response.blob();
  },

  // Chat
  async chat(
    project_id: string,
    message: string,
    case_id: string = "base_case",
    auto_apply: boolean = false
  ): Promise<ChatResponse> {
    const response = await fetch(`${API_URL}/api/projects/${project_id}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...get_auth_header(),
      },
      body: JSON.stringify({ message, case_id, auto_apply }),
    });
    return handle_response(response);
  },

  async apply_chat_updates(
    project_id: string,
    updates: ChatUpdate[],
    case_id: string = "base_case"
  ): Promise<ChatResponse> {
    const response = await fetch(
      `${API_URL}/api/projects/${project_id}/chat/apply?case_id=${encodeURIComponent(case_id)}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...get_auth_header(),
        },
        body: JSON.stringify(updates),
      }
    );
    return handle_response(response);
  },

  // Payments
  async get_subscription(): Promise<SubscriptionResponse> {
    const response = await fetch(`${API_URL}/api/payments/subscription`, {
      headers: get_auth_header(),
    });
    return handle_response(response);
  },

  async create_checkout(price_id: string): Promise<CheckoutResponse> {
    const response = await fetch(`${API_URL}/api/payments/create-checkout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...get_auth_header(),
      },
      body: JSON.stringify({
        price_id,
        success_url: `${window.location.origin}/settings?payment=success`,
        cancel_url: `${window.location.origin}/settings?payment=cancelled`,
      }),
    });
    return handle_response(response);
  },

  async create_portal(): Promise<PortalResponse> {
    const response = await fetch(`${API_URL}/api/payments/portal`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...get_auth_header(),
      },
      body: JSON.stringify({
        return_url: `${window.location.origin}/settings`,
      }),
    });
    return handle_response(response);
  },
};
