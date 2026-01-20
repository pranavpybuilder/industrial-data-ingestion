/**
 * Dashboard Blueprint Contract
 * System-generated, immutable, run-scoped
 */

export type WidgetType =
  | "chart"
  | "metric"
  | "map"
  | "text"
  | "image";

export interface DashboardWidgetContract {
  widget_id: string;
  widget_type: WidgetType;
  title: string;

  // Data binding (precomputed)
  data_key?: string;

  // Visualization rules
  default_visual?: string;
  allowed_visuals?: string[];

  // Drill capabilities
  drill_down?: boolean;
  drill_through?: boolean;
}

export interface DashboardBlueprintContract {
  run_id: string;
  dashboard_id: string;
  title: string;
  description?: string;

  widgets: DashboardWidgetContract[];

  // Available slicers for this dashboard
  slicers: Array<{
    slicer_id: string;
    label: string;
    type: "time" | "dimension";
    allowed_values?: string[];
  }>;
}