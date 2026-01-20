import { FiRotateCcw, FiRotateCw } from "react-icons/fi";
import { dashboardsUI } from "../../state/dashboards_ui_store";
import { useDashboardsUI } from "../../state/useDashboardsUI";
import { RunGuard } from "../../components/RunGuard/RunGuard";
import GlobalFilterBar from "../../components/Filters/GlobalFilterBar";
import ChartWidget from "../../components/Widgets/ChartWidget";
import VisualizationSwitcher from "../../components/Widgets/VisualizationSwitcher";
import type { DashboardBlueprint } from "../../state/dashboards_ui_store";

/**
 * Dashboards Page
 * ----------------
 * Pure render-only dashboard view.
 * No initialization, no side effects.
 */
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
        <p>No dashboard available for the selected run.</p>
      </section>
    );
  }

  const interactionState = state.interactionState;

  return (
    <RunGuard>
      <section>
        <header>
          <h1>{state.blueprint.title}</h1>
          <p>
            Interactive dashboards generated automatically from
            industrial data.
          </p>
        </header>

        {/* Global Filters */}
        <GlobalFilterBar />

        {/* Undo / Redo Toolbar */}
        <div style={{ display: "flex", gap: "0.5rem", margin: "1rem 0" }}>
          <button
            title="Undo"
            disabled={state.undoStack.length === 0}
            onClick={() => dashboardsUI.undo()}
          >
            <FiRotateCcw size={18} />
          </button>

          <button
            title="Redo"
            disabled={state.redoStack.length === 0}
            onClick={() => dashboardsUI.redo()}
          >
            <FiRotateCw size={18} />
          </button>
        </div>

        {/* Widgets */}
        {state.blueprint.widgets.map(
          (widget: DashboardBlueprint["widgets"][number]) => {
            if (widget.widgetType !== "chart") return null;

            const visual =
              interactionState.visualTypes[widget.widgetId] ??
              widget.allowedVisualTypes?.[0] ??
              "line";

            const mockData = [
              { x: "Jan", y: 30 },
              { x: "Feb", y: 45 },
              { x: "Mar", y: 25 },
              { x: "Apr", y: 60 },
            ];

            return (
              <div key={widget.widgetId}>
                <VisualizationSwitcher
                  widgetId={widget.widgetId}
                  allowed={widget.allowedVisualTypes ?? ["line"]}
                />

                <ChartWidget
                  title={widget.widgetId.replace("_", " ")}
                  visualType={visual as "line" | "bar"}
                  data={mockData}
                />
              </div>
            );
          }
        )}
      </section>
    </RunGuard>
  );
};

export default Dashboards;