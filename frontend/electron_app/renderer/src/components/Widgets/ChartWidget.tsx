import { dashboardsUI } from "../../state/dashboards_ui_store";

/**
 * ChartWidgetProps
 * ----------------
 * Generic chart widget abstraction for Phase 1.
 * Real chart libraries will replace the visual layer later
 * without changing interaction logic.
 */
interface ChartWidgetProps {
  title: string;
  visualType: "line" | "bar";
  data: Array<{
    x: string;
    y: number;
  }>;
}

/**
 * ChartWidget
 *
 * Responsibilities:
 * - Display chart data (mock rendering)
 * - Handle drill-down interaction
 * - Update drillContext in a controlled, undoable way
 *
 * Does NOT:
 * - Apply filters to data
 * - Fetch data
 * - Persist anything
 */
const ChartWidget = ({
  title,
  visualType,
  data,
}: ChartWidgetProps) => {
  /**
   * Drill-down handler
   * ------------------
   * In Phase 1, drill is simulated by selecting the first data point.
   * In later phases, this will be replaced by real chart click events.
   */
  const handleDrill = (dimensionValue: string) => {
    dashboardsUI.updateInteraction((prev) => ({
      ...prev,
      drillContext: {
        dimension: "x",
        value: dimensionValue,
      },
    }));
  };

  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 6,
        padding: "1rem",
        background: "#ffffff",
      }}
    >
      {/* ---------- Title ---------- */}
      <h3 style={{ marginBottom: "0.25rem" }}>
        {title}
      </h3>

      <p
        style={{
          fontSize: "0.8rem",
          color: "#6b7280",
          marginBottom: "0.5rem",
        }}
      >
        Visualization: {visualType.toUpperCase()}
      </p>

      {/* ---------- Drill Instruction ---------- */}
      <p
        style={{
          fontSize: "0.75rem",
          color: "#9ca3af",
          marginBottom: "0.5rem",
        }}
      >
        Click anywhere on the chart to drill down
      </p>

      {/* ---------- Chart Area (Mock) ---------- */}
      <div
        onClick={() => handleDrill(data[0]?.x)}
        style={{
          cursor: "pointer",
          background: "#f9fafb",
          border: "1px dashed #d1d5db",
          padding: "0.75rem",
        }}
      >
        <pre
          style={{
            fontSize: "0.7rem",
            margin: 0,
          }}
        >
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default ChartWidget;