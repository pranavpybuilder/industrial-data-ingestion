/**
 * Dashboards Page — Power BI-style auto-generated dashboard
 * Generates KPI cards, charts, tables, and gauges from real pipeline data
 * Professional layout with sections: KPIs → System Health → Charts → Details
 */

import { useEffect, useState } from "react";
import {
  FiSave,
  FiRotateCcw,
  FiRotateCw,
  FiExternalLink,
  FiEye,
  FiActivity,
  FiClock,
  FiRefreshCw,
} from "react-icons/fi";
import { useNavigate } from "react-router-dom";

import { dashboardsUI } from "../../state/dashboards_ui_store";
import { useDashboardsUI } from "../../state/useDashboardsUI";
import { useRunUI } from "../../state/useRunUI";
import { frontendApi } from "../../services/frontendApi";

import { RunGuard } from "../../components/RunGuard/RunGuard";
import DashboardCanvas from "../../components/Dashboard/DashboardCanvas";
import type { DashboardBlueprint, InteractionState } from "../../state/dashboards_ui_store";

/* ─── Smart dashboard generator ─── */

interface PipelineData {
  insights: any[];
  profiling: any;
  equipmentIntel: any;
  dashboard: any;
}

function generatePowerBIDashboard(
  runId: string,
  pipelineData: PipelineData
): { blueprint: DashboardBlueprint; widgetData: Record<string, any> } {
  const { insights, profiling, equipmentIntel } = pipelineData;
  const widgets: DashboardBlueprint["widgets"] = [];
  const widgetData: Record<string, any> = {};
  const sections: DashboardBlueprint["sections"] = [];

  // ═══ SECTION 1: KPI Metrics ═══
  sections.push({ sectionId: "kpis", title: "Key Performance Indicators", order: 1 });

  // Total insights
  const criticalCount = insights.filter((i: any) =>
    i.severity === "CRITICAL" || i.severity === "critical"
  ).length;
  const highCount = insights.filter((i: any) =>
    i.severity === "HIGH" || i.severity === "high"
  ).length;

  widgets.push({
    widgetId: "kpi_total_insights",
    widgetType: "metric",
    title: "Total Insights",
    gridSpan: 3,
    sectionId: "kpis",
  });
  widgetData["kpi_total_insights"] = {
    title: "Total Insights",
    value: insights.length,
    subtitle: `${criticalCount} critical, ${highCount} high`,
    severity: criticalCount > 0 ? "critical" : highCount > 0 ? "high" : "low",
    icon: "activity",
    trend: insights.length > 5 ? "up" : "flat",
    trendValue: `${insights.length} findings`,
  };

  // Critical alerts
  widgets.push({
    widgetId: "kpi_critical_alerts",
    widgetType: "metric",
    title: "Critical Alerts",
    gridSpan: 3,
    sectionId: "kpis",
  });
  widgetData["kpi_critical_alerts"] = {
    title: "Critical Alerts",
    value: criticalCount,
    subtitle: criticalCount > 0 ? "Immediate action required" : "All clear",
    severity: criticalCount > 0 ? "critical" : "low",
    icon: criticalCount > 0 ? "alert" : "check",
  };

  // Health score
  const healthScore = profiling?.health_score ?? profiling?.completeness ?? 0;
  widgets.push({
    widgetId: "kpi_health_score",
    widgetType: "metric",
    title: "Data Health",
    gridSpan: 3,
    sectionId: "kpis",
  });
  widgetData["kpi_health_score"] = {
    title: "Data Health Score",
    value: `${Math.round(healthScore)}%`,
    subtitle: healthScore >= 80 ? "Good quality" : healthScore >= 50 ? "Needs attention" : "Poor quality",
    severity: healthScore >= 80 ? "low" : healthScore >= 50 ? "medium" : "critical",
    icon: "check",
    trend: healthScore >= 80 ? "up" : healthScore >= 50 ? "flat" : "down",
    trendValue: `${Math.round(healthScore)}/100`,
  };

  // Equipment count
  const equipCount = equipmentIntel?.equipment_frequency?.total_equipment ?? 0;
  const breakdowns = equipmentIntel?.equipment_frequency?.total_breakdowns ?? 0;
  widgets.push({
    widgetId: "kpi_equipment",
    widgetType: "metric",
    title: "Equipment Monitored",
    gridSpan: 3,
    sectionId: "kpis",
  });
  widgetData["kpi_equipment"] = {
    title: "Equipment Monitored",
    value: equipCount,
    subtitle: `${breakdowns} total breakdowns`,
    severity: breakdowns > equipCount * 3 ? "high" : "info",
    icon: "activity",
    trend: breakdowns > 0 ? "down" : "flat",
    trendValue: `${breakdowns} events`,
  };

  // ═══ SECTION 2: System Health ═══
  sections.push({ sectionId: "health", title: "System Health Overview", order: 2 });

  // Health gauge
  widgets.push({
    widgetId: "gauge_health",
    widgetType: "chart",
    title: "Overall Health Score",
    allowedVisualTypes: ["gauge"],
    gridSpan: 4,
    sectionId: "health",
  });
  widgetData["gauge_health"] = [{ x: "Health", y: Math.round(healthScore) }];

  // Severity distribution donut
  const severityCounts: Record<string, number> = {};
  insights.forEach((i: any) => {
    const sev = (i.severity || "INFO").toUpperCase();
    severityCounts[sev] = (severityCounts[sev] || 0) + 1;
  });
  if (Object.keys(severityCounts).length > 0) {
    widgets.push({
      widgetId: "donut_severity",
      widgetType: "chart",
      title: "Insight Severity Distribution",
      allowedVisualTypes: ["donut", "pie", "bar"],
      gridSpan: 4,
      sectionId: "health",
    });
    widgetData["donut_severity"] = Object.entries(severityCounts).map(([k, v]) => ({
      x: k,
      y: v,
    }));
  }

  // Source distribution pie
  const sourceCounts: Record<string, number> = {};
  insights.forEach((i: any) => {
    const src = (i.source || i.insight_source || "UNKNOWN").toUpperCase();
    sourceCounts[src] = (sourceCounts[src] || 0) + 1;
  });
  if (Object.keys(sourceCounts).length > 0) {
    widgets.push({
      widgetId: "pie_sources",
      widgetType: "chart",
      title: "Insight Sources",
      allowedVisualTypes: ["pie", "donut", "bar"],
      gridSpan: 4,
      sectionId: "health",
    });
    widgetData["pie_sources"] = Object.entries(sourceCounts).map(([k, v]) => ({
      x: k,
      y: v,
    }));
  }

  // ═══ SECTION 3: Equipment Analytics ═══
  if (equipmentIntel && Object.keys(equipmentIntel).length > 0) {
    sections.push({ sectionId: "equipment", title: "Equipment Analytics", order: 3 });

    // Top failing equipment bar chart
    const topEquipment = equipmentIntel?.equipment_frequency?.top_equipment;
    if (topEquipment && topEquipment.length > 0) {
      widgets.push({
        widgetId: "bar_top_equipment",
        widgetType: "chart",
        title: "Top Failing Equipment",
        allowedVisualTypes: ["bar", "column", "line"],
        gridSpan: 6,
        sectionId: "equipment",
      });
      widgetData["bar_top_equipment"] = topEquipment.map((eq: any) => ({
        x: eq.equipment || eq.name || eq[0] || String(eq),
        y: eq.count || eq.breakdowns || eq[1] || 0,
      }));
    }

    // Failure type distribution
    const failureTypes = equipmentIntel?.failure_types;
    if (failureTypes) {
      widgets.push({
        widgetId: "donut_failure_types",
        widgetType: "chart",
        title: "Failure Type Breakdown",
        allowedVisualTypes: ["donut", "pie"],
        gridSpan: 6,
        sectionId: "equipment",
      });
      const ftData: Array<{ x: string; y: number }> = [];
      if (failureTypes.mechanical != null) ftData.push({ x: "Mechanical", y: failureTypes.mechanical });
      if (failureTypes.electrical != null) ftData.push({ x: "Electrical", y: failureTypes.electrical });
      if (failureTypes.other != null) ftData.push({ x: "Other", y: failureTypes.other });
      if (ftData.length === 0 && typeof failureTypes === "object") {
        Object.entries(failureTypes).forEach(([k, v]) => {
          if (typeof v === "number") ftData.push({ x: k, y: v });
        });
      }
      widgetData["donut_failure_types"] = ftData;
    }

    // Downtime analysis
    const downtime = equipmentIntel?.downtime;
    if (downtime?.by_equipment && Array.isArray(downtime.by_equipment)) {
      widgets.push({
        widgetId: "bar_downtime",
        widgetType: "chart",
        title: "Downtime by Equipment (Hours)",
        allowedVisualTypes: ["bar", "area", "line"],
        gridSpan: 6,
        sectionId: "equipment",
      });
      widgetData["bar_downtime"] = downtime.by_equipment.slice(0, 10).map((d: any) => ({
        x: d.equipment || d.name || String(d),
        y: Math.round((d.total_hours || d.downtime || 0) * 10) / 10,
      }));
    }

    // Root causes
    const rootCauses = equipmentIntel?.root_causes;
    if (rootCauses && Array.isArray(rootCauses) && rootCauses.length > 0) {
      widgets.push({
        widgetId: "bar_root_causes",
        widgetType: "chart",
        title: "Top Root Causes",
        allowedVisualTypes: ["bar", "column"],
        gridSpan: 6,
        sectionId: "equipment",
      });
      widgetData["bar_root_causes"] = rootCauses.slice(0, 8).map((rc: any) => ({
        x: rc.cause || rc.name || rc[0] || String(rc),
        y: rc.count || rc.frequency || rc[1] || 0,
      }));
    }

    // Risk classification
    const riskData = equipmentIntel?.risk_scores;
    if (riskData && Array.isArray(riskData) && riskData.length > 0) {
      widgets.push({
        widgetId: "bar_risk_scores",
        widgetType: "chart",
        title: "Equipment Risk Scores",
        allowedVisualTypes: ["bar", "scatter"],
        gridSpan: 12,
        sectionId: "equipment",
      });
      widgetData["bar_risk_scores"] = riskData.slice(0, 15).map((r: any) => ({
        x: r.equipment || r.name || String(r),
        y: Math.round((r.score || r.risk_score || 0) * 100),
      }));
    }
  }

  // ═══ SECTION 4: Profiling & Quality ═══
  if (profiling) {
    sections.push({ sectionId: "quality", title: "Data Quality & Profiling", order: 4 });

    // Column completeness chart
    const profiles = profiling.profiles || profiling.columns;
    if (profiles && typeof profiles === "object") {
      const profileEntries = Array.isArray(profiles) ? profiles : Object.entries(profiles);
      if (profileEntries.length > 0) {
        widgets.push({
          widgetId: "bar_completeness",
          widgetType: "chart",
          title: "Column Completeness (%)",
          allowedVisualTypes: ["bar", "column"],
          gridSpan: 6,
          sectionId: "quality",
        });
        widgetData["bar_completeness"] = profileEntries.slice(0, 12).map((entry: any) => {
          const name = entry.column_name || entry.name || entry[0] || "—";
          const missing = entry.missing_pct ?? entry.missing_percentage ?? entry[1]?.missing_pct ?? 0;
          return {
            x: typeof name === "string" ? (name.length > 15 ? name.substring(0, 15) + "…" : name) : String(name),
            y: Math.round(100 - (typeof missing === "number" ? missing : 0)),
          };
        });
      }
    }

    // Quality summary metrics
    const qualityIssues = profiling.issues || profiling.quality_issues || [];
    widgets.push({
      widgetId: "kpi_data_rows",
      widgetType: "metric",
      title: "Data Quality",
      gridSpan: 3,
      sectionId: "quality",
    });
    widgetData["kpi_data_rows"] = {
      title: "Quality Issues",
      value: Array.isArray(qualityIssues) ? qualityIssues.length : 0,
      subtitle: "detected issues",
      severity: (Array.isArray(qualityIssues) && qualityIssues.length > 5) ? "high" : "low",
      icon: (Array.isArray(qualityIssues) && qualityIssues.length > 0) ? "alert" : "check",
    };

    widgets.push({
      widgetId: "kpi_completeness",
      widgetType: "metric",
      title: "Completeness",
      gridSpan: 3,
      sectionId: "quality",
    });
    widgetData["kpi_completeness"] = {
      title: "Data Completeness",
      value: `${Math.round(profiling.completeness ?? (100 - (profiling.missing_pct ?? 0)))}%`,
      subtitle: "non-null values",
      severity: (profiling.completeness ?? 100) >= 90 ? "low" : "medium",
      icon: "check",
    };
  }

  // ═══ SECTION 5: All Insights Table ═══
  if (insights.length > 0) {
    sections.push({ sectionId: "details", title: "Insight Details", order: 5 });

    widgets.push({
      widgetId: "table_insights",
      widgetType: "table",
      title: "All Insights",
      gridSpan: 12,
      sectionId: "details",
    });
    widgetData["table_insights"] = insights.map((i: any, idx: number) => ({
      "#": idx + 1,
      severity: (i.severity || "INFO").toUpperCase(),
      source: (i.source || i.insight_source || "—").toUpperCase(),
      summary: i.summary || i.message || i.description || "—",
      confidence: typeof i.confidence === "number" ? `${Math.round(i.confidence * 100)}%` : "—",
      resource: i.resource || i.equipment || "—",
    }));
  }

  return {
    blueprint: {
      dashboardId: `powerbi_${runId}`,
      title: "Maintenance Intelligence Dashboard",
      widgets,
      sections,
    },
    widgetData,
  };
}

/* ─── Main Dashboards Page Component ─── */

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.5; }
}
`;

const Dashboards = () => {
  const navigate = useNavigate();
  const run = useRunUI();
  const storeState = useDashboardsUI();
  const [localBlueprint, setLocalBlueprint] = useState<DashboardBlueprint | null>(null);
  const [localData, setLocalData] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<string>("");

  useEffect(() => {
    if (!run.activeRunId) return;
    loadDashboardData(run.activeRunId);
  }, [run.activeRunId]);

  async function loadDashboardData(runId: string) {
    setLoading(true);
    setError(null);

    try {
      // Fetch data from backend via IPC
      const [insightsRes, dashboardRes, healthRes] = await Promise.all([
        frontendApi.getInsights(runId),
        frontendApi.getDashboard(runId),
        frontendApi.getDataHealth(runId),
      ]);

      const insights = insightsRes.success ? (insightsRes.data?.insights || insightsRes.data || []) : [];
      const dashData = dashboardRes.success ? (dashboardRes.data || {}) : {};
      const profiling = healthRes.success ? (healthRes.data || {}) : {};
      const equipmentIntel = dashData.equipment_intelligence || dashData.equipment || {};

      // Generate Power BI-style dashboard from real data
      const { blueprint, widgetData } = generatePowerBIDashboard(runId, {
        insights: Array.isArray(insights) ? insights : [],
        profiling,
        equipmentIntel,
        dashboard: dashData,
      });

      setLocalBlueprint(blueprint);
      setLocalData(widgetData);

      // Initialize the store for undo/redo support
      if (!storeState.isLoaded) {
        dashboardsUI.initialize(blueprint, 1);
      }

      setLastRefresh(new Date().toLocaleTimeString());
    } catch (err) {
      console.error("Dashboard load error:", err);
      setError("Failed to load dashboard data. Showing demo view.");

      // Fallback demo dashboard
      const demoData = generateDemoDashboard(runId);
      setLocalBlueprint(demoData.blueprint);
      setLocalData(demoData.widgetData);

      if (!storeState.isLoaded) {
        dashboardsUI.initialize(demoData.blueprint, 1);
      }
    } finally {
      setLoading(false);
    }
  }

  // Use store interaction (for undo/redo/filters) but local blueprint + data
  const interaction: InteractionState = storeState.interactionState || {
    timeGranularity: "day",
    globalFilters: {},
    widgetFilters: {},
    sessionFilters: {},
    drillContext: null,
    visualTypes: {},
    hiddenWidgets: new Set(),
  };

  return (
    <RunGuard>
      <style>{fadeKeyframes}</style>
      <section style={styles.page}>
        {/* ═══ HEADER ═══ */}
        <div style={styles.headerRow}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={styles.logoIcon}>
                <FiActivity size={18} color="#6366f1" />
              </div>
              <div>
                <h1 style={styles.title}>Maintenance Intelligence</h1>
                <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                  <span style={styles.subtitle}>
                    Run: {run.activeRunId?.substring(0, 12)}…
                  </span>
                  {lastRefresh && (
                    <span style={styles.timestamp}>
                      <FiClock size={11} style={{ marginRight: "3px" }} />
                      Updated {lastRefresh}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div style={styles.actionsRow}>
            <button
              style={styles.btnPrimary}
              onClick={() => run.activeRunId && loadDashboardData(run.activeRunId)}
              title="Refresh dashboard"
            >
              <FiRefreshCw size={14} /> Refresh
            </button>
            <button
              style={styles.btn}
              onClick={() => {
                dashboardsUI.save();
                alert("Dashboard state saved.");
              }}
            >
              <FiSave size={14} /> Save
            </button>
            <button
              style={{
                ...styles.btn,
                opacity: storeState.undoStack.length === 0 ? 0.4 : 1,
              }}
              disabled={storeState.undoStack.length === 0}
              onClick={() => dashboardsUI.undo()}
              aria-label="Undo"
            >
              <FiRotateCcw size={14} />
            </button>
            <button
              style={{
                ...styles.btn,
                opacity: storeState.redoStack.length === 0 ? 0.4 : 1,
              }}
              disabled={storeState.redoStack.length === 0}
              onClick={() => dashboardsUI.redo()}
              aria-label="Redo"
            >
              <FiRotateCw size={14} />
            </button>
            <div style={styles.divider} />
            <button style={styles.btn} onClick={() => navigate("/insights")}>
              <FiEye size={14} /> Insights
            </button>
            <button style={styles.btn} onClick={() => navigate("/exports")}>
              <FiExternalLink size={14} /> Export
            </button>
          </div>
        </div>

        {/* ═══ STATUS BAR ═══ */}
        {error && (
          <div style={styles.errorBanner}>
            ⚠ {error}
          </div>
        )}

        {/* ═══ LOADING STATE ═══ */}
        {loading ? (
          <div style={styles.loadingWrap}>
            <div style={{ animation: "pulse 1.5s infinite" }}>
              <FiActivity size={40} color="#6366f1" />
            </div>
            <span style={{ marginTop: "12px", color: "#6b7280", fontSize: "14px" }}>
              Generating dashboard…
            </span>
          </div>
        ) : localBlueprint ? (
          <DashboardCanvas
            blueprint={localBlueprint}
            interaction={interaction}
            widgetData={localData}
          />
        ) : (
          <div style={styles.emptyState}>
            <FiActivity size={40} color="#d1d5db" />
            <p style={{ marginTop: "12px", color: "#9ca3af" }}>
              No dashboard data available for this run.
            </p>
          </div>
        )}
      </section>
    </RunGuard>
  );
};

/* ─── Demo dashboard fallback ─── */

function generateDemoDashboard(runId: string) {
  const blueprint: DashboardBlueprint = {
    dashboardId: `demo_${runId}`,
    title: "Demo Dashboard",
    sections: [
      { sectionId: "kpis", title: "Key Performance Indicators", order: 1 },
      { sectionId: "charts", title: "Analytics Overview", order: 2 },
      { sectionId: "equipment", title: "Equipment Analytics", order: 3 },
    ],
    widgets: [
      { widgetId: "demo_total", widgetType: "metric", title: "Total Events", gridSpan: 3, sectionId: "kpis" },
      { widgetId: "demo_critical", widgetType: "metric", title: "Critical", gridSpan: 3, sectionId: "kpis" },
      { widgetId: "demo_health", widgetType: "metric", title: "Health Score", gridSpan: 3, sectionId: "kpis" },
      { widgetId: "demo_equip", widgetType: "metric", title: "Equipment", gridSpan: 3, sectionId: "kpis" },
      { widgetId: "demo_gauge", widgetType: "chart", title: "System Health", allowedVisualTypes: ["gauge"], gridSpan: 4, sectionId: "charts" },
      { widgetId: "demo_pie", widgetType: "chart", title: "Severity Distribution", allowedVisualTypes: ["donut", "pie"], gridSpan: 4, sectionId: "charts" },
      { widgetId: "demo_trend", widgetType: "chart", title: "Monthly Trend", allowedVisualTypes: ["area", "line", "bar"], gridSpan: 4, sectionId: "charts" },
      { widgetId: "demo_equip_bar", widgetType: "chart", title: "Top Equipment Failures", allowedVisualTypes: ["bar", "column"], gridSpan: 6, sectionId: "equipment" },
      { widgetId: "demo_failure", widgetType: "chart", title: "Failure Types", allowedVisualTypes: ["donut", "pie"], gridSpan: 6, sectionId: "equipment" },
    ],
  };

  const widgetData: Record<string, any> = {
    demo_total: { title: "Total Events", value: 146, subtitle: "This quarter", severity: "info", icon: "activity" },
    demo_critical: { title: "Critical Alerts", value: 3, subtitle: "Action needed", severity: "critical", icon: "alert" },
    demo_health: { title: "Health Score", value: "76%", subtitle: "Medium quality", severity: "medium", icon: "check" },
    demo_equip: { title: "Equipment", value: 32, subtitle: "Being monitored", severity: "info", icon: "activity" },
    demo_gauge: [{ x: "Health", y: 76 }],
    demo_pie: [{ x: "Critical", y: 3 }, { x: "High", y: 4 }, { x: "Medium", y: 5 }, { x: "Low", y: 8 }],
    demo_trend: [
      { x: "Nov", y: 42 }, { x: "Dec", y: 38 }, { x: "Jan", y: 51 }, { x: "Feb", y: 46 },
    ],
    demo_equip_bar: [
      { x: "CNC-M01", y: 12 }, { x: "PUMP-H03", y: 9 }, { x: "CONV-L02", y: 7 },
      { x: "ROBOT-A01", y: 6 }, { x: "MILL-B04", y: 5 },
    ],
    demo_failure: [{ x: "Mechanical", y: 62 }, { x: "Electrical", y: 34 }, { x: "Other", y: 4 }],
  };

  return { blueprint, widgetData };
}

/* ═══ STYLES ═══ */

const styles: Record<string, React.CSSProperties> = {
  page: {
    animation: "fadeIn 0.3s ease-out",
    paddingBottom: "40px",
  },

  headerRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "24px",
    paddingBottom: "20px",
    borderBottom: "1px solid #e5e7eb",
  },

  logoIcon: {
    width: 38,
    height: 38,
    borderRadius: "10px",
    background: "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },

  title: {
    fontSize: "20px",
    fontWeight: 800,
    color: "#111827",
    margin: 0,
    letterSpacing: "-0.03em",
  },

  subtitle: {
    color: "#6b7280",
    fontSize: "12px",
    fontFamily: "'JetBrains Mono', monospace",
  },

  timestamp: {
    color: "#9ca3af",
    fontSize: "11px",
    display: "flex",
    alignItems: "center",
  },

  actionsRow: {
    display: "flex",
    gap: 6,
    alignItems: "center",
  },

  divider: {
    width: 1,
    height: 24,
    background: "#e5e7eb",
    margin: "0 4px",
  },

  btn: {
    background: "#f9fafb",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    padding: "7px 12px",
    fontSize: 12,
    fontWeight: 600,
    color: "#374151",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "5px",
    transition: "all 0.15s ease",
  },

  btnPrimary: {
    background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
    border: "none",
    borderRadius: "8px",
    padding: "7px 14px",
    fontSize: 12,
    fontWeight: 600,
    color: "#ffffff",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "5px",
    transition: "all 0.15s ease",
    boxShadow: "0 1px 3px rgba(99,102,241,0.3)",
  },

  errorBanner: {
    background: "#fffbeb",
    border: "1px solid #fcd34d",
    borderRadius: "10px",
    padding: "10px 16px",
    fontSize: "13px",
    color: "#92400e",
    marginBottom: "16px",
    fontWeight: 500,
  },

  loadingWrap: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    minHeight: "400px",
  },

  emptyState: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    minHeight: "400px",
    textAlign: "center" as const,
  },
};

export default Dashboards;