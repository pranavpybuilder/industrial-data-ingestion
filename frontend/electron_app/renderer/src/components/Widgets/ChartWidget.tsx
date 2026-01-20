/**
 * ChartWidget
 *
 * Lightweight, dependency-free chart renderer.
 * Uses SVG to render basic line and bar charts.
 * Designed for offline Phase 1 validation.
 */

interface ChartWidgetProps {
  title: string;
  visualType: "line" | "bar";
  data: Array<{ x: string; y: number }>;
}

const ChartWidget = ({ title, visualType, data }: ChartWidgetProps) => {
  const width = 500;
  const height = 220;
  const padding = 40;

  const maxY = Math.max(...data.map((d) => d.y), 1);

  const xStep =
    (width - padding * 2) / Math.max(data.length - 1, 1);

  const points = data.map((d, i) => ({
    x: padding + i * xStep,
    y:
      height -
      padding -
      (d.y / maxY) * (height - padding * 2),
  }));

  return (
    <div style={{ marginBottom: "2rem" }}>
      <h3>{title}</h3>

      <svg width={width} height={height}>
        {/* Axes */}
        <line
          x1={padding}
          y1={padding}
          x2={padding}
          y2={height - padding}
          stroke="#999"
        />
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          stroke="#999"
        />

        {/* Chart */}
        {visualType === "line" ? (
          <polyline
            fill="none"
            stroke="#2563eb"
            strokeWidth="2"
            points={points.map((p) => `${p.x},${p.y}`).join(" ")}
          />
        ) : (
          points.map((p, i) => (
            <rect
              key={i}
              x={p.x - 10}
              y={p.y}
              width={20}
              height={height - padding - p.y}
              fill="#2563eb"
            />
          ))
        )}

        {/* X labels */}
        {points.map((p, i) => (
          <text
            key={i}
            x={p.x}
            y={height - padding + 15}
            fontSize="10"
            textAnchor="middle"
          >
            {data[i].x}
          </text>
        ))}
      </svg>
    </div>
  );
};

export default ChartWidget;
