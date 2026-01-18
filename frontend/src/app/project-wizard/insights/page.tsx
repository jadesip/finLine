"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Building2,
  Globe,
  FileText,
  Users,
  Target,
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  Loader2,
  Info,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { useWizard } from "@/contexts/wizard-context";
import { ProjectJsonViewer } from "@/components/debug/project-json-viewer";
import { api, InsightsData } from "@/lib/api";

export default function InsightsPage() {
  const router = useRouter();
  const { state, mark_step_visited } = useWizard();
  const [active_tab, set_active_tab] = useState("overview");
  const [insights, set_insights] = useState<InsightsData | null>(null);
  const [is_loading, set_is_loading] = useState(true);
  const [error, set_error] = useState<string | null>(null);

  // Mark step as visited on mount
  useEffect(() => {
    mark_step_visited("insights");
  }, [mark_step_visited]);

  // Redirect if no project
  useEffect(() => {
    if (!state.project_id) {
      router.push("/project-wizard/type");
      return;
    }

    // Fetch insights
    fetch_insights();
  }, [state.project_id, router]);

  const fetch_insights = async () => {
    if (!state.project_id) return;

    set_is_loading(true);
    set_error(null);

    try {
      const data = await api.get_insights(state.project_id, [
        "industry",
        "competitors",
        "market_trends",
        "risks",
        "opportunities",
      ]);
      set_insights(data);
    } catch (err: any) {
      set_error(err.detail || "Failed to load insights");
    } finally {
      set_is_loading(false);
    }
  };

  // Count risk flags
  const risk_flag_count = insights?.strategic_analysis?.risk_analysis
    ? Object.values(insights.strategic_analysis.risk_analysis).filter(
        (risk: any) => risk && typeof risk === "object" && risk.flag === true
      ).length
    : 0;

  const handle_continue = () => {
    // For now, go to dashboard since we haven't built the rest of the wizard
    router.push("/dashboard");
  };

  const handle_skip = () => {
    router.push("/dashboard");
  };

  if (is_loading) {
    return (
      <div className="py-8">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold tracking-tight mb-2">
            Business Intelligence Review
          </h1>
          <p className="text-muted-foreground">
            Loading business insights...
          </p>
        </div>
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (error || !insights) {
    return (
      <div className="py-8">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold tracking-tight mb-2">
            Business Intelligence Review
          </h1>
          <p className="text-muted-foreground">
            Review extracted business insights and strategic analysis
          </p>
        </div>

        <Alert className="max-w-2xl mx-auto mb-8">
          <Info className="h-4 w-4" />
          <AlertTitle>No Business Intelligence Available</AlertTitle>
          <AlertDescription>
            Business intelligence extraction is not available for this project yet.
            You can continue without it or try again later.
          </AlertDescription>
        </Alert>

        <div className="flex items-center justify-between max-w-2xl mx-auto">
          <Button variant="outline" onClick={() => router.push("/project-wizard/financials")}>
            Back
          </Button>
          <Button onClick={handle_skip}>
            Skip and Continue
          </Button>
        </div>
      </div>
    );
  }

  const { business_insights, strategic_analysis } = insights;

  return (
    <div className="py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          Business Intelligence Review
        </h1>
        <p className="text-muted-foreground">
          Review extracted business insights and strategic analysis
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={active_tab} onValueChange={set_active_tab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="business">Business Model</TabsTrigger>
          <TabsTrigger value="management">Management</TabsTrigger>
          <TabsTrigger value="strategy">Strategy & SWOT</TabsTrigger>
          <TabsTrigger value="risks" className="flex items-center gap-2">
            Risk Analysis
            {risk_flag_count > 0 && (
              <Badge variant="destructive" className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs">
                {risk_flag_count}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Business Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                Business Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground leading-relaxed">
                {business_insights?.business_description?.summary || "No description available."}
              </p>
              {business_insights?.business_description?.confidence && (
                <Badge variant="outline" className="mt-4">
                  Confidence: {business_insights.business_description.confidence}
                </Badge>
              )}
            </CardContent>
          </Card>

          {/* Industry Context */}
          {strategic_analysis?.industry_context && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  Industry Context
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {strategic_analysis.industry_context.market_characteristics && (
                  <div>
                    <h4 className="font-medium mb-1">Market Characteristics</h4>
                    <p className="text-sm text-muted-foreground">
                      {strategic_analysis.industry_context.market_characteristics}
                    </p>
                  </div>
                )}
                {strategic_analysis.industry_context.growth_trends && (
                  <div>
                    <h4 className="font-medium mb-1">Growth Trends</h4>
                    <p className="text-sm text-muted-foreground">
                      {strategic_analysis.industry_context.growth_trends}
                    </p>
                  </div>
                )}
                {strategic_analysis.industry_context.regulatory_factors?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-1">Regulatory Factors</h4>
                    <ul className="list-disc list-inside text-sm text-muted-foreground">
                      {strategic_analysis.industry_context.regulatory_factors.map((factor, i) => (
                        <li key={i}>{factor}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {strategic_analysis.industry_context.competitive_dynamics && (
                  <div>
                    <h4 className="font-medium mb-1">Competitive Dynamics</h4>
                    <p className="text-sm text-muted-foreground">
                      {strategic_analysis.industry_context.competitive_dynamics}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Recent Events */}
          {strategic_analysis?.recent_events?.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Recent Events
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {strategic_analysis.recent_events.map((event, i) => (
                    <div key={i} className="flex items-start gap-4 border-l-4 border-primary/20 pl-4">
                      <div className="flex-1">
                        <p className="text-sm">{event.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="secondary">{event.event_type}</Badge>
                          {event.impact && (
                            <Badge variant={event.impact === "high impact" ? "destructive" : "outline"}>
                              {event.impact}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Business Model Tab */}
        <TabsContent value="business" className="space-y-6">
          {/* Revenue Model */}
          {business_insights?.revenue_model && (
            <Card>
              <CardHeader>
                <CardTitle>Revenue Model</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {business_insights.revenue_model.key_products_services?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Key Products & Services</h4>
                    <div className="flex flex-wrap gap-2">
                      {business_insights.revenue_model.key_products_services.map((item, i) => (
                        <Badge key={i} variant="secondary">{item}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {business_insights.revenue_model.revenue_streams?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Revenue Streams</h4>
                    <ul className="list-disc list-inside text-sm text-muted-foreground">
                      {business_insights.revenue_model.revenue_streams.map((stream, i) => (
                        <li key={i}>{stream}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {business_insights.revenue_model.customer_segments?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Customer Segments</h4>
                    <div className="flex flex-wrap gap-2">
                      {business_insights.revenue_model.customer_segments.map((seg, i) => (
                        <Badge key={i} variant="outline">{seg}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {business_insights.revenue_model.geographic_markets?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Geographic Markets</h4>
                    <div className="flex flex-wrap gap-2">
                      {business_insights.revenue_model.geographic_markets.map((market, i) => (
                        <Badge key={i} variant="outline">{market}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Cost Structure */}
          {business_insights?.cost_structure && (
            <Card>
              <CardHeader>
                <CardTitle>Cost Structure</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {business_insights.cost_structure.fixed_costs?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Fixed Costs</h4>
                    <ul className="list-disc list-inside text-sm text-muted-foreground">
                      {business_insights.cost_structure.fixed_costs.map((cost, i) => (
                        <li key={i}>{cost}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {business_insights.cost_structure.variable_costs?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Variable Costs</h4>
                    <ul className="list-disc list-inside text-sm text-muted-foreground">
                      {business_insights.cost_structure.variable_costs.map((cost, i) => (
                        <li key={i}>{cost}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {business_insights.cost_structure.key_cost_drivers?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Key Cost Drivers</h4>
                    <div className="flex flex-wrap gap-2">
                      {business_insights.cost_structure.key_cost_drivers.map((driver, i) => (
                        <Badge key={i} variant="secondary">{driver}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Capital Requirements */}
          {business_insights?.capital_requirements && (
            <Card>
              <CardHeader>
                <CardTitle>Capital Requirements</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {business_insights.capital_requirements.capital_intensity && (
                  <div>
                    <h4 className="font-medium mb-1">Capital Intensity</h4>
                    <Badge
                      variant={
                        business_insights.capital_requirements.capital_intensity === "high"
                          ? "destructive"
                          : business_insights.capital_requirements.capital_intensity === "medium"
                          ? "warning"
                          : "success"
                      }
                    >
                      {business_insights.capital_requirements.capital_intensity}
                    </Badge>
                  </div>
                )}
                {business_insights.capital_requirements.capex_types?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Capex Types</h4>
                    <ul className="list-disc list-inside text-sm text-muted-foreground">
                      {business_insights.capital_requirements.capex_types.map((type, i) => (
                        <li key={i}>{type}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {business_insights.capital_requirements.key_assets?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Key Assets</h4>
                    <div className="flex flex-wrap gap-2">
                      {business_insights.capital_requirements.key_assets.map((asset, i) => (
                        <Badge key={i} variant="outline">{asset}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Management Tab */}
        <TabsContent value="management" className="space-y-4">
          {business_insights?.management_team?.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {business_insights.management_team.map((member, i) => (
                <Card key={i}>
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                        <Users className="h-6 w-6 text-primary" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold">{member.name}</h3>
                        <p className="text-sm text-muted-foreground">{member.position}</p>
                        {member.tenure && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Tenure: {member.tenure}
                          </p>
                        )}
                        {member.career_summary && (
                          <p className="text-sm mt-2">{member.career_summary}</p>
                        )}
                        {member.linkedin_profile && (
                          <a
                            href={member.linkedin_profile}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-sm text-primary hover:underline mt-2"
                          >
                            LinkedIn <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>No management information available.</AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Strategy & SWOT Tab */}
        <TabsContent value="strategy" className="space-y-6">
          {/* Strategy */}
          {strategic_analysis?.strategy && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Business Strategy
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {strategic_analysis.strategy.business_strategy && (
                  <div>
                    <h4 className="font-medium mb-1">Strategy</h4>
                    <p className="text-sm text-muted-foreground">
                      {strategic_analysis.strategy.business_strategy}
                    </p>
                  </div>
                )}
                {strategic_analysis.strategy.competitive_positioning && (
                  <div>
                    <h4 className="font-medium mb-1">Competitive Positioning</h4>
                    <p className="text-sm text-muted-foreground">
                      {strategic_analysis.strategy.competitive_positioning}
                    </p>
                  </div>
                )}
                {strategic_analysis.strategy.differentiation && (
                  <div>
                    <h4 className="font-medium mb-1">Differentiation</h4>
                    <p className="text-sm text-muted-foreground">
                      {strategic_analysis.strategy.differentiation}
                    </p>
                  </div>
                )}
                {strategic_analysis.strategy.growth_initiatives?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Growth Initiatives</h4>
                    <ul className="list-disc list-inside text-sm text-muted-foreground">
                      {strategic_analysis.strategy.growth_initiatives.map((init, i) => (
                        <li key={i}>{init}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* SWOT */}
          {strategic_analysis?.swot_analysis && (
            <Card>
              <CardHeader>
                <CardTitle>SWOT Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {/* Strengths */}
                  <div className="bg-green-50 rounded-lg p-4">
                    <h4 className="font-medium text-green-800 mb-2">Strengths</h4>
                    <ul className="text-sm text-green-700 space-y-1">
                      {strategic_analysis.swot_analysis.strengths?.map((s, i) => (
                        <li key={i}>• {s}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Weaknesses */}
                  <div className="bg-red-50 rounded-lg p-4">
                    <h4 className="font-medium text-red-800 mb-2">Weaknesses</h4>
                    <ul className="text-sm text-red-700 space-y-1">
                      {strategic_analysis.swot_analysis.weaknesses?.map((w, i) => (
                        <li key={i}>• {w}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Opportunities */}
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-medium text-blue-800 mb-2">Opportunities</h4>
                    <ul className="text-sm text-blue-700 space-y-1">
                      {strategic_analysis.swot_analysis.opportunities?.map((o, i) => (
                        <li key={i}>• {o}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Threats */}
                  <div className="bg-orange-50 rounded-lg p-4">
                    <h4 className="font-medium text-orange-800 mb-2">Threats</h4>
                    <ul className="text-sm text-orange-700 space-y-1">
                      {strategic_analysis.swot_analysis.threats?.map((t, i) => (
                        <li key={i}>• {t}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Risk Analysis Tab */}
        <TabsContent value="risks" className="space-y-4">
          {/* Overall Risk Assessment */}
          {strategic_analysis?.risk_analysis?.overall_risk_assessment && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Overall Risk Assessment</h3>
                    <p className="text-sm text-muted-foreground">
                      {risk_flag_count} risk{risk_flag_count !== 1 ? "s" : ""} identified
                    </p>
                  </div>
                  <Badge
                    variant={
                      strategic_analysis.risk_analysis.overall_risk_assessment === "critical"
                        ? "destructive"
                        : strategic_analysis.risk_analysis.overall_risk_assessment === "high"
                        ? "destructive"
                        : strategic_analysis.risk_analysis.overall_risk_assessment === "medium"
                        ? "warning"
                        : "success"
                    }
                    className="text-lg px-4 py-1"
                  >
                    {strategic_analysis.risk_analysis.overall_risk_assessment.toUpperCase()}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Individual Risk Cards */}
          {strategic_analysis?.risk_analysis && (
            <div className="space-y-4">
              {Object.entries(strategic_analysis.risk_analysis).map(([key, risk]) => {
                if (key === "overall_risk_assessment" || typeof risk !== "object" || risk === null) {
                  return null;
                }

                const risk_title = key
                  .split("_")
                  .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                  .join(" ");

                const has_risk = (risk as any).flag === true;

                return (
                  <Card
                    key={key}
                    className={cn(
                      "border-l-4",
                      has_risk ? "border-l-red-500" : "border-l-green-500"
                    )}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-start gap-4">
                        {has_risk ? (
                          <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
                        ) : (
                          <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <h4 className={cn("font-medium", has_risk ? "text-red-800" : "text-green-800")}>
                            {risk_title}
                          </h4>
                          {(risk as any).details && (
                            <p className="text-sm text-muted-foreground mt-1">
                              {(risk as any).details}
                            </p>
                          )}
                          {/* Render specific risk details */}
                          {(risk as any).top_client_percentage && (
                            <p className="text-sm text-muted-foreground mt-1">
                              Top client: {(risk as any).top_client_percentage}%
                            </p>
                          )}
                          {(risk as any).cash_runway && (
                            <p className="text-sm text-muted-foreground mt-1">
                              Cash runway: {(risk as any).cash_runway}
                            </p>
                          )}
                          {(risk as any).transactions?.length > 0 && (
                            <ul className="list-disc list-inside text-sm text-muted-foreground mt-1">
                              {(risk as any).transactions.map((t: string, i: number) => (
                                <li key={i}>{t}</li>
                              ))}
                            </ul>
                          )}
                          {(risk as any).issues?.length > 0 && (
                            <ul className="list-disc list-inside text-sm text-muted-foreground mt-1">
                              {(risk as any).issues.map((issue: string, i: number) => (
                                <li key={i}>{issue}</li>
                              ))}
                            </ul>
                          )}
                          {(risk as any).risks?.length > 0 && (
                            <ul className="list-disc list-inside text-sm text-muted-foreground mt-1">
                              {(risk as any).risks.map((r: string, i: number) => (
                                <li key={i}>{r}</li>
                              ))}
                            </ul>
                          )}
                          {(risk as any).flags?.length > 0 && (
                            <ul className="list-disc list-inside text-sm text-muted-foreground mt-1">
                              {(risk as any).flags.map((f: string, i: number) => (
                                <li key={i}>{f}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Debug JSON Panel */}
      <div className="mt-8">
        <ProjectJsonViewer data={state.project_data} title="Debug: Full Project Data" />
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-8">
        <Button variant="outline" onClick={() => router.push("/project-wizard/financials")}>
          Back
        </Button>

        <Button size="lg" onClick={handle_continue}>
          Complete Setup
        </Button>
      </div>
    </div>
  );
}
