import React from "react";
import { runUI } from "../../state/run_ui_store";

export function RunGuard({ children }: { children: React.ReactNode }) {
  const { activeRunId } = React.useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  if (!activeRunId) {
    return (
      <div style={container}>
        <h2 style={title}>No ingestion run selected</h2>
        <p style={subtitle}>
          Please select an ingestion run from the Home page to access this section.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}

const container: React.CSSProperties = {
  padding: "48px 32px",
  textAlign: "center",
};

const title: React.CSSProperties = {
  fontSize: 22,
  fontWeight: 600,
  marginBottom: 8,
};

const subtitle: React.CSSProperties = {
  fontSize: 15,
  color: "#6b7280",
};