/**
 * DashboardCanvas — Power BI-style sectioned grid layout
 * Groups widgets by section and renders them in a 12-column grid
 */

import DashboardSection from "./DashboardSection";
import type {
  DashboardBlueprint,
  InteractionState,
} from "../../state/dashboards_ui_store";

interface DashboardCanvasProps {
  blueprint: DashboardBlueprint;
  interaction: InteractionState;
  widgetData: Record<string, any>;
}

const DashboardCanvas = ({
  blueprint,
  interaction,
  widgetData,
}: DashboardCanvasProps) => {
  // Group widgets by section if sections exist
  const sections = blueprint.sections?.length
    ? blueprint.sections.sort((a, b) => a.order - b.order)
    : null;

  if (sections) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {sections.map((section) => {
          const sectionWidgets = blueprint.widgets.filter(
            (w) => w.sectionId === section.sectionId
          );
          if (sectionWidgets.length === 0) return null;

          return (
            <div key={section.sectionId}>
              <h2 style={sectionHeaderStyle}>{section.title}</h2>
              <div style={gridStyle}>
                {sectionWidgets.map((widget) => {
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
            </div>
          );
        })}

        {/* Widgets without a section */}
        {(() => {
          const sectionIds = new Set(sections.map((s) => s.sectionId));
          const orphans = blueprint.widgets.filter(
            (w) => !w.sectionId || !sectionIds.has(w.sectionId)
          );
          if (orphans.length === 0) return null;
          return (
            <div style={gridStyle}>
              {orphans.map((widget) => {
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
        })()}
      </div>
    );
  }

  // Flat layout (no sections)
  return (
    <div style={gridStyle}>
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

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(12, 1fr)",
  gap: "16px",
  alignItems: "start",
};

const sectionHeaderStyle: React.CSSProperties = {
  fontSize: "16px",
  fontWeight: 700,
  color: "#111827",
  marginBottom: "12px",
  paddingBottom: "8px",
  borderBottom: "2px solid #e5e7eb",
  letterSpacing: "-0.02em",
};

export default DashboardCanvas;