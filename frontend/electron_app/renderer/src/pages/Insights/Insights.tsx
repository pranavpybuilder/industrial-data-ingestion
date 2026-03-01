import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { useNavigate } from "react-router-dom";
import { FiArrowRight, FiBarChart2, FiDownload, FiAlertTriangle, FiInfo, FiAlertCircle } from "react-icons/fi";

import { frontendApi } from "../../services/frontendApi";
import { runUI } from "../../state/run_ui_store";

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

/* ─── Severity helpers (plain English labels, never raw values) ─── */
const SEV_CONFIG: Record<string, { label: string; color: string; bg: string; border: string; icon: string }> = {
  CRITICAL: { label: "Needs Immediate Attention", color: "#dc2626", bg: "#fef2f2", border: "#fecaca", icon: "alert-circle" },
  WARNING:  { label: "Worth Investigating",       color: "#d97706", bg: "#fffbeb", border: "#fde68a", icon: "alert-triangle" },
  INFO:     { label: "For Your Information",       color: "#059669", bg: "#ecfdf5", border: "#a7f3d0", icon: "info" },
};

function sevOf(raw: string | undefined): string {
  return (raw || "INFO").toUpperCase();
}

function humanizeKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/\bMttr\b/i, "Mean Time to Repair")
    .replace(/\bMttf\b/i, "Mean Time to Failure");
}

function formatMetricValue(key: string, val: unknown): string {
  if (val === null || val === undefined) return "\u2014";
  const n = Number(val);
  if (Number.isNaN(n)) return String(val);
  const lk = key.toLowerCase();
  if (lk.includes("score") || lk.includes("confidence") || lk.includes("health") || lk.includes("maturity")) {
    if (n <= 1) return `${(n * 100).toFixed(0)}%`;
    return `${n.toFixed(0)}%`;
  }
  if (n === Math.floor(n)) return String(n);
  return n.toFixed(2);
}

type Insight = {
  insight_id?: string;
  title?: string;
  description?: string;
  severity?: string;
  source?: string;
  remediation?: string;
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

/* ─── Verdict → plain English risk badge ─── */
function verdictRiskLabel(verdict?: { risk_score?: number; verdict?: string }): { label: string; color: string } {
  if (!verdict) return { label: "Analysis Complete", color: "#6366f1" };
  const rs = verdict.risk_score ?? 0;
  if (rs >= 0.7) return { label: "High Risk \u2014 Action Needed", color: "#dc2626" };
  if (rs >= 0.4) return { label: "Moderate Risk \u2014 Monitor Closely", color: "#d97706" };
  return { label: "Low Risk \u2014 System Healthy", color: "#059669" };
}

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

  // Sort by severity (critical first)
  const sortedInsights = useMemo(() => {
    const order: Record<string, number> = { CRITICAL: 0, WARNING: 1, INFO: 2 };
    return [...operationalInsights].sort(
      (a, b) => (order[sevOf(a.severity)] ?? 3) - (order[sevOf(b.severity)] ?? 3)
    );
  }, [operationalInsights]);

  const criticalCount = useMemo(
    () => operationalInsights.filter((i) => sevOf(i.severity) === "CRITICAL").length,
    [operationalInsights]
  );
  const warningCount = useMemo(
    () => operationalInsights.filter((i) => sevOf(i.severity) === "WARNING").length,
    [operationalInsights]
  );
  const infoCount = useMemo(
    () => operationalInsights.length - criticalCount - warningCount,
    [operationalInsights, criticalCount, warningCount]
  );

  // Bucket recommendations into tiers
  const tiers = useMemo(() => {
    const immediate: string[] = [];
    const investigate: string[] = [];
    const strategic: string[] = [];
    for (const i of operationalInsights) {
      const action = i.remediation || i.details?.remediation || "";
      if (!action) continue;
      const sev = sevOf(i.severity);
      if (sev === "CRITICAL") immediate.push(action);
      else if (sev === "WARNING") investigate.push(action);
      else strategic.push(action);
    }
    return { immediate, investigate, strategic };
  }, [operationalInsights]);

  // Overall risk from verdict
  const riskBadge = useMemo(
    () => verdictRiskLabel(executiveNarrative?.sections?.["System Verdict"]),
    [executiveNarrative]
  );

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
      <section style={st.page}>
        {/* ── Header with risk badge ── */}
        <header style={st.header}>
          <div style={st.headerIcon}>
            <FiBarChart2 size={22} color="#6366f1" />
          </div>
          <div style={{ flex: 1 }}>
            <h1 style={st.title}>Analysis Results</h1>
            <p style={st.subtitle}>Run: <strong>{activeRun}</strong></p>
          </div>
          {!loading && !error && operationalInsights.length > 0 && (
            <span style={{ ...st.riskBadge, color: riskBadge.color, borderColor: riskBadge.color }}>
              {riskBadge.label}
            </span>
          )}
        </header>

        {loading && <div style={st.card}>Loading insights...</div>}
        {error && <div style={{ ...st.card, borderLeft: "4px solid #ef4444", color: "#991b1b" }}>{error}</div>}

        {!loading && !error && (
          <>
            {/* ── Executive Summary Card ── */}
            {executiveNarrative?.sections && (
              <div style={{ ...st.card, borderLeft: `4px solid ${riskBadge.color}` }}>
                <h3 style={st.sectionTitle}>Executive Summary</h3>
                <p style={st.paragraph}>
                  {executiveNarrative.sections["Executive Summary"] || "No executive summary generated."}
                </p>

                {executiveNarrative.sections["Key Decision Insight"] && (
                  <>
                    <h4 style={st.subSectionTitle}>Key Decision</h4>
                    <p style={st.paragraph}>
                      {executiveNarrative.sections["Key Decision Insight"]}
                    </p>
                  </>
                )}

                {/* Verdict as plain English — no raw scores exposed */}
                {executiveNarrative.sections["System Verdict"]?.verdict && (
                  <div style={st.verdictBox}>
                    <p style={{ ...st.paragraph, margin: 0 }}>
                      {executiveNarrative.sections["System Verdict"].verdict}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* ── Priority Overview — 3 metric cards ── */}
            <div style={st.metricRow}>
              <PriorityCard
                label="Needs Immediate Attention"
                count={criticalCount}
                color="#dc2626"
                bg="#fef2f2"
              />
              <PriorityCard
                label="Worth Investigating"
                count={warningCount}
                color="#d97706"
                bg="#fffbeb"
              />
              <PriorityCard
                label="For Your Information"
                count={infoCount}
                color="#059669"
                bg="#ecfdf5"
              />
            </div>

            {/* ── Key Alerts & Intelligence (collapsed sections) ── */}
            {executiveNarrative?.sections && (
              <div style={st.twoCol}>
                <SectionCard
                  title="Critical Alerts"
                  items={executiveNarrative.sections["Critical Alerts"]}
                  emptyText="No critical alerts."
                  accentColor="#dc2626"
                />
                <SectionCard
                  title="Predictive Insights"
                  items={executiveNarrative.sections["Predictive Insights"]}
                  emptyText="No predictive insights generated."
                  accentColor="#6366f1"
                />
              </div>
            )}

            {/* ── Findings Grid (2-column, severity-colored) ── */}
            <h3 style={{ ...st.sectionTitle, marginTop: 8 }}>Findings</h3>
            {sortedInsights.length === 0 ? (
              <p style={st.emptyText}>No findings generated for this run.</p>
            ) : (
              <div style={st.findingsGrid}>
                {sortedInsights.map((insight, idx) => {
                  const sev = sevOf(insight.severity);
                  const cfg = SEV_CONFIG[sev] || SEV_CONFIG.INFO;
                  return (
                    <div
                      key={insight.insight_id || idx}
                      style={{ ...st.findingCard, borderLeftColor: cfg.color }}
                    >
                      <div style={st.findingHeader}>
                        <span style={{ ...st.sevBadge, color: cfg.color, background: cfg.bg, borderColor: cfg.border }}>
                          {cfg.label}
                        </span>
                        {insight.confidence != null && (
                          <span style={st.confLabel}>
                            {Number(insight.confidence) >= 0.8
                              ? "High confidence"
                              : Number(insight.confidence) >= 0.5
                              ? "Moderate confidence"
                              : "Low confidence"}
                          </span>
                        )}
                      </div>
                      {insight.title && (
                        <h4 style={st.findingTitle}>{insight.title}</h4>
                      )}
                      <p style={st.findingDesc}>
                        {insight.description || "No details available."}
                      </p>
                      {(insight.remediation || insight.details?.remediation) && (
                        <p style={st.findingAction}>
                          <strong>Recommended:</strong>{" "}
                          {insight.remediation || insight.details?.remediation}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* ── 3-Tier Recommendations ── */}
            {(tiers.immediate.length > 0 || tiers.investigate.length > 0 || tiers.strategic.length > 0) && (
              <>
                <h3 style={{ ...st.sectionTitle, marginTop: 12 }}>Recommendations</h3>
                {tiers.immediate.length > 0 && (
                  <TierBlock
                    title="Immediate Action Required"
                    items={tiers.immediate}
                    color="#dc2626"
                    bg="#fef2f2"
                  />
                )}
                {tiers.investigate.length > 0 && (
                  <TierBlock
                    title="Investigate This Week"
                    items={tiers.investigate}
                    color="#d97706"
                    bg="#fffbeb"
                  />
                )}
                {tiers.strategic.length > 0 && (
                  <TierBlock
                    title="Strategic Improvement"
                    items={tiers.strategic}
                    color="#2563eb"
                    bg="#eff6ff"
                  />
                )}
              </>
            )}

            {/* ── Optimization & Additional Intelligence ── */}
            {executiveNarrative?.sections?.["Optimization Opportunities"] &&
              executiveNarrative.sections["Optimization Opportunities"].length > 0 && (
              <div style={{ ...st.card, marginTop: 8 }}>
                <h3 style={st.sectionTitle}>Optimization Opportunities</h3>
                <ul style={st.list}>
                  {executiveNarrative.sections["Optimization Opportunities"].map((item, idx) => (
                    <li key={`opt-${idx}`} style={st.listItem}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* ── Actions ── */}
            <div style={st.actions}>
              <button style={st.primaryBtn} onClick={() => navigate("/dashboards")}>
                <FiArrowRight size={15} />
                Go to Dashboards
              </button>

              <button style={st.secondaryBtn} onClick={() => navigate("/exports")}>
                <FiDownload size={15} />
                Export Report
              </button>
            </div>
          </>
        )}
      </section>
    </>
  );
};

/* ─── Sub-components ─── */

const PriorityCard = ({ label, count, color, bg }: {
  label: string; count: number; color: string; bg: string;
}) => (
  <div style={{ ...st.priorityCard, borderTop: `3px solid ${color}` }}>
    <div style={{ fontSize: 28, fontWeight: 700, color }}>{count}</div>
    <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>{label}</div>
  </div>
);

const SectionCard = ({ title, items, emptyText, accentColor }: {
  title: string; items?: string[]; emptyText: string; accentColor: string;
}) => (
  <div style={{ ...st.card, borderLeft: `3px solid ${accentColor}` }}>
    <h4 style={{ ...st.subSectionTitle, margin: "0 0 8px 0" }}>{title}</h4>
    {items && items.length > 0 ? (
      <ul style={st.list}>
        {items.map((item, idx) => (
          <li key={idx} style={st.listItem}>{item}</li>
        ))}
      </ul>
    ) : (
      <p style={st.emptyText}>{emptyText}</p>
    )}
  </div>
);

const TierBlock = ({ title, items, color, bg }: {
  title: string; items: string[]; color: string; bg: string;
}) => (
  <div style={{ ...st.tierBlock, background: bg, borderLeft: `4px solid ${color}` }}>
    <h4 style={{ ...st.subSectionTitle, color, margin: "0 0 6px 0" }}>{title}</h4>
    <ul style={{ ...st.list, margin: 0 }}>
      {items.map((item, idx) => (
        <li key={idx} style={{ ...st.listItem, color: "#374151" }}>{item}</li>
      ))}
    </ul>
  </div>
);

/* ─── Styles ─── */

const st: Record<string, React.CSSProperties> = {
  page: { maxWidth: "1100px", animation: "fadeIn 0.3s ease-out" },
  header: { display: "flex", alignItems: "center", gap: "14px", marginBottom: "24px" },
  headerIcon: {
    width: 44, height: 44, borderRadius: 12, background: "#eef2ff",
    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  title: { fontSize: "22px", fontWeight: 700, color: "#111827", margin: 0 },
  subtitle: { fontSize: "14px", color: "#6b7280", margin: 0, marginTop: 2 },
  riskBadge: {
    fontSize: 12, fontWeight: 600, padding: "6px 14px", borderRadius: 20,
    border: "1.5px solid", whiteSpace: "nowrap" as const,
  },
  card: {
    background: "#ffffff", borderRadius: "12px", padding: "20px", marginBottom: "16px",
    border: "1px solid #e5e7eb", boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },
  sectionTitle: { fontSize: "16px", fontWeight: 600, marginBottom: "12px", color: "#111827", marginTop: 0 },
  subSectionTitle: { fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "6px" },
  paragraph: { margin: "0 0 10px 0", color: "#374151", fontSize: "14px", lineHeight: 1.6 },
  emptyText: { margin: 0, color: "#6b7280", fontSize: "14px" },
  verdictBox: {
    border: "1px solid #dbeafe", background: "#eff6ff",
    borderRadius: "8px", padding: "12px", marginTop: 8,
  },
  list: { paddingLeft: "18px", fontSize: "14px", lineHeight: 1.8, color: "#374151", margin: "0 0 8px 0" },
  listItem: { marginBottom: "4px" },

  /* ── Priority metric cards ── */
  metricRow: {
    display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
    gap: "14px", marginBottom: "20px",
  },
  priorityCard: {
    background: "#ffffff", borderRadius: "12px", padding: "16px 20px",
    border: "1px solid #e5e7eb", boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
    textAlign: "center" as const,
  },

  /* ── Two-column layout ── */
  twoCol: {
    display: "grid", gridTemplateColumns: "1fr 1fr",
    gap: "14px", marginBottom: "16px",
  },

  /* ── Findings grid ── */
  findingsGrid: {
    display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "20px",
  },
  findingCard: {
    background: "#ffffff", borderRadius: "10px", padding: "16px",
    border: "1px solid #e5e7eb", borderLeft: "4px solid #059669",
    boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
  },
  findingHeader: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    marginBottom: 6, flexWrap: "wrap" as const, gap: 6,
  },
  sevBadge: {
    fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 12,
    border: "1px solid", whiteSpace: "nowrap" as const,
  },
  confLabel: { fontSize: 11, color: "#9ca3af" },
  findingTitle: { fontSize: 14, fontWeight: 600, color: "#111827", margin: "4px 0 4px 0" },
  findingDesc: { fontSize: 13, color: "#4b5563", lineHeight: 1.55, margin: "0 0 6px 0" },
  findingAction: { fontSize: 12, color: "#6b7280", lineHeight: 1.5, margin: 0, fontStyle: "italic" as const },

  /* ── Tier blocks ── */
  tierBlock: {
    borderRadius: "10px", padding: "14px 18px", marginBottom: "12px",
  },

  /* ── Actions ── */
  actions: { display: "flex", gap: "12px", marginTop: 8, marginBottom: 12 },
  primaryBtn: {
    background: "#6366f1", color: "#ffffff", border: "none", borderRadius: "8px",
    padding: "10px 18px", fontSize: "14px", fontWeight: 500, cursor: "pointer",
    display: "flex", alignItems: "center", gap: "6px",
  },
  secondaryBtn: {
    background: "#ffffff", color: "#111827", border: "1px solid #e5e7eb", borderRadius: "8px",
    padding: "10px 18px", fontSize: "14px", fontWeight: 500, cursor: "pointer",
    display: "flex", alignItems: "center", gap: "6px",
  },
};

export default Insights;
