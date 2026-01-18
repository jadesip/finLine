"use client";

import { useWizard } from "@/contexts/wizard-context";
import { WIZARD_STEPS } from "@/types/wizard";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";

interface WizardHeaderProps {
  title: string;
  description?: string;
  show_navigation?: boolean;
  show_back?: boolean;
  show_next?: boolean;
  next_label?: string;
  on_next?: () => void | Promise<void>;
  next_disabled?: boolean;
  is_loading?: boolean;
}

export function WizardHeader({
  title,
  description,
  show_navigation = true,
  show_back = true,
  show_next = true,
  next_label = "Continue",
  on_next,
  next_disabled = false,
  is_loading = false,
}: WizardHeaderProps) {
  const { state, prev_step, next_step } = useWizard();

  // Get current step info
  const current_index = WIZARD_STEPS.findIndex(s => s.id === state.current_step);
  const is_first_step = current_index === 0;
  const is_last_step = current_index === WIZARD_STEPS.length - 1;

  const handle_next = async () => {
    if (on_next) {
      await on_next();
    } else {
      next_step();
    }
  };

  return (
    <div className="mb-8">
      {/* Step indicator */}
      <div className="text-sm text-muted-foreground mb-2">
        Step {current_index + 1} of {WIZARD_STEPS.length}
      </div>

      {/* Title and description */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {description && (
          <p className="text-muted-foreground mt-1">{description}</p>
        )}
      </div>

      {/* Navigation buttons (optional, shown at bottom in most cases) */}
      {show_navigation && (
        <div className="flex items-center justify-between">
          {show_back && !is_first_step ? (
            <Button
              variant="ghost"
              onClick={prev_step}
              disabled={is_loading}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
          ) : (
            <div />
          )}

          {show_next && !is_last_step && (
            <Button
              onClick={handle_next}
              disabled={next_disabled || is_loading}
            >
              {is_loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  {next_label}
                  <ChevronRight className="h-4 w-4 ml-1" />
                </>
              )}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

interface WizardFooterProps {
  show_back?: boolean;
  show_next?: boolean;
  next_label?: string;
  on_next?: () => void | Promise<void>;
  next_disabled?: boolean;
  is_loading?: boolean;
}

export function WizardFooter({
  show_back = true,
  show_next = true,
  next_label = "Continue",
  on_next,
  next_disabled = false,
  is_loading = false,
}: WizardFooterProps) {
  const { state, prev_step, next_step } = useWizard();

  const current_index = WIZARD_STEPS.findIndex(s => s.id === state.current_step);
  const is_first_step = current_index === 0;
  const is_last_step = current_index === WIZARD_STEPS.length - 1;

  const handle_next = async () => {
    if (on_next) {
      await on_next();
    } else {
      next_step();
    }
  };

  return (
    <div className="flex items-center justify-between mt-8 pt-6 border-t">
      {show_back && !is_first_step ? (
        <Button
          variant="outline"
          onClick={prev_step}
          disabled={is_loading}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back
        </Button>
      ) : (
        <div />
      )}

      {show_next && (
        <Button
          onClick={handle_next}
          disabled={next_disabled || is_loading}
          size="lg"
        >
          {is_loading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              {is_last_step ? "Complete" : next_label}
              {!is_last_step && <ChevronRight className="h-4 w-4 ml-1" />}
            </>
          )}
        </Button>
      )}
    </div>
  );
}
