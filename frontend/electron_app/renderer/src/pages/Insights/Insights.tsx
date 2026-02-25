import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { useNavigate } from "react-router-dom";
import { FiArrowRight, FiBarChart2, FiDownload } from "react-icons/fi";

import { frontendApi } from "../../services/frontendApi";
import { runUI } from "../../state/run_ui_store";

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

type Insight = {
  insight_id?: string;
  title?: string;
  description?: string;
  severity?: string;
  source?: string;
  priority_score?: number;
  confidence?: number;
  details?: Record<string, any>;
};

type ExecutiveNarrative = {
  sections?: {
    "Executive Summary"?: string;
    "Key Decision Insight"?: string;
    "Core Metrics"?: Record<string, any>;
    "Critical Alerts"?: string[];
    "Machine Intelligence"?: string[];
    "Predictive Insights"?: string[];
    "Optimization Opportunities"?: string[];
    "System Verdict"?: {
      verdict?: string;
      risk_score?: number;
      machine_health_score?: number;
      system_maturity_score?: number;
      prediction_confidence?: number;
    };
  };
};

const Insights = () => {
  const navigate = useNavigate();
  const runState = useSyncExternalStore(runUI.subscribe, runUI.getSnapshot);
  const activeRun = runState.activeRunId;

  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeRun) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      const response = await frontendApi.getInsights(activeRun);
      setLoading(false);

      if (!response.success) {
        setError(response.message || "Failed to load insights");
        setInsights([]);
        return;
      }

      setInsights(Array.isArray(response.data) ? response.data : []);
    };

    load();
  }, [activeRun]);

  const executiveNarrative = useMemo<ExecutiveNarrative | null>(() => {
    for (const insight of insights) {
      const narrative = insight.details?.executive_narrative;
      if (narrative && typeof narrative === "object") {
        return narrative as ExecutiveNarrative;
      }
    }
    return null;
  }, [insights]);

  const operationalInsights = useMemo(
    () => insights.filter((insight) => !insight.details?.executive_narrative),
    [insights]
  );

  const summaryPoints = useMemo(() => {
    return operationalInsights
      .slice(0, 3)
      .map((insight) => insight.description || insight.title || "No description");
  }, [operationalInsights]);

  const criticalCount = useMemo(
    () => operationalInsights.filter((i) => (i.severity || "").toUpperCase() === "CRITICAL").length,
    [operationalInsights]
  );
  const warningCount = useMemo(
    () => operationalInsights.filter((i) => (i.severity || "").toUpperCase() === "WARNING").length,
    [operationalInsights]
  );
  const avgPriority = useMemo(() => {
    if (!operationalInsights.length) return 0;
    const values = operationalInsights.map((i) => Number(i.priority_score ?? 0));
    return values.reduce((acc, v) => acc + v, 0) / values.length;
  }, [operationalInsights]);

  if (!activeRun) {
    return (
      <section>
        <h1>Insights</h1>
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
            <FiBarChart2 size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={styles.title}>Insights</h1>
            <p style={styles.subtitle}>Run: <strong>{activeRun}</strong></p>
          </div>
        </header>

        {loading && <div style={styles.card}>Loading insights...</div>}
        {error && <div style={{ ...styles.card, ...styles.error }}>{error}</div>}

        {!loading && !error && (
          <>
            {executiveNarrative?.sections && (
              <div style={styles.card}>
                <h3 style={styles.cardTitle}>Executive Summary</h3>
                <p style={styles.paragraph}>
                  {executiveNarrative.sections["Executive Summary"] || "No executive summary generated."}
                </p>

                <h3 style={styles.cardTitle}>Key Decision Insight</h3>
                <p style={styles.paragraph}>
                  {executiveNarrative.sections["Key Decision Insight"] || "No key decision insight generated."}
                </p>

                <h3 style={styles.cardTitle}>Core Metrics</h3>
                <div style={styles.metricGrid}>
                  {Object.entries(executiveNarrative.sections["Core Metrics"] || {}).map(([key, value]) => (
                    <div key={key} style={styles.inlineMetric}>
                      <span style={styles.inlineMetricLabel}>{key}</span>
                      <strong style={styles.inlineMetricValue}>{String(value)}</strong>
                    </div>
                  ))}
                </div>

                <h3 style={styles.cardTitle}>Critical Alerts</h3>
                <ul style={styles.list}>
                  {(executiveNarrative.sections["Critical Alerts"] || ["No critical alerts generated."]).map((item, idx) => (
                    <li key={`alert-${idx}`} style={styles.listItem}>{item}</li>
                  ))}
                </ul>

                <h3 style={styles.cardTitle}>Machine Intelligence</h3>
                <ul style={styles.list}>
                  {(executiveNarrative.sections["Machine Intelligence"] || ["No machine intelligence generated."]).map((item, idx) => (
                    <li key={`machine-${idx}`} style={styles.listItem}>{item}</li>
                  ))}
                </ul>

                <h3 style={styles.cardTitle}>Predictive Insights (ML-backed)</h3>
                <ul style={styles.list}>
                  {(executiveNarrative.sections["Predictive Insights"] || ["No predictive insights generated."]).map((item, idx) => (
                    <li key={`predictive-${idx}`} style={styles.listItem}>{item}</li>
                  ))}
                </ul>

                <h3 style={styles.cardTitle}>Optimization Opportunities</h3>
                <ul style={styles.list}>
                  {(executiveNarrative.sections["Optimization Opportunities"] || ["No optimization opportunities generated."]).map((item, idx) => (
                    <li key={`opt-${idx}`} style={styles.listItem}>{item}</li>
                  ))}
                </ul>

                <h3 style={styles.cardTitle}>System Verdict</h3>
                <div style={styles.verdictBox}>
                  <p style={styles.paragraph}>
                    {executiveNarrative.sections["System Verdict"]?.verdict || "No verdict generated."}
                  </p>
                  <p style={styles.paragraph}>
                    Risk Score: <strong>{String(executiveNarrative.sections["System Verdict"]?.risk_score ?? 0)}</strong> |{" "}
                    Machine Health Score: <strong>{String(executiveNarrative.sections["System Verdict"]?.machine_health_score ?? 0)}</strong> |{" "}
                    System Maturity Score: <strong>{String(executiveNarrative.sections["System Verdict"]?.system_maturity_score ?? 0)}</strong>
                  </p>
                </div>
              </div>
            )}

            <div style={styles.card}>
              <h3 style={styles.cardTitle}>Summary</h3>
              {summaryPoints.length ? (
                <ul style={styles.list}>
                  {summaryPoints.map((point, idx) => (
                    <li key={idx} style={styles.listItem}>{point}</li>
                  ))}
                </ul>
              ) : (
                <p style={styles.emptyText}>No insights generated for this run.</p>
              )}
            </div>

            <div style={styles.aggregationGrid}>
              <MetricCard label="Total Insights" value={String(operationalInsights.length)} color="#6366f1" />
              <MetricCard label="Critical Alerts" value={String(criticalCount)} color="#ef4444" />
              <MetricCard label="Warnings" value={String(warningCount)} color="#f59e0b" />
              <MetricCard label="Avg Priority Score" value={avgPriority.toFixed(2)} color="#10b981" />
            </div>

            <div style={styles.actions}>
              <button style={styles.primaryBtn} onClick={() => navigate("/dashboards")}>
                <FiArrowRight size={15} />
                Go to Dashboards
              </button>

              <button style={styles.secondaryBtn} onClick={() => navigate("/exports")}>
                <FiDownload size={15} />
                Open Exports
              </button>
            </div>
          </>
        )}
      </section>
    </>
  );
};

const MetricCard = ({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) => (
  <div style={styles.metricCard}>
    <div style={{ ...styles.metricTopBorder, borderTopColor: color }} />
    <div style={styles.metricBody}>
      <div style={styles.metricLabel}>{label}</div>
      <div style={styles.metricValue}>{value}</div>
    </div>
  </div>
);

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
    padding: "20px",
    marginBottom: "20px",
    border: "1px solid #e5e7eb",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },
  error: { borderLeft: "4px solid #ef4444", color: "#991b1b" },
  cardTitle: { fontSize: "15px", fontWeight: 600, marginBottom: "10px", color: "#111827" },
  paragraph: { margin: "0 0 10px 0", color: "#374151", fontSize: "14px", lineHeight: 1.5 },
  list: { paddingLeft: "18px", fontSize: "14px", lineHeight: 1.8, color: "#374151", margin: 0 },
  listItem: { marginBottom: "4px" },
  emptyText: { margin: 0, color: "#6b7280", fontSize: "14px" },
  metricGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "10px",
    marginBottom: "14px",
  },
  inlineMetric: {
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    padding: "10px",
    background: "#fafafa",
  },
  inlineMetricLabel: {
    display: "block",
    fontSize: "12px",
    color: "#6b7280",
    marginBottom: "4px",
    textTransform: "uppercase",
  },
  inlineMetricValue: { fontSize: "14px", color: "#111827" },
  verdictBox: {
    border: "1px solid #dbeafe",
    background: "#eff6ff",
    borderRadius: "10px",
    padding: "12px",
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
  metricTopBorder: { height: 3, borderTop: "3px solid transparent" },
  metricBody: { padding: "16px" },
  metricLabel: { fontSize: "13px", color: "#6b7280", marginBottom: "6px" },
  metricValue: { fontSize: "20px", fontWeight: 700, color: "#111827" },
  actions: { display: "flex", gap: "12px" },
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
  },
};

export default Insights;
