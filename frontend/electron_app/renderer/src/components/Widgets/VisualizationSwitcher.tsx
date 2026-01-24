import { dashboardsUI } from "../../state/dashboards_ui_store";

interface Props {
  widgetId: string;
  allowed: string[];
}

const VisualizationSwitcher = ({ widgetId, allowed }: Props) => {
  return (
    <select
      onChange={(e) =>
        dashboardsUI.updateInteraction(prev => ({
          ...prev,
          visualTypes: { ...prev.visualTypes, [widgetId]: e.target.value },
        }))
      }
    >
      {allowed.map(v => (
        <option key={v} value={v}>{v.toUpperCase()}</option>
      ))}
    </select>
  );
};

export default VisualizationSwitcher;