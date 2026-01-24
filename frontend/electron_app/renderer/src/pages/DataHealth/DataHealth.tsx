import { useSyncExternalStore } from "react";
import { useNavigate } from "react-router-dom";
import { runUI } from "../../state/run_ui_store";

/**
 * Data Health Page
 *
 * Explains ingestion success or failure
 * and provides column-level diagnostics.
 */
const DataHealth = () => {
  const navigate = useNavigate();

  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const activeRun = runState.activeRunId;

  /* 🔹 MOCKED STATUS – backend will control this */
  const ingestionStatus: "success" | "failed" = activeRun
    ? "success"
    : "failed";

  /* 🔹 MOCKED DATA */
  const usedColumns = [
    "timestamp",
    "machine_id",
    "downtime_minutes",
    "energy_kwh",
    "shift",
  ];

  const failedReasons = [
    {
      issue: "Missing required column",
      detail: "Column 'machine_id' not found",
      suggestion:
        "Rename existing column 'machineId' to 'machine_id'",
    },
    {
      issue: "Invalid data type",
      detail: "Column 'timestamp' contains non-date values",
      suggestion:
        "Ensure timestamp column contains valid datetime values",
    },
  ];

  return (
    <section style={styles.page}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.title}>Data Health</h1>
        <p style={styles.subtitle}>
          {ingestionStatus === "success"
            ? `Data validation results for ${activeRun}`
            : "Ingestion validation failed"}
        </p>
      </header>

      {/* SUCCESS CASE */}
      {ingestionStatus === "success" && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>
            Columns Used for Analysis
          </h3>

          <p style={styles.infoText}>
            The following columns were successfully validated and
            used to generate insights and dashboards.
          </p>

          <ul style={styles.columnList}>
            {usedColumns.map((col) => (
              <li key={col}>{col}</li>
            ))}
          </ul>
        </div>
      )}

      {/* FAILURE CASE */}
      {ingestionStatus === "failed" && (
        <div style={{ ...styles.card, ...styles.errorCard }}>
          <h3 style={styles.cardTitle}>
            Ingestion Issues Detected
          </h3>

          <p style={styles.infoText}>
            The ingestion process failed due to the following
            issues. Please review and correct the file.
          </p>

          {failedReasons.map((item, idx) => (
            <div key={idx} style={styles.issueBox}>
              <div style={styles.issueTitle}>
                {item.issue}
              </div>
              <div style={styles.issueDetail}>
                {item.detail}
              </div>
              <div style={styles.issueSuggestion}>
                Suggestion: {item.suggestion}
              </div>
            </div>
          ))}

          <div style={styles.actions}>
            <button
              style={styles.primaryBtn}
              onClick={() => navigate("/ingestion")}
            >
              Retry Ingestion
            </button>
          </div>
        </div>
      )}
    </section>
  );
};

/* ================= STYLES ================= */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: "1000px",
  },

  header: {
    marginBottom: "24px",
  },

  title: {
    fontSize: "24px",
    fontWeight: 600,
    marginBottom: "4px",
  },

  subtitle: {
    fontSize: "14px",
    color: "#4b5563",
  },

  card: {
    background: "#ffffff",
    borderRadius: "8px",
    padding: "20px",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },

  errorCard: {
    borderLeft: "4px solid #dc2626",
  },

  cardTitle: {
    fontSize: "16px",
    fontWeight: 600,
    marginBottom: "12px",
  },

  infoText: {
    fontSize: "14px",
    color: "#374151",
    marginBottom: "14px",
  },

  columnList: {
    paddingLeft: "18px",
    fontSize: "14px",
    lineHeight: 1.6,
  },

  issueBox: {
    background: "#fef2f2",
    border: "1px solid #fecaca",
    borderRadius: "6px",
    padding: "12px",
    marginBottom: "12px",
  },

  issueTitle: {
    fontSize: "14px",
    fontWeight: 600,
    color: "#991b1b",
    marginBottom: "4px",
  },

  issueDetail: {
    fontSize: "13px",
    marginBottom: "4px",
  },

  issueSuggestion: {
    fontSize: "13px",
    fontStyle: "italic",
  },

  actions: {
    marginTop: "16px",
  },

  primaryBtn: {
    background: "#dc2626",
    color: "#ffffff",
    border: "none",
    borderRadius: "6px",
    padding: "10px 16px",
    fontSize: "14px",
    cursor: "pointer",
  },
};

export default DataHealth;