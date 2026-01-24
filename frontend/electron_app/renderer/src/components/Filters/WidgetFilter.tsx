import { dashboardsUI } from "../../state/dashboards_ui_store";

const WidgetFilter = ({ widgetId }: { widgetId: string }) => {
  return (
    <button
      onClick={() =>
        dashboardsUI.updateInteraction(prev => ({
          ...prev,
          widgetFilters: {
            ...prev.widgetFilters,
            [widgetId]: { active: true },
          },
        }))
      }
    >
      Widget Filter
    </button>
  );
};

export default WidgetFilter;