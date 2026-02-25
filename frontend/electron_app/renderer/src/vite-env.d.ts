/// <reference types="vite/client" />

declare module "*.svg" {
  const src: string;
  export default src;
}
/// <reference types="vite/client" />

interface FrontendAPI {
  upload_file: (file_path: string, source_type: string, callback?: (res: any) => void) => any;
  select_file: (callback?: (res: any) => void) => any;
  select_directory: (callback?: (res: any) => void) => any;
  get_ingestion_status: (run_id: string, callback?: (res: any) => void) => any;
  get_runs: (callback?: (res: any) => void) => any;
  search_runs: (query: string, callback?: (res: any) => void) => any;
  get_insights: (run_id: string, callback?: (res: any) => void) => any;
  get_dashboard: (run_id: string, callback?: (res: any) => void) => any;
  save_dashboard_layout: (run_id: string, blueprint_id: string, user_layout: Record<string, any>, callback?: (res: any) => void) => any;
  get_dashboard_layout: (run_id: string, callback?: (res: any) => void) => any;
  get_data_health: (run_id: string, callback?: (res: any) => void) => any;
  get_exports: (run_id: string, callback?: (res: any) => void) => any;
  generate_export: (run_id: string, export_type: string, scope: string, output_dir: string, callback?: (res: any) => void) => any;
  get_explorer_data: (run_id: string, limit: number, callback?: (res: any) => void) => any;
}

interface Window {
  frontendAPI?: FrontendAPI;
}
