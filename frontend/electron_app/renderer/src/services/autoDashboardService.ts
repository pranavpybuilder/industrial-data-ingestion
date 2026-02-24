/**
 * Auto Dashboard Service
 * ----------------------
 * Builds a dashboard shell from schema metadata only.
 * This service does not fabricate chart values.
 */

export interface DatasetSchema {
  time: string[];
  categorical: string[];
  numeric: string[];
}

export interface AutoWidget {
  widgetId: string;
  widgetType: "chart";
  allowedVisualTypes: string[];
}

export function generateAutoDashboard(
  schema: DatasetSchema,
  runId: string,
  widgetDataInput: Record<string, Array<{ x: string; y: number }>> = {}
) {
  const widgets: AutoWidget[] = schema.numeric.map((metric) => ({
    widgetId: `${metric}_trend`,
    widgetType: "chart",
    allowedVisualTypes: ["line", "bar"],
  }));

  const widgetData: Record<
    string,
    Array<{ x: string; y: number }>
  > = {};

  widgets.forEach((w) => {
    widgetData[w.widgetId] = widgetDataInput[w.widgetId] || [];
  });

  return {
    blueprint: {
      dashboardId: `auto_${runId}`,
      title: "Maintenance Overview",
      widgets,
    },
    widgetData,
  };
}
