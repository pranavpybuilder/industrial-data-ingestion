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
        padding: "16px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
      }}
    >
      {/* Widget Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "8px",
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