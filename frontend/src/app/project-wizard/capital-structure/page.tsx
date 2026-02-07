"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Plus,
  Trash2,
  Calculator,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWizard } from "@/contexts/wizard-context";
import { ProjectJsonViewer } from "@/components/debug/project-json-viewer";

// Types
interface DebtTranche {
  id: string;
  label: string;
  type: "Loan" | "Revolver" | "Bond";
  size: number;
  interest_rate: number;
  pik_rate: number;
  financing_fees: number;
  drawn_percentage: number;
  amortization: string;
  maturity: string;
  seniority: number;
}

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

// Sample debt tranches
const DEFAULT_TRANCHES: DebtTranche[] = [
  {
    id: "tl_1",
    label: "Term Loan A",
    type: "Loan",
    size: 400,
    interest_rate: 5.0,
    pik_rate: 0,
    financing_fees: 2.0,
    drawn_percentage: 100,
    amortization: "10/20/30/40",
    maturity: "2029-12-31",
    seniority: 1,
  },
  {
    id: "tl_2",
    label: "Term Loan B",
    type: "Loan",
    size: 200,
    interest_rate: 6.0,
    pik_rate: 0,
    financing_fees: 2.5,
    drawn_percentage: 100,
    amortization: "",
    maturity: "2030-12-31",
    seniority: 2,
  },
  {
    id: "rcf_1",
    label: "Revolver",
    type: "Revolver",
    size: 100,
    interest_rate: 4.5,
    pik_rate: 0,
    financing_fees: 1.5,
    drawn_percentage: 0,
    amortization: "",
    maturity: "2028-12-31",
    seniority: 1,
  },
];

// Percentage Input Component - shows value with % suffix
function PercentageInput({
  value,
  onChange,
  placeholder = "0.0",
  className = "",
}: {
  value: number;
  onChange: (value: number) => void;
  placeholder?: string;
  className?: string;
}) {
  const [display_value, set_display_value] = useState(value.toString());
  const [is_focused, set_is_focused] = useState(false);

  useEffect(() => {
    if (!is_focused) {
      set_display_value(value.toString());
    }
  }, [value, is_focused]);

  const handle_change = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/%/g, "").trim();
    set_display_value(raw);
  };

  const handle_blur = () => {
    set_is_focused(false);
    const num = parseFloat(display_value) || 0;
    onChange(num);
    set_display_value(num.toString());
  };

  const handle_focus = () => {
    set_is_focused(true);
  };

  return (
    <div className="relative">
      <Input
        type="text"
        value={is_focused ? display_value : `${value}%`}
        onChange={handle_change}
        onBlur={handle_blur}
        onFocus={handle_focus}
        placeholder={placeholder}
        className={className}
      />
    </div>
  );
}

// Number Input Component - no spinners
function NumberInput({
  value,
  onChange,
  placeholder = "0",
  className = "",
}: {
  value: number;
  onChange: (value: number) => void;
  placeholder?: string;
  className?: string;
}) {
  const [display_value, set_display_value] = useState(value.toString());
  const [is_focused, set_is_focused] = useState(false);

  useEffect(() => {
    if (!is_focused) {
      set_display_value(value.toString());
    }
  }, [value, is_focused]);

  const handle_change = (e: React.ChangeEvent<HTMLInputElement>) => {
    set_display_value(e.target.value);
  };

  const handle_blur = () => {
    set_is_focused(false);
    const num = parseFloat(display_value) || 0;
    onChange(num);
    set_display_value(num.toString());
  };

  const handle_focus = () => {
    set_is_focused(true);
  };

  return (
    <Input
      type="text"
      value={display_value}
      onChange={handle_change}
      onBlur={handle_blur}
      onFocus={handle_focus}
      placeholder={placeholder}
      className={className}
    />
  );
}

// Debt Tranche Card Component
function DebtTrancheCard({
  tranche,
  onUpdate,
  onRemove,
}: {
  tranche: DebtTranche;
  onUpdate: (id: string, field: string, value: any) => void;
  onRemove: (id: string) => void;
}) {
  return (
    <div className="border-2 rounded-lg p-3 bg-gradient-to-r from-white to-gray-50 hover:from-gray-50 hover:to-gray-100 transition-colors border-gray-200">
      <div className="flex items-start gap-2">
        <div className="flex-1 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-8 bg-blue-500 rounded-full" />
              <Input
                value={tranche.label}
                onChange={(e) => onUpdate(tranche.id, "label", e.target.value)}
                className="text-sm font-semibold max-w-xs h-8 border-0 bg-transparent hover:bg-white focus:bg-white"
                placeholder="Tranche Name"
              />
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemove(tranche.id)}
              className="text-red-600 hover:text-red-700 h-8 w-8 p-0"
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-gray-600">Type</Label>
              <select
                value={tranche.type}
                onChange={(e) => onUpdate(tranche.id, "type", e.target.value)}
                className="w-full h-8 text-sm border border-gray-300 rounded px-2"
              >
                <option value="Loan">Term Loan</option>
                <option value="Revolver">Revolver</option>
                <option value="Bond">Bond</option>
              </select>
            </div>

            {tranche.type !== "Revolver" && (
              <div>
                <Label className="text-xs text-gray-600">Size</Label>
                <NumberInput
                  value={tranche.size}
                  onChange={(val) => onUpdate(tranche.id, "size", val)}
                  className="h-8 text-sm"
                  placeholder="0"
                />
              </div>
            )}

            <div>
              <Label className="text-xs text-gray-600">Interest Rate</Label>
              <PercentageInput
                value={tranche.interest_rate}
                onChange={(val) => onUpdate(tranche.id, "interest_rate", val)}
                className="h-8 text-sm"
                placeholder="0.0"
              />
            </div>

            {tranche.type !== "Revolver" && (
              <div>
                <Label className="text-xs text-gray-600">PIK Rate</Label>
                <PercentageInput
                  value={tranche.pik_rate}
                  onChange={(val) => onUpdate(tranche.id, "pik_rate", val)}
                  className="h-8 text-sm"
                  placeholder="0.0"
                />
              </div>
            )}

            <div>
              <Label className="text-xs text-gray-600">Financing Fees</Label>
              <PercentageInput
                value={tranche.financing_fees}
                onChange={(val) => onUpdate(tranche.id, "financing_fees", val)}
                className="h-8 text-sm"
                placeholder="0.0"
              />
            </div>

            <div>
              <Label className="text-xs text-gray-600">% Drawn at Deal Date</Label>
              <PercentageInput
                value={tranche.drawn_percentage}
                onChange={(val) =>
                  onUpdate(tranche.id, "drawn_percentage", Math.min(100, Math.max(0, val)))
                }
                className="h-8 text-sm"
                placeholder={tranche.type === "Revolver" ? "0" : "100"}
              />
            </div>

            <div>
              <Label className="text-xs text-gray-600">Amortization</Label>
              <Input
                value={tranche.amortization}
                onChange={(e) => onUpdate(tranche.id, "amortization", e.target.value)}
                className="h-8 text-sm"
                placeholder="10/20/30/40"
              />
            </div>

            <div>
              <Label className="text-xs text-gray-600">Maturity</Label>
              <Input
                value={tranche.maturity}
                disabled
                className="h-8 text-sm bg-gray-100 cursor-not-allowed"
                placeholder="2029-03-31"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-gray-500">Seniority</Label>
              <NumberInput
                value={tranche.seniority}
                onChange={(val) => onUpdate(tranche.id, "seniority", Math.max(1, Math.round(val)))}
                className="h-7 text-xs"
                placeholder="1"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CapitalStructurePage() {
  const router = useRouter();
  const { state, mark_step_visited } = useWizard();
  const [active_case, set_active_case] = useState("base_case");
  const [tranches, set_tranches] = useState<DebtTranche[]>(DEFAULT_TRANCHES);
  const [is_reference_rate_enabled, set_is_reference_rate_enabled] = useState(false);
  const [tax_rate, set_tax_rate] = useState("25.0");
  const [minimum_cash, set_minimum_cash] = useState("10.0");

  // Mark step as visited on mount
  useEffect(() => {
    mark_step_visited("capital_structure");
  }, [mark_step_visited]);

  // Redirect if no project
  useEffect(() => {
    if (!state.project_id) {
      router.push("/project-wizard/type");
    }
  }, [state.project_id, router]);

  const project_data = state.project_data;
  const meta = project_data?.meta;
  const currency = meta?.currency || "USD";
  const unit = meta?.unit || "M";

  // Calculate sources and uses
  const total_debt = tranches.reduce((sum, t) => sum + (t.type !== "Revolver" ? t.size : 0), 0);
  const purchase_price = 1050; // Sample value
  const fees = 21; // Sample value
  const total_uses = purchase_price + fees;
  const equity = Math.max(0, total_uses - total_debt);
  const total_sources = total_debt + equity;
  const is_balanced = Math.abs(total_sources - total_uses) < 0.01;

  // Update tranche
  const update_tranche = (id: string, field: string, value: any) => {
    set_tranches((prev) =>
      prev.map((t) => (t.id === id ? { ...t, [field]: value } : t))
    );
  };

  // Remove tranche
  const remove_tranche = (id: string) => {
    set_tranches((prev) => prev.filter((t) => t.id !== id));
  };

  // Add tranche
  const add_tranche = () => {
    const new_tranche: DebtTranche = {
      id: `tranche_${Date.now()}`,
      label: "New Debt Tranche",
      type: "Loan",
      size: 0,
      interest_rate: 5.0,
      pik_rate: 0,
      financing_fees: 2.0,
      drawn_percentage: 100,
      amortization: "",
      maturity: "",
      seniority: tranches.length + 1,
    };
    set_tranches((prev) => [...prev, new_tranche]);
  };

  const handle_back = () => {
    router.push(`/project-wizard/deal-assumptions?id=${state.project_id}`);
  };

  const handle_continue = () => {
    router.push(`/project-wizard/results?id=${state.project_id}`);
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

  // Reference rate curve sample data
  const reference_rate_points = [
    { period: "2024", rate: 2.5 },
    { period: "2025", rate: 2.4 },
    { period: "2026", rate: 2.3 },
    { period: "2027", rate: 2.2 },
    { period: "2028", rate: 2.1 },
    { period: "2029", rate: 2.0 },
  ];

  return (
    <div className="py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Capital Structure</h1>
        <p className="text-muted-foreground">Configure debt tranches and view sources & uses</p>
      </div>

      {/* Case Selector */}
      <div className="flex gap-3 mb-6">{CASES.map(render_case_card)}</div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Debt Tranches */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Debt Tranches</CardTitle>
                <Button variant="outline" size="sm" onClick={add_tranche}>
                  <Plus className="w-4 h-4 mr-1" />
                  Add Tranche
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {/* Info bar */}
              <Alert className="bg-blue-50 border-blue-200 mb-4">
                <Info className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800 ml-2">
                  Fill in the various debt tranches of the financing package
                </AlertDescription>
              </Alert>

              {tranches.map((tranche) => (
                <DebtTrancheCard
                  key={tranche.id}
                  tranche={tranche}
                  onUpdate={update_tranche}
                  onRemove={remove_tranche}
                />
              ))}

              {tranches.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Calculator className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                  <p>No debt tranches configured</p>
                  <p className="text-sm">Click &quot;Add Tranche&quot; to get started</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Reference Rate Curve */}
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 z-10 pointer-events-none">
              <div className="bg-amber-500 text-white px-12 py-1 transform rotate-45 translate-x-4 translate-y-6 shadow-lg">
                <span className="text-xs font-semibold tracking-wider">BEING IMPLEMENTED</span>
              </div>
            </div>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Reference Rate Curve</CardTitle>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">SOFR</span>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={is_reference_rate_enabled}
                      onChange={() => set_is_reference_rate_enabled(!is_reference_rate_enabled)}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm">Enable</span>
                  </label>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {is_reference_rate_enabled ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left text-xs font-medium text-gray-600 pb-2">Period</th>
                        {reference_rate_points.map((point, index) => (
                          <th key={index} className="text-center px-2">
                            <Input
                              value={point.period}
                              disabled
                              className="h-7 text-xs text-center"
                            />
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td className="text-xs font-medium text-gray-600 pt-2">Rate</td>
                        {reference_rate_points.map((point, index) => (
                          <td key={index} className="text-center px-2 pt-2">
                            <Input
                              type="text"
                              value={`${point.rate.toFixed(1)}%`}
                              className="h-7 text-xs text-center"
                            />
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-400">
                  <p className="text-sm">Reference rate curve disabled</p>
                  <p className="text-xs mt-1">Enable to add SOFR rates</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Other Assumptions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Other Assumptions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="tax-rate">Corporate Tax Rate</Label>
                  <PercentageInput
                    value={parseFloat(tax_rate) || 0}
                    onChange={(val) => set_tax_rate(val.toString())}
                    placeholder="25.0"
                  />
                  <p className="text-xs text-gray-500">
                    Applied to taxable income in all forecast periods
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="minimum-cash">Minimum Cash Balance</Label>
                  <div className="flex items-center gap-2">
                    <NumberInput
                      value={parseFloat(minimum_cash) || 0}
                      onChange={(val) => set_minimum_cash(val.toString())}
                      placeholder="0.0"
                    />
                    <span className="text-sm text-gray-600">
                      {currency} {unit}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">
                    Minimum operating cash required on the balance sheet
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sources & Uses */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Sources & Uses</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Sources */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Sources of Funds</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between font-semibold text-gray-900">
                    <span>Total Debt</span>
                    <span>{total_debt.toLocaleString()}</span>
                  </div>
                  {tranches
                    .filter((t) => t.type !== "Revolver")
                    .map((tranche) => (
                      <div key={tranche.id} className="flex justify-between ml-4">
                        <span className="text-gray-500">{tranche.label}</span>
                        <span className="font-medium">{tranche.size.toLocaleString()}</span>
                      </div>
                    ))}
                  <div className="flex justify-between text-blue-600 mt-2">
                    <span>Equity (Plug)</span>
                    <span className="font-semibold">{equity.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t font-semibold">
                    <span>Total Sources</span>
                    <span>{total_sources.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Uses */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Uses of Funds</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Purchase Price</span>
                    <span className="font-medium">{purchase_price.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Transaction Fees</span>
                    <span className="font-medium">{fees.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t font-semibold">
                    <span>Total Uses</span>
                    <span>{total_uses.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Balance Check - Only show if NOT balanced */}
              {!is_balanced && (
                <Alert className="bg-red-50 border-red-200">
                  <AlertDescription className="text-red-800">
                    ⚠ Sources and uses are not balanced (difference: {currency}{" "}
                    {Math.abs(total_sources - total_uses).toLocaleString()} {unit})
                  </AlertDescription>
                </Alert>
              )}

              <p className="text-xs text-gray-500">
                All amounts in {currency} {unit}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <Button variant="ghost" onClick={handle_back}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Button onClick={handle_continue}>
          Continue to Results
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
