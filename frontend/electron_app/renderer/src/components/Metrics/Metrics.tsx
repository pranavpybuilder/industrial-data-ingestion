import React from "react";
import { runUI } from "../../state/run_ui_store";
import { insightsUI } from "../../state/insights_ui_store";
import { dashboardsUI } from "../../state/dashboards_ui_store";
import { exportsUI } from "../../state/exports_ui_store";

const ACCENT_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444"];

export function Metrics() {
  const runState = React.useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const activeRun = runState.activeRunId ?? "—";

  return (
    <div style={grid}>
      <MetricCard title="Active Run" value={activeRun} mono accentColor={ACCENT_COLORS[0]} />
      <MetricCard title="Insights" value="0" accentColor={ACCENT_COLORS[1]} />
      <MetricCard title="Dashboards" value="0" accentColor={ACCENT_COLORS[2]} />
      <MetricCard title="Exports" value="0" accentColor={ACCENT_COLORS[3]} />
    </div>
  );
}

/* ------------------ Reusable Card ------------------ */

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
        title={value} // tooltip fallback
      >
        {value}
      </div>
    </div>
  );
}

/* ------------------ Styles ------------------ */

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

  /* 🔒 CRITICAL FIX */
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};