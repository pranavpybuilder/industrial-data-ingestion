import { useState, useSyncExternalStore } from "react";
import { runUI } from "../../state/run_ui_store";

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
    <section style={styles.page}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.title}>Explorer</h1>
        <p style={styles.subtitle}>
          Viewing data for <strong>{activeRun}</strong>
        </p>
      </header>

      {/* Controls */}
      <div style={styles.controls}>
        <input
          type="text"
          placeholder="Search data..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={styles.search}
        />

        <div style={styles.columnBox}>
          <span style={styles.columnLabel}>
            Columns
          </span>
          {columns.map((col) => (
            <label key={col} style={styles.checkbox}>
              <input
                type="checkbox"
                checked={visibleCols.includes(col)}
                onChange={() => toggleColumn(col)}
              />
              {col}
            </label>
          ))}
        </div>
      </div>

      {/* Table */}
      <div style={styles.tableWrap}>
        <table style={styles.table}>
          <thead>
            <tr>
              {visibleCols.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredData.map((row, idx) => (
              <tr key={idx}>
                {visibleCols.map((col) => (
                  <td key={col}>
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
  );
};

/* ================= STYLES ================= */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: "1200px",
  },

  header: {
    marginBottom: "20px",
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

  controls: {
    display: "flex",
    gap: "20px",
    marginBottom: "16px",
    flexWrap: "wrap",
  },

  search: {
    padding: "8px",
    fontSize: "14px",
    borderRadius: "6px",
    border: "1px solid #d1d5db",
    width: "240px",
  },

  columnBox: {
    background: "#ffffff",
    padding: "10px",
    borderRadius: "6px",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },

  columnLabel: {
    fontSize: "13px",
    fontWeight: 600,
    display: "block",
    marginBottom: "6px",
  },

  checkbox: {
    display: "block",
    fontSize: "13px",
  },

  tableWrap: {
    overflowX: "auto",
    background: "#ffffff",
    borderRadius: "8px",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },

  table: {
    width: "100%",
    borderCollapse: "collapse",
  },

  footer: {
    marginTop: "10px",
    fontSize: "13px",
    color: "#6b7280",
  },
};

export default Explorer;