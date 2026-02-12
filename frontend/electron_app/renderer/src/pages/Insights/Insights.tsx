import { useSyncExternalStore } from "react";
import { useNavigate } from "react-router-dom";
import { FiBarChart2, FiArrowRight, FiDownload } from "react-icons/fi";
import { runUI } from "../../state/run_ui_store";

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

const Insights = () => {
  const navigate = useNavigate();

  const runState = useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const activeRun = runState.activeRunId;

  if (!activeRun) {
    return (
      <section>
        <h1>Insights</h1>
        <p>No active run selected.</p>
      </section>
    );
  }

  /* 🔹 MOCKED DATA – Backend will replace this */
  const summaryPoints = [
    "The dataset contains consistent operational records across the observed period.",
    "Energy consumption shows noticeable variation during peak operating hours.",
    "Breakdown frequency is higher in specific operational intervals.",
  ];

  const decisionInsight =
    "Energy optimization opportunities exist during high-load operational windows, indicating potential cost-saving interventions.";

  const aggregations = [
    { label: "Total Breakdowns", value: "18", color: "#ef4444" },
    { label: "Total Energy Consumption", value: "12,450 kWh", color: "#6366f1" },
    { label: "Average Downtime", value: "42 mins", color: "#f59e0b" },
  ];

  return (
    <>
      <style>{fadeKeyframes}</style>
      <section style={styles.page}>
        {/* Header */}
        <header style={styles.header}>
          <div style={styles.headerIcon}>
            <FiBarChart2 size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={styles.title}>Insights</h1>
            <p style={styles.subtitle}>
              Generated insights for{" "}
              <strong>{activeRun}</strong>
            </p>
          </div>
        </header>

        {/* Summary */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Summary</h3>
          <ul style={styles.list}>
            {summaryPoints.map((point, idx) => (
              <li key={idx} style={styles.listItem}>{point}</li>
            ))}
          </ul>
        </div>

        {/* Decision Insight */}
        <div style={{ ...styles.card, ...styles.decisionCard }}>
          <h3 style={styles.cardTitle}>
            Key Decision Insight
          </h3>
          <p style={styles.decisionText}>
            {decisionInsight}
          </p>
        </div>

        {/* Aggregations */}
        <div style={styles.aggregationGrid}>
          {aggregations.map((item) => (
            <div key={item.label} style={styles.metricCard}>
              <div style={{ ...styles.metricTopBorder, borderTopColor: item.color }} />
              <div style={styles.metricBody}>
                <div style={styles.metricLabel}>
                  {item.label}
                </div>
                <div style={styles.metricValue}>
                  {item.value}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div style={styles.actions}>
          <button
            style={styles.primaryBtn}
            onClick={() => navigate("/dashboards")}
            onMouseEnter={(e) => { (e.currentTarget.style.background) = "#4f46e5"; }}
            onMouseLeave={(e) => { (e.currentTarget.style.background) = "#6366f1"; }}
          >
            <FiArrowRight size={15} />
            Go to Dashboards
          </button>

          <button
            style={styles.secondaryBtn}
            onClick={() => navigate("/exports")}
            onMouseEnter={(e) => { e.currentTarget.style.background = "#f3f4f6"; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = "#ffffff"; }}
          >
            <FiDownload size={15} />
            Export Insights
          </button>
        </div>
      </section>
    </>
  );
};

/* ================= STYLES ================= */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: "1100px",
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
    padding: "20px",
    marginBottom: "20px",
    border: "1px solid #e5e7eb",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },

  decisionCard: {
    borderLeft: "4px solid #6366f1",
  },

  cardTitle: {
    fontSize: "15px",
    fontWeight: 600,
    marginBottom: "10px",
    color: "#111827",
  },

  list: {
    paddingLeft: "18px",
    fontSize: "14px",
    lineHeight: 1.8,
    color: "#374151",
    margin: 0,
  },

  listItem: {
    marginBottom: "4px",
  },

  decisionText: {
    fontSize: "15px",
    fontWeight: 500,
    color: "#111827",
    lineHeight: 1.6,
  },

  aggregationGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "16px",
    marginBottom: "28px",
  },

  metricCard: {
    background: "#ffffff",
    borderRadius: "12px",
    overflow: "hidden",
    border: "1px solid #e5e7eb",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },

  metricTopBorder: {
    height: 3,
    borderTop: "3px solid transparent",
  },

  metricBody: {
    padding: "16px",
  },

  metricLabel: {
    fontSize: "13px",
    color: "#6b7280",
    marginBottom: "6px",
  },

  metricValue: {
    fontSize: "20px",
    fontWeight: 700,
    color: "#111827",
  },

  actions: {
    display: "flex",
    gap: "12px",
  },

  primaryBtn: {
    background: "#6366f1",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    padding: "10px 18px",
    fontSize: "14px",
    fontWeight: 500,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    transition: "background 0.15s",
  },

  secondaryBtn: {
    background: "#ffffff",
    color: "#111827",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    padding: "10px 18px",
    fontSize: "14px",
    fontWeight: 500,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    transition: "background 0.15s",
  },
};

export default Insights;