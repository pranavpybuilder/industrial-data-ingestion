import { dashboardsUI } from "../../state/dashboards_ui_store";

/**
 * SessionFilterBar
 * ----------------
 * Temporary analysis filters.
 *
 * Characteristics:
 * - Not part of base dashboard layout
 * - Included in export
 * - Included if dashboard is saved
 * - Undoable / Redoable
 */
const SessionFilterBar = () => {
  const state = dashboardsUI.getState();
  const interaction = state.interactionState;

  if (!interaction) return null;

  const currentValue =
    interaction.sessionFilters.global?.severity ?? "";

  const applyFilter = (value: string) => {
    dashboardsUI.updateInteraction((prev) => ({
      ...prev,
      sessionFilters: {
        ...prev.sessionFilters,
        global: {
          ...prev.sessionFilters.global,
          severity: value,
        },
      },
    }));
  };

  const clearFilter = () => {
    dashboardsUI.updateInteraction((prev) => ({
      ...prev,
      sessionFilters: {
        ...prev.sessionFilters,
        global: {},
      },
    }));
  };

  return (
    <div
      style={{
        margin: "0.75rem 0",
        padding: "0.5rem",
        border: "1px dashed #93c5fd",
        background: "#eff6ff",
      }}
    >
      <strong>Session Filter:</strong>

      <select
        style={{ marginLeft: "0.5rem" }}
        value={currentValue}
        onChange={(e) => applyFilter(e.target.value)}
      >
        <option value="">All Severities</option>
        <option value="critical">Critical</option>
        <option value="warning">Warning</option>
        <option value="normal">Normal</option>
      </select>

      <button
        style={{ marginLeft: "0.75rem" }}
        onClick={clearFilter}
        disabled={!currentValue}
      >
        Clear
      </button>
    </div>
  );
};

export default SessionFilterBar;