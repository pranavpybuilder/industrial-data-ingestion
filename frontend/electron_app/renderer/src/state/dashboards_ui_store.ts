/**
 * Dashboards UI Store
 * -------------------
 * Single source of truth for dashboard interaction state.
 * Supports:
 * - Filters
 * - Visualization state
 * - Undo / Redo
 * - Persistence (frontend)
 */

export type FilterMap = Record<string, any>;

export interface InteractionState {
  globalFilters: FilterMap;
  widgetFilters: {
    [widgetId: string]: FilterMap;
  };
  sessionFilters: {
    global?: FilterMap;
    widget?: {
      [widgetId: string]: FilterMap;
    };
  };
  drillContext: FilterMap | null;
  visualTypes: {
    [widgetId: string]: string;
  };
  hiddenWidgets: Set<string>;
}

export interface DashboardBlueprint {
  dashboardId: string;
  title: string;
  widgets: Array<{
    widgetId: string;
    widgetType: "chart" | "metric" | "map" | "text" | "image";
    allowedVisualTypes?: string[];
  }>;
}

export interface DashboardsUIState {
  isLoaded: boolean;
  dashboardCount: number;
  blueprint: DashboardBlueprint | null;
  interactionState: InteractionState | null;
  undoStack: InteractionState[];
  redoStack: InteractionState[];
}

type Listener = () => void;

class DashboardsUIStore {
  private listeners = new Set<Listener>();

  private state: DashboardsUIState = {
    isLoaded: false,
    dashboardCount: 0,
    blueprint: null,
    interactionState: null,
    undoStack: [],
    redoStack: [],
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
    return {
      ...this.state,
      interactionState: this.state.interactionState
        ? {
            ...this.state.interactionState,
            hiddenWidgets: new Set(
              this.state.interactionState.hiddenWidgets
            ),
          }
        : null,
    };
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
      interactionState: {
        globalFilters: {},
        widgetFilters: {},
        sessionFilters: {},
        drillContext: null,
        visualTypes: {},
        hiddenWidgets: new Set(),
      },
      undoStack: [],
      redoStack: [],
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
    };
    this.emit();
  }

  /* ---------- Interaction ---------- */

  updateInteraction(
    updater: (prev: InteractionState) => InteractionState
  ): void {
    if (!this.state.interactionState) return;

    this.state.undoStack.push(
      structuredClone(this.state.interactionState)
    );
    this.state.redoStack = [];

    this.state.interactionState = updater(
      this.state.interactionState
    );

    this.emit();
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

  saveDashboard(): InteractionState | null {
    if (!this.state.interactionState) return null;
    return structuredClone(this.state.interactionState);
  }

  loadDashboard(saved: InteractionState): void {
    this.state.interactionState = structuredClone(saved);
    this.state.undoStack = [];
    this.state.redoStack = [];
    this.emit();
  }
}

/* ---------- Public API ---------- */

const store = new DashboardsUIStore();

export const dashboardsUI = {
  subscribe: (l: Listener) => store.subscribe(l),
  getState: () => store.getState(),

  initialize: (
    blueprint: DashboardBlueprint,
    count: number
  ) => store.initialize(blueprint, count),

  updateInteraction: (
    updater: (prev: InteractionState) => InteractionState
  ) => store.updateInteraction(updater),

  undo: () => store.undo(),
  redo: () => store.redo(),
  reset: () => store.reset(),

  save: () => store.saveDashboard(),
  load: (state: InteractionState) =>
    store.loadDashboard(state),
};