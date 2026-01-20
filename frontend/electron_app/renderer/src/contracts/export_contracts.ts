/**
 * Export Request Contract
 * Export reflects CURRENT interaction state
 */

import { DashboardInteractionState } from "./dashboard_interaction_contracts";

export interface DashboardExportRequest {
  run_id: string;
  dashboard_id: string;
  interaction_state: DashboardInteractionState;
  export_format: "pdf" | "excel";
}