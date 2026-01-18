"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Code } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Only show in development mode
const IS_DEV = process.env.NODE_ENV === "development";

interface ProjectJsonViewerProps {
  data: any;
  title?: string;
}

/**
 * Debug component to view raw project JSON data.
 * Only renders in development mode.
 */
export function ProjectJsonViewer({ data, title = "Debug: Raw Project Data" }: ProjectJsonViewerProps) {
  const [is_expanded, set_is_expanded] = useState(false);

  // Don't render in production
  if (!IS_DEV) {
    return null;
  }

  return (
    <Card className="border-dashed border-orange-300 bg-orange-50/30">
      <CardHeader
        className="cursor-pointer py-3"
        onClick={() => set_is_expanded(!is_expanded)}
      >
        <div className="flex items-center gap-2">
          <Code className="h-4 w-4 text-orange-500" />
          <CardTitle className="text-sm text-orange-600">{title}</CardTitle>
          {is_expanded ? (
            <ChevronUp className="h-4 w-4 text-orange-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-orange-500" />
          )}
        </div>
      </CardHeader>
      {is_expanded && (
        <CardContent className="pt-0">
          <pre className="text-xs bg-slate-900 text-slate-100 p-4 rounded-lg overflow-auto max-h-[500px]">
            {JSON.stringify(data, null, 2)}
          </pre>
        </CardContent>
      )}
    </Card>
  );
}
