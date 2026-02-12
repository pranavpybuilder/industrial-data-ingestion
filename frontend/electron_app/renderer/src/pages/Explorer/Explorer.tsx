import { useState, useSyncExternalStore } from "react";
import { FiSearch, FiDatabase } from "react-icons/fi";
import { runUI } from "../../state/run_ui_store";

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

/**
 * Explorer Page
 *
 * Allows users to explore raw, run-level data
 * in tabular form without affecting dashboards.
 */
const Explorer = () => {
  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const activeRun = runState.activeRunId;

  /* 🔹 MOCK DATA – backend will replace */
  const rawData = [
    {
      timestamp: "2026-01-21 08:00",
      machine_id: "M-01",
      energy_kwh: 32,
      downtime_min: 5,
      shift: "A",
    },
    {
      timestamp: "2026-01-21 09:00",
      machine_id: "M-02",
      energy_kwh: 45,
      downtime_min: 0,
      shift: "A",
    },
    {
      timestamp: "2026-01-21 10:00",
      machine_id: "M-01",
      energy_kwh: 38,
      downtime_min: 12,
      shift: "B",
    },
  ];

  const columns = Object.keys(rawData[0] || {});
  const [visibleCols, setVisibleCols] =
    useState<string[]>(columns);
  const [search, setSearch] = useState("");

  if (!activeRun) {
    return (
      <section>
        <h1>Explorer</h1>
        <p>No active run selected.</p>
      </section>
    );
  }

  const filteredData = rawData.filter((row) =>
    Object.values(row)
      .join(" ")
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  const toggleColumn = (col: string) => {
    setVisibleCols((prev) =>
      prev.includes(col)
        ? prev.filter((c) => c !== col)
        : [...prev, col]
    );
  };

  return (
    <>
      <style>{fadeKeyframes}</style>
      <section style={styles.page}>
        {/* Header */}
        <header style={styles.header}>
          <div style={styles.headerIcon}>
            <FiDatabase size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={styles.title}>Explorer</h1>
            <p style={styles.subtitle}>
              Viewing data for <strong>{activeRun}</strong>
            </p>
          </div>
        </header>

        {/* Controls */}
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
            <span style={styles.columnLabel}>
              Columns
            </span>
            <div style={styles.pillRow}>
              {columns.map((col) => {
                const active = visibleCols.includes(col);
                return (
                  <button
                    key={col}
                    onClick={() => toggleColumn(col)}
                    style={{
                      ...styles.pill,
                      background: active ? "#6366f1" : "#f3f4f6",
                      color: active ? "#ffffff" : "#6b7280",
                      border: active
                        ? "1px solid #6366f1"
                        : "1px solid #e5e7eb",
                    }}
                  >
                    {col}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Table */}
        <div style={styles.tableWrap}>
          <table style={styles.table}>
            <thead>
              <tr>
                {visibleCols.map((col) => (
                  <th key={col} style={styles.th}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredData.map((row, idx) => (
                <tr
                  key={idx}
                  style={{
                    background: idx % 2 === 0 ? "#ffffff" : "#f9fafb",
                  }}
                >
                  {visibleCols.map((col) => (
                    <td key={col} style={styles.td}>
                      {(row as any)[col]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div style={styles.footer}>
          Rows: {filteredData.length}
        </div>
      </section>
    </>
  );
};

/* ================= STYLES ================= */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: "1200px",
    animation: "fadeIn 0.3s ease-out",
  },

  header: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    marginBottom: "24px",
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
    minWidth: 220,
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
    textTransform: "uppercase" as const,
    letterSpacing: "0.5px",
  },

  pillRow: {
    display: "flex",
    gap: "6px",
    flexWrap: "wrap" as const,
  },

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

  table: {
    width: "100%",
    borderCollapse: "collapse",
  },

  th: {
    textAlign: "left" as const,
    padding: "12px 16px",
    fontSize: "12px",
    fontWeight: 600,
    color: "#6b7280",
    textTransform: "uppercase" as const,
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

  footer: {
    marginTop: "12px",
    fontSize: "13px",
    color: "#9ca3af",
    fontWeight: 500,
  },
};

export default Explorer;