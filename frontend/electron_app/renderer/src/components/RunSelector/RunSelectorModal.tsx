import React from "react";
import { runUI } from "../../state/run_ui_store";

interface Props {
  onClose: () => void;
}

export function RunSelectorModal({ onClose }: Props) {
  /**
   * UI-only placeholder.
   * These represent filenames on which ingestion occurred.
   * Will be replaced by backend-provided metadata later.
   */
  const ingestedFiles = [
    "sap_pm_iw29_2024_01_12.xlsx",
    "rfid_log_shiftA_2024_01_13.csv",
    "plc_snapshot_line2_2024_01_14.json",
  ];

  return (
    <div style={overlay}>
      <div style={modal}>
        <h3>Select Ingested File</h3>

        {ingestedFiles.length === 0 ? (
          <p style={muted}>
            No ingested files available yet.
            <br />
            Please ingest data to continue.
          </p>
        ) : (
          <ul style={list}>
            {ingestedFiles.map((fileName) => (
              <li key={fileName}>
                <button
                  style={fileButton}
                  onClick={() => {
                    runUI.setActiveRun(fileName);
                    onClose();
                  }}
                >
                  {fileName}
                </button>
              </li>
            ))}
          </ul>
        )}

        <button onClick={onClose} style={closeButton}>
          Cancel
        </button>
      </div>
    </div>
  );
}

/* ---------- Styles ---------- */

const overlay: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.4)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 1000,
};

const modal: React.CSSProperties = {
  background: "#ffffff",
  padding: 24,
  borderRadius: 8,
  width: 420,
};

const muted: React.CSSProperties = {
  color: "#6b7280",
  fontSize: 14,
  lineHeight: 1.5,
};

const list: React.CSSProperties = {
  listStyle: "none",
  padding: 0,
  marginTop: 16,
  marginBottom: 16,
};

const fileButton: React.CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  textAlign: "left",
  borderRadius: 6,
  border: "1px solid #e5e7eb",
  background: "#f9fafb",
  cursor: "pointer",
  marginBottom: 8,
  fontSize: 14,
  fontFamily: "monospace",
};

const closeButton: React.CSSProperties = {
  marginTop: 8,
};