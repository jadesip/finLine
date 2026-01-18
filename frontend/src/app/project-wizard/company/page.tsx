"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle, Pencil } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useWizard } from "@/contexts/wizard-context";
import { WizardFooter } from "@/components/layout/wizard-header";
import { ProjectJsonViewer } from "@/components/debug/project-json-viewer";
import type { ProjectMeta } from "@/lib/api";

const CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"];
const UNITS = ["millions", "thousands", "billions"];
const FREQUENCIES = ["annual", "quarterly", "monthly"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];
const FORECAST_YEARS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// Generate years for dropdown
const YEARS = Array.from({ length: 10 }, (_, i) => (2020 + i).toString());

export default function CompanyInfoPage() {
  const router = useRouter();
  const { state, update_field, load_project, mark_step_visited } = useWizard();
  const [is_saving, set_is_saving] = useState(false);

  // Mark step as visited on mount
  useEffect(() => {
    mark_step_visited("company");
  }, [mark_step_visited]);

  // Local state for form fields
  const meta = (state.project_data?.meta || {}) as Partial<ProjectMeta>;
  const [company_name, set_company_name] = useState(meta.company_name || "");
  const [country, set_country] = useState(meta.country_of_headquarters || "United States");
  const [currency, set_currency] = useState(meta.currency || "USD");
  const [unit, set_unit] = useState(meta.unit || "millions");
  const [frequency, set_frequency] = useState(meta.frequency || "annual");
  const [fiscal_year_end, set_fiscal_year_end] = useState(meta.financial_year_end || "December");
  const [last_hist_month, set_last_hist_month] = useState("Dec");
  const [last_hist_year, set_last_hist_year] = useState("2024");
  const [forecast_horizon, set_forecast_horizon] = useState(meta.number_of_periods_forecast || 3);

  // Redirect if no project
  useEffect(() => {
    if (!state.project_id) {
      router.push("/project-wizard/type");
    }
  }, [state.project_id, router]);

  // Parse last_historical_period if exists
  useEffect(() => {
    if (meta.last_historical_period) {
      // Format: "Dec-24" or "Dec-2024"
      const parts = meta.last_historical_period.split("-");
      if (parts.length === 2) {
        set_last_hist_month(parts[0]);
        const year = parts[1].length === 2 ? `20${parts[1]}` : parts[1];
        set_last_hist_year(year);
      }
    }
  }, [meta.last_historical_period]);

  // Update local state when project data changes
  useEffect(() => {
    if (meta.company_name) set_company_name(meta.company_name);
    if (meta.currency) set_currency(meta.currency);
    if (meta.unit) set_unit(meta.unit);
    if (meta.frequency) set_frequency(meta.frequency);
    if (meta.financial_year_end) set_fiscal_year_end(meta.financial_year_end);
    if (meta.number_of_periods_forecast) set_forecast_horizon(meta.number_of_periods_forecast);
  }, [meta]);

  const handle_field_blur = async (path: string, value: any) => {
    if (!state.project_id) return;
    set_is_saving(true);
    try {
      await update_field(path, value);
    } finally {
      set_is_saving(false);
    }
  };

  const handle_continue = async () => {
    // Save all fields before continuing
    const last_historical_period = `${last_hist_month}-${last_hist_year.slice(-2)}`;

    await Promise.all([
      update_field("meta.company_name", company_name),
      update_field("meta.country_of_headquarters", country),
      update_field("meta.currency", currency),
      update_field("meta.unit", unit),
      update_field("meta.frequency", frequency),
      update_field("meta.financial_year_end", fiscal_year_end),
      update_field("meta.last_historical_period", last_historical_period),
      update_field("meta.number_of_periods_forecast", forecast_horizon),
    ]);

    router.push("/project-wizard/financials");
  };

  const extraction_success = state.extraction_status === "completed";

  return (
    <div className="py-8">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          Company Information
        </h1>
        <p className="text-muted-foreground">
          Review and complete company details
        </p>
      </div>

      {/* Success Alert */}
      {extraction_success && (
        <Alert variant="success" className="max-w-3xl mx-auto mb-6">
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Data extracted successfully! Review and edit as needed.
          </AlertDescription>
        </Alert>
      )}

      {/* Company Details Card */}
      <Card className="max-w-3xl mx-auto">
        <CardHeader>
          <CardTitle>Company Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Row 1: Company Name & Country */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="company-name" className="flex items-center gap-1">
                Company Name <span className="text-destructive">*</span>
                <Pencil className="h-3 w-3 text-muted-foreground" />
              </Label>
              <Input
                id="company-name"
                value={company_name}
                onChange={(e) => set_company_name(e.target.value)}
                onBlur={() => handle_field_blur("meta.company_name", company_name)}
                placeholder="Enter company name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="country" className="flex items-center gap-1">
                Country of Headquarters <span className="text-destructive">*</span>
                <Pencil className="h-3 w-3 text-muted-foreground" />
              </Label>
              <Input
                id="country"
                value={country}
                onChange={(e) => set_country(e.target.value)}
                onBlur={() => handle_field_blur("meta.country_of_headquarters", country)}
                placeholder="e.g., United States"
              />
            </div>
          </div>

          {/* Row 2: Currency, Unit Scale, Reporting Frequency */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label className="flex items-center gap-1">
                Currency
                <Pencil className="h-3 w-3 text-muted-foreground" />
              </Label>
              <Select
                value={currency}
                onValueChange={(value) => {
                  set_currency(value);
                  handle_field_blur("meta.currency", value);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select currency" />
                </SelectTrigger>
                <SelectContent>
                  {CURRENCIES.map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-1">
                Unit Scale
                <Pencil className="h-3 w-3 text-muted-foreground" />
              </Label>
              <Select
                value={unit}
                onValueChange={(value) => {
                  set_unit(value);
                  handle_field_blur("meta.unit", value);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select unit" />
                </SelectTrigger>
                <SelectContent>
                  {UNITS.map((u) => (
                    <SelectItem key={u} value={u}>{u}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-1">
                Reporting Frequency
                <Pencil className="h-3 w-3 text-muted-foreground" />
              </Label>
              <Select
                value={frequency}
                onValueChange={(value) => {
                  set_frequency(value);
                  handle_field_blur("meta.frequency", value);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select frequency" />
                </SelectTrigger>
                <SelectContent>
                  {FREQUENCIES.map((f) => (
                    <SelectItem key={f} value={f}>{f}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Row 3: Fiscal Year End, Last Historical Period, Forecast Horizon */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Fiscal Year End</Label>
              <Select
                value={fiscal_year_end}
                onValueChange={(value) => {
                  set_fiscal_year_end(value);
                  handle_field_blur("meta.financial_year_end", value);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select month" />
                </SelectTrigger>
                <SelectContent>
                  {MONTHS.map((m) => (
                    <SelectItem key={m} value={m}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Last Historical Period</Label>
              <div className="flex gap-2">
                <Select
                  value={last_hist_month}
                  onValueChange={set_last_hist_month}
                >
                  <SelectTrigger className="w-24">
                    <SelectValue placeholder="Month" />
                  </SelectTrigger>
                  <SelectContent>
                    {["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].map((m) => (
                      <SelectItem key={m} value={m}>{m}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select
                  value={last_hist_year}
                  onValueChange={set_last_hist_year}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Year" />
                  </SelectTrigger>
                  <SelectContent>
                    {YEARS.map((y) => (
                      <SelectItem key={y} value={y}>{y}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Forecast Horizon (years)</Label>
              <Select
                value={forecast_horizon.toString()}
                onValueChange={(value) => {
                  const v = parseInt(value, 10);
                  set_forecast_horizon(v);
                  handle_field_blur("meta.number_of_periods_forecast", v);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select years" />
                </SelectTrigger>
                <SelectContent>
                  {FORECAST_YEARS.map((y) => (
                    <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Debug JSON Panel */}
      <div className="mt-8 max-w-3xl mx-auto">
        <ProjectJsonViewer data={state.project_data} title="Debug: Full Project Data" />
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-8 max-w-3xl mx-auto">
        <Button
          variant="outline"
          onClick={() => router.push("/project-wizard/upload")}
        >
          Back
        </Button>

        <Button
          size="lg"
          onClick={handle_continue}
          disabled={!company_name.trim()}
        >
          Continue
        </Button>
      </div>
    </div>
  );
}
