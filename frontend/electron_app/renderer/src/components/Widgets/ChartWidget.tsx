import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface ChartWidgetProps {
  title: string;
  visualType: "line" | "bar";
  data: Array<{ x: string; y: number }>;
}

const tooltipStyle: React.CSSProperties = {
  borderRadius: "8px",
  border: "1px solid #e5e7eb",
  boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
  fontSize: "13px",
};

const ChartWidget = ({
  title,
  visualType,
  data,
}: ChartWidgetProps) => {
  return (
    <div>
      <h3
        style={{
          marginBottom: "0.75rem",
          fontSize: "15px",
          fontWeight: 600,
          color: "#374151",
        }}
      >
        {title}
      </h3>

      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer>
          {visualType === "line" ? (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="x" tick={{ fontSize: 12, fill: "#6b7280" }} />
              <YAxis tick={{ fontSize: 12, fill: "#6b7280" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line
                type="monotone"
                dataKey="y"
                stroke="#6366f1"
                strokeWidth={2}
                dot={{ r: 3, fill: "#6366f1" }}
                activeDot={{ r: 5, fill: "#4f46e5" }}
              />
            </LineChart>
          ) : (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="x" tick={{ fontSize: 12, fill: "#6b7280" }} />
              <YAxis tick={{ fontSize: 12, fill: "#6b7280" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="y" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ChartWidget;