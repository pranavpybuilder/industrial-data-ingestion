// src/services/frontendApi.ts

export interface RunMeta {
  run_id: string;
}

const isDesktop =
  typeof window !== "undefined" &&
  typeof (window as any).frontendAPI !== "undefined";

export const frontendApi = {
  async getRuns(): Promise<RunMeta[]> {
    if (isDesktop) {
      return (window as any).frontendAPI.get_runs();
    }

    // Browser dev fallback
    return [];
  },
};