import { useState, useSyncExternalStore } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar/Sidebar";
import Logo from "../assets/logo.svg";
import { runUI } from "../state/run_ui_store";
import { RunSelectorModal } from "../components/RunSelector/RunSelectorModal";

const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [showRunSelector, setShowRunSelector] = useState(false);

  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  return (
    <div style={styles.root}>
      {/* ================= TOP BAR ================= */}
      <header style={styles.topbar}>
        <div style={styles.brand}>
          <img src={Logo} alt="Endurance" style={styles.logo} />
          <span style={styles.appName}>Offline Intelligence</span>
        </div>

        <div style={styles.runSection}>
          <span style={styles.runText}>
            Active Run:{" "}
            <strong>
              {runState.activeRunId ?? "None"}
            </strong>
          </span>

          <button
            style={styles.runButton}
            onClick={() => setShowRunSelector(true)}
          >
            {runState.activeRunId ? "Change Run" : "Select Run"}
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
    height: "56px",
    background: "linear-gradient(90deg, #1e1b4b 0%, #312e81 100%)",
    color: "#ffffff",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 20px",
    flexShrink: 0,
  },

  brand: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },

  logo: {
    height: "28px",
  },

  appName: {
    fontSize: "16px",
    fontWeight: 600,
  },

  runSection: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },

  runText: {
    fontSize: "13px",
    opacity: 0.95,
  },

  runButton: {
    background: "#6366f1",
    color: "#ffffff",
    border: "none",
    borderRadius: "6px",
    padding: "6px 10px",
    fontSize: "12px",
    cursor: "pointer",
  },

  /* Body */
  body: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
  },

  content: {
    flex: 1,
    background: "#ffffff",
    padding: "24px",
    overflowY: "auto",
  },
};

export default AppLayout;