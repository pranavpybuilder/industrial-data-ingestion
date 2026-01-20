/**
 * Dashboard Data Contract
 * Fully precomputed, no raw data exposure
 */

export interface DashboardDataContract {
  run_id: string;

  data: {
    [data_key: string]: unknown;
  };
}