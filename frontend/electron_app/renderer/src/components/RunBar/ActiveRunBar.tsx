import { useState, useSyncExternalStore } from "react";
import { runUI } from "../../state/run_ui_store";
import { RunSelectorModal } from "../RunSelector/RunSelectorModal";

const ActiveRunBar = () => {
  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const [showSelector, setShowSelector] = useState(false);
  const hasRun = Boolean(runState.activeRunId);

  return (
    <div style={styles.bar}>
      <div>
        <strong>Active Run:</strong>{" "}
        <span style={styles.runName}>
          {runState.activeRunId ?? "None"}
        </span>
      </div>

      <div style={styles.actions}>
        <button onClick={() => setShowSelector(true)}>
          {hasRun ? "Change Run" : "Select Run"}
        </button>

        {hasRun && (
          <button onClick={() => runUI.clearRun()}>
            Clear
          </button>
        )}
      </div>

      {showSelector && (
        <RunSelectorModal onClose={() => setShowSelector(false)} />
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  bar: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    height: "48px",
    background: "#ffffff",
    borderBottom: "1px solid #e5e7eb",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 16px",
    zIndex: 1000,
  },
  runName: {
    fontFamily: "monospace",
    marginLeft: "6px",
  },
  actions: {
    display: "flex",
    gap: "8px",
  },
};

export default ActiveRunBar;