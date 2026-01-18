"use client";

import React, { createContext, useContext, useReducer, useCallback, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api, ProjectResponse, ProjectData } from "@/lib/api";
import {
  WizardStepId,
  WIZARD_STEPS,
  ExtractionStatus,
  ProjectType,
  FinancialsValidation
} from "@/types/wizard";
import { set_nested_value } from "@/lib/utils";

// ============================================================
// State Types
// ============================================================

interface WizardState {
  // Project data
  project_id: string | null;
  project_data: ProjectData | null;
  project_name: string;
  project_type: ProjectType | null;

  // Navigation
  current_step: WizardStepId;
  visited_steps: WizardStepId[];

  // Extraction
  extraction_id: string | null;
  extraction_status: ExtractionStatus;
  extraction_progress: number;
  extraction_message: string;

  // Validation
  financials_validation: FinancialsValidation;

  // UI State
  is_loading: boolean;
  is_saving: boolean;
  error: string | null;
}

type WizardAction =
  | { type: "SET_PROJECT"; payload: { id: string; data: ProjectData; name: string } }
  | { type: "SET_PROJECT_TYPE"; payload: ProjectType }
  | { type: "SET_PROJECT_NAME"; payload: string }
  | { type: "UPDATE_PROJECT_DATA"; payload: ProjectData }
  | { type: "SET_CURRENT_STEP"; payload: WizardStepId }
  | { type: "MARK_STEP_VISITED"; payload: WizardStepId }
  | { type: "SET_EXTRACTION_STATUS"; payload: { status: ExtractionStatus; progress?: number; message?: string; id?: string } }
  | { type: "SET_VALIDATION"; payload: { metric: string; year: string; validated: boolean } }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_SAVING"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null }
  | { type: "RESET" };

// ============================================================
// Initial State & Reducer
// ============================================================

const initial_state: WizardState = {
  project_id: null,
  project_data: null,
  project_name: "",
  project_type: null,
  current_step: "type",
  visited_steps: [],
  extraction_id: null,
  extraction_status: "idle",
  extraction_progress: 0,
  extraction_message: "",
  financials_validation: {},
  is_loading: false,
  is_saving: false,
  error: null,
};

function wizard_reducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case "SET_PROJECT":
      return {
        ...state,
        project_id: action.payload.id,
        project_data: action.payload.data,
        project_name: action.payload.name,
        is_loading: false,
        error: null,
      };

    case "SET_PROJECT_TYPE":
      return {
        ...state,
        project_type: action.payload,
      };

    case "SET_PROJECT_NAME":
      return {
        ...state,
        project_name: action.payload,
      };

    case "UPDATE_PROJECT_DATA":
      return {
        ...state,
        project_data: action.payload,
        is_saving: false,
      };

    case "SET_CURRENT_STEP":
      return {
        ...state,
        current_step: action.payload,
      };

    case "MARK_STEP_VISITED":
      if (state.visited_steps.includes(action.payload)) {
        return state;
      }
      return {
        ...state,
        visited_steps: [...state.visited_steps, action.payload],
      };

    case "SET_EXTRACTION_STATUS":
      return {
        ...state,
        extraction_status: action.payload.status,
        extraction_progress: action.payload.progress ?? state.extraction_progress,
        extraction_message: action.payload.message ?? state.extraction_message,
        extraction_id: action.payload.id ?? state.extraction_id,
      };

    case "SET_VALIDATION":
      const { metric, year, validated } = action.payload;
      return {
        ...state,
        financials_validation: {
          ...state.financials_validation,
          [metric]: {
            ...state.financials_validation[metric],
            [year]: validated,
          },
        },
      };

    case "SET_LOADING":
      return {
        ...state,
        is_loading: action.payload,
      };

    case "SET_SAVING":
      return {
        ...state,
        is_saving: action.payload,
      };

    case "SET_ERROR":
      return {
        ...state,
        error: action.payload,
        is_loading: false,
        is_saving: false,
      };

    case "RESET":
      return initial_state;

    default:
      return state;
  }
}

// ============================================================
// Context
// ============================================================

interface WizardContextValue {
  state: WizardState;

  // Project actions
  create_project: (type: ProjectType, name: string) => Promise<string>;
  load_project: (project_id: string) => Promise<void>;
  update_field: (path: string, value: any) => Promise<void>;

  // Navigation
  go_to_step: (step_id: WizardStepId) => void;
  next_step: () => void;
  prev_step: () => void;
  can_access_step: (step_id: WizardStepId) => boolean;
  mark_step_visited: (step_id: WizardStepId) => void;

  // Extraction
  upload_and_extract: (file: File) => Promise<void>;

  // Validation
  set_field_validated: (metric: string, year: string, validated: boolean) => void;

  // Misc
  set_project_name: (name: string) => void;
  set_project_type: (type: ProjectType) => void;
  reset: () => void;
}

const WizardContext = createContext<WizardContextValue | null>(null);

// ============================================================
// Provider
// ============================================================

export function WizardProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(wizard_reducer, initial_state);
  const router = useRouter();

  // Create a new project
  const create_project = useCallback(async (type: ProjectType, name: string): Promise<string> => {
    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR", payload: null });

    try {
      // Project name is the project identifier, company_name will be extracted from document
      const project = await api.create_project(name, "", "USD", "millions");

      dispatch({
        type: "SET_PROJECT",
        payload: {
          id: project.id,
          data: project.data,
          name: project.name,
        },
      });

      dispatch({ type: "SET_PROJECT_TYPE", payload: type });
      dispatch({ type: "MARK_STEP_VISITED", payload: "type" });
      dispatch({ type: "MARK_STEP_VISITED", payload: "name" });

      return project.id;
    } catch (error: any) {
      dispatch({ type: "SET_ERROR", payload: error.detail || "Failed to create project" });
      throw error;
    }
  }, []);

  // Load an existing project
  const load_project = useCallback(async (project_id: string): Promise<void> => {
    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR", payload: null });

    try {
      const project = await api.get_project(project_id);

      dispatch({
        type: "SET_PROJECT",
        payload: {
          id: project.id,
          data: project.data,
          name: project.name,
        },
      });
    } catch (error: any) {
      dispatch({ type: "SET_ERROR", payload: error.detail || "Failed to load project" });
      throw error;
    }
  }, []);

  // Update a field in the project
  const update_field = useCallback(async (path: string, value: any): Promise<void> => {
    if (!state.project_id || !state.project_data) return;

    // Optimistic update
    const updated_data = set_nested_value(state.project_data, path, value);
    dispatch({ type: "UPDATE_PROJECT_DATA", payload: updated_data });
    dispatch({ type: "SET_SAVING", payload: true });

    try {
      const updated = await api.update_project(state.project_id, path, value);
      dispatch({ type: "UPDATE_PROJECT_DATA", payload: updated.data });
    } catch (error: any) {
      // Rollback on error
      dispatch({ type: "UPDATE_PROJECT_DATA", payload: state.project_data });
      dispatch({ type: "SET_ERROR", payload: error.detail || "Failed to save" });
    }
  }, [state.project_id, state.project_data]);

  // Navigation
  const go_to_step = useCallback((step_id: WizardStepId) => {
    const step = WIZARD_STEPS.find(s => s.id === step_id);
    if (step) {
      dispatch({ type: "SET_CURRENT_STEP", payload: step_id });
      router.push(step.path);
    }
  }, [router]);

  const next_step = useCallback(() => {
    const current_index = WIZARD_STEPS.findIndex(s => s.id === state.current_step);
    if (current_index < WIZARD_STEPS.length - 1) {
      const next = WIZARD_STEPS[current_index + 1];
      dispatch({ type: "MARK_STEP_VISITED", payload: state.current_step });
      dispatch({ type: "SET_CURRENT_STEP", payload: next.id });
      router.push(next.path);
    }
  }, [state.current_step, router]);

  const prev_step = useCallback(() => {
    const current_index = WIZARD_STEPS.findIndex(s => s.id === state.current_step);
    if (current_index > 0) {
      const prev = WIZARD_STEPS[current_index - 1];
      dispatch({ type: "SET_CURRENT_STEP", payload: prev.id });
      router.push(prev.path);
    }
  }, [state.current_step, router]);

  const can_access_step = useCallback((step_id: WizardStepId): boolean => {
    // First two steps (type, name) are always accessible once started
    if (step_id === "type" || step_id === "name") {
      return true;
    }

    // Other steps require project to exist
    if (!state.project_id) {
      return false;
    }

    // Can access if already visited or is next unvisited step
    if (state.visited_steps.includes(step_id)) {
      return true;
    }

    const step_index = WIZARD_STEPS.findIndex(s => s.id === step_id);
    const last_visited_index = state.visited_steps.length > 0
      ? Math.max(...state.visited_steps.map(id => WIZARD_STEPS.findIndex(s => s.id === id)))
      : -1;

    return step_index <= last_visited_index + 1;
  }, [state.project_id, state.visited_steps]);

  // Mark a step as visited (for pages to call on mount)
  const mark_step_visited = useCallback((step_id: WizardStepId) => {
    dispatch({ type: "MARK_STEP_VISITED", payload: step_id });
  }, []);

  // Upload and extract
  const upload_and_extract = useCallback(async (file: File): Promise<void> => {
    if (!state.project_id) {
      dispatch({ type: "SET_ERROR", payload: "No project loaded" });
      return;
    }

    dispatch({ type: "SET_EXTRACTION_STATUS", payload: { status: "uploading", progress: 5, message: "Uploading file..." } });

    try {
      // Upload and start extraction
      const result = await api.upload_and_extract(state.project_id, file);

      dispatch({
        type: "SET_EXTRACTION_STATUS",
        payload: {
          status: "extracting",
          progress: 10,
          message: "Analyzing document...",
          id: result.extraction_id
        }
      });

      // Poll for completion
      let poll_count = 0;
      const max_polls = 300; // 5 minutes max

      while (poll_count < max_polls) {
        const status = await api.get_extraction_status(state.project_id, result.extraction_id);

        if (status.status === "completed") {
          dispatch({
            type: "SET_EXTRACTION_STATUS",
            payload: { status: "completed", progress: 100, message: "Extraction complete!" }
          });

          // Merge the extraction results
          await api.merge_extraction(state.project_id, result.extraction_id, "overlay");

          // Reload project data
          await load_project(state.project_id);

          return;
        }

        if (status.status === "failed") {
          throw new Error(status.message || "Extraction failed");
        }

        // Update progress
        const progress = Math.min(10 + (poll_count / max_polls) * 85, 95);
        let message = "Processing document...";
        if (poll_count > 10) message = "Extracting financial data...";
        if (poll_count > 30) message = "Analyzing business information...";
        if (poll_count > 60) message = "Almost done...";

        dispatch({
          type: "SET_EXTRACTION_STATUS",
          payload: { status: "extracting", progress, message }
        });

        // Adaptive polling delay
        const delay = poll_count < 30 ? 1000 : poll_count < 60 ? 2000 : 3000;
        await new Promise(resolve => setTimeout(resolve, delay));
        poll_count++;
      }

      throw new Error("Extraction timed out");

    } catch (error: any) {
      dispatch({
        type: "SET_EXTRACTION_STATUS",
        payload: { status: "failed", progress: 0, message: error.message || "Extraction failed" }
      });
      dispatch({ type: "SET_ERROR", payload: error.message || "Extraction failed" });
    }
  }, [state.project_id, load_project]);

  // Validation
  const set_field_validated = useCallback((metric: string, year: string, validated: boolean) => {
    dispatch({ type: "SET_VALIDATION", payload: { metric, year, validated } });
  }, []);

  // Setters
  const set_project_name = useCallback((name: string) => {
    dispatch({ type: "SET_PROJECT_NAME", payload: name });
  }, []);

  const set_project_type = useCallback((type: ProjectType) => {
    dispatch({ type: "SET_PROJECT_TYPE", payload: type });
  }, []);

  // Reset
  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  const value: WizardContextValue = {
    state,
    create_project,
    load_project,
    update_field,
    go_to_step,
    next_step,
    prev_step,
    can_access_step,
    mark_step_visited,
    upload_and_extract,
    set_field_validated,
    set_project_name,
    set_project_type,
    reset,
  };

  return (
    <WizardContext.Provider value={value}>
      {children}
    </WizardContext.Provider>
  );
}

// ============================================================
// Hook
// ============================================================

export function useWizard() {
  const context = useContext(WizardContext);
  if (!context) {
    throw new Error("useWizard must be used within a WizardProvider");
  }
  return context;
}
