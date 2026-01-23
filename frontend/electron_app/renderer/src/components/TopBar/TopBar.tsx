import { useSyncExternalStore } from "react";
import Logo from "assets/logo.svg";
import { runUI } from "../../state/run_ui_store";

const TopBar = () => {
  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  return (
    <header
      style={{
        height: "56px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 16px",
        background: "#1e1b4b",
        color: "#ffffff",
      }}
    >
      {/* LEFT */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <img src={Logo} alt="Endurance" style={{ height: "28px" }} />
        <strong>Offline Intelligence</strong>
      </div>

      {/* RIGHT – ACTIVE RUN */}
      <div style={{ fontSize: "13px" }}>
        <strong>Active Run:</strong>{" "}
        {runState.activeRunId ?? "None"}
      </div>
    </header>
  );
};

export default TopBar;