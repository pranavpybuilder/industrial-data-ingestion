import VisualizationSwitcher from "../Widgets/VisualizationSwitcher";
import ChartWidget from "../Widgets/ChartWidget";
import WidgetFilter from "../Filters/WidgetFilter";
import type {
  InteractionState,
  DashboardBlueprint,
} from "../../state/dashboards_ui_store";

export interface DashboardSectionProps {
  widget: DashboardBlueprint["widgets"][number];
  interaction: InteractionState;
  data: Array<{ x: string; y: number }>;
}

const DashboardSection = ({
  widget,
  interaction,
  data,
}: DashboardSectionProps) => {
  if (widget.widgetType !== "chart") return null;

  const visualType =
    interaction.visualTypes[widget.widgetId] ??
    widget.allowedVisualTypes?.[0] ??
    "line";

  return (
    <div
      style={{
        gridColumn: "span 6",
        background: "#ffffff",
        borderRadius: "12px",
        padding: "20px",
        border: "1px solid #e5e7eb",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
      }}
    >
      {/* Widget Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "12px",
          padding: "8px 12px",
          background: "#f9fafb",
          borderRadius: "8px",
        }}
      >
        <VisualizationSwitcher
          widgetId={widget.widgetId}
          allowed={widget.allowedVisualTypes || ["line", "bar"]}
        />
        <WidgetFilter widgetId={widget.widgetId} />
      </div>

      {/* Chart */}
      <ChartWidget
        title={widget.widgetId.replace(/_/g, " ")}
        visualType={visualType as "line" | "bar"}
        data={data}
      />
    </div>
  );
};

export default DashboardSection;