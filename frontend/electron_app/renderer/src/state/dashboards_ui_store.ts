/**
 * Dashboards UI Store
 * -------------------
 * Reactive, undo/redo capable, run-scoped dashboard state.
 */

export type TimeGranularity = "day" | "month" | "year";

export interface InteractionState {
  timeGranularity: TimeGranularity;
  slicers: Record<string, string | string[]>;
  visualTypes: Record<string, string>;
  hiddenWidgets: Set<string>;
  drillContext: Record<string, unknown> | null;
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

  /* ---------------- subscriptions ---------------- */

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private emit(): void {
    this.listeners.forEach((l) => l());
  }

  /* ---------------- getters ---------------- */

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

  /* ---------------- lifecycle ---------------- */

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
        timeGranularity: "month",
        slicers: {},
        visualTypes: {},
        hiddenWidgets: new Set(),
        drillContext: null,
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

  /* ---------------- interaction ---------------- */

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

  /* ---------------- undo / redo ---------------- */

  undo(): void {
    if (
      this.state.undoStack.length === 0 ||
      !this.state.interactionState
    )
      return;

    const previous = this.state.undoStack.pop()!;
    this.state.redoStack.push(
      structuredClone(this.state.interactionState)
    );

    this.state.interactionState = previous;
    this.emit();
  }

  redo(): void {
    if (
      this.state.redoStack.length === 0 ||
      !this.state.interactionState
    )
      return;

    const next = this.state.redoStack.pop()!;
    this.state.undoStack.push(
      structuredClone(this.state.interactionState)
    );

    this.state.interactionState = next;
    this.emit();
  }
}

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
  redo: () => store.redo(), // ✅ ADDED
  reset: () => store.reset(),
};