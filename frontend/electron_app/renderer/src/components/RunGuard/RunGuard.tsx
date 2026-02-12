import React from "react";
import { FiAlertTriangle } from "react-icons/fi";
import { runUI } from "../../state/run_ui_store";

export function RunGuard({ children }: { children: React.ReactNode }) {
  const { activeRunId } = React.useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  if (!activeRunId) {
    return (
      <div style={container}>
        <div style={card}>
          <div style={iconWrap}>
            <FiAlertTriangle size={36} color="#6366f1" />
          </div>
          <h2 style={title}>No ingestion run selected</h2>
          <p style={subtitle}>
            Please select an ingestion run from the Home page to access this section.
          </p>
          <div style={btnWrap}>
            <span style={selectBtn}>Select Run</span>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

const container: React.CSSProperties = {
  padding: "64px 32px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: "50vh",
};

const card: React.CSSProperties = {
  background: "#ffffff",
  border: "1px solid #e5e7eb",
  borderRadius: "12px",
  padding: "48px 40px",
  textAlign: "center",
  maxWidth: 440,
  width: "100%",
  boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
};

const iconWrap: React.CSSProperties = {
  marginBottom: 16,
};

const title: React.CSSProperties = {
  fontSize: 20,
  fontWeight: 700,
  marginBottom: 8,
  color: "#111827",
};

const subtitle: React.CSSProperties = {
  fontSize: 14,
  color: "#6b7280",
  lineHeight: 1.5,
  marginBottom: 24,
};

const btnWrap: React.CSSProperties = {
  marginTop: 8,
};

const selectBtn: React.CSSProperties = {
  display: "inline-block",
  padding: "10px 20px",
  background: "#f0f1f5",
  color: "#6366f1",
  borderRadius: "8px",
  fontWeight: 600,
  fontSize: 13,
  letterSpacing: "0.3px",
};