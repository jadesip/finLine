"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import {
  api,
  ProjectResponse,
  AnalysisResult,
  ChatUpdate,
  ChatResponse,
} from "@/lib/api";
import {
  ArrowLeft,
  Play,
  Download,
  MessageSquare,
  Loader2,
  Check,
  X,
  Send,
  Plus,
  Trash2,
} from "lucide-react";

// ============================================================
// Data Format Utilities
// ============================================================

type YearValue = { year: string; value: number };
type YearValueArray = YearValue[];

// Convert array format [{year, value}] to object format {2024: value, 2025: value}
function array_to_year_map(arr: YearValueArray | undefined): Record<string, number> {
  if (!arr || !Array.isArray(arr)) return {};
  const map: Record<string, number> = {};
  for (const item of arr) {
    if (item.year && typeof item.value === "number") {
      map[item.year] = item.value;
    }
  }
  return map;
}

// Convert object format back to array format
function year_map_to_array(map: Record<string, number>): YearValueArray {
  return Object.entries(map)
    .filter(([year]) => /^\d{4}$/.test(year))
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([year, value]) => ({ year, value }));
}

// Get years from financials data
function get_years_from_financials(financials: any): string[] {
  const years = new Set<string>();

  // Check revenue
  const revenue = financials?.income_statement?.revenue;
  if (Array.isArray(revenue)) {
    revenue.forEach((r: YearValue) => years.add(r.year));
  }

  // Check EBITDA
  const ebitda = financials?.income_statement?.ebitda;
  if (Array.isArray(ebitda)) {
    ebitda.forEach((e: YearValue) => years.add(e.year));
  }

  // Check CAPEX
  const capex = financials?.cash_flow_statement?.capex;
  if (Array.isArray(capex)) {
    capex.forEach((c: YearValue) => years.add(c.year));
  }

  return Array.from(years).filter(y => /^\d{4}$/.test(y)).sort();
}

// ============================================================
// Main Component
// ============================================================

export default function ProjectPage() {
  const router = useRouter();
  const params = useParams();
  const project_id = params.id as string;

  const [project, set_project] = useState<ProjectResponse | null>(null);
  const [loading, set_loading] = useState(true);
  const [active_tab, set_active_tab] = useState<
    "financials" | "deal" | "debt" | "results"
  >("financials");
  const [active_case, set_active_case] = useState("base_case");
  const [show_chat, set_show_chat] = useState(false);

  // Analysis state
  const [analysis_result, set_analysis_result] = useState<AnalysisResult | null>(null);
  const [analyzing, set_analyzing] = useState(false);
  const [analysis_error, set_analysis_error] = useState<string | null>(null);

  // Export state
  const [exporting, set_exporting] = useState(false);

  useEffect(() => {
    load_project();
  }, [project_id]);

  const load_project = async () => {
    try {
      const data = await api.get_project(project_id);
      set_project(data);
      // Set first case as active if base_case doesn't exist
      if (data.data.cases && !data.data.cases[active_case]) {
        const first_case = Object.keys(data.data.cases)[0];
        if (first_case) set_active_case(first_case);
      }
    } catch (err: any) {
      console.error("Failed to load project:", err);
      if (err.status === 401) {
        router.push("/login");
      } else if (err.status === 404) {
        router.push("/dashboard");
      }
    } finally {
      set_loading(false);
    }
  };

  const handle_update = async (path: string, value: any) => {
    if (!project) return;

    try {
      const updated = await api.update_project(project_id, path, value);
      set_project(updated);
      // Clear analysis when data changes
      set_analysis_result(null);
    } catch (err) {
      console.error("Update failed:", err);
    }
  };

  const handle_analyze = async () => {
    set_analyzing(true);
    set_analysis_error(null);
    try {
      const result = await api.analyze(project_id, active_case);
      set_analysis_result(result);
      set_active_tab("results");
    } catch (err: any) {
      set_analysis_error(err.detail || err.message || "Analysis failed");
    } finally {
      set_analyzing(false);
    }
  };

  const handle_export = async () => {
    set_exporting(true);
    try {
      const blob = await api.export_excel(project_id, active_case);
      // Create download link
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${project?.name.replace(/\s+/g, "_").toLowerCase()}_${active_case}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error("Export failed:", err);
      alert(err.detail || "Export failed");
    } finally {
      set_exporting(false);
    }
  };

  const handle_chat_update = useCallback((updated_project: ProjectResponse) => {
    set_project(updated_project);
    set_analysis_result(null); // Clear analysis when chat updates data
  }, []);

  if (loading || !project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const current_case = project.data.cases[active_case];
  const cases = Object.keys(project.data.cases);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-card border-b sticky top-0 z-10">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <h1 className="font-bold text-lg">{project.name}</h1>
            <span className="text-sm text-muted-foreground">
              {project.data.meta.currency} {project.data.meta.unit}
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Case Selector */}
            <select
              value={active_case}
              onChange={(e) => {
                set_active_case(e.target.value);
                set_analysis_result(null);
              }}
              className="px-3 py-1.5 border rounded-md bg-background text-sm"
            >
              {cases.map((case_id) => (
                <option key={case_id} value={case_id}>
                  {case_id.replace(/_/g, " ")}
                </option>
              ))}
            </select>

            <button
              onClick={() => set_show_chat(!show_chat)}
              className={`p-2 rounded-md transition-colors ${
                show_chat
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-secondary"
              }`}
              title="Chat Assistant"
            >
              <MessageSquare className="h-5 w-5" />
            </button>

            <button
              onClick={handle_export}
              disabled={exporting}
              className="flex items-center gap-2 px-3 py-1.5 border rounded-md hover:bg-secondary text-sm disabled:opacity-50"
              title="Export to Excel"
            >
              {exporting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Export
            </button>

            <button
              onClick={handle_analyze}
              disabled={analyzing}
              className="flex items-center gap-2 bg-primary text-primary-foreground px-3 py-1.5 rounded-md hover:bg-primary/90 text-sm disabled:opacity-50"
              title="Run Analysis"
            >
              {analyzing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              Analyze
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="container mx-auto px-4">
          <div className="flex border-b">
            {(["financials", "deal", "debt", "results"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => set_active_tab(tab)}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  active_tab === tab
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {analysis_error && (
        <div className="bg-destructive/10 border-b border-destructive/20 px-4 py-2 text-sm text-destructive flex items-center justify-between">
          <span>{analysis_error}</span>
          <button onClick={() => set_analysis_error(null)}>
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Content Area */}
        <main className="flex-1 p-6 overflow-auto">
          {active_tab === "financials" && current_case && (
            <FinancialsTab
              case_data={current_case}
              case_id={active_case}
              on_update={handle_update}
              currency={project.data.meta.currency}
              unit={project.data.meta.unit}
            />
          )}
          {active_tab === "deal" && current_case && (
            <DealTab
              deal_params={current_case.deal_parameters}
              case_id={active_case}
              on_update={handle_update}
            />
          )}
          {active_tab === "debt" && current_case && (
            <DebtTab
              capital_structure={current_case.deal_parameters.capital_structure}
              case_id={active_case}
              on_update={handle_update}
            />
          )}
          {active_tab === "results" && (
            <ResultsTab
              result={analysis_result}
              analyzing={analyzing}
              on_analyze={handle_analyze}
            />
          )}
        </main>

        {/* Chat Panel */}
        {show_chat && (
          <ChatPanel
            project_id={project_id}
            case_id={active_case}
            on_update={handle_chat_update}
          />
        )}
      </div>
    </div>
  );
}

// ============================================================
// Financials Tab
// ============================================================

function FinancialsTab({
  case_data,
  case_id,
  on_update,
  currency,
  unit,
}: {
  case_data: any;
  case_id: string;
  on_update: (path: string, value: any) => void;
  currency: string;
  unit: string;
}) {
  const financials = case_data.financials;
  const income = financials?.income_statement || {};
  const cash_flow = financials?.cash_flow_statement || {};

  // Convert array data to maps for display
  const revenue_map = array_to_year_map(income.revenue);
  const ebitda_map = array_to_year_map(income.ebitda);
  const capex_map = array_to_year_map(cash_flow.capex);
  const wc_map = array_to_year_map(cash_flow.working_capital);

  // Get all years
  const years = get_years_from_financials(financials);

  // If no years, show empty state with ability to add years
  const [new_year, set_new_year] = useState("");

  const add_year = () => {
    if (!new_year || !/^\d{4}$/.test(new_year)) return;

    // Add year to revenue array
    const current_revenue = Array.isArray(income.revenue) ? income.revenue : [];
    const updated_revenue = [...current_revenue, { year: new_year, value: 0 }];
    updated_revenue.sort((a, b) => a.year.localeCompare(b.year));

    on_update(`cases.${case_id}.financials.income_statement.revenue`, updated_revenue);
    set_new_year("");
  };

  const update_metric = (
    metric_path: string,
    current_data: YearValueArray | undefined,
    year: string,
    value: number
  ) => {
    const current = Array.isArray(current_data) ? [...current_data] : [];
    const index = current.findIndex((item) => item.year === year);

    if (index >= 0) {
      current[index] = { year, value };
    } else {
      current.push({ year, value });
      current.sort((a, b) => a.year.localeCompare(b.year));
    }

    on_update(`cases.${case_id}.${metric_path}`, current);
  };

  return (
    <div className="space-y-6">
      {/* Add Year */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          placeholder="Add year (e.g., 2024)"
          value={new_year}
          onChange={(e) => set_new_year(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add_year()}
          className="px-3 py-1.5 border rounded-md bg-background text-sm w-40"
        />
        <button
          onClick={add_year}
          className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-md hover:bg-secondary"
        >
          <Plus className="h-4 w-4" />
          Add Year
        </button>
      </div>

      {years.length === 0 ? (
        <div className="bg-card rounded-lg border p-8 text-center text-muted-foreground">
          No financial data yet. Add a year to start entering data.
        </div>
      ) : (
        <>
          {/* Income Statement */}
          <div className="bg-card rounded-lg border p-4">
            <h3 className="font-medium mb-4">
              Income Statement ({currency} {unit})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 pr-4 font-medium w-40">Metric</th>
                    {years.map((year) => (
                      <th key={year} className="text-right py-2 px-2 font-medium min-w-24">
                        {year}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <FinancialRow
                    label="Revenue"
                    data={revenue_map}
                    years={years}
                    on_change={(year, value) =>
                      update_metric(
                        "financials.income_statement.revenue",
                        income.revenue,
                        year,
                        value
                      )
                    }
                  />
                  <FinancialRow
                    label="EBITDA"
                    data={ebitda_map}
                    years={years}
                    on_change={(year, value) =>
                      update_metric(
                        "financials.income_statement.ebitda",
                        income.ebitda,
                        year,
                        value
                      )
                    }
                  />
                </tbody>
              </table>
            </div>
          </div>

          {/* Cash Flow Items */}
          <div className="bg-card rounded-lg border p-4">
            <h3 className="font-medium mb-4">
              Cash Flow Items ({currency} {unit})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 pr-4 font-medium w-40">Metric</th>
                    {years.map((year) => (
                      <th key={year} className="text-right py-2 px-2 font-medium min-w-24">
                        {year}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <FinancialRow
                    label="CAPEX"
                    data={capex_map}
                    years={years}
                    on_change={(year, value) =>
                      update_metric(
                        "financials.cash_flow_statement.capex",
                        cash_flow.capex,
                        year,
                        value
                      )
                    }
                  />
                  <FinancialRow
                    label="Working Capital"
                    data={wc_map}
                    years={years}
                    on_change={(year, value) =>
                      update_metric(
                        "financials.cash_flow_statement.working_capital",
                        cash_flow.working_capital,
                        year,
                        value
                      )
                    }
                  />
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function FinancialRow({
  label,
  data,
  years,
  on_change,
}: {
  label: string;
  data: Record<string, number>;
  years: string[];
  on_change: (year: string, value: number) => void;
}) {
  return (
    <tr className="border-b hover:bg-muted/50">
      <td className="py-2 pr-4 font-medium">{label}</td>
      {years.map((year) => {
        const value = data[year];
        return (
          <td key={year} className="py-2 px-2 text-right">
            <input
              type="number"
              step="0.1"
              defaultValue={value ?? ""}
              placeholder="-"
              className="w-24 text-right px-2 py-1 border rounded bg-background text-sm"
              onBlur={(e) => {
                const new_value = parseFloat(e.target.value);
                if (!isNaN(new_value) && new_value !== value) {
                  on_change(year, new_value);
                }
              }}
            />
          </td>
        );
      })}
    </tr>
  );
}

// ============================================================
// Deal Tab
// ============================================================

function DealTab({
  deal_params,
  case_id,
  on_update,
}: {
  deal_params: any;
  case_id: string;
  on_update: (path: string, value: any) => void;
}) {
  const base_path = `cases.${case_id}.deal_parameters`;

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Dates */}
      <div className="bg-card rounded-lg border p-4">
        <h3 className="font-medium mb-4">Transaction Dates</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Deal Date
            </label>
            <input
              type="date"
              defaultValue={deal_params.deal_date || ""}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
              onChange={(e) =>
                on_update(`${base_path}.deal_date`, e.target.value)
              }
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Exit Date
            </label>
            <input
              type="date"
              defaultValue={deal_params.exit_date || ""}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
              onChange={(e) =>
                on_update(`${base_path}.exit_date`, e.target.value)
              }
            />
          </div>
        </div>
      </div>

      {/* Valuation */}
      <div className="bg-card rounded-lg border p-4">
        <h3 className="font-medium mb-4">Valuation</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Entry Multiple (x EBITDA)
            </label>
            <input
              type="number"
              step="0.1"
              defaultValue={deal_params.entry_valuation?.multiple ?? ""}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
              onBlur={(e) => {
                const val = parseFloat(e.target.value);
                if (!isNaN(val)) {
                  on_update(`${base_path}.entry_valuation`, {
                    method: "multiple",
                    metric: "EBITDA",
                    multiple: val,
                  });
                }
              }}
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Exit Multiple (x EBITDA)
            </label>
            <input
              type="number"
              step="0.1"
              defaultValue={deal_params.exit_valuation?.multiple ?? ""}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
              onBlur={(e) => {
                const val = parseFloat(e.target.value);
                if (!isNaN(val)) {
                  on_update(`${base_path}.exit_valuation`, {
                    method: "multiple",
                    metric: "EBITDA",
                    multiple: val,
                  });
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* Fees & Tax */}
      <div className="bg-card rounded-lg border p-4">
        <h3 className="font-medium mb-4">Fees & Tax</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Tax Rate (%)
            </label>
            <input
              type="number"
              step="0.1"
              defaultValue={
                deal_params.tax_rate != null
                  ? (deal_params.tax_rate * 100).toFixed(1)
                  : ""
              }
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
              onBlur={(e) => {
                const val = parseFloat(e.target.value);
                if (!isNaN(val)) {
                  on_update(`${base_path}.tax_rate`, val / 100);
                }
              }}
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Entry Fee (%)
            </label>
            <input
              type="number"
              step="0.1"
              defaultValue={deal_params.entry_fee_percentage ?? ""}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
              onBlur={(e) => {
                const val = parseFloat(e.target.value);
                if (!isNaN(val)) {
                  on_update(`${base_path}.entry_fee_percentage`, val);
                }
              }}
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Exit Fee (%)
            </label>
            <input
              type="number"
              step="0.1"
              defaultValue={deal_params.exit_fee_percentage ?? ""}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
              onBlur={(e) => {
                const val = parseFloat(e.target.value);
                if (!isNaN(val)) {
                  on_update(`${base_path}.exit_fee_percentage`, val);
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* Other Parameters */}
      <div className="bg-card rounded-lg border p-4">
        <h3 className="font-medium mb-4">Other Parameters</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Minimum Cash
            </label>
            <input
              type="number"
              step="0.1"
              defaultValue={deal_params.minimum_cash ?? ""}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
              onBlur={(e) => {
                const val = parseFloat(e.target.value);
                if (!isNaN(val)) {
                  on_update(`${base_path}.minimum_cash`, val);
                }
              }}
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Equity Injection (override)
            </label>
            <input
              type="number"
              step="0.1"
              defaultValue={deal_params.equity_injection ?? ""}
              placeholder="Auto-calculated"
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
              onBlur={(e) => {
                const val = e.target.value ? parseFloat(e.target.value) : null;
                on_update(`${base_path}.equity_injection`, val);
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// Debt Tab
// ============================================================

function DebtTab({
  capital_structure,
  case_id,
  on_update,
}: {
  capital_structure: any;
  case_id: string;
  on_update: (path: string, value: any) => void;
}) {
  const tranches = capital_structure?.tranches || [];
  const base_path = `cases.${case_id}.deal_parameters.capital_structure.tranches`;

  const add_tranche = () => {
    const new_tranche = {
      tranche_id: `tranche_${Date.now()}`,
      label: "New Tranche",
      type: "term_loan",
      currency: "USD",
      original_size: 0,
      amount: 0,
      interest_rate: 0.06,
      amortization_rate: 0,
      maturity: "",
    };
    on_update(base_path, [...tranches, new_tranche]);
  };

  const update_tranche = (index: number, field: string, value: any) => {
    const updated = [...tranches];
    updated[index] = { ...updated[index], [field]: value };
    // Keep amount and original_size in sync
    if (field === "original_size") {
      updated[index].amount = value;
    }
    on_update(base_path, updated);
  };

  const delete_tranche = (index: number) => {
    const updated = tranches.filter((_: any, i: number) => i !== index);
    on_update(base_path, updated);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">Debt Tranches</h3>
        <button
          onClick={add_tranche}
          className="flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <Plus className="h-4 w-4" />
          Add Tranche
        </button>
      </div>

      {tranches.length === 0 ? (
        <div className="bg-card rounded-lg border p-8 text-center text-muted-foreground">
          No debt tranches configured. Add a tranche to model debt financing.
        </div>
      ) : (
        <div className="space-y-4">
          {tranches.map((tranche: any, index: number) => (
            <div
              key={tranche.tranche_id || index}
              className="bg-card rounded-lg border p-4"
            >
              <div className="flex items-start justify-between mb-4">
                <input
                  type="text"
                  value={tranche.label || ""}
                  onChange={(e) => update_tranche(index, "label", e.target.value)}
                  className="font-medium bg-transparent border-b border-transparent hover:border-muted-foreground focus:border-primary focus:outline-none"
                />
                <button
                  onClick={() => delete_tranche(index)}
                  className="p-1 text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <label className="block text-muted-foreground mb-1">Type</label>
                  <select
                    value={tranche.type || "term_loan"}
                    onChange={(e) => update_tranche(index, "type", e.target.value)}
                    className="w-full px-2 py-1.5 border rounded bg-background text-sm"
                  >
                    <option value="term_loan">Term Loan</option>
                    <option value="revolver">Revolver</option>
                    <option value="senior_secured">Senior Secured</option>
                    <option value="mezzanine">Mezzanine</option>
                    <option value="pik">PIK</option>
                  </select>
                </div>
                <div>
                  <label className="block text-muted-foreground mb-1">Size</label>
                  <input
                    type="number"
                    step="0.1"
                    value={tranche.original_size || tranche.amount || ""}
                    onChange={(e) =>
                      update_tranche(index, "original_size", parseFloat(e.target.value) || 0)
                    }
                    className="w-full px-2 py-1.5 border rounded bg-background text-sm"
                  />
                </div>
                <div>
                  <label className="block text-muted-foreground mb-1">
                    Interest Rate (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={
                      tranche.interest_rate != null
                        ? (tranche.interest_rate * 100).toFixed(1)
                        : tranche.cash_interest_rate != null
                        ? (tranche.cash_interest_rate * 100).toFixed(1)
                        : ""
                    }
                    onChange={(e) => {
                      const rate = parseFloat(e.target.value) / 100;
                      update_tranche(index, "interest_rate", rate);
                      update_tranche(index, "cash_interest_rate", rate);
                    }}
                    className="w-full px-2 py-1.5 border rounded bg-background text-sm"
                  />
                </div>
                <div>
                  <label className="block text-muted-foreground mb-1">
                    Amortization (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={
                      tranche.amortization_rate != null
                        ? (tranche.amortization_rate * 100).toFixed(1)
                        : ""
                    }
                    onChange={(e) =>
                      update_tranche(index, "amortization_rate", parseFloat(e.target.value) / 100 || 0)
                    }
                    className="w-full px-2 py-1.5 border rounded bg-background text-sm"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================
// Results Tab
// ============================================================

function ResultsTab({
  result,
  analyzing,
  on_analyze,
}: {
  result: AnalysisResult | null;
  analyzing: boolean;
  on_analyze: () => void;
}) {
  if (analyzing) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Running LBO analysis...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-card rounded-lg border p-8 text-center">
        <h3 className="font-medium mb-2">Analysis Results</h3>
        <p className="text-muted-foreground mb-4">
          Click &quot;Analyze&quot; to run the LBO analysis and see results here.
        </p>
        <button
          onClick={on_analyze}
          className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
        >
          <Play className="h-4 w-4" />
          Run Analysis
        </button>
      </div>
    );
  }

  const { summary, sources_uses, debt_schedules, annual_cash_flows } = result;

  // Helper to filter out total fields from sources/uses
  const filter_totals = (obj: Record<string, number>) =>
    Object.entries(obj).filter(([key]) => !key.startsWith("total_"));

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground mb-1">IRR</div>
          <div className="text-3xl font-bold text-primary">
            {(summary.irr * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground mb-1">MOIC</div>
          <div className="text-3xl font-bold text-primary">
            {summary.moic.toFixed(2)}x
          </div>
        </div>
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground mb-1">Equity Invested</div>
          <div className="text-2xl font-bold">
            {summary.entry_equity.toFixed(1)}
          </div>
        </div>
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground mb-1">Exit Proceeds</div>
          <div className="text-2xl font-bold">
            {summary.exit_proceeds.toFixed(1)}
          </div>
        </div>
      </div>

      {/* Sources & Uses */}
      {sources_uses && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-card rounded-lg border p-4">
            <h3 className="font-medium mb-4">Sources</h3>
            <div className="space-y-2 text-sm">
              {filter_totals(sources_uses.sources).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-muted-foreground capitalize">
                    {key.replace(/_/g, " ")}
                  </span>
                  <span>{(value as number).toFixed(1)}</span>
                </div>
              ))}
              <div className="flex justify-between font-medium pt-2 border-t">
                <span>Total Sources</span>
                <span>{(sources_uses.sources.total_sources || 0).toFixed(1)}</span>
              </div>
            </div>
          </div>
          <div className="bg-card rounded-lg border p-4">
            <h3 className="font-medium mb-4">Uses</h3>
            <div className="space-y-2 text-sm">
              {filter_totals(sources_uses.uses).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-muted-foreground capitalize">
                    {key.replace(/_/g, " ")}
                  </span>
                  <span>{(value as number).toFixed(1)}</span>
                </div>
              ))}
              <div className="flex justify-between font-medium pt-2 border-t">
                <span>Total Uses</span>
                <span>{(sources_uses.uses.total_uses || 0).toFixed(1)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cash Flows */}
      {annual_cash_flows && Object.keys(annual_cash_flows).length > 0 && (
        <div className="bg-card rounded-lg border p-4">
          <h3 className="font-medium mb-4">Cash Flow Projections</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 pr-4 font-medium">Year</th>
                  <th className="text-right py-2 px-2 font-medium">EBITDA</th>
                  <th className="text-right py-2 px-2 font-medium">CAPEX</th>
                  <th className="text-right py-2 px-2 font-medium">FCF</th>
                  <th className="text-right py-2 px-2 font-medium">CFADS</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(annual_cash_flows)
                  .sort(([a], [b]) => a.localeCompare(b))
                  .map(([year, cf]: [string, any]) => (
                    <tr key={year} className="border-b">
                      <td className="py-2 pr-4">{year}</td>
                      <td className="py-2 px-2 text-right">
                        {cf.ebitda?.toFixed(1) ?? "-"}
                      </td>
                      <td className="py-2 px-2 text-right">
                        {Math.abs(cf.capex || 0).toFixed(1)}
                      </td>
                      <td className="py-2 px-2 text-right">
                        {cf.fcf?.toFixed(1) ?? "-"}
                      </td>
                      <td className="py-2 px-2 text-right">
                        {cf.cfads?.toFixed(1) ?? "-"}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Debt Schedule */}
      {debt_schedules && Object.keys(debt_schedules).length > 0 && (
        <div className="bg-card rounded-lg border p-4">
          <h3 className="font-medium mb-4">Debt Schedule</h3>
          {Object.entries(debt_schedules).map(([tranche_name, tranche]: [string, any]) => (
            <div key={tranche_name} className="mb-4 last:mb-0">
              <h4 className="text-sm font-medium text-muted-foreground mb-2">{tranche_name}</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 pr-4 font-medium">Year</th>
                      <th className="text-right py-2 px-2 font-medium">Balance</th>
                      <th className="text-right py-2 px-2 font-medium">Interest</th>
                      <th className="text-right py-2 px-2 font-medium">Principal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(tranche.balances || {})
                      .sort(([a], [b]) => a.localeCompare(b))
                      .map(([year, balance]: [string, any]) => (
                        <tr key={year} className="border-b">
                          <td className="py-2 pr-4">{year}</td>
                          <td className="py-2 px-2 text-right">
                            {balance?.toFixed(1) ?? "-"}
                          </td>
                          <td className="py-2 px-2 text-right">
                            {tranche.interest_expense?.[year]?.toFixed(1) ?? "-"}
                          </td>
                          <td className="py-2 px-2 text-right">
                            {tranche.principal_payments?.[year]?.total?.toFixed(1) ?? "-"}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================
// Chat Panel
// ============================================================

function ChatPanel({
  project_id,
  case_id,
  on_update,
}: {
  project_id: string;
  case_id: string;
  on_update: (project: ProjectResponse) => void;
}) {
  const [message, set_message] = useState("");
  const [sending, set_sending] = useState(false);
  const [messages, set_messages] = useState<
    Array<{
      role: "user" | "assistant";
      content: string;
      updates?: ChatUpdate[];
      applied?: boolean;
    }>
  >([]);
  const [pending_updates, set_pending_updates] = useState<ChatUpdate[] | null>(null);

  const send_message = async () => {
    if (!message.trim() || sending) return;

    const user_msg = message.trim();
    set_message("");
    set_sending(true);
    set_messages((prev) => [...prev, { role: "user", content: user_msg }]);

    try {
      const response = await api.chat(project_id, user_msg, case_id, false);

      set_messages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.response,
          updates: response.updates,
          applied: response.applied,
        },
      ]);

      if (response.updates && response.updates.length > 0 && !response.applied) {
        set_pending_updates(response.updates);
      }
    } catch (err: any) {
      set_messages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err.detail || err.message || "Failed to process request"}`,
        },
      ]);
    } finally {
      set_sending(false);
    }
  };

  const apply_updates = async () => {
    if (!pending_updates) return;

    set_sending(true);
    try {
      const response = await api.apply_chat_updates(project_id, pending_updates, case_id);

      // Reload project to get updated data
      const updated = await api.get_project(project_id);
      on_update(updated);

      set_messages((prev) => [
        ...prev,
        { role: "assistant", content: "Changes applied successfully." },
      ]);
      set_pending_updates(null);
    } catch (err: any) {
      set_messages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Failed to apply: ${err.detail || err.message}`,
        },
      ]);
    } finally {
      set_sending(false);
    }
  };

  return (
    <aside className="w-96 border-l bg-card flex flex-col">
      <div className="p-4 border-b">
        <h2 className="font-medium">Chat Assistant</h2>
        <p className="text-xs text-muted-foreground mt-1">
          Ask to update your model in natural language
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-sm text-muted-foreground">
            <p className="mb-3">Try asking:</p>
            <ul className="space-y-2 text-xs">
              <li className="p-2 bg-muted rounded cursor-pointer hover:bg-muted/80"
                  onClick={() => set_message("Set EBITDA to 100M for 2024")}>
                &quot;Set EBITDA to 100M for 2024&quot;
              </li>
              <li className="p-2 bg-muted rounded cursor-pointer hover:bg-muted/80"
                  onClick={() => set_message("Change entry multiple to 10x")}>
                &quot;Change entry multiple to 10x&quot;
              </li>
              <li className="p-2 bg-muted rounded cursor-pointer hover:bg-muted/80"
                  onClick={() => set_message("Set tax rate to 25%")}>
                &quot;Set tax rate to 25%&quot;
              </li>
            </ul>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`text-sm ${
              msg.role === "user"
                ? "bg-primary text-primary-foreground rounded-lg p-3 ml-8"
                : "bg-muted rounded-lg p-3 mr-8"
            }`}
          >
            {msg.content}
            {msg.updates && msg.updates.length > 0 && !msg.applied && (
              <div className="mt-2 pt-2 border-t border-border/50">
                <p className="text-xs opacity-75 mb-1">Proposed changes:</p>
                <ul className="text-xs space-y-1">
                  {msg.updates.map((u, j) => (
                    <li key={j}>• {u.description}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}

        {sending && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Processing...
          </div>
        )}
      </div>

      {/* Pending Updates Actions */}
      {pending_updates && (
        <div className="p-4 border-t bg-muted/50">
          <p className="text-sm mb-2">Apply these changes?</p>
          <div className="flex gap-2">
            <button
              onClick={apply_updates}
              disabled={sending}
              className="flex-1 flex items-center justify-center gap-1 bg-primary text-primary-foreground px-3 py-1.5 rounded text-sm disabled:opacity-50"
            >
              <Check className="h-4 w-4" />
              Apply
            </button>
            <button
              onClick={() => set_pending_updates(null)}
              disabled={sending}
              className="flex-1 flex items-center justify-center gap-1 border px-3 py-1.5 rounded text-sm disabled:opacity-50"
            >
              <X className="h-4 w-4" />
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => set_message(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send_message()}
            placeholder="Type your request..."
            disabled={sending}
            className="flex-1 px-3 py-2 border rounded-md bg-background text-sm disabled:opacity-50"
          />
          <button
            onClick={send_message}
            disabled={sending || !message.trim()}
            className="p-2 bg-primary text-primary-foreground rounded-md disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
