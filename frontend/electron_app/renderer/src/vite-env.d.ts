/// <reference types="vite/client" />

declare module "*.svg" {
  const src: string;
  export default src;
}
/// <reference types="vite/client" />

interface FrontendAPI {
  // Ingestion
  upload_file: (file_path: string, source_type: string, callback?: (res: any) => void) => any;
  select_file: (callback?: (res: any) => void) => any;
  select_directory: (callback?: (res: any) => void) => any;
  get_ingestion_status: (run_id: string, callback?: (res: any) => void) => any;

  // Runs
  get_runs: (callback?: (res: any) => void) => any;
  search_runs: (query: string, callback?: (res: any) => void) => any;

  // Insights
  get_insights: (run_id: string, callback?: (res: any) => void) => any;

  // Dashboard
  get_dashboard: (run_id: string, callback?: (res: any) => void) => any;
  save_dashboard_layout: (run_id: string, blueprint_id: string, user_layout: Record<string, any>, callback?: (res: any) => void) => any;
  get_dashboard_layout: (run_id: string, callback?: (res: any) => void) => any;

  // Data Health
  get_data_health: (run_id: string, callback?: (res: any) => void) => any;

  // Exports — Legacy
  get_exports: (run_id: string, callback?: (res: any) => void) => any;
  generate_export: (run_id: string, export_type: string, scope: string, output_dir: string, callback?: (res: any) => void) => any;

  // Exports — New 7 handlers
  get_export_history: (run_id: string, callback?: (res: any) => void) => any;
  export_insights_docx: (run_id: string, output_dir: string, callback?: (res: any) => void) => any;
  export_insights_pdf: (run_id: string, output_dir: string, callback?: (res: any) => void) => any;
  export_dashboard_pdf: (run_id: string, image_data_base64: string, output_dir: string, callback?: (res: any) => void) => any;
  export_dashboard_json: (run_id: string, output_dir: string, callback?: (res: any) => void) => any;
  export_full_report: (run_id: string, image_data_base64: string, output_dir: string, callback?: (res: any) => void) => any;
  open_export_file: (file_path: string, callback?: (res: any) => void) => any;

  // Data Explorer
  get_explorer_data: (run_id: string, limit: number, callback?: (res: any) => void) => any;
}

interface Window {
  frontendAPI?: FrontendAPI;
}
