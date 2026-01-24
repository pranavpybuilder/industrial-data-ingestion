import DashboardSection from "./DashboardSection";
import type {
  DashboardBlueprint,
  InteractionState,
} from "../../state/dashboards_ui_store";

interface DashboardCanvasProps {
  blueprint: DashboardBlueprint;
  interaction: InteractionState;
  widgetData: Record<string, any[]>;
}

const DashboardCanvas = ({
  blueprint,
  interaction,
  widgetData,
}: DashboardCanvasProps) => {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(12, 1fr)",
        gap: "16px",
      }}
    >
      {blueprint.widgets.map((widget) => {
        if (interaction.hiddenWidgets.has(widget.widgetId)) return null;

        return (
          <DashboardSection
            key={widget.widgetId}
            widget={widget}     
            interaction={interaction}
            data={widgetData[widget.widgetId] ?? []}
          />
        );
      })}
    </div>
  );
};

export default DashboardCanvas;