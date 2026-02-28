/**
 * Dashboards UI Store
 * -------------------
 * Single source of truth for dashboard interaction state.
 * Supports:
 * - Filters
 * - Visualization state
 * - Undo / Redo
 * - Persistence (frontend)
 *
 * FIXES vs previous version:
 * - hiddenWidgets changed from Set<string> → string[]
 *   because Set is NOT structuredClone-safe in older Electron/Node
 *   and silently breaks undo/redo and JSON persistence.
 * - Added lastSaved timestamp for DashboardHeader
 * - Added markSaved() method
 * - getState() no longer wraps hiddenWidgets in new Set()
 *   (consumers use array methods or convert locally if needed)
 */

export type FilterMap = Record<string, any>;

/* =====================================================
   Interaction State (SINGLE SOURCE OF TRUTH)
   ===================================================== */

export interface InteractionState {
  /* 🔹 Time slicing */
  timeGranularity: "day" | "month" | "year";

  /* 🔹 Global filters (e.g., equipment, line, shift) */
  globalFilters: FilterMap;

  /* 🔹 Widget-level filters */
  widgetFilters: {
    [widgetId: string]: FilterMap;
  };

  /* 🔹 Session-only filters */
  sessionFilters: {
    global?: FilterMap;
    widget?: {
      [widgetId: string]: FilterMap;
    };
  };

  /* 🔹 Drill-down context */
  drillContext: FilterMap | null;

  /* 🔹 Visualization overrides */
  visualTypes: {
    [widgetId: string]: string;
  };

  /**
   * Hidden widget IDs stored as a plain string array.
   *
   * WHY NOT Set<string>?
   * - structuredClone() (used by undo/redo) silently drops Set contents
   *   in Electron's older V8 versions, making undo restore empty sets.
   * - JSON.stringify() drops Set entirely, breaking localStorage persistence.
   *
   * Consumers that need Set behavior should do:
   *   const hiddenSet = new Set(interaction.hiddenWidgets);
   */
  hiddenWidgets: string[];
}

/* =====================================================
   Dashboard Blueprint
   ===================================================== */

export interface DashboardBlueprint {
  dashboardId: string;
  title: string;
  widgets: Array<{
    widgetId: string;
    widgetType: "chart" | "metric" | "map" | "text" | "image" | "table";
    title?: string;
    allowedVisualTypes?: string[];
    gridSpan?: number;
    sectionId?: string;
  }>;
  sections?: Array<{
    sectionId: string;
    title: string;
    order: number;
  }>;
}

/* =====================================================
   Store State
   ===================================================== */

export interface DashboardsUIState {
  isLoaded: boolean;
  dashboardCount: number;
  blueprint: DashboardBlueprint | null;
  interactionState: InteractionState | null;
  undoStack: InteractionState[];
  redoStack: InteractionState[];
  /** ISO timestamp of last successful save, or null if never saved */
  lastSaved: string | null;
}

type Listener = () => void;

/* =====================================================
   Default interaction state factory
   ===================================================== */

function defaultInteractionState(): InteractionState {
  return {
    timeGranularity: "day",
    globalFilters: {},
    widgetFilters: {},
    sessionFilters: {},
    drillContext: null,
    visualTypes: {},
    hiddenWidgets: [],   // ← plain array, not Set
  };
}

/* =====================================================
   Store Implementation
   ===================================================== */

class DashboardsUIStore {
  private listeners = new Set<Listener>();

  private state: DashboardsUIState = {
    isLoaded: false,
    dashboardCount: 0,
    blueprint: null,
    interactionState: null,
    undoStack: [],
    redoStack: [],
    lastSaved: null,
  };

  /* ---------- Subscriptions ---------- */

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private emit() {
    this.listeners.forEach((l) => l());
  }

  /* ---------- State Access ---------- */

  getState(): DashboardsUIState {
    // Return a shallow copy — no Set wrapping needed anymore
    return { ...this.state };
  }

  /* ---------- Lifecycle ---------- */

  initialize(
    blueprint: DashboardBlueprint,
    dashboardCount: number
  ): void {
    if (this.state.isLoaded) return;

    this.state = {
      isLoaded: true,
      dashboardCount,
      blueprint,
      interactionState: defaultInteractionState(),
      undoStack: [],
      redoStack: [],
      lastSaved: null,
    };

    this.emit();
  }

  reset(): void {
    this.state = {
      isLoaded: false,
      dashboardCount: 0,
      blueprint: null,
      interactionState: null,
      undoStack: [],
      redoStack: [],
      lastSaved: null,
    };
    this.emit();
  }

  /* ---------- Interaction ---------- */

  updateInteraction(
    updater: (prev: InteractionState) => InteractionState
  ): void {
    if (!this.state.interactionState) return;

    // structuredClone is now safe because hiddenWidgets is string[]
    this.state.undoStack.push(
      structuredClone(this.state.interactionState)
    );

    // Cap undo stack at 50 to prevent unbounded memory growth
    if (this.state.undoStack.length > 50) {
      this.state.undoStack.shift();
    }

    this.state.redoStack = [];
    this.state.interactionState = updater(this.state.interactionState);

    this.emit();
  }

  /* ---------- Hidden Widgets Helpers ---------- */

  /**
   * Toggle a widget's hidden state.
   * Convenience wrapper around updateInteraction.
   */
  toggleHiddenWidget(widgetId: string): void {
    this.updateInteraction((prev) => {
      const isHidden = prev.hiddenWidgets.includes(widgetId);
      return {
        ...prev,
        hiddenWidgets: isHidden
          ? prev.hiddenWidgets.filter((id) => id !== widgetId)
          : [...prev.hiddenWidgets, widgetId],
      };
    });
  }

  /**
   * Check if a widget is currently hidden.
   * Consumers can also check interaction.hiddenWidgets.includes(id) directly.
   */
  isWidgetHidden(widgetId: string): boolean {
    return (
      this.state.interactionState?.hiddenWidgets.includes(widgetId) ?? false
    );
  }

  /* ---------- Undo / Redo ---------- */

  undo(): void {
    if (
      !this.state.interactionState ||
      this.state.undoStack.length === 0
    )
      return;

    const prev = this.state.undoStack.pop()!;
    this.state.redoStack.push(
      structuredClone(this.state.interactionState)
    );
    this.state.interactionState = prev;
    this.emit();
  }

  redo(): void {
    if (
      !this.state.interactionState ||
      this.state.redoStack.length === 0
    )
      return;

    const next = this.state.redoStack.pop()!;
    this.state.undoStack.push(
      structuredClone(this.state.interactionState)
    );
    this.state.interactionState = next;
    this.emit();
  }

  /* ---------- Persistence ---------- */

  /**
   * Returns a plain-object snapshot of interaction state
   * safe for JSON.stringify and localStorage.
   */
  saveDashboard(): InteractionState | null {
    if (!this.state.interactionState) return null;
    return structuredClone(this.state.interactionState);
  }

  /**
   * Restores interaction state from a saved snapshot.
   * Handles both old (Set-serialized) and new (array) formats gracefully.
   */
  loadDashboard(saved: InteractionState): void {
    // Defensive: if somehow a legacy Set was saved, convert it
    const hiddenWidgets = Array.isArray(saved.hiddenWidgets)
      ? saved.hiddenWidgets
      : [];

    this.state.interactionState = {
      ...structuredClone(saved),
      hiddenWidgets,
    };
    this.state.undoStack = [];
    this.state.redoStack = [];
    this.emit();
  }

  /**
   * Mark the current state as saved, recording a timestamp.
   * Call this after a successful API save response.
   */
  markSaved(): void {
    this.state.lastSaved = new Date().toISOString();
    this.emit();
  }

  /**
   * Get the lastSaved timestamp (ISO string or null).
   */
  getLastSaved(): string | null {
    return this.state.lastSaved;
  }
}

/* =====================================================
   Public API
   ===================================================== */

const store = new DashboardsUIStore();

export const dashboardsUI = {
  /* Core */
  subscribe:         (l: Listener) => store.subscribe(l),
  getState:          () => store.getState(),

  /* Lifecycle */
  initialize:        (blueprint: DashboardBlueprint, count: number) =>
                       store.initialize(blueprint, count),
  reset:             () => store.reset(),

  /* Interaction */
  updateInteraction: (updater: (prev: InteractionState) => InteractionState) =>
                       store.updateInteraction(updater),

  /* Hidden widget helpers */
  toggleHiddenWidget: (widgetId: string) => store.toggleHiddenWidget(widgetId),
  isWidgetHidden:     (widgetId: string) => store.isWidgetHidden(widgetId),

  /* Undo / Redo */
  undo:              () => store.undo(),
  redo:              () => store.redo(),

  /* Persistence */
  save:              () => store.saveDashboard(),
  load:              (state: InteractionState) => store.loadDashboard(state),
  markSaved:         () => store.markSaved(),
  getLastSaved:      () => store.getLastSaved(),
};