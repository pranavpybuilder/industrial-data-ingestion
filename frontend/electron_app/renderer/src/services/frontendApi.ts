export interface RunMeta {
  run_id: string;
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
}

// Check if running in Electron / desktop mode with Qt bridge
const isDesktop =
  typeof window !== "undefined" &&
  typeof (window as any).frontendAPI !== "undefined";

// Wait for Qt bridge to be ready
const waitForBridge = (): Promise<void> => {
  return new Promise((resolve) => {
    if (isDesktop && (window as any).frontendAPI) {
      resolve();
    } else if (typeof window !== "undefined") {
      window.addEventListener("qt-ready", () => resolve());
      setTimeout(() => resolve(), 2000); // Fallback timeout
    } else {
      resolve();
    }
  });
};

export const frontendApi = {
  // =============================================
  // Ingestion APIs
  // =============================================
  async uploadFile(
    filePath: string,
    sourceType?: string
  ): Promise<UploadResult> {
    await waitForBridge();
    if (isDesktop) {
      try {
        return (window as any).frontendAPI.upload_file(
          filePath,
          sourceType || ""
        );
      } catch (error) {
        return {
          success: false,
          message: `Upload failed: ${error}`,
        };
      }
    }
    return {
      success: false,
      message: "Desktop bridge not available",
    };
  },

  async getIngestionStatus(runId: string): Promise<IPCResponse> {
    await waitForBridge();
    if (isDesktop) {
      try {
        return (window as any).frontendAPI.get_ingestion_status(runId);
      } catch (error) {
        return {
          success: false,
          message: `Failed to get ingestion status: ${error}`,
        };
      }
    }
    return {
      success: false,
      message: "Desktop bridge not available",
    };
  },

  // =============================================
  // Run APIs
  // =============================================
  async getRuns(): Promise<RunMeta[]> {
    await waitForBridge();
    if (isDesktop) {
      try {
        return (window as any).frontendAPI.get_runs();
      } catch (error) {
        console.error("Failed to fetch runs:", error);
        return [];
      }
    }
    return [];
  },

  async searchRuns(query: string): Promise<RunMeta[]> {
    await waitForBridge();
    if (isDesktop) {
      try {
        return (window as any).frontendAPI.search_runs(query);
      } catch (error) {
        console.error("Failed to search runs:", error);
        return [];
      }
    }
    return [];
  },

  // =============================================
  // Insights APIs
  // =============================================
  async getInsights(runId: string): Promise<IPCResponse> {
    await waitForBridge();
    if (isDesktop) {
      try {
        return (window as any).frontendAPI.get_insights(runId);
      } catch (error) {
        return {
          success: false,
          message: `Failed to get insights: ${error}`,
        };
      }
    }
    return {
      success: false,
      message: "Desktop bridge not available",
    };
  },

  // =============================================
  // Dashboard APIs
  // =============================================
  async getDashboard(runId: string): Promise<IPCResponse> {
    await waitForBridge();
    if (isDesktop) {
      try {
        return (window as any).frontendAPI.get_dashboard(runId);
      } catch (error) {
        return {
          success: false,
          message: `Failed to get dashboard: ${error}`,
        };
      }
    }
    return {
      success: false,
      message: "Desktop bridge not available",
    };
  },

  // =============================================
  // Data Health APIs
  // =============================================
  async getDataHealth(runId: string): Promise<IPCResponse> {
    await waitForBridge();
    if (isDesktop) {
      try {
        return (window as any).frontendAPI.get_data_health(runId);
      } catch (error) {
        return {
          success: false,
          message: `Failed to get data health: ${error}`,
        };
      }
    }
    return {
      success: false,
      message: "Desktop bridge not available",
    };
  },

  // =============================================
  // Export APIs
  // =============================================
  async getExports(runId: string): Promise<IPCResponse> {
    await waitForBridge();
    if (isDesktop) {
      try {
        return (window as any).frontendAPI.get_exports(runId);
      } catch (error) {
        return {
          success: false,
          message: `Failed to get exports: ${error}`,
        };
      }
    }
    return {
      success: false,
      message: "Desktop bridge not available",
    };
  },
};