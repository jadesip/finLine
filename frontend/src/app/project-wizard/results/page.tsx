"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle,
  Download,
  FileSpreadsheet,
  DollarSign,
  Percent,
  BarChart3,
  Activity,
  TrendingUp,
  ChevronDown,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useWizard } from "@/contexts/wizard-context";
import { ProjectJsonViewer } from "@/components/debug/project-json-viewer";

// Case selector
interface CaseOption {
  id: string;
  name: string;
  icon: string;
  color: string;
}

const CASES: CaseOption[] = [
  { id: "base_case", name: "Base Case", icon: "—", color: "blue" },
  { id: "upside_case", name: "Upside Case", icon: "↗", color: "green" },
  { id: "downside_case", name: "Downside Case", icon: "↘", color: "orange" },
];

// Format helpers
const formatCurrency = (value: number, decimals: number = 0): string => {
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

const formatMultiple = (value: number): string => {
  return `${value.toFixed(1)}x`;
};

export default function ResultsPage() {
  const router = useRouter();
  const { state, mark_step_visited } = useWizard();
  const [active_case, set_active_case] = useState("base_case");
  const [show_entry_details, set_show_entry_details] = useState(false);
  const [show_exit_details, set_show_exit_details] = useState(false);

  // Sample data for UI display
  const sample_data = {
    company_name: "Sample Company",
    sector: "Industrial",
    currency: "USD",
    unit: "M",
    deal_date: "Dec-25",
    entry: {
      purchase_price: 1050,
      transaction_fees: 21,
      financing_fees: 15,
      minimum_cash: 10,
      total_uses: 1096,
      total_debt: 600,
      equity: 496,
      multiple: 7.0,
    },
    exit: {
      enterprise_value: 1500,
      cash_at_exit: 50,
      debt_at_exit: 300,
      exit_fees: 30,
      equity_proceeds: 1220,
      multiple: 6.0,
    },
    returns: {
      irr: 0.245,
      moic: 2.46,
      holding_period: 5,
      value_created: 724,
    },
    sources: [
      { label: "Term Loan A", amount: 400 },
      { label: "Term Loan B", amount: 200 },
      { label: "Equity", amount: 496 },
    ],
    uses: [
      { label: "Purchase Price", amount: 1050 },
      { label: "Transaction Fees", amount: 21 },
      { label: "Financing Fees", amount: 15 },
      { label: "Minimum Cash", amount: 10 },
    ],
    years: ["2025", "2026", "2027", "2028", "2029", "2030"],
    cash_flows: {
      revenue: [500, 550, 605, 666, 732, 805],
      growth: [0, 0.1, 0.1, 0.1, 0.1, 0.1],
      ebitda: [150, 165, 182, 200, 220, 242],
      capex: [25, 28, 30, 33, 37, 40],
      working_capital: [5, 6, 6, 7, 7, 8],
      free_cash_flow: [120, 131, 146, 160, 176, 194],
    },
    leverage: {
      gross_leverage: [4.0, 3.5, 3.0, 2.5, 2.0, 1.5],
      net_leverage: [3.9, 3.4, 2.9, 2.4, 1.9, 1.4],
      interest_coverage: [3.2, 3.5, 4.0, 4.5, 5.2, 6.0],
    },
  };

  // Mark step as visited on mount
  useEffect(() => {
    mark_step_visited("results");
  }, [mark_step_visited]);

  // Redirect if no project
  useEffect(() => {
    if (!state.project_id) {
      router.push("/project-wizard/type");
    }
  }, [state.project_id, router]);

  const project_data = state.project_data;
  const meta = project_data?.meta;
  const currency = meta?.currency || sample_data.currency;
  const unit = meta?.unit || sample_data.unit;

  const handle_back = () => {
    router.push(`/project-wizard/capital-structure?id=${state.project_id}`);
  };

  const handle_finish = () => {
    router.push("/dashboard");
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
          "flex-1 p-3 rounded-lg border-2 transition-all",
          is_active
            ? "border-blue-500 bg-blue-50"
            : case_exists
            ? "border-gray-200 hover:border-gray-300 cursor-pointer"
            : "border-dashed border-gray-200 opacity-60"
        )}
      >
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
          <span className="font-medium text-sm">{case_option.name}</span>
          {is_active && (
            <span className="ml-auto text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full">
              Active
            </span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="py-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Transaction Dashboard</h1>
        <p className="text-muted-foreground">
          Comprehensive analysis for {meta?.company_name || sample_data.company_name}
        </p>
      </div>

      {/* Case Selector */}
      <div className="flex gap-3 mb-6">{CASES.map(render_case_card)}</div>

      {/* Project Overview Bar */}
      <div className="bg-gray-50 border rounded-lg p-3 mb-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-6 flex-1">
            <div className="flex items-center">
              <span className="text-xs text-gray-500">Company:</span>
              <span className="ml-2 font-medium text-sm">
                {meta?.company_name || sample_data.company_name}
              </span>
            </div>
            <div className="flex items-center">
              <span className="text-xs text-gray-500">Sector:</span>
              <span className="ml-2 font-medium text-sm">{sample_data.sector}</span>
            </div>
            <div className="flex items-center">
              <span className="text-xs text-gray-500">Currency:</span>
              <span className="ml-2 font-medium text-sm">
                {currency} ({unit})
              </span>
            </div>
            <div className="flex items-center">
              <span className="text-xs text-gray-500">Deal Date:</span>
              <span className="ml-2 font-medium text-sm">{sample_data.deal_date}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 bg-green-50 border border-green-200 rounded-md flex-shrink-0">
            <CheckCircle className="h-3 w-3 text-green-600" />
            <span className="text-xs text-green-800 font-medium">Model Ready</span>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Executive Summary - Base Case</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <tbody>
                <tr className="border-b">
                  <td className="py-1.5 pr-4 font-semibold text-gray-700">
                    Key Transaction Metrics
                  </td>
                  <td className="py-1.5 px-2" />
                  <td className="py-1.5 px-2" />
                  <td className="py-1.5 px-2" />
                </tr>
                <tr className="border-b">
                  <td className="py-1.5 pr-2 text-gray-600">Entry Enterprise Value:</td>
                  <td className="py-1.5 px-2 font-medium">
                    {currency} {formatCurrency(sample_data.entry.purchase_price)}
                  </td>
                  <td className="py-1.5 px-2 text-right font-semibold text-gray-600">
                    Equity Investment:
                  </td>
                  <td className="py-1.5 px-2 font-medium">
                    {currency} {formatCurrency(sample_data.entry.equity)}
                  </td>
                </tr>
                <tr className="border-b">
                  <td className="py-1.5 pr-2 text-gray-600">Exit Enterprise Value:</td>
                  <td className="py-1.5 px-2 font-medium">
                    {currency} {formatCurrency(sample_data.exit.enterprise_value)}
                  </td>
                  <td className="py-1.5 px-2 text-right font-semibold text-gray-600">
                    Total Debt:
                  </td>
                  <td className="py-1.5 px-2 font-medium">
                    {currency} {formatCurrency(sample_data.entry.total_debt)}
                  </td>
                </tr>
                <tr className="border-b">
                  <td className="py-1.5 pr-2 text-gray-600">Entry Multiple:</td>
                  <td className="py-1.5 px-2 font-medium">
                    {formatMultiple(sample_data.entry.multiple)}
                  </td>
                  <td className="py-1.5 px-2 text-right font-semibold text-gray-600">IRR:</td>
                  <td className="py-1.5 px-2 font-medium text-green-600">
                    {formatPercent(sample_data.returns.irr)}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 pr-2 text-gray-600">Exit Multiple:</td>
                  <td className="py-1.5 px-2 font-medium">
                    {formatMultiple(sample_data.exit.multiple)}
                  </td>
                  <td className="py-1.5 px-2 text-right font-semibold text-gray-600">MOIC:</td>
                  <td className="py-1.5 px-2 font-medium text-green-600">
                    {formatMultiple(sample_data.returns.moic)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Sources & Uses */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Sources */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-green-600" />
              Sources
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b text-gray-500">
                    <th className="text-left py-1 pr-2">Type</th>
                    <th className="text-center py-1 px-2">% of Total</th>
                    <th className="text-right py-1 pl-2">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {sample_data.sources.map((source, idx) => {
                    const total = sample_data.sources.reduce((sum, s) => sum + s.amount, 0);
                    const percentage = (source.amount / total) * 100;
                    const isEquity = source.label === "Equity";

                    return (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className={cn("py-1.5 pr-2", isEquity && "text-blue-600")}>
                          {source.label}
                          {isEquity && " (Plug)"}
                        </td>
                        <td className="text-center py-1.5 px-2">{percentage.toFixed(1)}%</td>
                        <td className="text-right py-1.5 pl-2 font-medium">
                          {formatCurrency(source.amount)}
                        </td>
                      </tr>
                    );
                  })}
                  <tr className="border-t-2 font-semibold">
                    <td className="pt-2 pb-1 pr-2">Total Sources</td>
                    <td className="text-center pt-2 pb-1 px-2">100.0%</td>
                    <td className="text-right pt-2 pb-1 pl-2">
                      {formatCurrency(sample_data.sources.reduce((sum, s) => sum + s.amount, 0))}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Uses */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-blue-600" />
              Uses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b text-gray-500">
                    <th className="text-left py-1 pr-2">Type</th>
                    <th className="text-center py-1 px-2">% of Total</th>
                    <th className="text-right py-1 pl-2">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {sample_data.uses.map((use, idx) => {
                    const total = sample_data.uses.reduce((sum, u) => sum + u.amount, 0);
                    const percentage = (use.amount / total) * 100;

                    return (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="py-1.5 pr-2">{use.label}</td>
                        <td className="text-center py-1.5 px-2">{percentage.toFixed(1)}%</td>
                        <td className="text-right py-1.5 pl-2 font-medium">
                          {formatCurrency(use.amount)}
                        </td>
                      </tr>
                    );
                  })}
                  <tr className="border-t-2 font-semibold">
                    <td className="pt-2 pb-1 pr-2">Total Uses</td>
                    <td className="text-center pt-2 pb-1 px-2">100.0%</td>
                    <td className="text-right pt-2 pb-1 pl-2">
                      {formatCurrency(sample_data.uses.reduce((sum, u) => sum + u.amount, 0))}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div className="mt-3 flex justify-center">
              <Badge variant="outline" className="text-xs bg-green-50 text-green-800">
                ✓ Balanced
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Returns Waterfall */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-blue-600" />
            Returns Waterfall
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {/* Entry */}
            <div className="pb-2 border-b">
              <div
                className="flex items-center justify-between cursor-pointer hover:bg-gray-50 -mx-2 px-2 py-1 rounded"
                onClick={() => set_show_entry_details(!show_entry_details)}
              >
                <p className="text-xs font-semibold text-gray-600">ENTRY</p>
                <ChevronDown
                  className={cn(
                    "h-3 w-3 text-gray-400 transition-transform",
                    show_entry_details && "rotate-180"
                  )}
                />
              </div>
              {show_entry_details && (
                <div className="space-y-1.5 mt-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs">Purchase Price</span>
                    <span className="text-xs">
                      {currency} {formatCurrency(sample_data.entry.purchase_price)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs">+ Transaction Fees</span>
                    <span className="text-xs">
                      {currency} {formatCurrency(sample_data.entry.transaction_fees)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs">+ Financing Fees</span>
                    <span className="text-xs">
                      {currency} {formatCurrency(sample_data.entry.financing_fees)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center pt-1 border-t">
                    <span className="text-xs font-medium">= Total Uses</span>
                    <span className="text-xs font-medium">
                      {currency} {formatCurrency(sample_data.entry.total_uses)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs">- Total Debt Raised</span>
                    <span className="text-xs">
                      ({currency} {formatCurrency(sample_data.entry.total_debt)})
                    </span>
                  </div>
                </div>
              )}
              <div className="flex justify-between items-center mt-2">
                <span className="text-xs font-bold">Entry Equity Investment</span>
                <span className="text-xs font-bold">
                  {currency} {formatCurrency(sample_data.entry.equity)}
                </span>
              </div>
            </div>

            {/* Exit */}
            <div className="pb-2 border-b">
              <div
                className="flex items-center justify-between cursor-pointer hover:bg-gray-50 -mx-2 px-2 py-1 rounded"
                onClick={() => set_show_exit_details(!show_exit_details)}
              >
                <p className="text-xs font-semibold text-gray-600">EXIT VALUE BUILD-UP</p>
                <ChevronDown
                  className={cn(
                    "h-3 w-3 text-gray-400 transition-transform",
                    show_exit_details && "rotate-180"
                  )}
                />
              </div>
              <div className="space-y-1.5 mt-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs">Exit Enterprise Value</span>
                  <span className="text-xs">
                    {currency} {formatCurrency(sample_data.exit.enterprise_value)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs">+ Cash Balance at Exit</span>
                  <span className="text-xs">
                    {currency} {formatCurrency(sample_data.exit.cash_at_exit)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs">- Debt Outstanding</span>
                  <span className="text-xs">
                    ({currency} {formatCurrency(sample_data.exit.debt_at_exit)})
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs">- Exit Fees (2%)</span>
                  <span className="text-xs">
                    ({currency} {formatCurrency(sample_data.exit.exit_fees)})
                  </span>
                </div>
                <div className="flex justify-between items-center pt-2 border-t">
                  <span className="text-xs font-bold">Exit Equity Proceeds</span>
                  <span className="text-xs font-bold">
                    {currency} {formatCurrency(sample_data.exit.equity_proceeds)}
                  </span>
                </div>
              </div>
            </div>

            {/* Returns Metrics */}
            <div>
              <p className="text-xs font-semibold text-gray-600 mb-2">RETURNS METRICS</p>
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="text-xs">Money Multiple (MOIC)</span>
                  <span className="text-xs font-bold text-green-600">
                    {formatMultiple(sample_data.returns.moic)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs">Internal Rate of Return (IRR)</span>
                  <span className="text-xs font-bold text-green-600">
                    {formatPercent(sample_data.returns.irr)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs">Holding Period</span>
                  <span className="text-xs">{sample_data.returns.holding_period} years</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs">Total Value Created</span>
                  <span className="text-xs font-bold">
                    {currency} {formatCurrency(sample_data.returns.value_created)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Forecast & Cash Flows */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4 text-purple-600" />
            Forecast & Cash Flows
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 pr-4">Metric</th>
                  {sample_data.years.map((year) => (
                    <th key={year} className="text-right py-2 px-3">
                      FY{year}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b hover:bg-gray-50">
                  <td className="py-2 pr-4">Revenue</td>
                  {sample_data.cash_flows.revenue.map((val, idx) => (
                    <td key={idx} className="text-right py-2 px-3">
                      {formatCurrency(val)}
                    </td>
                  ))}
                </tr>
                <tr className="border-b hover:bg-gray-50 italic text-gray-600">
                  <td className="py-2 pr-4">Growth %</td>
                  {sample_data.cash_flows.growth.map((val, idx) => (
                    <td key={idx} className="text-right py-2 px-3">
                      {idx === 0 ? "-" : formatPercent(val)}
                    </td>
                  ))}
                </tr>
                <tr className="border-b hover:bg-gray-50">
                  <td className="py-2 pr-4">EBITDA</td>
                  {sample_data.cash_flows.ebitda.map((val, idx) => (
                    <td key={idx} className="text-right py-2 px-3">
                      {formatCurrency(val)}
                    </td>
                  ))}
                </tr>
                <tr className="border-b hover:bg-gray-50">
                  <td className="py-2 pr-4">(-) Capex</td>
                  {sample_data.cash_flows.capex.map((val, idx) => (
                    <td key={idx} className="text-right py-2 px-3">
                      ({formatCurrency(val)})
                    </td>
                  ))}
                </tr>
                <tr className="border-b hover:bg-gray-50">
                  <td className="py-2 pr-4">(-) Change in WC</td>
                  {sample_data.cash_flows.working_capital.map((val, idx) => (
                    <td key={idx} className="text-right py-2 px-3">
                      ({formatCurrency(val)})
                    </td>
                  ))}
                </tr>
                <tr className="font-semibold bg-gray-50">
                  <td className="py-2 pr-4">Free Cash Flow</td>
                  {sample_data.cash_flows.free_cash_flow.map((val, idx) => (
                    <td key={idx} className="text-right py-2 px-3">
                      {formatCurrency(val)}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Credit Ratios */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Percent className="h-4 w-4 text-orange-600" />
            Credit Ratios
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 pr-4">Metric</th>
                  {sample_data.years.map((year) => (
                    <th key={year} className="text-right py-2 px-3">
                      FY{year}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b hover:bg-gray-50">
                  <td className="py-2 pr-4">Gross Leverage (Debt/EBITDA)</td>
                  {sample_data.leverage.gross_leverage.map((val, idx) => (
                    <td key={idx} className="text-right py-2 px-3">
                      {formatMultiple(val)}
                    </td>
                  ))}
                </tr>
                <tr className="border-b hover:bg-gray-50">
                  <td className="py-2 pr-4">Net Leverage</td>
                  {sample_data.leverage.net_leverage.map((val, idx) => (
                    <td key={idx} className="text-right py-2 px-3">
                      {formatMultiple(val)}
                    </td>
                  ))}
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="py-2 pr-4">Interest Coverage (EBITDA/Interest)</td>
                  {sample_data.leverage.interest_coverage.map((val, idx) => (
                    <td key={idx} className="text-right py-2 px-3">
                      {formatMultiple(val)}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between items-center mt-8">
        <Button variant="ghost" onClick={handle_back}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>

        <div className="flex gap-3">
          <Button variant="outline" disabled>
            <FileSpreadsheet className="w-4 h-4 mr-2" />
            Export to Excel
          </Button>

          <Button onClick={handle_finish}>
            <CheckCircle className="h-4 w-4 mr-2" />
            Complete Setup
          </Button>
        </div>
      </div>

      {/* Debug: JSON Viewer */}
      <div className="mt-8">
        <ProjectJsonViewer data={project_data} />
      </div>
    </div>
  );
}
