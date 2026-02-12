import {
  FiSave,
  FiRotateCcw,
  FiRotateCw,
  FiExternalLink,
  FiEye,
} from "react-icons/fi";
import { useNavigate } from "react-router-dom";

import { dashboardsUI } from "../../state/dashboards_ui_store";
import { useDashboardsUI } from "../../state/useDashboardsUI";
import { useRunUI } from "../../state/useRunUI";

import { RunGuard } from "../../components/RunGuard/RunGuard";
import DashboardCanvas from "../../components/Dashboard/DashboardCanvas";

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

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
        { x: "Feb", y: 5 },
        { x: "Mar", y: 25 },
        { x: "Apr", y: 60 },
      ],
    ])
  );

  return (
    <RunGuard>
      <style>{fadeKeyframes}</style>
      <section style={styles.page}>
        {/* ---------- HEADER ---------- */}
        <div style={styles.headerRow}>
          <div>
            <h1 style={styles.title}>
              {run.activeRunId}
            </h1>
            <span style={styles.subtitle}>
              Interactive dashboard (auto-generated)
            </span>
          </div>

          {/* ---------- ACTION BUTTONS ---------- */}
          <div style={styles.actionsRow}>
            <button
              style={styles.btn}
              onClick={() => {
                dashboardsUI.save();
                alert("Dashboard layout saved (session).");
              }}
            >
              <FiSave size={14} /> Save
            </button>

            <button
              style={{
                ...styles.btn,
                opacity: state.undoStack.length === 0 ? 0.45 : 1,
                cursor: state.undoStack.length === 0 ? "not-allowed" : "pointer",
              }}
              disabled={state.undoStack.length === 0}
              onClick={() => dashboardsUI.undo()}
              title="Undo"
              aria-label="Undo"
            >
              <FiRotateCcw size={14} />
            </button>

            <button
              style={{
                ...styles.btn,
                opacity: state.redoStack.length === 0 ? 0.45 : 1,
                cursor: state.redoStack.length === 0 ? "not-allowed" : "pointer",
              }}
              disabled={state.redoStack.length === 0}
              onClick={() => dashboardsUI.redo()}
              title="Redo"
              aria-label="Redo"
            >
              <FiRotateCw size={14} />
            </button>

            <button
              style={styles.btn}
              onClick={() => navigate("/insights")}
            >
              <FiEye size={14} /> Show Insights
            </button>

            {/* ✅ EXPORT = NAVIGATION ONLY */}
            <button
              style={styles.btn}
              onClick={() => navigate("/exports")}
            >
              <FiExternalLink size={14} /> Export
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

/* ================= STYLES ================= */

const styles: Record<string, React.CSSProperties> = {
  page: {
    animation: "fadeIn 0.3s ease-out",
  },

  headerRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
  },

  title: {
    fontSize: "22px",
    fontWeight: 700,
    color: "#111827",
    margin: 0,
    marginBottom: 4,
  },

  subtitle: {
    color: "#6b7280",
    fontSize: 13,
  },

  actionsRow: {
    display: "flex",
    gap: 8,
  },

  btn: {
    background: "#f3f4f6",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    padding: "8px 14px",
    fontSize: 13,
    fontWeight: 500,
    color: "#111827",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    transition: "background 0.15s",
  },
};

export default Dashboards;