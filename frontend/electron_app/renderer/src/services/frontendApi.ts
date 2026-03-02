export interface RunMeta {
  run_id: string;
  run_name?: string;
  source_type?: string;
  status?: string;
  created_at?: string;
  failed_step?: string;
  error_message?: string;
}

export interface UploadResult {
  success: boolean;
  data?: any;
  message: string;
}

export interface IPCResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface ExportRecord {
  export_id: string;
  export_type: string;
  scope: string;
  file_path: string;
  created_at: string;
  file_exists?: boolean;
}

const hasBridge = (): boolean =>
  typeof window !== "undefined" &&
  typeof window.frontendAPI !== "undefined";

const waitForBridge = (): Promise<void> => {
  return new Promise((resolve) => {
    if (hasBridge()) {
      resolve();
      return;
    }

    if (typeof window === "undefined") {
      resolve();
      return;
    }

    const onReady = () => {
      window.removeEventListener("qt-ready", onReady);
      resolve();
    };

    window.addEventListener("qt-ready", onReady);
    setTimeout(() => {
      window.removeEventListener("qt-ready", onReady);
      resolve();
    }, 5000);
  });
};

const invokeBridge = async <T = any>(
  method: keyof NonNullable<typeof window.frontendAPI>,
  ...args: any[]
): Promise<T> => {
  await waitForBridge();
  if (!hasBridge() || !window.frontendAPI) {
    throw new Error("Desktop bridge not available");
  }

  return new Promise<T>((resolve, reject) => {
    let settled = false;
    try {
      const callback = (result: T) => {
        settled = true;
        resolve(result);
      };

      const fn: any = (window.frontendAPI as any)[method];
      const maybeReturn = fn(...args, callback);

      if (maybeReturn instanceof Promise) {
        maybeReturn.then((result: T) => {
          if (!settled) {
            settled = true;
            resolve(result);
          }
        }).catch((err: unknown) => {
          if (!settled) {
            settled = true;
            reject(err);
          }
        });
        return;
      }

      if (typeof maybeReturn !== "undefined") {
        settled = true;
        resolve(maybeReturn as T);
        return;
      }

      setTimeout(() => {
        if (!settled) {
          settled = true;
          reject(new Error(`No response from bridge method '${String(method)}'`));
        }
      }, 30000);
    } catch (error) {
      reject(error);
    }
  });
};

export const frontendApi = {
  async selectFile(): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>("select_file");
    } catch (error) {
      return { success: false, message: `File selection failed: ${error}` };
    }
  },

  async selectDirectory(): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>("select_directory");
    } catch (error) {
      return { success: false, message: `Directory selection failed: ${error}` };
    }
  },

  async uploadFile(
    filePath: string,
    sourceType?: string
  ): Promise<UploadResult> {
    try {
      return await invokeBridge<UploadResult>(
        "upload_file",
        filePath,
        sourceType || ""
      );
    } catch (error) {
      return {
        success: false,
        message: `Upload failed: ${error}`,
      };
    }
  },

  async getIngestionStatus(runId: string): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>("get_ingestion_status", runId);
    } catch (error) {
      return {
        success: false,
        message: `Failed to get ingestion status: ${error}`,
      };
    }
  },

  async getRuns(): Promise<RunMeta[]> {
    try {
      const result = await invokeBridge<RunMeta[]>("get_runs");
      return Array.isArray(result) ? result : [];
    } catch (error) {
      console.error("Failed to fetch runs:", error);
      return [];
    }
  },

  async searchRuns(query: string): Promise<RunMeta[]> {
    try {
      const result = await invokeBridge<RunMeta[]>("search_runs", query);
      return Array.isArray(result) ? result : [];
    } catch (error) {
      console.error("Failed to search runs:", error);
      return [];
    }
  },

  async getInsights(runId: string): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>("get_insights", runId);
    } catch (error) {
      return {
        success: false,
        message: `Failed to get insights: ${error}`,
      };
    }
  },

  async getDashboard(runId: string): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>("get_dashboard", runId);
    } catch (error) {
      return {
        success: false,
        message: `Failed to get dashboard: ${error}`,
      };
    }
  },

  async saveDashboardLayout(
    runId: string,
    blueprintId: string,
    userLayout: Record<string, any>
  ): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>(
        "save_dashboard_layout",
        runId,
        blueprintId || "",
        userLayout || {}
      );
    } catch (error) {
      return {
        success: false,
        message: `Failed to save dashboard layout: ${error}`,
      };
    }
  },

  async getDashboardLayout(runId: string): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>("get_dashboard_layout", runId);
    } catch (error) {
      return {
        success: false,
        message: `Failed to load dashboard layout: ${error}`,
      };
    }
  },

  async getDataHealth(runId: string): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>("get_data_health", runId);
    } catch (error) {
      return {
        success: false,
        message: `Failed to get data health: ${error}`,
      };
    }
  },

  // ─────────────────────────────────────────────
  // Export APIs — Legacy
  // ─────────────────────────────────────────────

  async getExports(runId: string): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>("get_exports", runId);
    } catch (error) {
      return {
        success: false,
        message: `Failed to get exports: ${error}`,
      };
    }
  },

  async generateExport(
    runId: string,
    exportType: "excel" | "pdf" | "docx",
    scope: "insights" | "dashboards" | "both",
    outputDir = ""
  ): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>(
        "generate_export",
        runId,
        exportType,
        scope,
        outputDir
      );
    } catch (error) {
      return {
        success: false,
        message: `Failed to generate export: ${error}`,
      };
    }
  },

  // ─────────────────────────────────────────────
  // Export APIs — New 7 handlers
  // ─────────────────────────────────────────────

  async getExportHistory(
    runId: string
  ): Promise<IPCResponse<{ exports: ExportRecord[] }>> {
    try {
      return await invokeBridge<IPCResponse<{ exports: ExportRecord[] }>>(
        "get_export_history",
        runId
      );
    } catch (error) {
      return {
        success: false,
        message: `Failed to get export history: ${error}`,
      };
    }
  },

  async exportInsightsDocx(
    runId: string,
    outputDir = ""
  ): Promise<IPCResponse<{ file_path: string }>> {
    try {
      return await invokeBridge<IPCResponse<{ file_path: string }>>(
        "export_insights_docx",
        runId,
        outputDir
      );
    } catch (error) {
      return {
        success: false,
        message: `DOCX export failed: ${error}`,
      };
    }
  },

  async exportInsightsPdf(
    runId: string,
    outputDir = ""
  ): Promise<IPCResponse<{ file_path: string }>> {
    try {
      return await invokeBridge<IPCResponse<{ file_path: string }>>(
        "export_insights_pdf",
        runId,
        outputDir
      );
    } catch (error) {
      return {
        success: false,
        message: `PDF export failed: ${error}`,
      };
    }
  },

  async exportDashboardPdf(
    runId: string,
    imageDataBase64: string,
    outputDir = ""
  ): Promise<IPCResponse<{ file_path: string }>> {
    try {
      return await invokeBridge<IPCResponse<{ file_path: string }>>(
        "export_dashboard_pdf",
        runId,
        imageDataBase64,
        outputDir
      );
    } catch (error) {
      return {
        success: false,
        message: `Dashboard PDF export failed: ${error}`,
      };
    }
  },

  async exportDashboardJson(
    runId: string,
    outputDir = ""
  ): Promise<IPCResponse<{ file_path: string }>> {
    try {
      return await invokeBridge<IPCResponse<{ file_path: string }>>(
        "export_dashboard_json",
        runId,
        outputDir
      );
    } catch (error) {
      return {
        success: false,
        message: `Dashboard JSON export failed: ${error}`,
      };
    }
  },

  async exportFullReport(
    runId: string,
    imageDataBase64: string,
    outputDir = ""
  ): Promise<IPCResponse<{ file_path: string }>> {
    try {
      return await invokeBridge<IPCResponse<{ file_path: string }>>(
        "export_full_report",
        runId,
        imageDataBase64,
        outputDir
      );
    } catch (error) {
      return {
        success: false,
        message: `Full report export failed: ${error}`,
      };
    }
  },

  async openExportFile(
    filePath: string
  ): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>(
        "open_export_file",
        filePath
      );
    } catch (error) {
      return {
        success: false,
        message: `Failed to open file: ${error}`,
      };
    }
  },

  // ─────────────────────────────────────────────
  // Explorer
  // ─────────────────────────────────────────────

  async getExplorerData(runId: string, limit = 500): Promise<IPCResponse> {
    try {
      return await invokeBridge<IPCResponse>(
        "get_explorer_data",
        runId,
        limit
      );
    } catch (error) {
      return {
        success: false,
        message: `Failed to load explorer data: ${error}`,
      };
    }
  },
};
