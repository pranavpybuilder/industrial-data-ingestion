import { dashboardsUI } from "../../state/dashboards_ui_store";

interface WidgetFilterProps {
  widgetId: string;
}

/**
 * WidgetFilter
 *
 * Advanced, widget-scoped filter.
 * Applies ONLY to the given widget.
 */
const WidgetFilter = ({ widgetId }: WidgetFilterProps) => {
  const state = dashboardsUI.getState();
  const interaction = state.interactionState;

  if (!interaction) return null;

  const currentFilter =
    interaction.widgetFilters[widgetId]?.category ?? "";

  const onChange = (value: string) => {
    dashboardsUI.updateInteraction((prev) => ({
      ...prev,
      widgetFilters: {
        ...prev.widgetFilters,
        [widgetId]: {
          ...prev.widgetFilters[widgetId],
          category: value,
        },
      },
    }));
  };

  return (
    <div style={{ marginBottom: "0.5rem" }}>
      <label style={{ marginRight: "0.5rem" }}>
        Widget Filter:
      </label>
      <select
        value={currentFilter}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">All</option>
        <option value="critical">Critical</option>
        <option value="warning">Warning</option>
        <option value="normal">Normal</option>
      </select>
    </div>
  );
};

export default WidgetFilter;