import {
  DashboardsUIState,
  InteractionState,
} from "../state/dashboards_ui_store";
import { runUI } from "../state/run_ui_store";

/**
 * ExportSnapshot
 * --------------
 * Pure export representation of the dashboard state.
 * This object is used for:
 * - Export
 * - Save Dashboard
 * - Audit & debugging
 */
export interface ExportSnapshot {
  runId: string;
  dashboardId: string;
  generatedAt: string;

  blueprint: any;

  interaction: {
    globalFilters: Record<string, any>;
    widgetFilters: Record<string, Record<string, any>>;
    sessionFilters: Record<string, any>;
    drillContext: Record<string, any> | null;
    visualTypes: Record<string, string>;
    hiddenWidgets: string[];
  };

  effectiveFilters: {
    global: Record<string, any>;
    widgets: {
      [widgetId: string]: Record<string, any>;
    };
  };
}

/**
 * Merge filters according to precedence:
 *
 * globalFilters
 * → sessionFilters.global
 * → widgetFilters[widgetId]
 * → sessionFilters.widget[widgetId]
 * → drillContext
 */
function computeEffectiveFilters(
  interaction: InteractionState,
  widgetIds: string[]
) {
  const global = {
    ...interaction.globalFilters,
    ...(interaction.sessionFilters.global ?? {}),
    ...(interaction.drillContext ?? {}),
  };

  const widgets: Record<string, Record<string, any>> = {};

  for (const widgetId of widgetIds) {
    widgets[widgetId] = {
      ...global,
      ...(interaction.widgetFilters[widgetId] ?? {}),
      ...(interaction.sessionFilters.widget?.[widgetId] ??
        {}),
    };
  }

  return { global, widgets };
}

/**
 * Create export snapshot
 * ----------------------
 * Pure function.
 */
export function createExportSnapshot(
  dashboardsState: DashboardsUIState
): ExportSnapshot {
  if (
    !dashboardsState.isLoaded ||
    !dashboardsState.blueprint ||
    !dashboardsState.interactionState
  ) {
    throw new Error(
      "Dashboard state not ready for export"
    );
  }

  const runId = runUI.getSnapshot().activeRunId;
  if (!runId) {
    throw new Error("No active run selected");
  }

  const { blueprint, interactionState } = dashboardsState;

  const widgetIds = blueprint.widgets.map(
    (w) => w.widgetId
  );

  const effectiveFilters = computeEffectiveFilters(
    interactionState,
    widgetIds
  );

  return {
    runId,
    dashboardId: blueprint.dashboardId,
    generatedAt: new Date().toISOString(),

    blueprint,

    interaction: {
      globalFilters: interactionState.globalFilters,
      widgetFilters: interactionState.widgetFilters,
      sessionFilters: interactionState.sessionFilters,
      drillContext: interactionState.drillContext,
      visualTypes: interactionState.visualTypes,
      hiddenWidgets: Array.from(
        interactionState.hiddenWidgets
      ),
    },

    effectiveFilters,
  };
}