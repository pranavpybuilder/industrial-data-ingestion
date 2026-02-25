import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { FiActivity, FiAlertTriangle, FiCheckCircle } from "react-icons/fi";

import { frontendApi } from "../../services/frontendApi";
import { runUI } from "../../state/run_ui_store";

type ProfilingRow = {
  column_name: string;
  missing_percentage: number;
  outlier_count: number;
  detected_type: string;
  health_status: string;
};

type DataHealthPayload = {
  run_id: string;
  run_status: string;
  failed_step?: string | null;
  error_message?: string | null;
  profiling_results: ProfilingRow[];
  has_profiling_data: boolean;
};

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

const DataHealth = () => {
  const runState = useSyncExternalStore(runUI.subscribe, runUI.getSnapshot);
  const activeRun = runState.activeRunId;

  const [rows, setRows] = useState<ProfilingRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<DataHealthPayload | null>(null);

  useEffect(() => {
    if (!activeRun) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      const response = await frontendApi.getDataHealth(activeRun);
      setLoading(false);

      if (!response.success) {
        setError(response.message || "Failed to load data health");
        setRows([]);
        setPayload(null);
        return;
      }

      const data = response.data;
      if (Array.isArray(data)) {
        // Backward-compatible payload shape.
        setRows(data);
        setPayload(null);
        return;
      }

      const normalized: DataHealthPayload = {
        run_id: String(data?.run_id || activeRun),
        run_status: String(data?.run_status || "UNKNOWN").toUpperCase(),
        failed_step: data?.failed_step || null,
        error_message: data?.error_message || null,
        profiling_results: Array.isArray(data?.profiling_results)
          ? data.profiling_results
          : [],
        has_profiling_data: Boolean(data?.has_profiling_data),
      };
      setPayload(normalized);
      setRows(normalized.profiling_results);
    };

    load();
  }, [activeRun]);

  const alertCount = useMemo(
    () => rows.filter((r) => r.health_status === "alert").length,
    [rows]
  );

  if (!activeRun) {
    return (
      <section>
        <h1>Data Health</h1>
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
            <FiActivity size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={styles.title}>Data Health</h1>
            <p style={styles.subtitle}>Run: <strong>{activeRun}</strong></p>
          </div>
        </header>

        {loading && <div style={styles.card}>Loading data health...</div>}
        {error && <div style={{ ...styles.card, ...styles.errorCard }}>{error}</div>}

        {!loading && !error && payload?.run_status === "FAILED" && (
          <div style={{ ...styles.card, ...styles.errorCard }}>
            <h3 style={styles.cardTitle}>Run Failure Diagnostics</h3>
            <p style={styles.infoText}>
              This run failed and data health is showing diagnostics for the active failed run.
            </p>
            <p style={styles.infoText}>
              Failed step: <strong>{payload.failed_step || "unknown"}</strong>
            </p>
            <p style={styles.infoText}>
              Error: <strong>{payload.error_message || "No error message recorded"}</strong>
            </p>
          </div>
        )}

        {!loading && !error && (
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>Profiling Summary</h3>
            <p style={styles.infoText}>
              Columns profiled: <strong>{rows.length}</strong> | Alerts: <strong>{alertCount}</strong>
            </p>

            {rows.length === 0 ? (
              <p style={styles.infoText}>No profiling results available for this run.</p>
            ) : (
              <div style={styles.tableWrap}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Column</th>
                      <th style={styles.th}>Type</th>
                      <th style={styles.th}>Missing %</th>
                      <th style={styles.th}>Outliers</th>
                      <th style={styles.th}>Health</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.column_name}>
                        <td style={styles.td}>{row.column_name}</td>
                        <td style={styles.td}>{row.detected_type}</td>
                        <td style={styles.td}>{Number(row.missing_percentage || 0).toFixed(2)}</td>
                        <td style={styles.td}>{row.outlier_count || 0}</td>
                        <td style={styles.td}>
                          {row.health_status === "good" ? (
                            <span style={styles.good}><FiCheckCircle size={14} /> good</span>
                          ) : (
                            <span style={styles.alert}><FiAlertTriangle size={14} /> {row.health_status}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </section>
    </>
  );
};

const styles: Record<string, React.CSSProperties> = {
  page: { maxWidth: "1100px", animation: "fadeIn 0.3s ease-out" },
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
  },
  errorCard: { borderLeft: "4px solid #ef4444", color: "#991b1b" },
  cardTitle: { fontSize: "16px", fontWeight: 600, marginBottom: "10px", color: "#111827" },
  infoText: { fontSize: "14px", color: "#6b7280", marginBottom: "16px" },
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
  td: { fontSize: "14px", color: "#111827", borderBottom: "1px solid #f3f4f6", padding: "10px" },
  good: {
    display: "inline-flex",
    alignItems: "center",
    gap: "5px",
    color: "#047857",
    fontWeight: 600,
  },
  alert: {
    display: "inline-flex",
    alignItems: "center",
    gap: "5px",
    color: "#b45309",
    fontWeight: 600,
  },
};

export default DataHealth;
