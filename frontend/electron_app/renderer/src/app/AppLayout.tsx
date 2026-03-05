import { useState, useSyncExternalStore } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar/Sidebar";
import Logo from "../assets/logo.svg";
import { runUI } from "../state/run_ui_store";
import RunSelectorModal from "../components/RunSelector/RunSelectorModal";
import { FiPlay, FiChevronDown } from "react-icons/fi";

const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [showRunSelector, setShowRunSelector] = useState(false);
  const [runBtnHover, setRunBtnHover] = useState(false);

  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const hasRun = Boolean(runState.activeRunId);

  return (
    <div style={styles.root}>
      {/* ================= TOP BAR ================= */}
      <header style={styles.topbar}>
        {/* LEFT — Brand */}
        <div style={styles.brand}>
          <img src={Logo} alt="Endurance" style={styles.logo} />
          <div>
            <span style={styles.appName}>Offline Intelligence</span>
            <span style={styles.appTag}>Industrial Data Platform</span>
          </div>
        </div>

        {/* RIGHT — Run Control */}
        <div style={styles.runSection}>
          {/* Run indicator dot */}
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: hasRun ? "#34d399" : "#9ca3af",
              boxShadow: hasRun ? "0 0 8px rgba(52, 211, 153, 0.5)" : "none",
              transition: "all 0.3s ease",
            }}
          />
          <span style={styles.runText}>
            {hasRun ? (runState.activeFileName || runState.activeRunId) : "No active run"}
          </span>

          <button
            style={{
              ...styles.runButton,
              background: runBtnHover
                ? "rgba(255,255,255,0.2)"
                : "rgba(255,255,255,0.1)",
              borderColor: runBtnHover
                ? "rgba(255,255,255,0.35)"
                : "rgba(255,255,255,0.2)",
            }}
            onMouseEnter={() => setRunBtnHover(true)}
            onMouseLeave={() => setRunBtnHover(false)}
            onClick={() => setShowRunSelector(true)}
          >
            <FiPlay size={12} />
            {hasRun ? "Change" : "Select Run"}
            <FiChevronDown size={13} />
          </button>
        </div>
      </header>

      {/* ================= BODY ================= */}
      <div style={styles.body}>
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed((v) => !v)}
        />

        <main style={styles.content}>
          <Outlet />
        </main>
      </div>

      {showRunSelector && (
        <RunSelectorModal onClose={() => setShowRunSelector(false)} />
      )}
    </div>
  );
};

/* ================= STYLES ================= */

const styles: Record<string, React.CSSProperties> = {
  root: {
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },

  /* Top bar */
  topbar: {
    height: "52px",
    background: "linear-gradient(90deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%)",
    color: "#ffffff",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 20px",
    flexShrink: 0,
    borderBottom: "1px solid rgba(99, 102, 241, 0.2)",
    zIndex: 200,
  },

  brand: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },

  logo: {
    height: "26px",
    filter: "drop-shadow(0 0 4px rgba(129,140,248,0.3))",
  },

  appName: {
    fontSize: "15px",
    fontWeight: 700,
    display: "block",
    letterSpacing: "-0.01em",
  },

  appTag: {
    fontSize: "10px",
    fontWeight: 400,
    color: "rgba(199, 210, 254, 0.6)",
    display: "block",
    marginTop: "-2px",
  },

  runSection: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },

  runText: {
    fontSize: "13px",
    fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
    color: "rgba(224, 231, 255, 0.85)",
    maxWidth: "220px",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },

  runButton: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    background: "rgba(255,255,255,0.1)",
    color: "#ffffff",
    border: "1px solid rgba(255,255,255,0.2)",
    borderRadius: "8px",
    padding: "6px 12px",
    fontSize: "12px",
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.2s ease",
    backdropFilter: "blur(4px)",
  },

  /* Body */
  body: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
  },

  content: {
    flex: 1,
    background: "#f0f1f5",
    padding: "28px 32px",
    overflowY: "auto",
  },
};

export default AppLayout;