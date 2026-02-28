/**
 * DashboardSection — Power BI-style widget container
 * ---------------------------------------------------
 * Handles: chart, metric, table, map, text, image widgets
 * Supports:
 *  - Dynamic 12-column grid spanning
 *  - Visual type switching via VisualizationSwitcher
 *  - Metric cards with trend, sparkline, severity
 *  - Table with sticky header, zebra rows, pagination label
 *  - Empty / error states
 *
 * Design language: matches Dashboards.tsx
 *  - Same color tokens, card radius, shadow
 *  - Indigo accent, clean grays, minimal chrome
 */

import { useMemo } from "react";
import ChartWidget, { CHART_COLORS } from "../Widgets/ChartWidget";
import type { VisualType } from "../Widgets/ChartWidget";
import type {
  InteractionState,
  DashboardBlueprint,
} from "../../state/dashboards_ui_store";
import { dashboardsUI } from "../../state/dashboards_ui_store";
import {
  FiTrendingUp,
  FiTrendingDown,
  FiMinus,
  FiAlertCircle,
  FiCheckCircle,
  FiAlertTriangle,
} from "react-icons/fi";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface DashboardSectionProps {
  widget: DashboardBlueprint["widgets"][number];
  interaction: InteractionState;
  data: any;
  gridSpan?: number;
}

// Shape that widget data may conform to for metric widgets
interface MetricData {
  title?: string;
  value?: number | string;
  subtitle?: string;
  unit?: string;
  description?: string;
  trend?: "up" | "down" | "flat" | null;
  trendValue?: string;
  severity?: "critical" | "warning" | "info" | "success" | string;
  sparklineData?: Array<{ x: string; y: number }>;
  metrics?: Record<string, any>;
  icon?: string;
}

// ─── Main Component ───────────────────────────────────────────────────────────

const DashboardSection = ({
  widget,
  interaction,
  data,
  gridSpan,
}: DashboardSectionProps) => {
  const span = Math.min(gridSpan ?? widget.gridSpan ?? 6, 12);
  const label = (widget.title || widget.widgetId).replace(/_/g, " ");

  // ── Metric Widget ──────────────────────────────────────────────────────────
  if (widget.widgetType === "metric") {
    const md = (data ?? {}) as MetricData;
    return (
      <div style={{ gridColumn: `span ${Math.min(span, 3)}` }}>
        <MetricCard
          title={md.title || label}
          value={md.value}
          subtitle={md.subtitle}
          unit={md.unit}
          description={md.description}
          trend={md.trend}
          trendValue={md.trendValue}
          severity={md.severity || "info"}
          sparklineData={md.sparklineData}
          metrics={md.metrics}
        />
      </div>
    );
  }

  // ── Table Widget ───────────────────────────────────────────────────────────
  if (widget.widgetType === "table") {
    const rows = Array.isArray(data) ? data : [];
    return (
      <div style={{ gridColumn: `span ${span}`, ...cardStyle }}>
        <SectionHeader title={label} />
        <TableView rows={rows} />
      </div>
    );
  }

  // ── Text Widget ────────────────────────────────────────────────────────────
  if (widget.widgetType === "text") {
    const text = typeof data === "string" ? data : (data?.content ?? data?.text ?? "");
    return (
      <div style={{ gridColumn: `span ${Math.min(span, 6)}`, ...cardStyle }}>
        <SectionHeader title={label} />
        <p style={{ margin: 0, fontSize: 13, color: "#374151", lineHeight: 1.7 }}>{text}</p>
      </div>
    );
  }

  // ── Image Widget ───────────────────────────────────────────────────────────
  if (widget.widgetType === "image") {
    const src = typeof data === "string" ? data : (data?.url ?? data?.src ?? "");
    return (
      <div style={{ gridColumn: `span ${span}`, ...cardStyle }}>
        <SectionHeader title={label} />
        {src ? (
          <img
            src={src}
            alt={label}
            style={{ width: "100%", borderRadius: 8, objectFit: "cover", maxHeight: 280 }}
          />
        ) : (
          <EmptyState message="No image source provided" />
        )}
      </div>
    );
  }

  // ── Chart Widget (default) ─────────────────────────────────────────────────
  const visualType = (
    interaction.visualTypes[widget.widgetId] ??
    widget.allowedVisualTypes?.[0] ??
    "line"
  ) as VisualType;

  const chartData = Array.isArray(data) ? data : [];
  const hasVizSwitch = (widget.allowedVisualTypes?.length ?? 0) > 1;

  return (
    <div style={{ gridColumn: `span ${span}`, ...cardStyle }}>
      {/* Controls row */}
      <div style={controlsRow}>
        <span style={widgetLabel}>{label}</span>
        {hasVizSwitch && (
          <VizSwitcher
            widgetId={widget.widgetId}
            current={visualType}
            allowed={(widget.allowedVisualTypes ?? ["line", "bar"]) as VisualType[]}
          />
        )}
      </div>

      {/* Chart body */}
      {chartData.length > 0 ? (
        <ChartWidget
          visualType={visualType}
          data={chartData}
          height={270}
          colors={CHART_COLORS}
        />
      ) : (
        <EmptyState message="No data available" />
      )}
    </div>
  );
};

// ─── Sub-components ───────────────────────────────────────────────────────────

// ── Metric Card ───────────────────────────────────────────────────────────────

interface MetricCardProps extends MetricData {
  title: string;
}

const MetricCard = ({
  title,
  value,
  subtitle,
  unit,
  description,
  trend,
  trendValue,
  severity = "info",
  sparklineData,
  metrics,
}: MetricCardProps) => {
  const TrendIcon =
    trend === "up" ? FiTrendingUp :
    trend === "down" ? FiTrendingDown :
    FiMinus;

  const trendColor =
    trend === "up" ? "#10b981" :
    trend === "down" ? "#ef4444" :
    "#9ca3af";

  const SeverityIcon =
    severity === "critical" ? FiAlertCircle :
    severity === "warning" ? FiAlertTriangle :
    severity === "success" ? FiCheckCircle :
    null;

  const severityColor =
    severity === "critical" ? "#ef4444" :
    severity === "warning" ? "#f59e0b" :
    severity === "success" ? "#10b981" :
    "#6366f1";

  const cardBg =
    severity === "critical"
      ? "linear-gradient(135deg,#fff 60%,#fef2f2)"
      : severity === "warning"
      ? "linear-gradient(135deg,#fff 60%,#fffbeb)"
      : severity === "success"
      ? "linear-gradient(135deg,#fff 60%,#f0fdf4)"
      : "linear-gradient(135deg,#ffffff 60%,#f5f3ff)";

  const borderColor =
    severity === "critical" ? "#fecaca" :
    severity === "warning" ? "#fde68a" :
    severity === "success" ? "#bbf7d0" :
    "#ede9fe";

  return (
    <div style={{
      ...cardStyle,
      background: cardBg,
      borderColor,
      padding: "16px 18px",
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Severity accent stripe */}
      <div style={{
        position: "absolute",
        top: 0, left: 0,
        width: 3, height: "100%",
        background: severityColor,
        borderRadius: "12px 0 0 12px",
      }} />

      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10, paddingLeft: 8 }}>
        <span style={{ fontSize: 11, fontWeight: 700, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.5px", lineHeight: 1.3 }}>
          {title}
        </span>
        {SeverityIcon && (
          <SeverityIcon size={14} color={severityColor} style={{ flexShrink: 0 }} />
        )}
      </div>

      {/* Value */}
      <div style={{ paddingLeft: 8 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 4, marginBottom: 4 }}>
          <span style={{ fontSize: 30, fontWeight: 800, color: "#111827", lineHeight: 1, letterSpacing: "-0.03em" }}>
            {value !== undefined ? String(value) : "—"}
          </span>
          {unit && (
            <span style={{ fontSize: 14, fontWeight: 500, color: "#9ca3af" }}>{unit}</span>
          )}
        </div>

        {/* Trend row */}
        {(trend || trendValue) && (
          <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 6 }}>
            <TrendIcon size={13} color={trendColor} />
            {trendValue && (
              <span style={{ fontSize: 12, color: trendColor, fontWeight: 600 }}>{trendValue}</span>
            )}
          </div>
        )}

        {/* Subtitle / description */}
        {(subtitle || description) && (
          <p style={{ margin: "4px 0 0", fontSize: 11, color: "#9ca3af", lineHeight: 1.5 }}>
            {subtitle || description}
          </p>
        )}

        {/* Sparkline */}
        {sparklineData && sparklineData.length > 0 && (
          <div style={{ marginTop: 10, height: 44 }}>
            <ChartWidget
              visualType="sparkline"
              data={sparklineData}
              height={44}
              colors={[severityColor]}
            />
          </div>
        )}

        {/* Sub-metrics grid */}
        {metrics && Object.keys(metrics).length > 0 && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(72px, 1fr))", gap: 6, marginTop: 10 }}>
            {Object.entries(metrics).map(([k, v]) => (
              <div key={k} style={{
                background: "rgba(255,255,255,0.7)",
                border: "1px solid #f3f4f6",
                borderRadius: 7,
                padding: "6px 8px",
                display: "flex",
                flexDirection: "column",
                gap: 2,
              }}>
                <span style={{ fontSize: 9, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.4px", fontWeight: 700 }}>{k}</span>
                <strong style={{ fontSize: 13, color: "#111827", fontWeight: 700 }}>{String(v)}</strong>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ── Table View ────────────────────────────────────────────────────────────────

const TableView = ({ rows }: { rows: Record<string, any>[] }) => {
  const cols = useMemo(
    () => (rows.length > 0 ? Object.keys(rows[0]) : []),
    [rows]
  );

  if (!rows.length) return <EmptyState message="No rows to display" />;

  return (
    <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: 400 }}>
      <table style={tableStyle}>
        <thead>
          <tr>
            {cols.map((col) => (
              <th key={col} style={thStyle}>
                {col.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 60).map((row, i) => (
            <tr
              key={i}
              style={i % 2 === 1 ? trOdd : {}}
            >
              {cols.map((col) => (
                <td key={col} style={tdStyle}>
                  {formatCell(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 60 && (
        <div style={{ textAlign: "center", padding: "8px 0", color: "#9ca3af", fontSize: 11 }}>
          Showing 60 of {rows.length} rows
        </div>
      )}
    </div>
  );
};

// ── Viz Switcher ──────────────────────────────────────────────────────────────

const VizSwitcher = ({
  widgetId,
  current,
  allowed,
}: {
  widgetId: string;
  current: VisualType;
  allowed: VisualType[];
}) => {
  return (
    <div style={{ display: "flex", gap: 3 }}>
      {allowed.map((vt) => (
        <button
          key={vt}
          onClick={() =>
            dashboardsUI.updateInteraction((prev) => ({
              ...prev,
              visualTypes: { ...prev.visualTypes, [widgetId]: vt },
            }))
          }
          style={{
            padding: "3px 8px",
            fontSize: 10,
            fontWeight: 700,
            border: "1px solid",
            borderRadius: 5,
            cursor: "pointer",
            textTransform: "uppercase",
            letterSpacing: "0.3px",
            transition: "all 0.12s ease",
            borderColor: vt === current ? "#6366f1" : "#e5e7eb",
            background: vt === current ? "#eef2ff" : "#fff",
            color: vt === current ? "#4f46e5" : "#9ca3af",
          }}
        >
          {vt}
        </button>
      ))}
    </div>
  );
};

// ── Section Header ────────────────────────────────────────────────────────────

const SectionHeader = ({ title }: { title: string }) => (
  <div style={{ marginBottom: 14 }}>
    <span style={{
      fontSize: 12,
      fontWeight: 700,
      color: "#374151",
      letterSpacing: "-0.01em",
      textTransform: "capitalize",
    }}>
      {title}
    </span>
  </div>
);

// ── Empty State ───────────────────────────────────────────────────────────────

const EmptyState = ({ message = "No data available" }: { message?: string }) => (
  <div style={{
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: 200,
    color: "#d1d5db",
    fontSize: 13,
    fontStyle: "italic",
  }}>
    {message}
  </div>
);

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

// ─── Shared Styles ────────────────────────────────────────────────────────────

const cardStyle: React.CSSProperties = {
  background: "#ffffff",
  borderRadius: 12,
  padding: "18px 20px",
  border: "1px solid #e5e7eb",
  boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)",
  transition: "box-shadow 0.15s ease",
};

const controlsRow: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: 14,
  gap: 8,
};

const widgetLabel: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 700,
  color: "#374151",
  letterSpacing: "-0.01em",
  textTransform: "capitalize",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: 12,
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "9px 12px",
  fontSize: 10,
  fontWeight: 700,
  color: "#6b7280",
  borderBottom: "2px solid #e5e7eb",
  background: "#f9fafb",
  position: "sticky",
  top: 0,
  textTransform: "uppercase",
  letterSpacing: "0.5px",
  whiteSpace: "nowrap",
};

const tdStyle: React.CSSProperties = {
  padding: "8px 12px",
  borderBottom: "1px solid #f3f4f6",
  color: "#374151",
  whiteSpace: "nowrap",
};

const trOdd: React.CSSProperties = { background: "#fafbfc" };

export default DashboardSection;