export interface RunUIState {
  activeRunId: string | null;
  activeFileName: string | null;
}

class RunUIStore {
  private state: RunUIState = {
    activeRunId: null,
    activeFileName: null,
  };

  private listeners = new Set<() => void>();

  getSnapshot = (): RunUIState => this.state;

  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  private emit() {
    this.listeners.forEach((l) => l());
  }

  setActiveRun(runId: string, fileName?: string) {
    if (this.state.activeRunId === runId && this.state.activeFileName === (fileName ?? null)) return;
    this.state = { activeRunId: runId, activeFileName: fileName ?? null };
    this.emit();
  }

  clearRun() {
    if (this.state.activeRunId === null) return;
    this.state = { activeRunId: null, activeFileName: null };
    this.emit();
  }
}

export const runUI = new RunUIStore();