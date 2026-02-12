import { dashboardsUI } from "../../state/dashboards_ui_store";

const OPTIONS = ["day", "month", "year"] as const;

const TimeSlicer = () => {
  const state = dashboardsUI.getState();
  const interaction = state.interactionState;

  if (!interaction) return null;

  const onChange = (value: "day" | "month" | "year") => {
    dashboardsUI.updateInteraction((prev) => ({
      ...prev,
      timeGranularity: value,
    }));
  };

  return (
    <div>
      <label htmlFor="time-granularity">Time Granularity</label>
      <select
        id="time-granularity"
        title="Time granularity"
        value={interaction.timeGranularity}
        onChange={(e) =>
          onChange(e.target.value as "day" | "month" | "year")
        }
      >
        {OPTIONS.map((opt) => (
          <option key={opt} value={opt}>
            {opt.toUpperCase()}
          </option>
        ))}
      </select>
    </div>
  );
};

export default TimeSlicer;