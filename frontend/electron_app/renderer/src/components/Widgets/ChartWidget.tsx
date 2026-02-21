/**
 * ChartWidget — Power BI-style multi-chart renderer
 * Supports: line, area, bar, column, pie, donut, scatter, gauge, histogram
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
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
  RadialBarChart,
  RadialBar,
} from "recharts";

export type VisualType =
  | "line"
  | "area"
  | "bar"
  | "column"
  | "pie"
  | "donut"
  | "scatter"
  | "gauge"
  | "histogram";

interface ChartWidgetProps {
  title: string;
  visualType: VisualType;
  data: Array<Record<string, any>>;
  height?: number;
  colors?: string[];
}

const CHART_COLORS = [
  "#6366f1", "#8b5cf6", "#ec4899", "#14b8a6",
  "#f59e0b", "#3b82f6", "#10b981", "#ef4444",
  "#06b6d4", "#84cc16", "#f97316", "#a855f7",
];

const tooltipStyle: React.CSSProperties = {
  borderRadius: "10px",
  border: "1px solid #e5e7eb",
  boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
  fontSize: "13px",
  padding: "10px 14px",
  background: "#ffffff",
};

const axisStyle = { fontSize: 11, fill: "#9ca3af", fontWeight: 500 };

const ChartWidget = ({
  title,
  visualType,
  data,
  height = 280,
  colors = CHART_COLORS,
}: ChartWidgetProps) => {
  return (
    <div>
      <h3 style={{
        marginBottom: "12px",
        fontSize: "14px",
        fontWeight: 700,
        color: "#374151",
        letterSpacing: "-0.01em",
      }}>
        {title}
      </h3>

      <div style={{ width: "100%", height }}>
        <ResponsiveContainer>
          {renderChart(visualType, data, colors)}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

function renderChart(
  type: VisualType,
  data: Array<Record<string, any>>,
  colors: string[]
) {
  switch (type) {
    case "line":
      return (
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="x" tick={axisStyle} axisLine={{ stroke: "#e5e7eb" }} tickLine={false} />
          <YAxis tick={axisStyle} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Line
            type="monotone" dataKey="y" stroke={colors[0]}
            strokeWidth={2.5} dot={{ r: 3, fill: colors[0], strokeWidth: 0 }}
            activeDot={{ r: 6, fill: colors[0], stroke: "#fff", strokeWidth: 2 }}
          />
        </LineChart>
      );

    case "area":
      return (
        <AreaChart data={data}>
          <defs>
            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={colors[0]} stopOpacity={0.3} />
              <stop offset="100%" stopColor={colors[0]} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="x" tick={axisStyle} axisLine={{ stroke: "#e5e7eb" }} tickLine={false} />
          <YAxis tick={axisStyle} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Area
            type="monotone" dataKey="y"
            stroke={colors[0]} strokeWidth={2}
            fill="url(#areaGrad)"
          />
        </AreaChart>
      );

    case "bar":
    case "column":
      return (
        <BarChart data={data} barCategoryGap="20%">
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
          <XAxis dataKey="x" tick={axisStyle} axisLine={{ stroke: "#e5e7eb" }} tickLine={false} />
          <YAxis tick={axisStyle} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(99,102,241,0.06)" }} />
          <Bar dataKey="y" radius={[6, 6, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Bar>
        </BarChart>
      );

    case "pie":
      return (
        <PieChart>
          <Pie
            data={data} dataKey="y" nameKey="x"
            cx="50%" cy="50%" outerRadius="80%"
            strokeWidth={2} stroke="#ffffff"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
          <Legend
            wrapperStyle={{ fontSize: "12px", color: "#6b7280" }}
            iconType="circle"
            iconSize={8}
          />
        </PieChart>
      );

    case "donut":
      return (
        <PieChart>
          <Pie
            data={data} dataKey="y" nameKey="x"
            cx="50%" cy="50%"
            innerRadius="55%" outerRadius="80%"
            strokeWidth={2} stroke="#ffffff"
            paddingAngle={2}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
          <Legend
            wrapperStyle={{ fontSize: "12px", color: "#6b7280" }}
            iconType="circle"
            iconSize={8}
          />
        </PieChart>
      );

    case "scatter":
      return (
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="x" name="X" tick={axisStyle} axisLine={{ stroke: "#e5e7eb" }} tickLine={false} type="number" />
          <YAxis dataKey="y" name="Y" tick={axisStyle} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: "3 3" }} />
          <Scatter data={data} fill={colors[0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Scatter>
        </ScatterChart>
      );

    case "gauge": {
      // Radial bar as gauge — expect data[0].y to be 0-100
      const val = data[0]?.y ?? 0;
      const gaugeColor = val >= 80 ? "#10b981" : val >= 50 ? "#f59e0b" : "#ef4444";
      const gaugeData = [{ name: "value", value: val, fill: gaugeColor }];
      return (
        <RadialBarChart
          cx="50%" cy="50%"
          innerRadius="60%" outerRadius="90%"
          data={gaugeData}
          startAngle={180} endAngle={0}
          barSize={16}
        >
          <RadialBar
            dataKey="value"
            cornerRadius={8}
            background={{ fill: "#f3f4f6" }}
          />
          <text
            x="50%" y="55%" textAnchor="middle"
            style={{ fontSize: "28px", fontWeight: 800, fill: "#111827" }}
          >
            {val}%
          </text>
          <text
            x="50%" y="68%" textAnchor="middle"
            style={{ fontSize: "12px", fontWeight: 500, fill: "#9ca3af" }}
          >
            Score
          </text>
        </RadialBarChart>
      );
    }

    case "histogram":
      return (
        <BarChart data={data} barCategoryGap="5%">
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
          <XAxis dataKey="x" tick={axisStyle} axisLine={{ stroke: "#e5e7eb" }} tickLine={false} />
          <YAxis tick={axisStyle} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey="y" fill={colors[0]} radius={[2, 2, 0, 0]} />
        </BarChart>
      );

    default:
      return (
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="x" tick={axisStyle} />
          <YAxis tick={axisStyle} />
          <Tooltip contentStyle={tooltipStyle} />
          <Line type="monotone" dataKey="y" stroke={colors[0]} strokeWidth={2} />
        </LineChart>
      );
  }
}

export default ChartWidget;