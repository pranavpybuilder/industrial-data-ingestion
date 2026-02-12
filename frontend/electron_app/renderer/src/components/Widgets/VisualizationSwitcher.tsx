import { dashboardsUI } from "../../state/dashboards_ui_store";

interface Props {
  widgetId: string;
  allowed: string[];
}

const VisualizationSwitcher = ({ widgetId, allowed }: Props) => {
  return (
    <select
      aria-label="Visualization type"
      title="Visualization type"
      onChange={(e) =>
        dashboardsUI.updateInteraction(prev => ({
          ...prev,
          visualTypes: { ...prev.visualTypes, [widgetId]: e.target.value },
        }))
      }
      style={selectStyle}
    >
      {allowed.map(v => (
        <option key={v} value={v}>{v.toUpperCase()}</option>
      ))}
    </select>
  );
};

const selectStyle: React.CSSProperties = {
  borderRadius: "6px",
  border: "1px solid #e5e7eb",
  padding: "6px 10px",
  fontSize: "13px",
  color: "#374151",
  background: "#ffffff",
  outline: "none",
  cursor: "pointer",
  transition: "border-color 0.2s ease, box-shadow 0.2s ease",
};

export default VisualizationSwitcher;