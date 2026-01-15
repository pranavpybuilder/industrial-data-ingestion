// src/components/RunSelector/RunSelector.tsx
import { onRunChange } from "../../state/state_reset";
import { useRunUI } from "../../state/useRunUI";

const RunSelector = () => {
  const { activeRunId } = useRunUI();

  return (
    <div>
      <p>{activeRunId ?? "No run selected"}</p>

      <button onClick={() => onRunChange("RUN_SELECTED_BY_USER")}>
        Select Run
      </button>

      {activeRunId && (
        <button onClick={() => onRunChange("")}>Clear</button>
      )}
    </div>
  );
};

export default RunSelector;