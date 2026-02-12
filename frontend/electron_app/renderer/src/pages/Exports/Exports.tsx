import { useState, useSyncExternalStore } from "react";
import { FiDownload, FiCheckCircle, FiAlertCircle } from "react-icons/fi";
import { runUI } from "../../state/run_ui_store";

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

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
    <>
      <style>{fadeKeyframes}</style>
      <section style={styles.page}>
        {/* Header */}
        <header style={styles.header}>
          <div style={styles.headerIcon}>
            <FiDownload size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={styles.title}>Exports</h1>
            <p style={styles.subtitle}>
              Export data for <strong>{activeRun}</strong>
            </p>
          </div>
        </header>

        {/* Export Options */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Export Options</h3>

          {/* Scope */}
          <div style={styles.group}>
            <label style={styles.label} htmlFor="export-scope">
              What do you want to export?
            </label>

            <select
              id="export-scope"
              title="Export scope"
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
            <label style={styles.label} htmlFor="export-format">
              Export format
            </label>

            <select
              id="export-format"
              title="Export format"
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
            onMouseEnter={(e) => {
              if (exportScope && format) e.currentTarget.style.background = "#4f46e5";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "#6366f1";
            }}
          >
            <FiDownload size={14} />
            Export
          </button>

          {/* Status */}
          {status === "success" && (
            <div style={styles.successBanner}>
              <FiCheckCircle size={16} color="#10b981" />
              Export completed successfully.
            </div>
          )}

          {status === "failed" && (
            <div style={styles.errorBanner}>
              <FiAlertCircle size={16} color="#ef4444" />
              Export failed. Please try again.
            </div>
          )}
        </div>
      </section>
    </>
  );
};

/* ================= STYLES ================= */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: "700px",
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

  cardTitle: {
    fontSize: "15px",
    fontWeight: 600,
    marginBottom: "20px",
    color: "#111827",
  },

  group: {
    marginBottom: "18px",
  },

  label: {
    display: "block",
    fontSize: "14px",
    fontWeight: 500,
    marginBottom: "6px",
    color: "#111827",
  },

  select: {
    width: "100%",
    padding: "10px",
    fontSize: "14px",
    borderRadius: "8px",
    border: "1.5px solid #e5e7eb",
    background: "#ffffff",
    color: "#111827",
    outline: "none",
    appearance: "auto" as any,
    transition: "border-color 0.15s",
  },

  primaryBtn: {
    background: "#6366f1",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    padding: "10px 20px",
    fontSize: "14px",
    fontWeight: 500,
    marginTop: "8px",
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    transition: "background 0.15s",
  },

  successBanner: {
    marginTop: "16px",
    padding: "12px 16px",
    background: "#ecfdf5",
    borderLeft: "4px solid #10b981",
    borderRadius: "8px",
    color: "#065f46",
    fontSize: "14px",
    fontWeight: 500,
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },

  errorBanner: {
    marginTop: "16px",
    padding: "12px 16px",
    background: "#fef2f2",
    borderLeft: "4px solid #ef4444",
    borderRadius: "8px",
    color: "#991b1b",
    fontSize: "14px",
    fontWeight: 500,
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
};

export default Exports;