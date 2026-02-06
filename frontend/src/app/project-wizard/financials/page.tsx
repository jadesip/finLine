"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { ChevronDown, ChevronUp, Check, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { useWizard } from "@/contexts/wizard-context";
import { ProjectJsonViewer } from "@/components/debug/project-json-viewer";
import type { ProjectMeta, Financials } from "@/lib/api";

// Financial metrics configuration (keys match finForge schema)
const KEY_FINANCIALS = [
  { key: "revenue", label: "Revenue", path: "financials.income_statement.revenue" },
  { key: "cogs", label: "COGS", path: "financials.income_statement.cogs" },
  { key: "opex", label: "Operating Expenses", path: "financials.income_statement.opex" },
  { key: "d&a", label: "D&A", path: "financials.income_statement.d&a" },
  { key: "ebit", label: "EBIT", path: "financials.income_statement.ebit" },
  { key: "capex", label: "Capex", path: "financials.cash_flow_statement.capex" },
  { key: "working_capital", label: "Working Capital", path: "financials.balance_sheet.working_capital" },
];

const OTHER_FINANCIALS = [
  { key: "profit_before_tax", label: "Profit Before Tax", path: "financials.income_statement.profit_before_tax" },
  { key: "tax", label: "Tax", path: "financials.income_statement.tax" },
  { key: "net_income", label: "Net Income", path: "financials.income_statement.net_income" },
  { key: "ebitda", label: "EBITDA", path: "financials.income_statement.ebitda" },
  { key: "receivables", label: "Receivables", path: "financials.balance_sheet.receivables" },
  { key: "inventory", label: "Inventory", path: "financials.balance_sheet.inventory" },
  { key: "payables", label: "Payables", path: "financials.balance_sheet.payables" },
];

type YearData = { [year: string]: number | null };

export default function FinancialsPage() {
  const router = useRouter();
  const { state, update_field, set_field_validated, mark_step_visited } = useWizard();
  const [show_other, set_show_other] = useState(false);
  const [editing_cell, set_editing_cell] = useState<{ metric: string; year: string } | null>(null);

  // Mark step as visited on mount
  useEffect(() => {
    mark_step_visited("financials");
  }, [mark_step_visited]);

  // Redirect if no project
  useEffect(() => {
    if (!state.project_id) {
      router.push("/project-wizard/type");
    }
  }, [state.project_id, router]);

  const base_case = state.project_data?.cases?.base_case;
  const meta = (state.project_data?.meta || {}) as Partial<ProjectMeta>;
  const financials = (base_case?.financials || {}) as Partial<Financials>;

  // Determine EBITDA source (from document vs calculated)
  const ebitda_source = useMemo(() => {
    const ebitda = financials.income_statement?.ebitda;
    if (Array.isArray(ebitda) && ebitda[0]) {
      const origin = ebitda[0].origin;
      if (origin === "sourced") {
        return "from source documents";
      } else if (origin === "calculated") {
        return "calculated from D&A + EBIT";
      }
    }
    // Default - assume from source if we have data
    return ebitda ? "from source documents" : null;
  }, [financials]);

  // Extract years from financial data
  const years = useMemo(() => {
    const year_set = new Set<string>();

    // Check income statement revenue
    const revenue = financials.income_statement?.revenue;
    if (Array.isArray(revenue)) {
      revenue.forEach((item: any) => {
        if (item.year) year_set.add(item.year);
      });
    } else if (revenue && typeof revenue === "object") {
      Object.keys(revenue).forEach(key => {
        if (/^\d{4}$/.test(key)) year_set.add(key);
      });
    }

    // Check EBITDA if revenue empty
    if (year_set.size === 0) {
      const ebitda = financials.income_statement?.ebitda;
      if (Array.isArray(ebitda)) {
        ebitda.forEach((entry: any) => {
          if (entry.data) {
            Object.keys(entry.data).forEach(key => {
              if (/^\d{4}$/.test(key)) year_set.add(key);
            });
          }
        });
      }
    }

    // If still empty, generate default years
    if (year_set.size === 0) {
      const last_hist = meta.last_historical_period;
      if (last_hist) {
        const year_match = last_hist.match(/(\d{2,4})$/);
        if (year_match) {
          let base_year = parseInt(year_match[1], 10);
          if (base_year < 100) base_year += 2000;
          for (let i = -2; i <= 2; i++) {
            year_set.add((base_year + i).toString());
          }
        }
      } else {
        // Default to current year range
        const current = new Date().getFullYear();
        for (let i = -2; i <= 2; i++) {
          year_set.add((current + i).toString());
        }
      }
    }

    return Array.from(year_set).sort();
  }, [financials, meta]);

  // Get value for a metric/year
  const get_value = (metric_key: string, year: string): number | null => {
    const income = (financials.income_statement || {}) as Record<string, any>;
    const cash_flow = (financials.cash_flow_statement || {}) as Record<string, any>;
    const balance = (financials.balance_sheet || {}) as Record<string, any>;

    // Check income statement, then cash flow, then balance sheet
    let data = income[metric_key];
    if (!data) {
      data = cash_flow[metric_key];
    }
    if (!data) {
      data = balance[metric_key];
    }

    if (!data) return null;

    // Handle array format [{year, value}]
    if (Array.isArray(data)) {
      // For EBITDA with nested structure
      if (metric_key === "ebitda" && data[0]?.data) {
        const entry = data.find((e: any) => e.primary_use === 1) || data[0];
        const year_data = entry?.data?.[year];
        return year_data?.value ?? null;
      }
      const item = data.find((d: any) => d.year === year);
      return item?.value ?? null;
    }

    // Handle object format {year: {value, value_type}}
    if (typeof data === "object") {
      const year_data = data[year];
      if (year_data?.value !== undefined) {
        return year_data.value;
      }
      // Direct value
      if (typeof year_data === "number") {
        return year_data;
      }
    }

    return null;
  };

  // Handle value change
  const handle_value_change = async (metric_key: string, year: string, value: number | null) => {
    const metric = [...KEY_FINANCIALS, ...OTHER_FINANCIALS].find(m => m.key === metric_key);
    if (!metric) return;

    // Construct the path
    const base_path = `cases.base_case.${metric.path}`;

    // Get current data to determine format
    const income = (financials.income_statement || {}) as Record<string, any>;
    const cash_flow = (financials.cash_flow_statement || {}) as Record<string, any>;
    let current_data = income[metric_key] || cash_flow[metric_key];

    if (Array.isArray(current_data)) {
      // Handle array format
      if (metric_key === "ebitda" && current_data[0]?.data) {
        // EBITDA with nested structure
        const entry = current_data.find((e: any) => e.primary_use === 1) || current_data[0];
        const entry_index = current_data.indexOf(entry);
        await update_field(`${base_path}[${entry_index}].data.${year}.value`, value);
      } else {
        // Simple array format
        const existing_index = current_data.findIndex((d: any) => d.year === year);
        if (existing_index >= 0) {
          await update_field(`${base_path}[${existing_index}].value`, value);
        } else {
          // Add new year
          const new_data = [...current_data, { year, value }].sort((a, b) => a.year.localeCompare(b.year));
          await update_field(base_path, new_data);
        }
      }
    } else {
      // Object format
      await update_field(`${base_path}.${year}`, { value, value_type: "hardcode" });
    }

    set_editing_cell(null);
  };

  // Count validated fields
  const validation_counts = useMemo(() => {
    let key_validated = 0;
    let key_total = 0;
    let other_validated = 0;
    let other_total = 0;

    KEY_FINANCIALS.forEach(metric => {
      years.forEach(year => {
        key_total++;
        if (state.financials_validation[metric.key]?.[year]) {
          key_validated++;
        }
      });
    });

    OTHER_FINANCIALS.forEach(metric => {
      years.forEach(year => {
        other_total++;
        if (state.financials_validation[metric.key]?.[year]) {
          other_validated++;
        }
      });
    });

    return { key_validated, key_total, other_validated, other_total };
  }, [state.financials_validation, years]);

  const handle_continue = () => {
    router.push("/project-wizard/insights");
  };

  return (
    <div className="py-8">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          Review Financial Data
        </h1>
        <p className="text-muted-foreground">
          Click any value to edit - changes save automatically
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          Click the checkbox next to each field to validate the extracted data
        </p>
      </div>

      {/* Key Financials */}
      <Card className="mb-6">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Key Financials</CardTitle>
            <p className="text-sm text-muted-foreground">
              ({meta.currency || "USD"} {meta.unit || "millions"}, {meta.financial_year_end || "Dec"}-YE)
            </p>
          </div>
          <span className="text-sm text-muted-foreground">
            {validation_counts.key_validated} / {validation_counts.key_total} validated
          </span>
        </CardHeader>
        <CardContent>
          <FinancialTable
            metrics={KEY_FINANCIALS}
            years={years}
            get_value={get_value}
            validation={state.financials_validation}
            on_value_change={handle_value_change}
            on_validate={set_field_validated}
            editing_cell={editing_cell}
            on_edit_cell={set_editing_cell}
          />
        </CardContent>
      </Card>

      {/* Other Financials (Collapsible) */}
      <Card className="mb-8">
        <CardHeader
          className="cursor-pointer"
          onClick={() => set_show_other(!show_other)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle>Other Financials</CardTitle>
              {show_other ? (
                <ChevronUp className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              )}
            </div>
            <span className="text-sm text-muted-foreground">
              {validation_counts.other_validated} / {validation_counts.other_total} validated
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            ({meta.currency || "USD"} {meta.unit || "millions"}, {meta.financial_year_end || "Dec"}-YE)
          </p>
        </CardHeader>
        {show_other && (
          <CardContent>
            <FinancialTable
              metrics={OTHER_FINANCIALS}
              years={years}
              get_value={get_value}
              validation={state.financials_validation}
              on_value_change={handle_value_change}
              on_validate={set_field_validated}
              editing_cell={editing_cell}
              on_edit_cell={set_editing_cell}
              ebitda_source={ebitda_source}
            />
          </CardContent>
        )}
      </Card>

      {/* Debug JSON Panel */}
      <div className="mb-8">
        <ProjectJsonViewer data={state.project_data} title="Debug: Full Project Data" />
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={() => router.push("/project-wizard/company")}
        >
          Back
        </Button>

        <Button size="lg" onClick={handle_continue}>
          Continue
        </Button>
      </div>
    </div>
  );
}

// Financial Table Component
interface FinancialTableProps {
  metrics: typeof KEY_FINANCIALS;
  years: string[];
  get_value: (metric: string, year: string) => number | null;
  validation: Record<string, Record<string, boolean>>;
  on_value_change: (metric: string, year: string, value: number | null) => void;
  on_validate: (metric: string, year: string, validated: boolean) => void;
  editing_cell: { metric: string; year: string } | null;
  on_edit_cell: (cell: { metric: string; year: string } | null) => void;
  ebitda_source?: string | null;
}

function FinancialTable({
  metrics,
  years,
  get_value,
  validation,
  on_value_change,
  on_validate,
  editing_cell,
  on_edit_cell,
  ebitda_source,
}: FinancialTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left py-3 pr-4 font-medium w-48">Metric</th>
            {years.map((year) => (
              <th key={year} className="text-right py-3 px-4 font-medium min-w-32">
                {year}A
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => (
            <tr key={metric.key} className="border-b hover:bg-muted/50">
              <td className="py-3 pr-4 font-medium">
                {metric.label}
                {metric.key === "ebitda" && ebitda_source && (
                  <span className="ml-2 text-xs text-muted-foreground font-normal inline-flex items-center gap-1">
                    <Info className="h-3 w-3" />
                    ({ebitda_source})
                  </span>
                )}
              </td>
              {years.map((year) => {
                const value = get_value(metric.key, year);
                const is_editing = editing_cell?.metric === metric.key && editing_cell?.year === year;
                const is_validated = validation[metric.key]?.[year] ?? false;

                return (
                  <td key={year} className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {is_editing ? (
                        <EditableCell
                          value={value}
                          on_save={(v) => on_value_change(metric.key, year, v)}
                          on_cancel={() => on_edit_cell(null)}
                        />
                      ) : (
                        <span
                          className="cursor-pointer hover:text-primary min-w-16 text-right"
                          onClick={() => on_edit_cell({ metric: metric.key, year })}
                        >
                          {value !== null ? value.toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) : "-"}
                        </span>
                      )}
                      <Checkbox
                        checked={is_validated}
                        onCheckedChange={(checked) => on_validate(metric.key, year, !!checked)}
                        className="h-4 w-4"
                      />
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Editable Cell Component
function EditableCell({
  value,
  on_save,
  on_cancel,
}: {
  value: number | null;
  on_save: (value: number | null) => void;
  on_cancel: () => void;
}) {
  const [input_value, set_input_value] = useState(value?.toString() || "");

  const handle_save = () => {
    const parsed = parseFloat(input_value);
    on_save(isNaN(parsed) ? null : parsed);
  };

  return (
    <input
      type="text"
      value={input_value}
      onChange={(e) => set_input_value(e.target.value)}
      onBlur={handle_save}
      onKeyDown={(e) => {
        if (e.key === "Enter") handle_save();
        if (e.key === "Escape") on_cancel();
      }}
      className="w-24 px-2 py-1 text-right border rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      autoFocus
    />
  );
}
