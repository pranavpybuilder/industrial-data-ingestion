import { useNavigate } from "react-router-dom";
import { useRunUI } from "../../state/useRunUI";

const Home = () => {
  const navigate = useNavigate();
  const run = useRunUI();

  /* TEMP COUNTS — backend / DB will replace */
  const totalInsightsAndDashboards = 0;
  const totalExports = 0;

  return (
    <section>
      {/* ---------- HEADER ---------- */}
      <header style={{ marginBottom: "24px" }}>
        <h1>Home</h1>
        <p style={{ color: "#6b7280", fontSize: "14px" }}>
          Offline Industrial Data Intelligence System
        </p>
      </header>

      {/* ---------- TOP SUMMARY BLOCKS ---------- */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "16px",
          marginBottom: "28px",
        }}
      >
        {/* Active Run */}
        <SummaryCard
          title="Active Run"
          value={run.activeRunId ?? "No run selected"}
          description="Currently selected ingestion run"
        />

        {/* Total Insights & Dashboards */}
        <SummaryCard
          title="Total Insights & Dashboards"
          value={totalInsightsAndDashboards.toString()}
          description="Generated from successful ingestions"
        />

        {/* Total Exports */}
        <SummaryCard
          title="Total Exports"
          value={totalExports.toString()}
          description="Insights and dashboards exported"
        />
      </div>

      {/* ---------- ACTION BUTTONS ---------- */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "20px",
        }}
      >
        <ActionCard
          title="Ingestion"
          description="Ingest industrial data files to generate insights and dashboards."
          onClick={() => navigate("/ingestion")}
        />

        <ActionCard
          title="Insights"
          description="View insights from previously successful ingestions."
          onClick={() => navigate("/insights")}
        />

        <ActionCard
          title="Dashboards"
          description="Explore auto-generated dashboards and saved layouts."
          onClick={() => navigate("/dashboards")}
        />

        <ActionCard
          title="Exports"
          description="Export insights, dashboards, and analytical reports."
          onClick={() => navigate("/exports")}
        />

        <ActionCard
          title="Data Health"
          description="Review data quality, schema issues, and ingestion diagnostics."
          onClick={() => navigate("/data-health")}
        />

        <ActionCard
          title="Explorer"
          description="Explore raw and processed datasets interactively."
          onClick={() => navigate("/explorer")}
        />
      </div>
    </section>
  );
};

/* ---------- COMPONENTS ---------- */

interface SummaryCardProps {
  title: string;
  value: string;
  description: string;
}

const SummaryCard = ({
  title,
  value,
  description,
}: SummaryCardProps) => (
  <div style={summaryCard}>
    <div style={summaryTitle}>{title}</div>
    <div style={summaryValue}>{value}</div>
    <div style={summaryDesc}>{description}</div>
  </div>
);

interface ActionCardProps {
  title: string;
  description: string;
  onClick: () => void;
}

const ActionCard = ({
  title,
  description,
  onClick,
}: ActionCardProps) => (
  <div
    style={actionCard}
    onClick={onClick}
    role="button"
  >
    <h3 style={{ marginBottom: "6px" }}>{title}</h3>
    <p style={{ fontSize: "13px", color: "#6b7280" }}>
      {description}
    </p>
  </div>
);

/* ---------- STYLES ---------- */

const summaryCard: React.CSSProperties = {
  background: "#ffffff",
  borderRadius: "12px",
  padding: "16px",
  boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
};

const summaryTitle: React.CSSProperties = {
  fontSize: "13px",
  color: "#6b7280",
  marginBottom: "6px",
};

const summaryValue: React.CSSProperties = {
  fontSize: "20px",
  fontWeight: 600,
  marginBottom: "4px",
};

const summaryDesc: React.CSSProperties = {
  fontSize: "12px",
  color: "#9ca3af",
};

const actionCard: React.CSSProperties = {
  background: "#ffffff",
  borderRadius: "12px",
  padding: "18px",
  boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
  cursor: "pointer",
  transition: "transform 0.15s ease, box-shadow 0.15s ease",
};

export default Home;