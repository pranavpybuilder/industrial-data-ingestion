/**
 * ChartWidget — Power BI-style multi-chart renderer
 * --------------------------------------------------
 * Supports: line, area, bar, column, pie, donut,
 *           scatter, gauge, histogram, sparkline
 *
 * Design language: matches Dashboards.tsx
 *  - Indigo primary (#6366f1), clean grays
 *  - Subtle grid lines, rounded bar tops
 *  - Custom tooltip with shadow
 *  - Gradient fills for area/gauge
 */

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
  RadialBarChart,
  RadialBar,
  ReferenceLine,
} from "recharts";

// ─── Types ────────────────────────────────────────────────────────────────────

export type VisualType =
  | "line"
  | "area"
  | "bar"
  | "column"
  | "pie"
  | "donut"
  | "scatter"
  | "gauge"
  | "histogram"
  | "sparkline";

interface ChartWidgetProps {
  title?: string;
  visualType: VisualType;
  data: Array<Record<string, any>>;
  height?: number;
  colors?: string[];
  showLegend?: boolean;
  referenceValue?: number;
  referenceLabel?: string;
}

// ─── Constants ────────────────────────────────────────────────────────────────

export const CHART_COLORS = [
  "#6366f1", "#8b5cf6", "#ec4899", "#14b8a6",
  "#f59e0b", "#3b82f6", "#10b981", "#ef4444",
  "#06b6d4", "#84cc16", "#f97316", "#a855f7",
];

const AXIS_TICK = { fontSize: 11, fill: "#9ca3af", fontWeight: 500 };
const AXIS_LINE = { stroke: "#e5e7eb" };
const GRID_STROKE = "#f3f4f6";

// ─── Custom Tooltip ───────────────────────────────────────────────────────────

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#fff",
      border: "1px solid #e5e7eb",
      borderRadius: 10,
      padding: "10px 14px",
      boxShadow: "0 8px 24px rgba(0,0,0,0.10)",
      fontSize: 12,
      minWidth: 100,
    }}>
      {label !== undefined && (
        <div style={{ color: "#6b7280", marginBottom: 6, fontWeight: 600, fontSize: 11 }}>
          {String(label)}
        </div>
      )}
      {payload.map((entry: any, i: number) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: i < payload.length - 1 ? 3 : 0 }}>
          <span style={{
            width: 8, height: 8, borderRadius: "50%",
            background: entry.color || entry.fill || CHART_COLORS[i],
            flexShrink: 0,
          }} />
          <span style={{ color: "#374151", fontWeight: 600 }}>
            {typeof entry.value === "number"
              ? entry.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
              : String(entry.value)}
          </span>
          {entry.name && entry.name !== "y" && (
            <span style={{ color: "#9ca3af", fontSize: 11 }}>{entry.name}</span>
          )}
        </div>
      ))}
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

const ChartWidget = ({
  title,
  visualType,
  data,
  height = 280,
  colors = CHART_COLORS,
  showLegend = false,
  referenceValue,
  referenceLabel,
}: ChartWidgetProps) => {
  return (
    <div>
      {title && (
        <h3 style={{
          margin: "0 0 12px",
          fontSize: 13,
          fontWeight: 700,
          color: "#374151",
          letterSpacing: "-0.01em",
        }}>
          {title}
        </h3>
      )}
      <div style={{ width: "100%", height }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart(visualType, data, colors, showLegend, referenceValue, referenceLabel)}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// ─── Chart Renderer ───────────────────────────────────────────────────────────

function renderChart(
  type: VisualType,
  data: Array<Record<string, any>>,
  colors: string[],
  showLegend: boolean,
  referenceValue?: number,
  referenceLabel?: string
): React.ReactElement {

  switch (type) {

    // ── Line ──────────────────────────────────────────────────────────────────
    case "line":
      return (
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
          <XAxis dataKey="x" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} />
          <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={40} />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend wrapperStyle={{ fontSize: 11, color: "#6b7280" }} iconType="circle" iconSize={7} />}
          {referenceValue !== undefined && (
            <ReferenceLine y={referenceValue} stroke="#f59e0b" strokeDasharray="4 3"
              label={{ value: referenceLabel || String(referenceValue), fill: "#f59e0b", fontSize: 10 }} />
          )}
          <Line
            type="monotone" dataKey="y" stroke={colors[0]}
            strokeWidth={2.5}
            dot={{ r: 3, fill: colors[0], strokeWidth: 0 }}
            activeDot={{ r: 6, fill: colors[0], stroke: "#fff", strokeWidth: 2 }}
          />
        </LineChart>
      );

    // ── Area ──────────────────────────────────────────────────────────────────
    case "area": {
      const gradId = `area_grad_${colors[0].replace("#", "")}`;
      return (
        <AreaChart data={data}>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={colors[0]} stopOpacity={0.28} />
              <stop offset="75%" stopColor={colors[0]} stopOpacity={0.04} />
              <stop offset="100%" stopColor={colors[0]} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
          <XAxis dataKey="x" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} />
          <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={40} />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend wrapperStyle={{ fontSize: 11, color: "#6b7280" }} iconType="circle" iconSize={7} />}
          <Area
            type="monotone" dataKey="y"
            stroke={colors[0]} strokeWidth={2.5}
            fill={`url(#${gradId})`}
            activeDot={{ r: 6, fill: colors[0], stroke: "#fff", strokeWidth: 2 }}
          />
        </AreaChart>
      );
    }

    // ── Bar / Column ──────────────────────────────────────────────────────────
    case "bar":
    case "column":
      return (
        <BarChart data={data} barCategoryGap="22%">
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
          <XAxis dataKey="x" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} />
          <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={40} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(99,102,241,0.05)" }} />
          {showLegend && <Legend wrapperStyle={{ fontSize: 11, color: "#6b7280" }} iconType="square" iconSize={8} />}
          {referenceValue !== undefined && (
            <ReferenceLine y={referenceValue} stroke="#f59e0b" strokeDasharray="4 3"
              label={{ value: referenceLabel || String(referenceValue), fill: "#f59e0b", fontSize: 10 }} />
          )}
          <Bar dataKey="y" radius={[5, 5, 0, 0]} maxBarSize={56}>
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Bar>
        </BarChart>
      );

    // ── Pie ───────────────────────────────────────────────────────────────────
    case "pie":
      return (
        <PieChart>
          <Pie
            data={data} dataKey="y" nameKey="x"
            cx="50%" cy="50%" outerRadius="78%"
            strokeWidth={2} stroke="#fff"
            paddingAngle={1}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: 11, color: "#6b7280" }}
            iconType="circle" iconSize={7}
          />
        </PieChart>
      );

    // ── Donut ─────────────────────────────────────────────────────────────────
    case "donut": {
      const total = data.reduce((sum, d) => sum + (Number(d.y) || 0), 0);
      return (
        <PieChart>
          <Pie
            data={data} dataKey="y" nameKey="x"
            cx="50%" cy="50%"
            innerRadius="52%" outerRadius="78%"
            strokeWidth={2} stroke="#fff"
            paddingAngle={2}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Pie>
          {/* Center label */}
          <text
            x="50%" y="47%" textAnchor="middle" dominantBaseline="middle"
            style={{ fontSize: 22, fontWeight: 800, fill: "#111827" }}
          >
            {total.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </text>
          <text
            x="50%" y="57%" textAnchor="middle" dominantBaseline="middle"
            style={{ fontSize: 10, fill: "#9ca3af", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}
          >
            Total
          </text>
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11, color: "#6b7280" }} iconType="circle" iconSize={7} />
        </PieChart>
      );
    }

    // ── Scatter ───────────────────────────────────────────────────────────────
    case "scatter":
      return (
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
          <XAxis dataKey="x" type="number" name="X" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} />
          <YAxis dataKey="y" type="number" name="Y" tick={AXIS_TICK} axisLine={false} tickLine={false} width={40} />
          <ZAxis range={[40, 160]} />
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: "3 3", stroke: "#e5e7eb" }} />
          <Scatter data={data} fill={colors[0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} fillOpacity={0.8} />
            ))}
          </Scatter>
        </ScatterChart>
      );

    // ── Gauge ─────────────────────────────────────────────────────────────────
    case "gauge": {
      const val = Math.max(0, Math.min(100, Number(data[0]?.y ?? 0)));
      const gaugeColor =
        val >= 80 ? "#10b981" :
        val >= 50 ? "#f59e0b" : "#ef4444";
      const trackColor = "#f3f4f6";
      const gaugeData = [
        { name: "value", value: val, fill: gaugeColor },
        { name: "track", value: 100 - val, fill: trackColor },
      ];
      return (
        <RadialBarChart
          cx="50%" cy="60%"
          innerRadius="55%" outerRadius="90%"
          startAngle={200} endAngle={-20}
          data={gaugeData}
          barSize={18}
        >
          <RadialBar
            dataKey="value"
            cornerRadius={9}
            background={false}
          />
          {/* Value text */}
          <text x="50%" y="58%" textAnchor="middle" dominantBaseline="middle"
            style={{ fontSize: 32, fontWeight: 800, fill: "#111827" }}>
            {val}
          </text>
          <text x="50%" y="70%" textAnchor="middle" dominantBaseline="middle"
            style={{ fontSize: 11, fill: "#9ca3af", fontWeight: 600 }}>
            out of 100
          </text>
          {/* Color indicator dot */}
          <circle cx="50%" cy="82%" r={4} fill={gaugeColor} />
        </RadialBarChart>
      );
    }

    // ── Histogram ─────────────────────────────────────────────────────────────
    case "histogram":
      return (
        <BarChart data={data} barCategoryGap="3%">
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
          <XAxis dataKey="x" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} />
          <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={40} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="y" fill={colors[0]} radius={[3, 3, 0, 0]} fillOpacity={0.85}>
            {data.map((_, i) => (
              <Cell key={i} fill={colors[0]} fillOpacity={0.7 + (i % 3) * 0.1} />
            ))}
          </Bar>
        </BarChart>
      );

    // ── Sparkline ─────────────────────────────────────────────────────────────
    case "sparkline": {
      const sGradId = `spark_grad_${colors[0].replace("#", "")}`;
      return (
        <AreaChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
          <defs>
            <linearGradient id={sGradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={colors[0]} stopOpacity={0.2} />
              <stop offset="100%" stopColor={colors[0]} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone" dataKey="y"
            stroke={colors[0]} strokeWidth={1.5}
            fill={`url(#${sGradId})`}
            dot={false}
          />
          <Tooltip content={<CustomTooltip />} />
        </AreaChart>
      );
    }

    // ── Default fallback ──────────────────────────────────────────────────────
    default:
      return (
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
          <XAxis dataKey="x" tick={AXIS_TICK} />
          <YAxis tick={AXIS_TICK} />
          <Tooltip content={<CustomTooltip />} />
          <Line type="monotone" dataKey="y" stroke={colors[0]} strokeWidth={2} dot={false} />
        </LineChart>
      );
  }
}

export default ChartWidget;