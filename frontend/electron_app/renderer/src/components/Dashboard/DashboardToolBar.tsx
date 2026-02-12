import { FiRotateCcw, FiRotateCw } from "react-icons/fi";
import { dashboardsUI } from "../../state/dashboards_ui_store";
import { useDashboardsUI } from "../../state/useDashboardsUI";

const DashboardToolBar = () => {
  const state = useDashboardsUI();

  return (
    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
      <button
        disabled={state.undoStack.length === 0}
        onClick={() => dashboardsUI.undo()}
        title="Undo"
        aria-label="Undo"
      >
        <FiRotateCcw />
      </button>

      <button
        disabled={state.redoStack.length === 0}
        onClick={() => dashboardsUI.redo()}
        title="Redo"
        aria-label="Redo"
      >
        <FiRotateCw />
      </button>
    </div>
  );
};

export default DashboardToolBar;