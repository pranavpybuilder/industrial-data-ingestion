import { useState, useSyncExternalStore } from "react";
import { runUI } from "../../state/run_ui_store";
import  RunSelectorModal  from "../RunSelector/RunSelectorModal";
import { clearActiveRunContext } from "../../state/state_reset";

const ActiveRunBar = () => {
  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const [showSelector, setShowSelector] = useState(false);
  const [hoveredBtn, setHoveredBtn] = useState<string | null>(null);
  const hasRun = Boolean(runState.activeRunId);

  return (
    <div style={styles.bar}>
      <div style={styles.label}>
        <span style={styles.labelText}>Active Run:</span>
        <span style={styles.runName}>
          {runState.activeRunId ?? "None"}
        </span>
      </div>

      <div style={styles.actions}>
        <button
          onClick={() => setShowSelector(true)}
          onMouseEnter={() => setHoveredBtn("select")}
          onMouseLeave={() => setHoveredBtn(null)}
          style={{
            ...styles.actionBtn,
            background: hoveredBtn === "select" ? "#f3f4f6" : "#ffffff",
          }}
        >
          {hasRun ? "Change Run" : "Select Run"}
        </button>

        {hasRun && (
          <button
            onClick={() => clearActiveRunContext()}
            onMouseEnter={() => setHoveredBtn("clear")}
            onMouseLeave={() => setHoveredBtn(null)}
            style={{
              ...styles.clearBtn,
              background: hoveredBtn === "clear" ? "#fef2f2" : "#ffffff",
            }}
          >
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
    background: "linear-gradient(180deg, #ffffff 0%, #fafbfc 100%)",
    borderBottom: "1px solid #e5e7eb",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 20px",
    zIndex: 1000,
  },
  label: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  labelText: {
    fontSize: "13px",
    fontWeight: 500,
    color: "#6b7280",
  },
  runName: {
    fontFamily: "monospace",
    fontSize: "13px",
    color: "#6366f1",
    fontWeight: 600,
  },
  actions: {
    display: "flex",
    gap: "8px",
  },
  actionBtn: {
    padding: "6px 14px",
    borderRadius: "8px",
    border: "1px solid #e5e7eb",
    background: "#ffffff",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    color: "#374151",
    transition: "all 0.2s ease",
  },
  clearBtn: {
    padding: "6px 14px",
    borderRadius: "8px",
    border: "1px solid #ef4444",
    background: "#ffffff",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    color: "#ef4444",
    transition: "all 0.2s ease",
  },
};

export default ActiveRunBar;
