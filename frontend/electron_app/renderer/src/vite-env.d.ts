/// <reference types="vite/client" />

declare module "*.svg" {
  const src: string;
  export default src;
}
/// <reference types="vite/client" />

interface FrontendAPI {
  get_runs: () => Promise<any[]>;
  get_insights: (run_id: string) => Promise<any>;
  get_dashboard: (run_id: string) => Promise<any>;
  get_data_health: (run_id: string) => Promise<any>;
  get_exports: (run_id: string) => Promise<any>;
}

interface Window {
  frontendAPI: FrontendAPI;
}
