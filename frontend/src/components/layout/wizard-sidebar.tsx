"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Check, Circle, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWizard } from "@/contexts/wizard-context";
import { WIZARD_STEPS, WizardStepId } from "@/types/wizard";

export function WizardSidebar() {
  const pathname = usePathname();
  const { state, can_access_step } = useWizard();

  // Determine current step from pathname
  const current_step_id = WIZARD_STEPS.find(step =>
    pathname.includes(step.path)
  )?.id;

  return (
    <aside className="w-64 bg-card border-r min-h-screen p-6">
      <div className="mb-8">
        <Link href="/dashboard" className="text-xl font-bold text-primary">
          finLine
        </Link>
      </div>

      <nav className="space-y-1">
        {WIZARD_STEPS.map((step, index) => {
          const is_current = step.id === current_step_id;
          const is_visited = state.visited_steps.includes(step.id);
          const is_accessible = can_access_step(step.id);

          // Determine step status
          let status: "completed" | "current" | "upcoming" | "locked" = "upcoming";
          if (is_visited && !is_current) {
            status = "completed";
          } else if (is_current) {
            status = "current";
          } else if (!is_accessible) {
            status = "locked";
          }

          return (
            <StepItem
              key={step.id}
              step={step}
              index={index}
              status={status}
              is_accessible={is_accessible}
            />
          );
        })}
      </nav>

      {/* Progress indicator */}
      <div className="mt-8 pt-6 border-t">
        <div className="text-sm text-muted-foreground mb-2">
          Progress
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{
                width: `${((state.visited_steps.length) / WIZARD_STEPS.length) * 100}%`
              }}
            />
          </div>
          <span className="text-xs text-muted-foreground">
            {state.visited_steps.length}/{WIZARD_STEPS.length}
          </span>
        </div>
      </div>
    </aside>
  );
}

interface StepItemProps {
  step: typeof WIZARD_STEPS[number];
  index: number;
  status: "completed" | "current" | "upcoming" | "locked";
  is_accessible: boolean;
}

function StepItem({ step, index, status, is_accessible }: StepItemProps) {
  const content = (
    <div
      className={cn(
        "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
        status === "current" && "bg-primary/10 text-primary",
        status === "completed" && "text-foreground hover:bg-secondary",
        status === "upcoming" && is_accessible && "text-muted-foreground hover:bg-secondary",
        status === "locked" && "text-muted-foreground/50 cursor-not-allowed",
        is_accessible && status !== "locked" && "cursor-pointer"
      )}
    >
      {/* Step indicator */}
      <div
        className={cn(
          "flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium",
          status === "completed" && "bg-primary text-primary-foreground",
          status === "current" && "bg-primary text-primary-foreground",
          status === "upcoming" && "bg-secondary text-secondary-foreground",
          status === "locked" && "bg-muted text-muted-foreground"
        )}
      >
        {status === "completed" ? (
          <Check className="h-3.5 w-3.5" />
        ) : status === "locked" ? (
          <Lock className="h-3 w-3" />
        ) : (
          index + 1
        )}
      </div>

      {/* Step info */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{step.title}</div>
        <div className="text-xs text-muted-foreground truncate">
          {step.description}
        </div>
      </div>
    </div>
  );

  if (is_accessible && status !== "locked") {
    return (
      <Link href={step.path}>
        {content}
      </Link>
    );
  }

  return content;
}
