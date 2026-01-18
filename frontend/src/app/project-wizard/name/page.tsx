"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useWizard } from "@/contexts/wizard-context";

export default function ProjectNamePage() {
  const router = useRouter();
  const { state, create_project, set_project_name, mark_step_visited } = useWizard();
  const [name, set_name] = useState(state.project_name || "");
  const [is_creating, set_is_creating] = useState(false);
  const [error, set_error] = useState<string | null>(null);

  // Mark step as visited on mount
  useEffect(() => {
    mark_step_visited("name");
  }, [mark_step_visited]);

  // Redirect to type selection if no type selected
  useEffect(() => {
    if (!state.project_type) {
      router.push("/project-wizard/type");
    }
  }, [state.project_type, router]);

  const handle_continue = async () => {
    if (!name.trim()) {
      set_error("Please enter a project name");
      return;
    }

    if (!state.project_type) {
      set_error("Please select a project type first");
      return;
    }

    set_is_creating(true);
    set_error(null);

    try {
      set_project_name(name.trim());
      await create_project(state.project_type, name.trim());
      router.push("/project-wizard/upload");
    } catch (err: any) {
      set_error(err.detail || err.message || "Failed to create project");
    } finally {
      set_is_creating(false);
    }
  };

  const handle_back = () => {
    router.push("/project-wizard/type");
  };

  return (
    <div className="py-8">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          Name your project
        </h1>
        <p className="text-muted-foreground">
          Give your analysis a name to help you identify it later
        </p>
      </div>

      {/* Name Input Card */}
      <Card className="max-w-xl mx-auto">
        <CardHeader>
          <CardTitle>Project Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="project-name">Project Name *</Label>
            <Input
              id="project-name"
              placeholder="e.g., Acme Corp LBO Analysis"
              value={name}
              onChange={(e) => {
                set_name(e.target.value);
                set_error(null);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && name.trim()) {
                  handle_continue();
                }
              }}
              disabled={is_creating}
              autoFocus
            />
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>

          <p className="text-xs text-muted-foreground">
            You can always rename your project later from the dashboard.
          </p>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-8 max-w-xl mx-auto">
        <Button
          variant="outline"
          onClick={handle_back}
          disabled={is_creating}
        >
          Back
        </Button>

        <Button
          size="lg"
          onClick={handle_continue}
          disabled={!name.trim() || is_creating}
        >
          {is_creating ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Creating...
            </>
          ) : (
            "Continue"
          )}
        </Button>
      </div>
    </div>
  );
}
