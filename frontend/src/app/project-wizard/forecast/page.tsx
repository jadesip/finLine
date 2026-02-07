"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Undo, Redo, Plus, MoreVertical } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { useWizard } from "@/contexts/wizard-context";
import { ProjectJsonViewer } from "@/components/debug/project-json-viewer";

// Types for the forecast table
interface YearData {
  value: number | null;
  value_type?: "hardcode" | "formula" | "growthFormula" | "margin";
}

interface CaseOption {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
}

const CASES: CaseOption[] = [
  {
    id: "base_case",
    name: "Base Case",
    description: "Most likely scenario based on current assumptions",
    icon: "—",
    color: "blue",
  },
  {
    id: "upside_case",
    name: "Upside Case",
    description: "Optimistic scenario with favorable market conditions",
    icon: "↗",
    color: "green",
  },
  {
    id: "downside_case",
    name: "Downside Case",
    description: "Conservative scenario with challenging conditions",
    icon: "↘",
    color: "orange",
  },
];

export default function ForecastPage() {
  const router = useRouter();
  const { state, mark_step_visited } = useWizard();
  const [active_case, set_active_case] = useState("base_case");
  const [driver_checkboxes, set_driver_checkboxes] = useState<Record<string, boolean>>({});

  // Mark step as visited on mount
  useEffect(() => {
    mark_step_visited("forecast");
  }, [mark_step_visited]);

  // Redirect if no project
  useEffect(() => {
    if (!state.project_id) {
      router.push("/project-wizard/type");
    }
  }, [state.project_id, router]);

  // Extract data from project
  const project_data = state.project_data;
  const meta = project_data?.meta;
  const case_data = project_data?.cases?.[active_case];
  const financials = case_data?.financials;

  // Determine currency and unit display
  const currency = meta?.currency || "USD";
  const unit = meta?.unit || "millions";
  const fiscal_year_end = meta?.financial_year_end || "December";

  // Extract years from financial data
  const years = useMemo(() => {
    const year_set = new Set<string>();

    // Check income statement
    const income = financials?.income_statement;
    if (income) {
      // Revenue
      if (income.revenue) {
        if (Array.isArray(income.revenue)) {
          income.revenue.forEach((item: any) => {
            if (item.year) year_set.add(String(item.year));
          });
        } else if (typeof income.revenue === "object") {
          Object.keys(income.revenue).forEach((y) => year_set.add(y));
        }
      }
      // EBITDA
      if (income.ebitda) {
        if (Array.isArray(income.ebitda)) {
          income.ebitda.forEach((item: any) => {
            if (item.year) year_set.add(String(item.year));
            if (item.data) Object.keys(item.data).forEach((y) => year_set.add(y));
          });
        }
      }
    }

    return Array.from(year_set).sort();
  }, [financials]);

  // Determine which years are forecast (vs historical)
  const last_historical_period = meta?.last_historical_period || "";
  const last_historical_year = useMemo(() => {
    const match = last_historical_period.match(/(\d{2,4})$/);
    if (match) {
      let year = parseInt(match[1]);
      if (year < 100) year += 2000;
      return year;
    }
    // Default: assume current year - 1
    return new Date().getFullYear() - 1;
  }, [last_historical_period]);

  const is_forecast_year = (year: string) => parseInt(year) > last_historical_year;

  // Get year label (e.g., "2024A" or "2025E")
  const get_year_label = (year: string) => {
    const suffix = is_forecast_year(year) ? "E" : "A";
    return `${year}${suffix}`;
  };

  // Helper to get metric value for a year
  const get_metric_value = (
    statement: "income_statement" | "cash_flow_statement",
    metric: string,
    year: string
  ): number | null => {
    const stmt = financials?.[statement] as Record<string, any> | undefined;
    if (!stmt) return null;

    const data = stmt[metric];
    if (!data) return null;

    // Handle array format (EBITDA, EBIT, D&A)
    if (Array.isArray(data)) {
      // Simple array format: [{year, value}, ...]
      const item = data.find((d: any) => String(d.year) === year);
      if (item?.value !== undefined) return item.value;

      // Complex format: [{data: {year: {value}}, ...}]
      if (data[0]?.data) {
        const year_data = data[0].data[year];
        if (year_data?.value !== undefined) return year_data.value;
      }
      return null;
    }

    // Handle object format: {year: value} or {year: {value}}
    if (typeof data === "object") {
      const year_data = data[year];
      if (year_data === null || year_data === undefined) return null;
      if (typeof year_data === "number") return year_data;
      if (year_data?.value !== undefined) return year_data.value;
    }

    return null;
  };

  // Calculate percentage (e.g., margin as % of revenue)
  const calculate_percentage = (value: number | null, base: number | null): number | null => {
    if (value === null || base === null || base === 0) return null;
    return (value / base) * 100;
  };

  // Calculate growth rate
  const calculate_growth = (current: number | null, previous: number | null): number | null => {
    if (current === null || previous === null || previous === 0) return null;
    return ((current - previous) / previous) * 100;
  };

  // Format number for display
  const format_number = (value: number | null, decimals: number = 1): string => {
    if (value === null || value === undefined) return "-";
    return value.toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  // Format percentage for display
  const format_percentage = (value: number | null): string => {
    if (value === null || value === undefined) return "-";
    return `${value.toFixed(1)}%`;
  };

  const handle_back = () => {
    router.push(`/project-wizard/insights?id=${state.project_id}`);
  };

  const handle_continue = () => {
    router.push(`/project-wizard/deal-assumptions?id=${state.project_id}`);
  };

  // Render case selector card
  const render_case_card = (case_option: CaseOption) => {
    const is_active = active_case === case_option.id;
    const case_exists = project_data?.cases?.[case_option.id];

    return (
      <div
        key={case_option.id}
        onClick={() => case_exists && set_active_case(case_option.id)}
        className={cn(
          "flex-1 p-4 rounded-lg border-2 transition-all",
          is_active
            ? "border-blue-500 bg-blue-50"
            : case_exists
            ? "border-gray-200 hover:border-gray-300 cursor-pointer"
            : "border-dashed border-gray-200 opacity-60"
        )}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "w-6 h-6 rounded flex items-center justify-center text-sm",
                case_option.color === "blue" && "bg-blue-100 text-blue-600",
                case_option.color === "green" && "bg-green-100 text-green-600",
                case_option.color === "orange" && "bg-orange-100 text-orange-600"
              )}
            >
              {case_option.icon}
            </span>
            <span className="font-medium">{case_option.name}</span>
          </div>
          {is_active && (
            <span className="text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full">
              Active
            </span>
          )}
          {!case_exists && (
            <Button variant="ghost" size="sm" className="text-xs">
              Add
            </Button>
          )}
          {case_exists && !is_active && (
            <Button variant="ghost" size="icon" className="h-6 w-6">
              <MoreVertical className="h-4 w-4" />
            </Button>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-1">{case_option.description}</p>
      </div>
    );
  };

  // Render editable cell
  const render_value_cell = (value: number | null, is_driver: boolean = false) => {
    return (
      <div
        className={cn(
          "text-right p-1.5 rounded cursor-pointer hover:bg-gray-100 transition-colors",
          is_driver && "bg-blue-50"
        )}
      >
        {format_number(value)}
      </div>
    );
  };

  // Render percentage cell
  const render_percentage_cell = (
    value: number | null,
    is_editable: boolean = false,
    is_driver: boolean = false
  ) => {
    return (
      <div
        className={cn(
          "text-right p-1.5 rounded transition-colors text-gray-600",
          is_editable && "cursor-pointer hover:bg-gray-100",
          is_driver && "bg-blue-50"
        )}
      >
        {format_percentage(value)}
      </div>
    );
  };

  return (
    <div className="py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Financial Modeling</h1>
        <p className="text-muted-foreground">Review and adjust financial projections</p>
      </div>

      {/* Case Selector */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div />
          <Button variant="outline" size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Custom Case
          </Button>
        </div>
        <div className="flex gap-4">{CASES.map(render_case_card)}</div>
      </div>

      {/* Financial Forecast Table */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Financial Forecast</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                ({currency} {unit}, {fiscal_year_end.slice(0, 3)}-YE)
              </p>
            </div>
            <div className="flex items-center gap-4">
              {/* Undo/Redo */}
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="sm" className="h-8 px-2" disabled>
                  <Undo className="h-4 w-4 mr-1" />
                  Undo
                </Button>
                <Button variant="ghost" size="sm" className="h-8 px-2" disabled>
                  <Redo className="h-4 w-4 mr-1" />
                  Redo
                </Button>
              </div>
              {/* Driver Legend */}
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="w-4 h-4 bg-blue-50 border border-blue-200 rounded" />
                <span>Driver</span>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                {/* Checkbox row for forecast years */}
                <tr>
                  <th className="text-left py-1 px-2 w-[200px]" />
                  {years.map((year) => (
                    <th key={`checkbox-${year}`} className="text-right py-1 px-2 min-w-[100px]">
                      {is_forecast_year(year) && (
                        <div className="flex justify-end">
                          <Checkbox
                            checked={driver_checkboxes[year] || false}
                            onCheckedChange={(checked) =>
                              set_driver_checkboxes((prev) => ({
                                ...prev,
                                [year]: checked as boolean,
                              }))
                            }
                          />
                        </div>
                      )}
                    </th>
                  ))}
                </tr>
                {/* Year headers */}
                <tr className="border-b">
                  <th className="text-left py-2 px-2 font-medium">Metric</th>
                  {years.map((year) => (
                    <th key={year} className="text-right py-2 px-2 font-medium min-w-[100px]">
                      {get_year_label(year)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {/* Revenue */}
                <tr className="border-b">
                  <td className="py-2 px-2 font-medium">Revenue</td>
                  {years.map((year) => {
                    const value = get_metric_value("income_statement", "revenue", year);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_value_cell(value, !is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>

                {/* Revenue Growth % */}
                <tr className="text-sm">
                  <td className="py-1 px-2 pl-6 text-muted-foreground">→ Revenue Growth %</td>
                  {years.map((year, index) => {
                    const current = get_metric_value("income_statement", "revenue", year);
                    const previous =
                      index > 0
                        ? get_metric_value("income_statement", "revenue", years[index - 1])
                        : null;
                    const growth = calculate_growth(current, previous);
                    return (
                      <td key={year} className="py-1 px-2">
                        {index === 0 ? (
                          <div className="text-right p-1.5 text-muted-foreground">-</div>
                        ) : (
                          render_percentage_cell(growth, is_forecast_year(year))
                        )}
                      </td>
                    );
                  })}
                </tr>

                {/* EBITDA */}
                <tr className="border-b">
                  <td className="py-2 px-2 font-medium">EBITDA</td>
                  {years.map((year) => {
                    const value = get_metric_value("income_statement", "ebitda", year);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_value_cell(value, !is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>

                {/* EBITDA % of Revenue */}
                <tr className="text-sm">
                  <td className="py-1 px-2 pl-6 text-muted-foreground">→ % of Revenue</td>
                  {years.map((year) => {
                    const ebitda = get_metric_value("income_statement", "ebitda", year);
                    const revenue = get_metric_value("income_statement", "revenue", year);
                    const margin = calculate_percentage(ebitda, revenue);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_percentage_cell(margin, is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>

                {/* EBITDA Growth % */}
                <tr className="text-sm">
                  <td className="py-1 px-2 pl-6 text-muted-foreground">→ EBITDA Growth %</td>
                  {years.map((year, index) => {
                    const current = get_metric_value("income_statement", "ebitda", year);
                    const previous =
                      index > 0
                        ? get_metric_value("income_statement", "ebitda", years[index - 1])
                        : null;
                    const growth = calculate_growth(current, previous);
                    return (
                      <td key={year} className="py-1 px-2">
                        {index === 0 ? (
                          <div className="text-right p-1.5 text-muted-foreground">-</div>
                        ) : (
                          render_percentage_cell(growth)
                        )}
                      </td>
                    );
                  })}
                </tr>

                {/* D&A */}
                <tr className="border-b">
                  <td className="py-2 px-2 font-medium">D&A</td>
                  {years.map((year) => {
                    const value = get_metric_value("income_statement", "d_and_a", year);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_value_cell(value, !is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>

                {/* D&A % of Revenue */}
                <tr className="text-sm">
                  <td className="py-1 px-2 pl-6 text-muted-foreground">→ % of Revenue</td>
                  {years.map((year) => {
                    const dna = get_metric_value("income_statement", "d_and_a", year);
                    const revenue = get_metric_value("income_statement", "revenue", year);
                    const margin = calculate_percentage(dna, revenue);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_percentage_cell(margin, is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>

                {/* EBIT */}
                <tr className="border-b">
                  <td className="py-2 px-2 font-medium">EBIT</td>
                  {years.map((year) => {
                    const value = get_metric_value("income_statement", "ebit", year);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_value_cell(value, !is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>

                {/* EBIT % of Revenue */}
                <tr className="text-sm">
                  <td className="py-1 px-2 pl-6 text-muted-foreground">→ % of Revenue</td>
                  {years.map((year) => {
                    const ebit = get_metric_value("income_statement", "ebit", year);
                    const revenue = get_metric_value("income_statement", "revenue", year);
                    const margin = calculate_percentage(ebit, revenue);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_percentage_cell(margin, is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>

                {/* Working Capital */}
                <tr className="border-b">
                  <td className="py-2 px-2 font-medium">Working Capital</td>
                  {years.map((year) => {
                    const value = get_metric_value("cash_flow_statement", "working_capital", year);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_value_cell(value, !is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>

                {/* Working Capital % of Revenue */}
                <tr className="text-sm">
                  <td className="py-1 px-2 pl-6 text-muted-foreground">→ % of Revenue</td>
                  {years.map((year) => {
                    const wc = get_metric_value("cash_flow_statement", "working_capital", year);
                    const revenue = get_metric_value("income_statement", "revenue", year);
                    const margin = calculate_percentage(wc, revenue);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_percentage_cell(margin, is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>

                {/* Capex */}
                <tr className="border-b">
                  <td className="py-2 px-2 font-medium">Capex</td>
                  {years.map((year) => {
                    let value = get_metric_value("cash_flow_statement", "capex", year);
                    // Capex is often stored as negative, display as positive
                    if (value !== null && value < 0) value = Math.abs(value);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_value_cell(value, !is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>

                {/* Capex % of Revenue */}
                <tr className="text-sm">
                  <td className="py-1 px-2 pl-6 text-muted-foreground">→ % of Revenue</td>
                  {years.map((year) => {
                    let capex = get_metric_value("cash_flow_statement", "capex", year);
                    if (capex !== null && capex < 0) capex = Math.abs(capex);
                    const revenue = get_metric_value("income_statement", "revenue", year);
                    const margin = calculate_percentage(capex, revenue);
                    return (
                      <td key={year} className="py-1 px-2">
                        {render_percentage_cell(margin, is_forecast_year(year))}
                      </td>
                    );
                  })}
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <Button variant="ghost" onClick={handle_back}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Button onClick={handle_continue}>
          Continue to Deal Assumptions
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>

      {/* Debug: JSON Viewer */}
      <div className="mt-8">
        <ProjectJsonViewer data={project_data} />
      </div>
    </div>
  );
}
