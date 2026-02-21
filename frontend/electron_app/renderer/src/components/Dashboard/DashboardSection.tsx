/**
 * DashboardSection — Power BI-style widget container
 * Handles chart, metric, table, and gauge widget types
 * Supports dynamic grid spanning based on widget config
 */

import VisualizationSwitcher from "../Widgets/VisualizationSwitcher";
import ChartWidget from "../Widgets/ChartWidget";
import MetricWidget from "../Widgets/MetricWidget";
import type {
  InteractionState,
  DashboardBlueprint,
} from "../../state/dashboards_ui_store";
import type { VisualType } from "../Widgets/ChartWidget";
import type { MetricWidgetProps } from "../Widgets/MetricWidget";

export interface DashboardSectionProps {
  widget: DashboardBlueprint["widgets"][number];
  interaction: InteractionState;
  data: any;
  gridSpan?: number;
}

const DashboardSection = ({
  widget,
  interaction,
  data,
  gridSpan,
}: DashboardSectionProps) => {
  const span = gridSpan || widget.gridSpan || 6;

  // ── Metric Widget ──
  if (widget.widgetType === "metric") {
    const metricData = data as MetricWidgetProps;
    return (
      <div style={{ gridColumn: `span ${Math.min(span, 3)}` }}>
        <MetricWidget
          title={metricData?.title || widget.title || widget.widgetId}
          value={metricData?.value ?? "—"}
          subtitle={metricData?.subtitle}
          trend={metricData?.trend}
          trendValue={metricData?.trendValue}
          severity={metricData?.severity || "info"}
          icon={metricData?.icon}
          sparklineData={metricData?.sparklineData}
        />
      </div>
    );
  }

  // ── Table Widget ──
  if (widget.widgetType === "table") {
    const rows = Array.isArray(data) ? data : [];
    const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
    return (
      <div style={{ gridColumn: `span ${span}`, ...cardStyle }}>
        <h3 style={sectionTitle}>{widget.title || widget.widgetId.replace(/_/g, " ")}</h3>
        <div style={{ overflowX: "auto", maxHeight: "400px", overflowY: "auto" }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col} style={thStyle}>
                    {col.replace(/_/g, " ").toUpperCase()}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 50).map((row: Record<string, any>, i: number) => (
                <tr key={i} style={i % 2 === 0 ? trEven : trOdd}>
                  {columns.map((col) => (
                    <td key={col} style={tdStyle}>
                      {formatCellValue(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length > 50 && (
          <div style={{ textAlign: "center", padding: "8px", color: "#9ca3af", fontSize: "12px" }}>
            Showing 50 of {rows.length} rows
          </div>
        )}
      </div>
    );
  }

  // ── Chart Widget (default) ──
  const visualType = (
    interaction.visualTypes[widget.widgetId] ??
    widget.allowedVisualTypes?.[0] ??
    "line"
  ) as VisualType;

  const chartData = Array.isArray(data) ? data : [];
  const hasMultipleViz = (widget.allowedVisualTypes?.length ?? 0) > 1;

  return (
    <div style={{ gridColumn: `span ${span}`, ...cardStyle }}>
      {/* Controls bar */}
      <div style={controlsBar}>
        <span style={widgetLabel}>{widget.title || widget.widgetId.replace(/_/g, " ")}</span>
        {hasMultipleViz && (
          <VisualizationSwitcher
            widgetId={widget.widgetId}
            allowed={widget.allowedVisualTypes || ["line", "bar"]}
          />
        )}
      </div>

      {/* Chart */}
      {chartData.length > 0 ? (
        <ChartWidget
          title=""
          visualType={visualType}
          data={chartData}
        />
      ) : (
        <div style={emptyState}>No data available</div>
      )}
    </div>
  );
};

// ── Helpers ──

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return String(value);
}

// ── Styles ──

const cardStyle: React.CSSProperties = {
  background: "#ffffff",
  borderRadius: "14px",
  padding: "20px 24px",
  border: "1px solid #e5e7eb",
  boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)",
  transition: "box-shadow 0.2s ease",
};

const controlsBar: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "12px",
};

const widgetLabel: React.CSSProperties = {
  fontSize: "13px",
  fontWeight: 700,
  color: "#374151",
  letterSpacing: "-0.01em",
  textTransform: "capitalize",
};

const sectionTitle: React.CSSProperties = {
  fontSize: "14px",
  fontWeight: 700,
  color: "#374151",
  marginBottom: "14px",
  letterSpacing: "-0.01em",
};

const emptyState: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  height: "200px",
  color: "#9ca3af",
  fontSize: "14px",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: "13px",
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "10px 12px",
  fontSize: "11px",
  fontWeight: 700,
  color: "#6b7280",
  borderBottom: "2px solid #e5e7eb",
  background: "#f9fafb",
  position: "sticky",
  top: 0,
  letterSpacing: "0.5px",
};

const tdStyle: React.CSSProperties = {
  padding: "9px 12px",
  borderBottom: "1px solid #f3f4f6",
  color: "#374151",
};

const trEven: React.CSSProperties = {};
const trOdd: React.CSSProperties = { background: "#fafbfc" };

export default DashboardSection;