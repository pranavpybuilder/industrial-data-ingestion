import { useState, useSyncExternalStore } from "react";
import { NavLink } from "react-router-dom";
import Logo from "assets/logo.svg";
import { runUI } from "../../state/run_ui_store";
import { RunSelectorModal } from "../RunSelector/RunSelectorModal";

const Sidebar = () => {
  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const [showRunSelector, setShowRunSelector] = useState(false);
  const hasRun = Boolean(runState.activeRunId);

  const guardedLink = (
  baseStyle: React.CSSProperties
): React.CSSProperties => ({
  ...baseStyle,
  opacity: hasRun ? 1 : 0.45,
  pointerEvents: "auto" as React.CSSProperties["pointerEvents"],
  cursor: hasRun ? "pointer" : "not-allowed",
});

  const guardTooltip = hasRun
    ? undefined
    : "Select an ingestion run to access this section";

  return (
    <nav style={styles.sidebar}>
      {/* Branding */}
      <div style={styles.brand}>
        <img src={Logo} alt="Company Logo" style={styles.logo} />
        <div style={styles.appName}>Offline Intelligence</div>
      </div>

      {/* Active Run */}
      <div style={styles.runBox}>
        <div style={styles.runLabel}>Active Run</div>
        <div
          style={styles.runValue}
          title={runState.activeRunId ?? ""}
        >
          {runState.activeRunId ?? "No run selected"}
        </div>

        <button
          style={styles.primaryBtn}
          onClick={() => setShowRunSelector(true)}
        >
          {hasRun ? "Change Run" : "Select Run"}
        </button>

        {hasRun && (
          <button
            style={styles.secondaryBtn}
            onClick={() => runUI.clearRun()}
          >
            Clear Run
          </button>
        )}
      </div>

      {/* Primary navigation */}
      <div style={styles.section}>
        <NavLink to="/" style={styles.primaryLink}>Home</NavLink>
        <NavLink to="/ingestion" style={styles.primaryLink}>Ingestion</NavLink>

        <NavLink
          to="/insights"
          style={guardedLink(styles.primaryLink)}
          title={guardTooltip}
        >
          Insights
        </NavLink>

        <NavLink
          to="/dashboards"
          style={guardedLink(styles.primaryLink)}
          title={guardTooltip}
        >
          Dashboards
        </NavLink>

        <NavLink
          to="/exports"
          style={guardedLink(styles.primaryLink)}
          title={guardTooltip}
        >
          Exports
        </NavLink>
      </div>

      <div style={styles.divider} />

      {/* Secondary navigation */}
      <div style={styles.section}>
        <div style={styles.sectionLabel}>Advanced</div>

        <NavLink
          to="/explorer"
          style={guardedLink(styles.secondaryLink)}
          title={guardTooltip}
        >
          Explorer
        </NavLink>

        <NavLink
          to="/data-health"
          style={guardedLink(styles.secondaryLink)}
          title={guardTooltip}
        >
          Data Health
        </NavLink>
      </div>

      {showRunSelector && (
        <RunSelectorModal onClose={() => setShowRunSelector(false)} />
      )}
    </nav>
  );
};

/* ================= STYLES (UNCHANGED) ================= */

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: "260px",
    padding: "20px 16px",
    backgroundColor: "#1f2933",
    color: "#ffffff",
    display: "flex",
    flexDirection: "column",
  },
  brand: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    marginBottom: "22px",
  },
  logo: {
    height: "100px",
    width: "100px",
    objectFit: "contain",
    marginBottom: "10px",
  },
  appName: {
    fontSize: "15px",
    fontWeight: 600,
    letterSpacing: "0.3px",
    textAlign: "center",
    color: "#ffffff",
  },
  runBox: {
    backgroundColor: "#111827",
    border: "1px solid #374151",
    borderRadius: "8px",
    padding: "12px",
    marginBottom: "20px",
    textAlign: "center",
  },
  runLabel: {
    fontSize: "11px",
    color: "#9ca3af",
    marginBottom: "4px",
  },
  runValue: {
    fontSize: "13px",
    fontWeight: 500,
    color: "#e5e7eb",
    marginBottom: "10px",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  primaryBtn: {
    width: "100%",
    padding: "6px 8px",
    fontSize: "12px",
    marginBottom: "6px",
    cursor: "pointer",
  },
  secondaryBtn: {
    width: "100%",
    padding: "6px 8px",
    fontSize: "12px",
    cursor: "pointer",
  },
  section: {
    display: "flex",
    flexDirection: "column",
    textAlign: "center",
    gap: "12px",
  },
  sectionLabel: {
    fontSize: "12px",
    color: "#9ca3af",
    marginBottom: "6px",
  },
  divider: {
    height: "1px",
    backgroundColor: "#374151",
    margin: "18px 0",
  },
  primaryLink: {
    color: "#e5e7eb",
    textDecoration: "none",
    fontSize: "14px",
    fontWeight: 500,
  },
  secondaryLink: {
    color: "#9ca3af",
    textDecoration: "none",
    fontSize: "13px",
  },
};

export default Sidebar;
