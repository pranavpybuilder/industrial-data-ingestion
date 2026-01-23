import { FiRotateCcw, FiRotateCw } from "react-icons/fi";
import { dashboardsUI } from "../../state/dashboards_ui_store";
import { useDashboardsUI } from "../../state/useDashboardsUI";
import { RunGuard } from "../../components/RunGuard/RunGuard";
import GlobalFilterBar from "../../components/Filters/GlobalFilterBar";
import SessionFilterBar from "../../components/Filters/SessionFilterBar";
import WidgetFilter from "../../components/Filters/WidgetFilter";
import VisualizationSwitcher from "../../components/Widgets/VisualizationSwitcher";
import ChartWidget from "../../components/Widgets/ChartWidget";
import type { DashboardBlueprint } from "../../state/dashboards_ui_store";

const Dashboards = () => {
  const state = useDashboardsUI();

  if (
    !state.isLoaded ||
    !state.blueprint ||
    state.interactionState === null
  ) {
    return (
      <section>
        <h1>Dashboards</h1>
        <p>No dashboard available.</p>
      </section>
    );
  }

  const interaction = state.interactionState;

  return (
    <RunGuard>
      <section>
        {/* ---------- Header ---------- */}
        <header style={{ marginBottom: "1rem" }}>
          <h1>{state.blueprint.title}</h1>
          <p>Interactive analytical dashboards</p>
        </header>

        {/* ---------- SLICER BAR ---------- */}
        <div
          style={{
            display: "flex",
            gap: "1rem",
            flexWrap: "wrap",
            padding: "0.75rem",
            marginBottom: "1rem",
            background: "#f9fafb",
            border: "1px solid #e5e7eb",
            borderRadius: "8px",
          }}
        >
          <GlobalFilterBar />
          <SessionFilterBar />
        </div>

        {/* ---------- Drill Context ---------- */}
        {interaction.drillContext && (
          <div
            style={{
              marginBottom: "1rem",
              padding: "0.5rem",
              background: "#fef3c7",
              border: "1px solid #fde68a",
              borderRadius: "6px",
            }}
          >
            <strong>Drill Context:</strong>{" "}
            {interaction.drillContext.dimension} ={" "}
            {interaction.drillContext.value}
            <button
              style={{ marginLeft: "1rem" }}
              onClick={() =>
                dashboardsUI.updateInteraction((prev) => ({
                  ...prev,
                  drillContext: null,
                }))
              }
            >
              Clear
            </button>
          </div>
        )}

        {/* ---------- Undo / Redo ---------- */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
          <button
            disabled={state.undoStack.length === 0}
            onClick={() => dashboardsUI.undo()}
          >
            <FiRotateCcw />
          </button>
          <button
            disabled={state.redoStack.length === 0}
            onClick={() => dashboardsUI.redo()}
          >
            <FiRotateCw />
          </button>
        </div>

        {/* ---------- DASHBOARD GRID ---------- */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(12, 1fr)",
            gap: "1rem",
          }}
        >
          {state.blueprint.widgets.map(
            (widget: DashboardBlueprint["widgets"][number]) => {
              if (widget.widgetType !== "chart") return null;
              if (interaction.hiddenWidgets.has(widget.widgetId)) return null;

              const visualType =
                interaction.visualTypes[widget.widgetId] ??
                widget.allowedVisualTypes?.[0] ??
                "line";

              const mockData = [
                { x: "Jan", y: 30 },
                { x: "Feb", y: 45 },
                { x: "Mar", y: 25 },
                { x: "Apr", y: 60 },
              ];

              return (
                <div
                  key={widget.widgetId}
                  style={{
                    gridColumn: "span 6",
                    background: "#ffffff",
                    borderRadius: "10px",
                    padding: "1rem",
                    boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
                  }}
                >
                  <VisualizationSwitcher
                    widgetId={widget.widgetId}
                    allowed={widget.allowedVisualTypes ?? ["line"]}
                  />

                  <WidgetFilter widgetId={widget.widgetId} />

                  <ChartWidget
                    title={widget.widgetId.replace("_", " ")}
                    visualType={visualType as "line" | "bar"}
                    data={mockData}
                  />
                </div>
              );
            }
          )}
        </div>
      </section>
    </RunGuard>
  );
};

export default Dashboards;