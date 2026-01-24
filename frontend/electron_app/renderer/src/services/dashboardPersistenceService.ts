/**
 * Dashboard Persistence Service
 * -----------------------------
 * Frontend-safe storage for saved dashboards
 * Scoped per active run
 */

import type { InteractionState } from "../state/dashboards_ui_store";

const STORAGE_PREFIX = "offline_dashboard_";

export function saveDashboardForRun(
  runId: string,
  state: InteractionState
) {
  localStorage.setItem(
    `${STORAGE_PREFIX}${runId}`,
    JSON.stringify(state)
  );
}

export function loadDashboardForRun(
  runId: string
): InteractionState | null {
  const raw = localStorage.getItem(`${STORAGE_PREFIX}${runId}`);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as InteractionState;
  } catch {
    return null;
  }
}

export function clearDashboardForRun(runId: string) {
  localStorage.removeItem(`${STORAGE_PREFIX}${runId}`);
}