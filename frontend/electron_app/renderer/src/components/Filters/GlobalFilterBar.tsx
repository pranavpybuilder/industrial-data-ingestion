import TimeSlicer from "./TimeSlicer";
import DimensionSlicer from "./DimensionSlicer";
import { dashboardsUI } from "../../state/dashboards_ui_store";

const GlobalFilterBar = () => {
  const state = dashboardsUI.getState();
  const blueprint = state.blueprint;

  if (!blueprint || !state.interactionState) return null;

  return (
    <div
      style={{
        display: "flex",
        gap: "1rem",
        padding: "0.5rem",
        borderBottom: "1px solid #ddd",
      }}
    >
      <TimeSlicer />

      {blueprint.widgets && (
        <DimensionSlicer
          slicerId="equipment"
          label="Equipment"
          options={["EQ-01", "EQ-02", "EQ-03"]}
        />
      )}
    </div>
  );
};

export default GlobalFilterBar;