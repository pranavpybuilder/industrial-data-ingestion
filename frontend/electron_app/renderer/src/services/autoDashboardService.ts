/**
 * Auto Dashboard Service
 * ----------------------
 * SAFE MODE
 * Generates widgets purely from schema
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
  runId: string
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
    widgetData[w.widgetId] = [
      { x: "Jan", y: 30 },
      { x: "Feb", y: 45 },
      { x: "Mar", y: 25 },
      { x: "Apr", y: 60 },
    ];
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