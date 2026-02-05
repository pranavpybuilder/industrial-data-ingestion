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

const ChartWidget = ({
  title,
  visualType,
  data,
}: ChartWidgetProps) => {
  return (
    <div>
      <h3
        style={{
          marginBottom: "0.5rem",
          fontSize: "16px",
          fontWeight: 600,
        }}
      >
        {title}
      </h3>

      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer>
          {visualType === "line" ? (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="y"
                stroke="#4740cd"
                strokeWidth={2}
              />
            </LineChart>
          ) : (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="y" fill="#4f46e5" />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ChartWidget;