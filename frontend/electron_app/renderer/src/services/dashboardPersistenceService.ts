/**
 * Dashboard Persistence Service
 * -----------------------------
 * Frontend-safe localStorage persistence for dashboard interaction state.
 * Scoped per active run ID.
 *
 * FIXES vs previous version:
 * - hiddenWidgets (Set) was silently dropped by JSON.stringify.
 *   Now explicitly serialized as string[] and restored correctly.
 * - Added schema version so stale saved states don't corrupt new loads.
 * - Added clearAll() for dev/debug resets.
 * - Wrapped all localStorage access in try/catch — localStorage can
 *   throw in Electron if storage is full or in private contexts.
 */

import type { InteractionState } from "../state/dashboards_ui_store";

// ─── Constants ────────────────────────────────────────────────────────────────

const STORAGE_PREFIX = "offline_dashboard_";

/**
 * Bump this when InteractionState shape changes in a breaking way.
 * If the saved version doesn't match, the load is discarded gracefully.
 */
const SCHEMA_VERSION = 2;

// ─── Serialization shape ──────────────────────────────────────────────────────

/**
 * What actually gets written to localStorage.
 * hiddenWidgets is stored as string[] (not Set) for JSON compatibility.
 */
interface PersistedState {
  schemaVersion: number;
  savedAt: string;           // ISO timestamp
  state: SerializedInteractionState;
}

/**
 * InteractionState with Set<string> replaced by string[]
 * so JSON.stringify/parse works correctly.
 */
type SerializedInteractionState = Omit<InteractionState, "hiddenWidgets"> & {
  hiddenWidgets: string[];
};

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Save the current interaction state for a run.
 *
 * Converts hiddenWidgets (string[] in new store, legacy Set in old)
 * to a plain array before serializing.
 */
export function saveDashboardForRun(
  runId: string,
  state: InteractionState
): void {
  try {
    // Normalize hiddenWidgets — handle both array (new) and Set (legacy)
    const hiddenWidgets = Array.isArray(state.hiddenWidgets)
      ? state.hiddenWidgets
      : Array.from(state.hiddenWidgets as unknown as Set<string>);

    const serialized: SerializedInteractionState = {
      ...state,
      hiddenWidgets,
    };

    const payload: PersistedState = {
      schemaVersion: SCHEMA_VERSION,
      savedAt: new Date().toISOString(),
      state: serialized,
    };

    localStorage.setItem(
      storageKey(runId),
      JSON.stringify(payload)
    );
  } catch (err) {
    console.warn(`[DashboardPersistence] Failed to save for run "${runId}":`, err);
  }
}

/**
 * Load a previously saved interaction state for a run.
 *
 * Returns null if:
 * - Nothing saved for this run
 * - Saved data is corrupt / unparseable
 * - Schema version mismatch (stale data)
 *
 * Restores hiddenWidgets as string[] (compatible with new store).
 */
export function loadDashboardForRun(
  runId: string
): InteractionState | null {
  try {
    const raw = localStorage.getItem(storageKey(runId));
    if (!raw) return null;

    const payload = JSON.parse(raw) as PersistedState;

    // Schema version check — discard stale saved states
    if (payload.schemaVersion !== SCHEMA_VERSION) {
      console.info(
        `[DashboardPersistence] Schema mismatch for run "${runId}" ` +
        `(saved v${payload.schemaVersion}, current v${SCHEMA_VERSION}). Discarding.`
      );
      clearDashboardForRun(runId);
      return null;
    }

    const saved = payload.state;

    // Ensure hiddenWidgets is always a plain array regardless of what was saved
    const hiddenWidgets = Array.isArray(saved.hiddenWidgets)
      ? saved.hiddenWidgets
      : [];

    const restored: InteractionState = {
      timeGranularity: saved.timeGranularity ?? "day",
      globalFilters: saved.globalFilters ?? {},
      widgetFilters: saved.widgetFilters ?? {},
      sessionFilters: saved.sessionFilters ?? {},
      drillContext: saved.drillContext ?? null,
      visualTypes: saved.visualTypes ?? {},
      hiddenWidgets,
    };

    return restored;
  } catch (err) {
    console.warn(`[DashboardPersistence] Failed to load for run "${runId}":`, err);
    return null;
  }
}

/**
 * Delete the saved state for a specific run.
 */
export function clearDashboardForRun(runId: string): void {
  try {
    localStorage.removeItem(storageKey(runId));
  } catch (err) {
    console.warn(`[DashboardPersistence] Failed to clear run "${runId}":`, err);
  }
}

/**
 * Get metadata about a saved state without fully deserializing it.
 * Useful for showing "Last saved at ..." in the UI.
 */
export function getSavedMeta(
  runId: string
): { savedAt: string; schemaVersion: number } | null {
  try {
    const raw = localStorage.getItem(storageKey(runId));
    if (!raw) return null;
    const payload = JSON.parse(raw) as PersistedState;
    return {
      savedAt: payload.savedAt,
      schemaVersion: payload.schemaVersion,
    };
  } catch {
    return null;
  }
}

/**
 * List all run IDs that have saved dashboard states.
 * Useful for a "restore previous session" feature.
 */
export function listSavedRunIds(): string[] {
  try {
    const ids: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(STORAGE_PREFIX)) {
        ids.push(key.slice(STORAGE_PREFIX.length));
      }
    }
    return ids;
  } catch {
    return [];
  }
}

/**
 * Clear ALL saved dashboard states.
 * Use for dev resets or a "clear all data" settings option.
 */
export function clearAllDashboards(): void {
  try {
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(STORAGE_PREFIX)) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach((key) => localStorage.removeItem(key));
  } catch (err) {
    console.warn("[DashboardPersistence] Failed to clear all dashboards:", err);
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function storageKey(runId: string): string {
  return `${STORAGE_PREFIX}${runId}`;
}