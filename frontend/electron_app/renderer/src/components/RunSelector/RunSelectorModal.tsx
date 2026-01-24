import React from "react";
import { onRunChange } from "../../state/state_reset";

interface Props {
  onClose: () => void;
}

/**
 * RunSelectorModal
 *
 * Purpose:
 * - Allows user to select an already ingested dataset (run)
 * - Delegates ALL state changes to the central orchestration layer
 *
 * IMPORTANT:
 * - This component NEVER talks directly to runUI or dashboardsUI
 * - All side effects go through `onRunChange`
 */
export function RunSelectorModal({ onClose }: Props) {
  /**
   * UI-only placeholder list.
   * Later this will come from backend / IPC.
   */
  const ingestedFiles = [
    "sap_pm_iw29_2024_01_12.xlsx",
    "rfid_log_shiftA_2024_01_13.csv",
    "plc_snapshot_line2_2024_01_14.json",
    "test_log.csv",
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
                    /**
                     * CENTRALIZED STATE CHANGE
                     * ------------------------
                     * This will:
                     * 1. Set active run
                     * 2. Reset dashboard state
                     * 3. Initialize dashboard for this run
                     */
                    onRunChange(fileName);
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

/* -------------------- Styles -------------------- */

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