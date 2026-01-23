import { dashboardsUI } from "../../state/dashboards_ui_store";

/**
 * DimensionSlicer
 * ----------------
 * Global dimension slicer (safe version).
 * Does NOT assume filter keys exist.
 */
const DimensionSlicer = () => {
  const state = dashboardsUI.getState();
  const interaction = state.interactionState;

  if (!interaction) return null;

  // ✅ SAFE access with fallback
  const equipment =
    interaction.globalFilters?.equipment ?? "";

  const onChange = (value: string) => {
    dashboardsUI.updateInteraction((prev) => ({
      ...prev,
      globalFilters: {
        ...prev.globalFilters,
        equipment: value,
      },
    }));
  };

  return (
    <div style={{ marginBottom: "0.5rem" }}>
      <label>Equipment:</label>
      <select
        value={equipment}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">All</option>
        <option value="Machine-1">Machine-1</option>
        <option value="Machine-2">Machine-2</option>
        <option value="Machine-3">Machine-3</option>
      </select>
    </div>
  );
};

export default DimensionSlicer;