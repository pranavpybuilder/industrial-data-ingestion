import { dashboardsUI } from "../../state/dashboards_ui_store";

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
    (interaction.slicers[slicerId] as string) || "";

  const onChange = (val: string) => {
    dashboardsUI.updateInteraction((prev) => ({
      ...prev,
      slicers: {
        ...prev.slicers,
        [slicerId]: val,
      },
    }));
  };

  return (
    <div>
      <label>{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
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