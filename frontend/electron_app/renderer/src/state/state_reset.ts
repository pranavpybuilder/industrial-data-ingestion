// src/state/state_reset.ts

import { runUI } from "./run_ui_store";
import { dashboardsUI } from "./dashboards_ui_store";

/**
 * Centralized handler for run changes.
 * This is the ONLY place where cross-state side effects are allowed.
 */
export function onRunChange(runId: string) {
  // ---------- CLEAR RUN ----------
  if (!runId) {
    runUI.clearRun();
    dashboardsUI.reset();
    return;
  }

  // ---------- SET ACTIVE RUN ----------
  runUI.setActiveRun(runId);

  // ---------- RESET DASHBOARD STATE ----------
  dashboardsUI.reset();

  // ---------- INITIALIZE DASHBOARD FOR THIS RUN ----------
  dashboardsUI.initialize(
    {
      dashboardId: `dashboard_${runId}`,
      title: "Maintenance Overview",
      widgets: [
        {
          widgetId: "downtime_trend",
          widgetType: "chart",
          allowedVisualTypes: ["line", "bar"],
        },
        {
          widgetId: "mttr_metric",
          widgetType: "metric",
        },
        {
          widgetId: "equipment_map",
          widgetType: "map",
        },
        {
          widgetId: "analysis_note",
          widgetType: "text",
        },
      ],
    },
    1
  );
}