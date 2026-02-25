import { useEffect, useState, useSyncExternalStore } from "react";
import { FiCheckCircle, FiDownload, FiRefreshCw } from "react-icons/fi";

import { frontendApi } from "../../services/frontendApi";
import { runUI } from "../../state/run_ui_store";

type ExportRow = {
  export_id: string;
  export_type: string;
  scope: string;
  file_path: string;
  created_at: string;
};

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

const Exports = () => {
  const runState = useSyncExternalStore(runUI.subscribe, runUI.getSnapshot);
  const activeRun = runState.activeRunId;

  const [exportScope, setExportScope] = useState<"insights" | "dashboards" | "both" | "">("");
  const [format, setFormat] = useState<"excel" | "pdf" | "csv" | "">("");
  const [status, setStatus] = useState<"idle" | "success" | "failed">("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [exportsList, setExportsList] = useState<ExportRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedOutputDir, setSelectedOutputDir] = useState<string>("");

  const loadExports = async () => {
    if (!activeRun) return;
    setLoading(true);
    const response = await frontendApi.getExports(activeRun);
    setLoading(false);

    if (!response.success) {
      setMessage(response.message || "Failed to load exports");
      setExportsList([]);
      return;
    }

    setExportsList(Array.isArray(response.data) ? response.data : []);
  };

  useEffect(() => {
    loadExports();
  }, [activeRun]);

  const handleExport = async () => {
    if (!activeRun || !exportScope || !format) return;

    setStatus("idle");
    setMessage(null);

    const targetDirResponse = await frontendApi.selectDirectory();
    const selectedDir = targetDirResponse.data?.directory_path;
    if (!targetDirResponse.success || !selectedDir) {
      setStatus("failed");
      setMessage(targetDirResponse.message || "Export folder selection was cancelled.");
      return;
    }
    setSelectedOutputDir(String(selectedDir));

    const response = await frontendApi.generateExport(
      activeRun,
      format,
      exportScope,
      String(selectedDir)
    );
    if (!response.success) {
      setStatus("failed");
      setMessage(response.message || "Export failed");
      return;
    }

    setStatus("success");
    setMessage(
      `${response.message || "Export completed"} Output folder: ${selectedDir}`
    );
    await loadExports();
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
        <header style={styles.header}>
          <div style={styles.headerIcon}>
            <FiDownload size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={styles.title}>Exports</h1>
            <p style={styles.subtitle}>Run: <strong>{activeRun}</strong></p>
          </div>
        </header>

        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Generate Export</h3>

          <div style={styles.group}>
            <label style={styles.label} htmlFor="export-scope">Scope</label>
            <select
              id="export-scope"
              title="Export scope"
              style={styles.select}
              value={exportScope}
              onChange={(e) => setExportScope(e.target.value as typeof exportScope)}
            >
              <option value="">Select scope</option>
              <option value="insights">Insights only</option>
              <option value="dashboards">Dashboards only</option>
              <option value="both">Insights & Dashboards</option>
            </select>
          </div>

          <div style={styles.group}>
            <label style={styles.label} htmlFor="export-format">Format</label>
            <select
              id="export-format"
              title="Export format"
              style={styles.select}
              value={format}
              onChange={(e) => setFormat(e.target.value as typeof format)}
            >
              <option value="">Select format</option>
              <option value="excel">Excel (.xlsx)</option>
              <option value="pdf">PDF (.pdf)</option>
              <option value="csv">CSV bundle</option>
            </select>
          </div>

          <button
            style={{
              ...styles.primaryBtn,
              opacity: exportScope && format ? 1 : 0.5,
              cursor: exportScope && format ? "pointer" : "not-allowed",
            }}
            disabled={!exportScope || !format}
            onClick={handleExport}
          >
            <FiDownload size={14} />
            Generate Export
          </button>

          {selectedOutputDir && (
            <p style={{ ...styles.subtitle, marginTop: "10px" }}>
              Output folder: <strong>{selectedOutputDir}</strong>
            </p>
          )}

          {status === "success" && (
            <div style={styles.successBanner}>
              <FiCheckCircle size={16} color="#10b981" />
              {message || "Export completed successfully."}
            </div>
          )}

          {status === "failed" && (
            <div style={styles.errorBanner}>
              {message || "Export failed. Please try again."}
            </div>
          )}
        </div>

        <div style={styles.card}>
          <div style={styles.listHeader}>
            <h3 style={styles.cardTitle}>Generated Files</h3>
            <button style={styles.refreshBtn} onClick={loadExports}>
              <FiRefreshCw size={14} />
              Refresh
            </button>
          </div>

          {loading ? (
            <p style={styles.subtitle}>Loading exports...</p>
          ) : exportsList.length === 0 ? (
            <p style={styles.subtitle}>No exports generated yet.</p>
          ) : (
            <div style={styles.tableWrap}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Type</th>
                    <th style={styles.th}>Scope</th>
                    <th style={styles.th}>Created</th>
                    <th style={styles.th}>Path</th>
                  </tr>
                </thead>
                <tbody>
                  {exportsList.map((item) => (
                    <tr key={item.export_id}>
                      <td style={styles.td}>{item.export_type}</td>
                      <td style={styles.td}>{item.scope}</td>
                      <td style={styles.td}>{item.created_at}</td>
                      <td style={styles.td}>{item.file_path}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </>
  );
};

const styles: Record<string, React.CSSProperties> = {
  page: { maxWidth: "1000px", animation: "fadeIn 0.3s ease-out" },
  header: { display: "flex", alignItems: "center", gap: "14px", marginBottom: "28px" },
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
  title: { fontSize: "22px", fontWeight: 700, color: "#111827", margin: 0 },
  subtitle: { fontSize: "14px", color: "#6b7280", margin: 0, marginTop: 2 },
  card: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    border: "1px solid #e5e7eb",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
    marginBottom: "16px",
  },
  cardTitle: { fontSize: "15px", fontWeight: 600, marginBottom: "16px", color: "#111827" },
  group: { marginBottom: "18px" },
  label: { display: "block", fontSize: "14px", fontWeight: 500, marginBottom: "6px", color: "#111827" },
  select: {
    width: "100%",
    padding: "10px",
    fontSize: "14px",
    borderRadius: "8px",
    border: "1.5px solid #e5e7eb",
    background: "#ffffff",
    color: "#111827",
    outline: "none",
    appearance: "auto",
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
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
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
  },
  listHeader: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  refreshBtn: {
    border: "1px solid #e5e7eb",
    background: "#ffffff",
    borderRadius: "8px",
    padding: "8px 12px",
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
  },
  tableWrap: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse" },
  th: {
    textAlign: "left",
    fontSize: "12px",
    color: "#6b7280",
    borderBottom: "1px solid #e5e7eb",
    padding: "10px",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  td: { fontSize: "13px", color: "#111827", borderBottom: "1px solid #f3f4f6", padding: "10px" },
};

export default Exports;
