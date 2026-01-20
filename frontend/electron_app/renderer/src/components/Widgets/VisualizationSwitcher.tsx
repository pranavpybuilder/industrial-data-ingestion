import { dashboardsUI } from "../../state/dashboards_ui_store";

interface VisualizationSwitcherProps {
  widgetId: string;
  allowed: string[];
}

const VisualizationSwitcher = ({
  widgetId,
  allowed,
}: VisualizationSwitcherProps) => {
  const state = dashboardsUI.getState();
  const interaction = state.interactionState;

  if (!interaction || allowed.length <= 1) return null;

  const current =
    interaction.visualTypes[widgetId] ?? allowed[0];

  const onChange = (value: string) => {
    dashboardsUI.updateInteraction((prev) => ({
      ...prev,
      visualTypes: {
        ...prev.visualTypes,
        [widgetId]: value,
      },
    }));
  };

  return (
    <div style={{ marginBottom: "0.5rem" }}>
      <label style={{ marginRight: "0.5rem" }}>
        Visualization:
      </label>
      <select
        value={current}
        onChange={(e) => onChange(e.target.value)}
      >
        {allowed.map((opt) => (
          <option key={opt} value={opt}>
            {opt.toUpperCase()}
          </option>
        ))}
      </select>
    </div>
  );
};

export default VisualizationSwitcher;