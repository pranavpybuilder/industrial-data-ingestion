import { dashboardsUI } from "../../state/dashboards_ui_store";

/**
 * DimensionSlicer
 * ----------------
 * Global dimension slicer (typed & safe).
 */

interface DimensionSlicerProps {
  slicerId: string;
  label: string;
  options: string[];
}

const DimensionSlicer = ({
  slicerId,
  label,
  options,
}: DimensionSlicerProps) => {
  const state = dashboardsUI.getState();
  const interaction = state.interactionState;

  if (!interaction) return null;

  const value =
    interaction.globalFilters[slicerId] ?? "";

  const onChange = (newValue: string) => {
    dashboardsUI.updateInteraction((prev) => ({
      ...prev,
      globalFilters: {
        ...prev.globalFilters,
        [slicerId]: newValue,
      },
    }));
  };

  return (
    <div style={{ marginBottom: "0.5rem" }}>
      <label htmlFor={`dim-${slicerId}`}>{label}:</label>
      <select
        id={`dim-${slicerId}`}
        title={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">All</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
};

export default DimensionSlicer;