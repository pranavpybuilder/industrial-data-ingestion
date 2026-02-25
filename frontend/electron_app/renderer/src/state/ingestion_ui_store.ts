export type IngestionStatus =
  | "idle"
  | "uploading"
  | "success"
  | "failed";

export interface IngestionUIState {
  status: IngestionStatus;
  selectedFile: string | null;
  errorMessage?: string;
}

class IngestionUIStore {
  private state: IngestionUIState = {
    status: "idle",
    selectedFile: null,
  };

  private listeners = new Set<() => void>();

  /* ---------- STORE API ---------- */

  getSnapshot = (): IngestionUIState => this.state;

  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  private emit() {
    this.listeners.forEach((l) => l());
  }

  /* ---------- ACTIONS ---------- */

  startIngestion(fileName: string) {
    this.state = {
      status: "uploading",
      selectedFile: fileName,
      errorMessage: undefined,
    };
    this.emit();
  }

  markSuccess(fileName: string) {
    this.state = {
      status: "success",
      selectedFile: fileName,
      errorMessage: undefined,
    };
    this.emit();
  }

  failIngestion(message: string) {
    this.state = {
      status: "failed",
      selectedFile: null,
      errorMessage: message,
    };
    this.emit();
  }

  reset() {
    this.state = {
      status: "idle",
      selectedFile: null,
    };
    this.emit();
  }
}

export const ingestionUIStore = new IngestionUIStore();

export const ingestionUI = {
  subscribe: ingestionUIStore.subscribe,
  getSnapshot: ingestionUIStore.getSnapshot,
  startIngestion: (file: string) =>
    ingestionUIStore.startIngestion(file),
  markSuccess: (file: string) =>
    ingestionUIStore.markSuccess(file),
  failIngestion: (msg: string) =>
    ingestionUIStore.failIngestion(msg),
  reset: () => ingestionUIStore.reset(),
};
