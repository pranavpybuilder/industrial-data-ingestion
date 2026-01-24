import { useSyncExternalStore } from "react";
import { useNavigate } from "react-router-dom";
import { runUI } from "../../state/run_ui_store";

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
    { label: "Total Breakdowns", value: "18" },
    { label: "Total Energy Consumption", value: "12,450 kWh" },
    { label: "Average Downtime", value: "42 mins" },
  ];

  return (
    <section style={styles.page}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.title}>Insights</h1>
        <p style={styles.subtitle}>
          Generated insights for{" "}
          <strong>{activeRun}</strong>
        </p>
      </header>

      {/* Summary */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Summary</h3>
        <ul style={styles.list}>
          {summaryPoints.map((point, idx) => (
            <li key={idx}>{point}</li>
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
            <div style={styles.metricLabel}>
              {item.label}
            </div>
            <div style={styles.metricValue}>
              {item.value}
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div style={styles.actions}>
        <button
          style={styles.primaryBtn}
          onClick={() => navigate("/dashboards")}
        >
          Go to Dashboards
        </button>

        <button
          style={styles.secondaryBtn}
          onClick={() => navigate("/exports")}
        >
          Export Insights
        </button>
      </div>
    </section>
  );
};

/* ================= STYLES ================= */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: "1100px",
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
    marginBottom: "20px",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },

  decisionCard: {
    borderLeft: "4px solid #6366f1",
  },

  cardTitle: {
    fontSize: "16px",
    fontWeight: 600,
    marginBottom: "10px",
  },

  list: {
    paddingLeft: "18px",
    fontSize: "14px",
    lineHeight: 1.6,
  },

  decisionText: {
    fontSize: "15px",
    fontWeight: 500,
    color: "#111827",
  },

  aggregationGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "16px",
    marginBottom: "28px",
  },

  metricCard: {
    background: "#ffffff",
    borderRadius: "8px",
    padding: "16px",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },

  metricLabel: {
    fontSize: "13px",
    color: "#6b7280",
    marginBottom: "6px",
  },

  metricValue: {
    fontSize: "18px",
    fontWeight: 600,
  },

  actions: {
    display: "flex",
    gap: "12px",
  },

  primaryBtn: {
    background: "#6366f1",
    color: "#ffffff",
    border: "none",
    borderRadius: "6px",
    padding: "10px 16px",
    fontSize: "14px",
    cursor: "pointer",
  },

  secondaryBtn: {
    background: "#e5e7eb",
    border: "none",
    borderRadius: "6px",
    padding: "10px 16px",
    fontSize: "14px",
    cursor: "pointer",
  },
};

export default Insights;