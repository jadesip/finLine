"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Calendar, DollarSign } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useWizard } from "@/contexts/wizard-context";
import { ProjectJsonViewer } from "@/components/debug/project-json-viewer";

// Month-Year date picker component
function MonthYearPicker({
  value,
  onChange,
  id,
}: {
  value: string;
  onChange: (value: string) => void;
  id: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedYear, setSelectedYear] = useState(() => {
    return value ? new Date(value).getFullYear() : new Date().getFullYear();
  });
  const [selectedMonth, setSelectedMonth] = useState(() => {
    return value ? new Date(value).getMonth() : new Date().getMonth();
  });

  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];

  // Format display value
  const formatDisplay = (isoDate: string) => {
    if (!isoDate) return "";
    const date = new Date(isoDate);
    return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
  };

  const handleSelectDate = () => {
    const lastDay = new Date(selectedYear, selectedMonth + 1, 0);
    onChange(lastDay.toISOString().split("T")[0]);
    setIsOpen(false);
  };

  // Update local state when value changes
  useEffect(() => {
    if (value) {
      const date = new Date(value);
      setSelectedYear(date.getFullYear());
      setSelectedMonth(date.getMonth());
    }
  }, [value]);

  // Handle click outside to close dropdown
  useEffect(() => {
    if (isOpen) {
      const handleClickOutside = (event: MouseEvent) => {
        const target = event.target as HTMLElement;
        if (!target.closest(`[data-month-picker="${id}"]`)) {
          setIsOpen(false);
        }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen, id]);

  return (
    <div className="relative" data-month-picker={id}>
      <div className="relative">
        <Input
          id={id}
          type="text"
          value={formatDisplay(value)}
          readOnly
          className="w-full pr-10 cursor-pointer"
          placeholder="Select month"
          onClick={() => setIsOpen(!isOpen)}
        />
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
        >
          <Calendar className="h-4 w-4 text-gray-400" />
        </button>
      </div>

      {isOpen && (
        <div className="absolute top-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-50 w-64">
          <div className="space-y-3">
            <div>
              <Label htmlFor={`${id}-year`} className="text-xs">
                Year
              </Label>
              <select
                id={`${id}-year`}
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm"
              >
                {Array.from({ length: 20 }, (_, i) => new Date().getFullYear() - 5 + i).map(
                  (year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  )
                )}
              </select>
            </div>
            <div>
              <Label htmlFor={`${id}-month`} className="text-xs">
                Month
              </Label>
              <select
                id={`${id}-month`}
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm"
              >
                {months.map((month, index) => (
                  <option key={index} value={index}>
                    {month}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-2 pt-2">
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => setIsOpen(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button type="button" size="sm" onClick={handleSelectDate} className="flex-1">
                Select
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Multiple input component with "x" suffix
function MultipleInput({
  id,
  value,
  onChange,
  placeholder = "7.0",
}: {
  id: string;
  value: number;
  onChange: (value: number) => void;
  placeholder?: string;
}) {
  const [isFocused, setIsFocused] = useState(false);
  const [inputValue, setInputValue] = useState(value.toString());

  useEffect(() => {
    if (!isFocused) {
      setInputValue(value.toFixed(1));
    }
  }, [value, isFocused]);

  const handleBlur = () => {
    setIsFocused(false);
    const numValue = parseFloat(inputValue) || 0;
    onChange(numValue);
    setInputValue(numValue.toFixed(1));
  };

  const handleFocus = () => {
    setIsFocused(true);
    setInputValue(value.toString());
  };

  const displayValue = isFocused ? inputValue : `${value.toFixed(1)}x`;

  return (
    <Input
      id={id}
      type="text"
      value={displayValue}
      onChange={(e) => {
        const newValue = e.target.value.replace(/x$/i, "");
        setInputValue(newValue);
      }}
      onBlur={handleBlur}
      onFocus={(e) => {
        handleFocus();
        const valueWithoutX = e.target.value.replace(/x$/i, "");
        setInputValue(valueWithoutX);
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          e.currentTarget.blur();
        }
        if (e.key === "Escape") {
          e.preventDefault();
          setInputValue(value.toString());
          setIsFocused(false);
          e.currentTarget.blur();
        }
      }}
      placeholder={`${placeholder}x`}
    />
  );
}

// Percentage Input Component - shows value with % suffix (no spinners)
function PercentageInput({
  id,
  value,
  onChange,
  placeholder = "0.0",
  className = "",
}: {
  id?: string;
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
    // Clamp between 0 and 10 for transaction fees
    const clamped = Math.min(Math.max(num, 0), 10);
    onChange(clamped);
    set_display_value(clamped.toString());
  };

  const handle_focus = () => {
    set_is_focused(true);
  };

  return (
    <Input
      id={id}
      type="text"
      value={is_focused ? display_value : `${value}%`}
      onChange={handle_change}
      onBlur={handle_blur}
      onFocus={handle_focus}
      placeholder={placeholder}
      className={className}
    />
  );
}

// Helper function to format numbers with commas
function formatNumber(value: number): string {
  return Math.round(value).toLocaleString("en-US");
}

// Helper function to format multiple with x
function formatMultiple(value: number): string {
  return value.toFixed(1) + "x";
}

// Case selector
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
    description: "Most likely scenario",
    icon: "—",
    color: "blue",
  },
  {
    id: "upside_case",
    name: "Upside Case",
    description: "Optimistic scenario",
    icon: "↗",
    color: "green",
  },
  {
    id: "downside_case",
    name: "Downside Case",
    description: "Conservative scenario",
    icon: "↘",
    color: "orange",
  },
];

export default function DealAssumptionsPage() {
  const router = useRouter();
  const { state, mark_step_visited } = useWizard();
  const [active_case, set_active_case] = useState("base_case");

  // Deal data state (UI only for now)
  const [deal_data, set_deal_data] = useState({
    entry: {
      date: new Date().toISOString().split("T")[0],
      ebitda: 150,
      multiple: 7.0,
      purchase_price: 1050,
      fee_percentage: 2.0,
      transaction_fees: 21,
      total_uses: 1071,
    },
    exit: {
      date: new Date(new Date().setFullYear(new Date().getFullYear() + 5))
        .toISOString()
        .split("T")[0],
      ebitda: 200,
      multiple: 6.0,
      firm_value: 1200,
      fee_percentage: 2.0,
    },
  });

  // Mark step as visited on mount
  useEffect(() => {
    mark_step_visited("deal_assumptions");
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

  // Calculate derived values
  const calculate_entry_values = (entry: typeof deal_data.entry) => {
    const purchase_price = entry.ebitda * entry.multiple;
    const transaction_fees = (purchase_price * entry.fee_percentage) / 100;
    const total_uses = purchase_price + transaction_fees;
    return { ...entry, purchase_price, transaction_fees, total_uses };
  };

  const calculate_exit_values = (exit: typeof deal_data.exit) => {
    const firm_value = exit.ebitda * exit.multiple;
    return { ...exit, firm_value };
  };

  // Handle entry changes
  const handle_entry_change = (field: string, value: any) => {
    set_deal_data((prev) => ({
      ...prev,
      entry: calculate_entry_values({ ...prev.entry, [field]: value }),
    }));
  };

  // Handle exit changes
  const handle_exit_change = (field: string, value: any) => {
    set_deal_data((prev) => ({
      ...prev,
      exit: calculate_exit_values({ ...prev.exit, [field]: value }),
    }));
  };

  // Calculate hold period
  const hold_period =
    deal_data.entry.date && deal_data.exit.date
      ? Math.round(
          (new Date(deal_data.exit.date).getTime() - new Date(deal_data.entry.date).getTime()) /
            (365 * 24 * 60 * 60 * 1000)
        )
      : 0;

  const handle_back = () => {
    router.push(`/project-wizard/forecast?id=${state.project_id}`);
  };

  const handle_continue = () => {
    router.push(`/project-wizard/capital-structure?id=${state.project_id}`);
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

  // Get years for valuation multiples display
  const entry_year = deal_data.entry.date
    ? new Date(deal_data.entry.date).getFullYear()
    : new Date().getFullYear();
  const exit_year = deal_data.exit.date
    ? new Date(deal_data.exit.date).getFullYear()
    : new Date().getFullYear() + 5;

  return (
    <div className="py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Deal Assumptions</h1>
        <p className="text-muted-foreground">Define deal entry and exit parameters</p>
      </div>

      {/* Case Selector */}
      <div className="flex gap-3 mb-6">{CASES.map(render_case_card)}</div>

      {/* Entry and Exit Cards Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Entry Assumptions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Entry Assumptions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="entry-date" className="text-sm">
                Entry Date (Month-Year)
              </Label>
              <MonthYearPicker
                id="entry-date"
                value={deal_data.entry.date}
                onChange={(value) => handle_entry_change("date", value)}
              />
              <p className="text-xs text-gray-500 mt-0.5">Deal closes at month end</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="entry-ebitda" className="text-sm">
                  EBITDA {entry_year}
                </Label>
                <div className="relative">
                  <DollarSign className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-400" />
                  <Input
                    id="entry-ebitda"
                    type="text"
                    value={formatNumber(deal_data.entry.ebitda)}
                    disabled
                    className="pl-8 bg-gray-50 h-9 text-sm"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  {currency} {unit}
                </p>
              </div>

              <div>
                <Label htmlFor="entry-multiple" className="text-sm">
                  Entry Multiple
                </Label>
                <MultipleInput
                  id="entry-multiple"
                  value={deal_data.entry.multiple}
                  onChange={(value) => handle_entry_change("multiple", value)}
                  placeholder="7.0"
                />
                <p className="text-xs text-gray-500 mt-0.5">EBITDA multiple</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="purchase-price" className="text-sm">
                  Purchase Price
                </Label>
                <div className="relative">
                  <DollarSign className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-400" />
                  <Input
                    id="purchase-price"
                    type="text"
                    value={formatNumber(deal_data.entry.purchase_price)}
                    disabled
                    className="pl-8 bg-gray-50 h-9 text-sm"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  {formatNumber(deal_data.entry.ebitda)} ×{" "}
                  {formatMultiple(deal_data.entry.multiple)} ={" "}
                  {formatNumber(deal_data.entry.purchase_price)}
                </p>
              </div>

              <div>
                <Label htmlFor="entry-fees" className="text-sm">
                  Transaction Fees
                </Label>
                <PercentageInput
                  id="entry-fees"
                  value={deal_data.entry.fee_percentage}
                  onChange={(value) => handle_entry_change("fee_percentage", value)}
                  placeholder="2.0"
                  className="h-9 text-sm"
                />
                <p className="text-xs text-gray-500 mt-0.5">% of Enterprise Value</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Exit Assumptions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Exit Assumptions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="exit-date" className="text-sm">
                Exit Date (Month-Year)
              </Label>
              <MonthYearPicker
                id="exit-date"
                value={deal_data.exit.date}
                onChange={(value) => handle_exit_change("date", value)}
              />
              <p className="text-xs text-gray-500 mt-0.5">Hold period: {hold_period} years</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="exit-ebitda" className="text-sm">
                  EBITDA {exit_year}
                </Label>
                <div className="relative">
                  <DollarSign className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-400" />
                  <Input
                    id="exit-ebitda"
                    type="text"
                    value={formatNumber(deal_data.exit.ebitda)}
                    disabled
                    className="pl-8 bg-gray-50 h-9 text-sm"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  {currency} {unit}
                </p>
              </div>

              <div>
                <Label htmlFor="exit-multiple" className="text-sm">
                  Exit Multiple
                </Label>
                <MultipleInput
                  id="exit-multiple"
                  value={deal_data.exit.multiple}
                  onChange={(value) => handle_exit_change("multiple", value)}
                  placeholder="6.0"
                />
                <p className="text-xs text-gray-500 mt-0.5">EBITDA multiple</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="firm-value" className="text-sm">
                  Firm Value Sale Price
                </Label>
                <div className="relative">
                  <DollarSign className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-400" />
                  <Input
                    id="firm-value"
                    type="text"
                    value={formatNumber(deal_data.exit.firm_value)}
                    disabled
                    className="pl-8 bg-gray-50 h-9 text-sm"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  {formatNumber(deal_data.exit.ebitda)} × {formatMultiple(deal_data.exit.multiple)}{" "}
                  = {formatNumber(deal_data.exit.firm_value)}
                </p>
              </div>

              <div>
                <Label htmlFor="exit-fees" className="text-sm">
                  Transaction Fees
                </Label>
                <PercentageInput
                  id="exit-fees"
                  value={deal_data.exit.fee_percentage}
                  onChange={(value) => handle_exit_change("fee_percentage", value)}
                  placeholder="2.0"
                  className="h-9 text-sm"
                />
                <p className="text-xs text-gray-500 mt-0.5">% of Enterprise Value</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Valuation Multiples Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6">
        {/* Entry Valuation Multiples */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Entry Valuation Multiples</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-1.5">Metric</th>
                      <th className="text-center py-1.5">FY{String(entry_year).slice(-2)}A</th>
                      <th className="text-center py-1.5">FY{String(entry_year + 1).slice(-2)}E</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b hover:bg-gray-50">
                      <td className="py-2">
                        <div className="font-medium text-sm">Revenue</div>
                        <div className="text-xs text-gray-500">500 / 550</div>
                      </td>
                      <td className="text-center py-2 font-medium text-sm">2.1x</td>
                      <td className="text-center py-2 font-medium text-sm">1.9x</td>
                    </tr>
                    <tr className="border-b hover:bg-gray-50">
                      <td className="py-2">
                        <div className="font-medium text-sm">EBITDA</div>
                        <div className="text-xs text-gray-500">150 / 165</div>
                      </td>
                      <td className="text-center py-2 font-medium text-sm text-blue-600">7.0x</td>
                      <td className="text-center py-2 font-medium text-sm text-blue-600">6.4x</td>
                    </tr>
                    <tr className="hover:bg-gray-50">
                      <td className="py-2">
                        <div className="font-medium text-sm">EBIT</div>
                        <div className="text-xs text-gray-500">120 / 132</div>
                      </td>
                      <td className="text-center py-2 font-medium text-sm">8.8x</td>
                      <td className="text-center py-2 font-medium text-sm">8.0x</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-gray-500">
                Purchase: {currency} {formatNumber(deal_data.entry.purchase_price)} {unit}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Exit Valuation Multiples */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Exit Valuation Multiples</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-1.5">Metric</th>
                      <th className="text-center py-1.5">FY{String(exit_year - 1).slice(-2)}E</th>
                      <th className="text-center py-1.5">FY{String(exit_year).slice(-2)}E</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b hover:bg-gray-50">
                      <td className="py-2">
                        <div className="font-medium text-sm">Revenue</div>
                        <div className="text-xs text-gray-500">680 / 720</div>
                      </td>
                      <td className="text-center py-2 font-medium text-sm">1.8x</td>
                      <td className="text-center py-2 font-medium text-sm">1.7x</td>
                    </tr>
                    <tr className="border-b hover:bg-gray-50">
                      <td className="py-2">
                        <div className="font-medium text-sm">EBITDA</div>
                        <div className="text-xs text-gray-500">190 / 200</div>
                      </td>
                      <td className="text-center py-2 font-medium text-sm text-blue-600">6.3x</td>
                      <td className="text-center py-2 font-medium text-sm text-blue-600">6.0x</td>
                    </tr>
                    <tr className="hover:bg-gray-50">
                      <td className="py-2">
                        <div className="font-medium text-sm">EBIT</div>
                        <div className="text-xs text-gray-500">155 / 165</div>
                      </td>
                      <td className="text-center py-2 font-medium text-sm">7.7x</td>
                      <td className="text-center py-2 font-medium text-sm">7.3x</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-gray-500">
                Exit Value: {currency} {formatNumber(deal_data.exit.firm_value)} {unit}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <Button variant="ghost" onClick={handle_back}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Button onClick={handle_continue}>
          Continue to Capital Structure
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
