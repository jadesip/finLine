"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, Loader2, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { useWizard } from "@/contexts/wizard-context";

const ACCEPTED_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/jpg",
];

const MAX_SIZE_MB = 50;

export default function UploadPage() {
  const router = useRouter();
  const { state, upload_and_extract, next_step, mark_step_visited } = useWizard();
  const [file, set_file] = useState<File | null>(null);
  const [drag_active, set_drag_active] = useState(false);
  const [validation_error, set_validation_error] = useState<string | null>(null);

  // Mark step as visited on mount
  useEffect(() => {
    mark_step_visited("upload");
  }, [mark_step_visited]);

  // Redirect if no project
  useEffect(() => {
    if (!state.project_id) {
      router.push("/project-wizard/type");
    }
  }, [state.project_id, router]);

  const validate_file = (file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return "Please upload a PDF or image file (PNG, JPG)";
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File is too large. Maximum size is ${MAX_SIZE_MB}MB`;
    }
    return null;
  };

  const handle_file_select = (selected_file: File) => {
    const error = validate_file(selected_file);
    if (error) {
      set_validation_error(error);
      return;
    }
    set_validation_error(null);
    set_file(selected_file);
  };

  const handle_drag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      set_drag_active(true);
    } else if (e.type === "dragleave") {
      set_drag_active(false);
    }
  }, []);

  const handle_drop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    set_drag_active(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handle_file_select(e.dataTransfer.files[0]);
    }
  }, []);

  const handle_input_change = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handle_file_select(e.target.files[0]);
    }
  };

  const handle_upload = async () => {
    if (!file) return;

    try {
      await upload_and_extract(file);
      // On success, the extraction will complete and we navigate
      router.push("/project-wizard/company");
    } catch (err) {
      // Error is handled in context
    }
  };

  const is_extracting = state.extraction_status === "uploading" || state.extraction_status === "extracting";
  const is_completed = state.extraction_status === "completed";
  const is_failed = state.extraction_status === "failed";

  return (
    <div className="py-8">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          Upload company information and financials
        </h1>
        <p className="text-muted-foreground">
          Upload a PDF file or image for information extraction
        </p>
      </div>

      {/* Upload Card */}
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Document Upload</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Extraction in progress */}
          {is_extracting && (
            <div className="space-y-4">
              <div className="flex items-center justify-center py-8">
                <div className="text-center">
                  <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
                  <p className="font-medium">{state.extraction_message || "Processing..."}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    This may take a few moments
                  </p>
                </div>
              </div>
              <Progress value={state.extraction_progress} className="h-2" />
              <p className="text-xs text-center text-muted-foreground">
                {Math.round(state.extraction_progress)}% complete
              </p>
            </div>
          )}

          {/* Extraction completed */}
          {is_completed && (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <p className="font-medium text-green-700">Extraction complete!</p>
              <p className="text-sm text-muted-foreground mt-1">
                Redirecting to review...
              </p>
            </div>
          )}

          {/* Extraction failed */}
          {is_failed && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {state.extraction_message || "Extraction failed. Please try again."}
              </AlertDescription>
            </Alert>
          )}

          {/* Upload dropzone (shown when not extracting) */}
          {!is_extracting && !is_completed && (
            <>
              <div
                className={cn(
                  "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
                  drag_active && "border-primary bg-primary/5",
                  file && !validation_error && "border-green-500 bg-green-50",
                  validation_error && "border-destructive bg-destructive/5"
                )}
                onDragEnter={handle_drag}
                onDragLeave={handle_drag}
                onDragOver={handle_drag}
                onDrop={handle_drop}
              >
                {file && !validation_error ? (
                  <div className="space-y-2">
                    <FileText className="h-10 w-10 text-green-500 mx-auto" />
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => set_file(null)}
                    >
                      Remove
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Upload className="h-10 w-10 text-muted-foreground mx-auto" />
                    <div>
                      <p className="font-medium">
                        Click to upload or drag and drop
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        PDF, PNG, JPG, JPEG (max {MAX_SIZE_MB}MB)
                      </p>
                    </div>
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <span className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2">
                        Select File
                      </span>
                      <input
                        id="file-upload"
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        className="sr-only"
                        onChange={handle_input_change}
                      />
                    </label>
                  </div>
                )}
              </div>

              {validation_error && (
                <p className="text-sm text-destructive mt-2">{validation_error}</p>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      {!is_extracting && !is_completed && (
        <div className="flex items-center justify-center mt-8 max-w-2xl mx-auto">
          <Button
            size="lg"
            onClick={handle_upload}
            disabled={!file || !!validation_error}
          >
            Upload and Extract
          </Button>
        </div>
      )}
    </div>
  );
}
