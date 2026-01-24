import {
  FiSave,
  FiRotateCcw,
  FiRotateCw,
  FiExternalLink,
} from "react-icons/fi";
import { useNavigate } from "react-router-dom";

import { dashboardsUI } from "../../state/dashboards_ui_store";
import { useDashboardsUI } from "../../state/useDashboardsUI";
import { useRunUI } from "../../state/useRunUI";

import { RunGuard } from "../../components/RunGuard/RunGuard";
import DashboardCanvas from "../../components/Dashboard/DashboardCanvas";

const Dashboards = () => {
  const navigate = useNavigate();
  const run = useRunUI();
  const state = useDashboardsUI();

  if (
    !run.activeRunId ||
    !state.isLoaded ||
    !state.blueprint ||
    !state.interactionState
  ) {
    return <p>No dashboard available.</p>;
  }

  /* TEMP MOCK DATA — backend will replace */
  const widgetData: Record<string, any[]> = Object.fromEntries(
    state.blueprint.widgets.map((w) => [
      w.widgetId,
      [
        { x: "Jan", y: 30 },
        { x: "Feb", y: 45 },
        { x: "Mar", y: 25 },
        { x: "Apr", y: 60 },
      ],
    ])
  );

  return (
    <RunGuard>
      <section>
        {/* ---------- HEADER ---------- */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "16px",
          }}
        >
          <div>
            <h1 style={{ marginBottom: 4 }}>
              {run.activeRunId}
            </h1>
            <span style={{ color: "#6b7280", fontSize: 13 }}>
              Interactive dashboard (auto-generated)
            </span>
          </div>

          {/* ---------- ACTION BUTTONS ---------- */}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => {
                dashboardsUI.save();
                alert("Dashboard layout saved (session).");
              }}
            >
              <FiSave /> Save
            </button>

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

            <button onClick={() => navigate("/insights")}>
              Show Insights
            </button>

            {/* ✅ EXPORT = NAVIGATION ONLY */}
            <button onClick={() => navigate("/exports")}>
              <FiExternalLink /> Export
            </button>
          </div>
        </div>

        {/* ---------- DASHBOARD CANVAS ---------- */}
        <DashboardCanvas
          blueprint={state.blueprint}
          interaction={state.interactionState}
          widgetData={widgetData}
        />
      </section>
    </RunGuard>
  );
};

export default Dashboards;