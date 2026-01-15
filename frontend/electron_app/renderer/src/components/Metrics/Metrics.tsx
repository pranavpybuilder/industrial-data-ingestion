import React from "react";
import { runUI } from "../../state/run_ui_store";
import { insightsUI } from "../../state/insights_ui_store";
import { dashboardsUI } from "../../state/dashboards_ui_store";
import { exportsUI } from "../../state/exports_ui_store";

export function Metrics() {
  const runState = React.useSyncExternalStore(
    runUI.subscribe,
    runUI.getSnapshot
  );

  const activeRun = runState.activeRunId ?? "—";

  return (
    <div style={grid}>
      <MetricCard title="Active Run" value={activeRun} mono />
      <MetricCard title="Insights" value="0" />
      <MetricCard title="Dashboards" value="0" />
      <MetricCard title="Exports" value="0" />
    </div>
  );
}

/* ------------------ Reusable Card ------------------ */

function MetricCard({
  title,
  value,
  mono = false,
}: {
  title: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div style={card}>
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
  borderRadius: 10,
  padding: "16px 18px",
  border: "1px solid #e5e7eb",
  minHeight: 96,
};

const titleStyle: React.CSSProperties = {
  fontSize: 14,
  color: "#6b7280",
  marginBottom: 8,
};

const valueStyle: React.CSSProperties = {
  fontSize: 22,
  fontWeight: 600,
  color: "#111827",

  /* 🔒 CRITICAL FIX */
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};