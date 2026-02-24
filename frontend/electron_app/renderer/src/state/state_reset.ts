// src/state/state_reset.ts

import { runUI } from "./run_ui_store";
import { dashboardsUI } from "./dashboards_ui_store";
import { insightsUI } from "./insights_ui_store";
import { ingestionUI } from "./ingestion_ui_store";
import { clearDashboardForRun } from "../services/dashboardPersistenceService";

/**
 * Centralized handler for run changes.
 * This is the ONLY place where cross-state side effects are allowed.
 */
export function onRunChange(runId: string) {
  const previousRunId = runUI.getSnapshot().activeRunId;
  const normalizedRunId = (runId || "").trim();

  if (previousRunId) {
    clearDashboardForRun(previousRunId);
  }
  resetRunScopedState();

  if (!normalizedRunId) {
    runUI.clearRun();
  } else {
    runUI.setActiveRun(normalizedRunId);
  }
}

export function clearActiveRunContext() {
  const previousRunId = runUI.getSnapshot().activeRunId;
  if (previousRunId) {
    clearDashboardForRun(previousRunId);
  }
  resetRunScopedState();
  runUI.clearRun();
}

function resetRunScopedState() {
  dashboardsUI.reset();
  insightsUI.reset();
  ingestionUI.reset();
}
