import { useEffect, useState } from "react";
import { dashboardsUI } from "./dashboards_ui_store";
import type { DashboardsUIState } from "./dashboards_ui_store";

export function useDashboardsUI(): DashboardsUIState {
  const [state, setState] = useState<DashboardsUIState>(
    dashboardsUI.getState()
  );

  useEffect(() => {
    const unsubscribe = dashboardsUI.subscribe(() => {
      setState(dashboardsUI.getState());
    });

    return unsubscribe;
  }, []);

  return state;
}