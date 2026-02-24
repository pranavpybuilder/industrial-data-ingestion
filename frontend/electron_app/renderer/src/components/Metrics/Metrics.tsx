import React from "react";
import { runUI } from "../../state/run_ui_store";
import { frontendApi } from "../../services/frontendApi";

const ACCENT_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444"];

export function Metrics() {
  const runState = React.useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const activeRun = runState.activeRunId ?? "N/A";
  const [insightsCount, setInsightsCount] = React.useState(0);
  const [dashboardsCount, setDashboardsCount] = React.useState(0);
  const [exportsCount, setExportsCount] = React.useState(0);

  React.useEffect(() => {
    const runId = runState.activeRunId;
    if (!runId) {
      setInsightsCount(0);
      setDashboardsCount(0);
      setExportsCount(0);
      return;
    }

    const load = async () => {
      const [insights, dashboards, exportsRes] = await Promise.all([
        frontendApi.getInsights(runId),
        frontendApi.getDashboard(runId),
        frontendApi.getExports(runId),
      ]);

      setInsightsCount(
        insights.success && Array.isArray(insights.data) ? insights.data.length : 0
      );
      setDashboardsCount(
        dashboards.success && dashboards.data?.dashboard_state ? 1 : 0
      );
      setExportsCount(
        exportsRes.success && Array.isArray(exportsRes.data) ? exportsRes.data.length : 0
      );
    };

    load();
  }, [runState.activeRunId]);

  return (
    <div style={grid}>
      <MetricCard
        title="Active Run"
        value={activeRun}
        mono
        accentColor={ACCENT_COLORS[0]}
      />
      <MetricCard
        title="Insights"
        value={String(insightsCount)}
        accentColor={ACCENT_COLORS[1]}
      />
      <MetricCard
        title="Dashboards"
        value={String(dashboardsCount)}
        accentColor={ACCENT_COLORS[2]}
      />
      <MetricCard
        title="Exports"
        value={String(exportsCount)}
        accentColor={ACCENT_COLORS[3]}
      />
    </div>
  );
}

function MetricCard({
  title,
  value,
  mono = false,
  accentColor = "#6366f1",
}: {
  title: string;
  value: string;
  mono?: boolean;
  accentColor?: string;
}) {
  return (
    <div style={card}>
      <div
        style={{
          width: 32,
          height: 4,
          borderRadius: 2,
          background: accentColor,
          marginBottom: 14,
        }}
      />
      <div style={titleStyle}>{title}</div>
      <div
        style={{
          ...valueStyle,
          fontFamily: mono ? "monospace" : "inherit",
        }}
        title={value}
      >
        {value}
      </div>
    </div>
  );
}

const grid: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 16,
  marginTop: 24,
};

const card: React.CSSProperties = {
  background: "#ffffff",
  borderRadius: 12,
  padding: 20,
  border: "1px solid #e5e7eb",
  minHeight: 96,
};

const titleStyle: React.CSSProperties = {
  fontSize: 12,
  color: "#6b7280",
  marginBottom: 8,
  textTransform: "uppercase",
  letterSpacing: "0.5px",
  fontWeight: 500,
};

const valueStyle: React.CSSProperties = {
  fontSize: 24,
  fontWeight: 700,
  color: "#111827",
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};
