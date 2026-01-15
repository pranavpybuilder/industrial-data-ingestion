// src/state/run_ui_store.ts
export interface RunUIState {
  activeRunId: string | null;
}

class RunUIStore {
  private state: RunUIState = {
    activeRunId: null,
  };

  private listeners = new Set<() => void>();

  /** ✅ STABLE SNAPSHOT */
  getSnapshot = (): RunUIState => this.state;

  /** ✅ STABLE SUBSCRIBE */
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  private emit() {
    this.listeners.forEach((l) => l());
  }

  setActiveRun(runId: string) {
    if (this.state.activeRunId === runId) return; // 🛑 GUARD
    this.state = { activeRunId: runId };
    this.emit();
  }

  clearRun() {
    if (this.state.activeRunId === null) return; // 🛑 GUARD
    this.state = { activeRunId: null };
    this.emit();
  }
}

export const runUI = new RunUIStore();