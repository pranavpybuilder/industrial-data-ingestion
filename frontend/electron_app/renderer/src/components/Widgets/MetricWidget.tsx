/**
 * MetricWidget — Power BI-style KPI card
 * Displays a single metric with trend indicator and sparkline
 */

import {
  AreaChart,
  Area,
  ResponsiveContainer,
} from "recharts";
import {
  FiTrendingUp,
  FiTrendingDown,
  FiMinus,
  FiAlertTriangle,
  FiCheckCircle,
  FiActivity,
} from "react-icons/fi";

export interface MetricWidgetProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "flat";
  trendValue?: string;
  severity?: "critical" | "high" | "medium" | "low" | "info";
  icon?: "alert" | "check" | "activity";
  sparklineData?: Array<{ y: number }>;
  compact?: boolean;
}

const severityConfig: Record<string, { color: string; bg: string; border: string }> = {
  critical: { color: "#ef4444", bg: "linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)", border: "#fca5a5" },
  high:     { color: "#f59e0b", bg: "linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)", border: "#fcd34d" },
  medium:   { color: "#6366f1", bg: "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)", border: "#a5b4fc" },
  low:      { color: "#10b981", bg: "linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)", border: "#6ee7b7" },
  info:     { color: "#3b82f6", bg: "linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)", border: "#93c5fd" },
};

const iconMap = {
  alert:    FiAlertTriangle,
  check:    FiCheckCircle,
  activity: FiActivity,
};

const MetricWidget = ({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  severity = "info",
  icon,
  sparklineData,
  compact = false,
}: MetricWidgetProps) => {
  const config = severityConfig[severity] || severityConfig.info;
  const IconComp = icon ? iconMap[icon] : null;
  const TrendIcon = trend === "up" ? FiTrendingUp : trend === "down" ? FiTrendingDown : FiMinus;

  return (
    <div
      style={{
        background: config.bg,
        borderRadius: "14px",
        padding: compact ? "16px 18px" : "22px 24px",
        border: `1px solid ${config.border}`,
        position: "relative",
        overflow: "hidden",
        transition: "all 0.2s ease",
        cursor: "default",
        minHeight: compact ? "auto" : "140px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
        {IconComp && (
          <div style={{
            width: 32, height: 32, borderRadius: "8px",
            background: `${config.color}18`,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <IconComp size={16} color={config.color} />
          </div>
        )}
        <span style={{
          fontSize: "12px", fontWeight: 600,
          color: "#6b7280", textTransform: "uppercase",
          letterSpacing: "0.5px", flex: 1,
        }}>
          {title}
        </span>
      </div>

      {/* Value */}
      <div style={{
        fontSize: compact ? "26px" : "32px",
        fontWeight: 800,
        color: "#111827",
        lineHeight: 1.1,
        marginBottom: "6px",
        fontVariantNumeric: "tabular-nums",
      }}>
        {value}
      </div>

      {/* Bottom row: subtitle + trend */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        {subtitle && (
          <span style={{ fontSize: "12px", color: "#6b7280" }}>{subtitle}</span>
        )}
        {trend && (
          <div style={{
            display: "flex", alignItems: "center", gap: "4px",
            fontSize: "12px", fontWeight: 600,
            color: trend === "up" ? "#10b981" : trend === "down" ? "#ef4444" : "#9ca3af",
          }}>
            <TrendIcon size={14} />
            {trendValue && <span>{trendValue}</span>}
          </div>
        )}
      </div>

      {/* Sparkline background */}
      {sparklineData && sparklineData.length > 1 && (
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0, height: "50px",
          opacity: 0.15, pointerEvents: "none",
        }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={sparklineData}>
              <Area
                type="monotone"
                dataKey="y"
                stroke={config.color}
                fill={config.color}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default MetricWidget;
