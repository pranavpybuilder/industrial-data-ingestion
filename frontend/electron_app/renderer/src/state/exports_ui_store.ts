/**
 * Exports UI Store
 * ----------------
 * Frontend contract for export operations.
 * Backend-ready.
 */

import type { InteractionState } from "./dashboards_ui_store";
import { frontendApi } from "../services/frontendApi";

export type ExportScope =
  | "insights"
  | "dashboards"
  | "both";

export type ExportFormat =
  | "pdf"
  | "excel"
  | "docx";

export interface ExportRequest {
  runId: string;
  scope: ExportScope;
  format: ExportFormat;
  dashboardState?: InteractionState | null;
}

class ExportsUIStore {
  async export(request: ExportRequest): Promise<void> {
    const response = await frontendApi.generateExport(
      request.runId,
      request.format,
      request.scope
    );

    if (!response.success) {
      throw new Error(response.message || "Export failed");
    }
  }
}

export const exportsUI = new ExportsUIStore();
