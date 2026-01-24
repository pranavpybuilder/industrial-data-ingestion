import { useState, useSyncExternalStore } from "react";
import { runUI } from "../../state/run_ui_store";

/**
 * Exports Page
 *
 * Allows exporting insights, dashboards,
 * or both for the active run.
 */
const Exports = () => {
  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const activeRun = runState.activeRunId;

  const [exportScope, setExportScope] = useState<
    "insights" | "dashboards" | "both" | ""
  >("");
  const [format, setFormat] = useState<
    "excel" | "pdf" | ""
  >("");
  const [status, setStatus] = useState<
    "idle" | "success" | "failed"
  >("idle");

  const handleExport = () => {
    if (!exportScope || !format) return;

    // 🔹 MOCK EXPORT LOGIC – backend/electron will replace
    const success =  true;

    setStatus(success ? "success" : "failed");
  };

  if (!activeRun) {
    return (
      <section>
        <h1>Exports</h1>
        <p>No active run selected.</p>
      </section>
    );
  }

  return (
    <section style={styles.page}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.title}>Exports</h1>
        <p style={styles.subtitle}>
          Export data for <strong>{activeRun}</strong>
        </p>
      </header>

      {/* Export Options */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Export Options</h3>

        {/* Scope */}
        <div style={styles.group}>
          <label style={styles.label}>
            What do you want to export?
          </label>

          <select
            style={styles.select}
            value={exportScope}
            onChange={(e) =>
              setExportScope(
                e.target.value as typeof exportScope
              )
            }
          >
            <option value="">Select option</option>
            <option value="insights">
              Insights only
            </option>
            <option value="dashboards">
              Dashboards only
            </option>
            <option value="both">
              Insights & Dashboards
            </option>
          </select>
        </div>

        {/* Format */}
        <div style={styles.group}>
          <label style={styles.label}>
            Export format
          </label>

          <select
            style={styles.select}
            value={format}
            onChange={(e) =>
              setFormat(
                e.target.value as typeof format
              )
            }
          >
            <option value="">Select format</option>
            <option value="excel">Excel (.xlsx)</option>
            <option value="pdf">PDF (.pdf)</option>
          </select>
        </div>

        {/* Action */}
        <button
          style={{
            ...styles.primaryBtn,
            opacity:
              exportScope && format ? 1 : 0.5,
            cursor:
              exportScope && format
                ? "pointer"
                : "not-allowed",
          }}
          disabled={!exportScope || !format}
          onClick={handleExport}
        >
          Export
        </button>

        {/* Status */}
        {status === "success" && (
          <p style={styles.successText}>
            Export completed successfully.
          </p>
        )}

        {status === "failed" && (
          <p style={styles.errorText}>
            Export failed. Please try again.
          </p>
        )}
      </div>
    </section>
  );
};

/* ================= STYLES ================= */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: "700px",
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

  cardTitle: {
    fontSize: "16px",
    fontWeight: 600,
    marginBottom: "16px",
  },

  group: {
    marginBottom: "16px",
  },

  label: {
    display: "block",
    fontSize: "14px",
    marginBottom: "6px",
  },

  select: {
    width: "100%",
    padding: "8px",
    fontSize: "14px",
    borderRadius: "6px",
    border: "1px solid #d1d5db",
  },

  primaryBtn: {
    background: "#6366f1",
    color: "#ffffff",
    border: "none",
    borderRadius: "6px",
    padding: "10px 16px",
    fontSize: "14px",
    marginTop: "8px",
  },

  successText: {
    marginTop: "12px",
    color: "#065f46",
    fontSize: "14px",
  },

  errorText: {
    marginTop: "12px",
    color: "#991b1b",
    fontSize: "14px",
  },
};

export default Exports;