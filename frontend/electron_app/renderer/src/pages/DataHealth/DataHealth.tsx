import { useSyncExternalStore } from "react";
import { useNavigate } from "react-router-dom";
import { FiCheckCircle, FiAlertTriangle, FiActivity, FiRefreshCw } from "react-icons/fi";
import { runUI } from "../../state/run_ui_store";

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

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
    <>
      <style>{fadeKeyframes}</style>
      <section style={styles.page}>
        {/* Header */}
        <header style={styles.header}>
          <div style={styles.headerIcon}>
            <FiActivity size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={styles.title}>Data Health</h1>
            <p style={styles.subtitle}>
              {ingestionStatus === "success"
                ? `Data validation results for ${activeRun}`
                : "Ingestion validation failed"}
            </p>
          </div>
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

            <div style={styles.columnGrid}>
              {usedColumns.map((col) => (
                <div key={col} style={styles.columnItem}>
                  <FiCheckCircle size={16} color="#10b981" style={{ flexShrink: 0 }} />
                  <span>{col}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* FAILURE CASE */}
        {ingestionStatus === "failed" && (
          <div style={{ ...styles.card, ...styles.errorCard }}>
            <h3 style={styles.cardTitle}>
              <FiAlertTriangle size={18} color="#ef4444" style={{ marginRight: 8, verticalAlign: "middle" }} />
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
                style={styles.retryBtn}
                onClick={() => navigate("/ingestion")}
                onMouseEnter={(e) => { e.currentTarget.style.background = "#dc2626"; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = "#ef4444"; }}
              >
                <FiRefreshCw size={14} />
                Retry Ingestion
              </button>
            </div>
          </div>
        )}
      </section>
    </>
  );
};

/* ================= STYLES ================= */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: "1000px",
    animation: "fadeIn 0.3s ease-out",
  },

  header: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    marginBottom: "28px",
  },

  headerIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    background: "#eef2ff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },

  title: {
    fontSize: "22px",
    fontWeight: 700,
    color: "#111827",
    margin: 0,
  },

  subtitle: {
    fontSize: "14px",
    color: "#6b7280",
    margin: 0,
    marginTop: 2,
  },

  card: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    border: "1px solid #e5e7eb",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },

  errorCard: {
    borderLeft: "4px solid #ef4444",
  },

  cardTitle: {
    fontSize: "15px",
    fontWeight: 600,
    marginBottom: "14px",
    color: "#111827",
  },

  infoText: {
    fontSize: "14px",
    color: "#6b7280",
    marginBottom: "18px",
    lineHeight: 1.6,
  },

  columnGrid: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "10px",
  },

  columnItem: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    fontSize: "14px",
    fontWeight: 500,
    color: "#111827",
    padding: "10px 14px",
    background: "#f0fdf4",
    borderRadius: "8px",
    border: "1px solid #bbf7d0",
  },

  issueBox: {
    background: "#fef2f2",
    borderLeft: "4px solid #ef4444",
    borderRadius: "8px",
    padding: "14px 16px",
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
    color: "#374151",
    marginBottom: "4px",
  },

  issueSuggestion: {
    fontSize: "13px",
    fontStyle: "italic",
    color: "#6b7280",
  },

  actions: {
    marginTop: "20px",
  },

  retryBtn: {
    background: "#ef4444",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    padding: "10px 20px",
    fontSize: "14px",
    fontWeight: 500,
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    transition: "background 0.15s",
  },
};

export default DataHealth;