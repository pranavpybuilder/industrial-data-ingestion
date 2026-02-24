import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { FiDatabase, FiSearch } from "react-icons/fi";

import { frontendApi } from "../../services/frontendApi";
import { runUI } from "../../state/run_ui_store";

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

const Explorer = () => {
  const runState = useSyncExternalStore(runUI.subscribe, runUI.getSnapshot);
  const activeRun = runState.activeRunId;

  const [rows, setRows] = useState<Record<string, any>[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [visibleCols, setVisibleCols] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeRun) return;

    const load = async () => {
      setLoading(true);
      setError(null);

      const response = await frontendApi.getExplorerData(activeRun, 500);
      setLoading(false);

      if (!response.success) {
        setError(response.message || "Failed to load explorer data");
        setRows([]);
        setColumns([]);
        setVisibleCols([]);
        return;
      }

      const nextRows = response.data?.rows || [];
      const nextCols = response.data?.columns || [];
      setRows(nextRows);
      setColumns(nextCols);
      setVisibleCols(nextCols);
    };

    load();
  }, [activeRun]);

  const filteredRows = useMemo(() => {
    if (!search.trim()) return rows;
    const needle = search.toLowerCase();
    return rows.filter((row) =>
      Object.values(row).join(" ").toLowerCase().includes(needle)
    );
  }, [rows, search]);

  if (!activeRun) {
    return (
      <section>
        <h1>Explorer</h1>
        <p>No active run selected.</p>
      </section>
    );
  }

  const toggleColumn = (column: string) => {
    setVisibleCols((prev) =>
      prev.includes(column) ? prev.filter((c) => c !== column) : [...prev, column]
    );
  };

  return (
    <>
      <style>{fadeKeyframes}</style>
      <section style={styles.page}>
        <header style={styles.header}>
          <div style={styles.headerIcon}>
            <FiDatabase size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={styles.title}>Explorer</h1>
            <p style={styles.subtitle}>Run: <strong>{activeRun}</strong></p>
          </div>
        </header>

        {loading && <div style={styles.card}>Loading data...</div>}
        {error && <div style={{ ...styles.card, ...styles.errorCard }}>{error}</div>}

        {!loading && !error && (
          <>
            <div style={styles.controls}>
              <div style={styles.searchWrap}>
                <FiSearch size={16} color="#9ca3af" style={{ flexShrink: 0 }} />
                <input
                  type="text"
                  placeholder="Search data..."
                  aria-label="Search data"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  style={styles.searchInput}
                />
              </div>

              <div style={styles.columnBox}>
                <span style={styles.columnLabel}>Columns</span>
                <div style={styles.pillRow}>
                  {columns.map((column) => {
                    const active = visibleCols.includes(column);
                    return (
                      <button
                        key={column}
                        onClick={() => toggleColumn(column)}
                        style={{
                          ...styles.pill,
                          background: active ? "#6366f1" : "#f3f4f6",
                          color: active ? "#ffffff" : "#6b7280",
                          border: active ? "1px solid #6366f1" : "1px solid #e5e7eb",
                        }}
                      >
                        {column}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <div style={styles.tableWrap}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    {visibleCols.map((column) => (
                      <th key={column} style={styles.th}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredRows.map((row, idx) => (
                    <tr key={idx} style={{ background: idx % 2 === 0 ? "#ffffff" : "#f9fafb" }}>
                      {visibleCols.map((column) => (
                        <td key={column} style={styles.td}>{String(row[column] ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={styles.footer}>
              Rows shown: {filteredRows.length} / {rows.length}
            </div>
          </>
        )}
      </section>
    </>
  );
};

const styles: Record<string, React.CSSProperties> = {
  page: { maxWidth: "1200px", animation: "fadeIn 0.3s ease-out" },
  header: { display: "flex", alignItems: "center", gap: "14px", marginBottom: "24px" },
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
    padding: "20px",
    border: "1px solid #e5e7eb",
  },
  errorCard: { borderLeft: "4px solid #ef4444", color: "#991b1b" },
  controls: {
    display: "flex",
    gap: "16px",
    marginBottom: "16px",
    flexWrap: "wrap",
    alignItems: "flex-start",
  },
  searchWrap: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    background: "#ffffff",
    border: "1.5px solid #e5e7eb",
    borderRadius: "8px",
    padding: "8px 12px",
    minWidth: 240,
  },
  searchInput: {
    border: "none",
    outline: "none",
    fontSize: "14px",
    color: "#111827",
    background: "transparent",
    width: "100%",
  },
  columnBox: {
    background: "#ffffff",
    padding: "12px 14px",
    borderRadius: "12px",
    border: "1px solid #e5e7eb",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },
  columnLabel: {
    fontSize: "12px",
    fontWeight: 600,
    display: "block",
    marginBottom: "8px",
    color: "#6b7280",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  pillRow: { display: "flex", gap: "6px", flexWrap: "wrap" },
  pill: {
    padding: "5px 12px",
    borderRadius: "20px",
    fontSize: "12px",
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.15s",
  },
  tableWrap: {
    overflowX: "auto",
    background: "#ffffff",
    borderRadius: "12px",
    border: "1px solid #e5e7eb",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },
  table: { width: "100%", borderCollapse: "collapse" },
  th: {
    textAlign: "left",
    padding: "12px 16px",
    fontSize: "12px",
    fontWeight: 600,
    color: "#6b7280",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    borderBottom: "1px solid #e5e7eb",
    background: "#f9fafb",
  },
  td: {
    padding: "10px 16px",
    fontSize: "14px",
    color: "#111827",
    borderBottom: "1px solid #f3f4f6",
  },
  footer: { marginTop: "12px", fontSize: "13px", color: "#9ca3af", fontWeight: 500 },
};

export default Explorer;
