/**
 * Dashboard Interaction State
 * Controlled entirely by frontend
 */

export type TimeGranularity = "day" | "month" | "year";

export interface DashboardInteractionState {
  time_granularity: TimeGranularity;

  slicers: Record<string, string | string[]>;

  visual_overrides: Record<string, string>;

  hidden_widgets: string[];

  drill_context?: {
    source_widget: string;
    entity_id?: string;
  };
}