"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FileText, Building2, FileSpreadsheet, TrendingUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useWizard } from "@/contexts/wizard-context";
import { PROJECT_TYPES, ProjectType } from "@/types/wizard";

const ICONS: Record<ProjectType, React.ElementType> = {
  lbo: FileText,
  corporate_financing: Building2,
  business_plan: FileSpreadsheet,
  public_equity: TrendingUp,
};

export default function ProjectTypePage() {
  const router = useRouter();
  const { state, set_project_type, mark_step_visited } = useWizard();
  const [selected_type, set_selected_type] = useState<ProjectType | null>(
    state.project_type
  );

  // Mark step as visited on mount
  useEffect(() => {
    mark_step_visited("type");
  }, [mark_step_visited]);

  const handle_select = (type: ProjectType) => {
    if (!PROJECT_TYPES.find(t => t.id === type)?.enabled) {
      return;
    }
    set_selected_type(type);
    set_project_type(type);
  };

  const handle_continue = () => {
    if (selected_type) {
      router.push("/project-wizard/name");
    }
  };

  return (
    <div className="py-8">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          What would you like to do?
        </h1>
        <p className="text-muted-foreground">
          Select the type of financial analysis you want to perform
        </p>
      </div>

      {/* Project Type Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {PROJECT_TYPES.map((type) => {
          const Icon = ICONS[type.id];
          const is_selected = selected_type === type.id;
          const is_disabled = !type.enabled;

          return (
            <Card
              key={type.id}
              className={cn(
                "relative cursor-pointer transition-all hover:shadow-md",
                is_selected && "ring-2 ring-primary",
                is_disabled && "opacity-60 cursor-not-allowed hover:shadow-none"
              )}
              onClick={() => handle_select(type.id)}
            >
              <CardContent className="p-6">
                {/* Under Development Badge */}
                {is_disabled && (
                  <Badge
                    variant="warning"
                    className="absolute top-4 right-4"
                  >
                    Under Development
                  </Badge>
                )}

                {/* Icon and Title */}
                <div className="flex items-start gap-4">
                  <div className={cn(
                    "p-2 rounded-lg",
                    is_selected ? "bg-primary/10 text-primary" : "bg-secondary"
                  )}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg mb-1">{type.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {type.description}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Continue Button */}
      <div className="flex justify-end">
        <Button
          size="lg"
          onClick={handle_continue}
          disabled={!selected_type}
        >
          Create Project
        </Button>
      </div>
    </div>
  );
}
