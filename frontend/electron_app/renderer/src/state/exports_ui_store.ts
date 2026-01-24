/**
 * Exports UI Store
 * ----------------
 * Frontend contract for export operations.
 * Backend-ready.
 */

import type { InteractionState } from "./dashboards_ui_store";

export type ExportScope =
  | "insights"
  | "dashboard"
  | "both";

export type ExportFormat =
  | "pdf"
  | "excel";

export interface ExportRequest {
  runId: string;
  scope: ExportScope;
  format: ExportFormat;
  dashboardState?: InteractionState | null;
}

class ExportsUIStore {
  export(request: ExportRequest): Promise<void> {
    // FRONTEND MOCK (Electron-safe)
    return new Promise((resolve) => {
      console.log("EXPORT REQUEST", request);

      // Later:
      // - Call IPC
      // - Generate PDF / Excel
      // - Ask file save location

      setTimeout(() => {
        alert(
          `Export successful\n\nRun: ${request.runId}\nScope: ${request.scope}\nFormat: ${request.format}`
        );
        resolve();
      }, 500);
    });
  }
}

export const exportsUI = new ExportsUIStore();
