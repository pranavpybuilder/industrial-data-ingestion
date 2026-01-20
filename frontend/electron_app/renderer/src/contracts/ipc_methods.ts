export interface DashboardIPC {
  get_dashboard_blueprint(run_id: string): Promise<any>;
  get_dashboard_data(run_id: string): Promise<any>;
  export_dashboard(payload: any): Promise<void>;
}