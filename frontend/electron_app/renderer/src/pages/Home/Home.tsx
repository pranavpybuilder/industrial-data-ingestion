import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRunUI } from "../../state/useRunUI";
import {
  FiUpload,
  FiZap,
  FiGrid,
  FiDownload,
  FiActivity,
  FiDatabase,
} from "react-icons/fi";

const Home = () => {
  const navigate = useNavigate();
  const run = useRunUI();

  /* TEMP COUNTS — backend / DB will replace */
  const totalInsightsAndDashboards = 0;
  const totalExports = 0;

  return (
    <section style={{ animation: "fadeIn 0.3s ease-out" }}>
      {/* ---------- HEADER ---------- */}
      <header style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "28px", fontWeight: 700, letterSpacing: "-0.02em" }}>
          Welcome back
        </h1>
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
          marginBottom: "32px",
        }}
      >
        <SummaryCard
          label="Active Run"
          value={run.activeRunId ?? "None"}
          description="Currently selected ingestion run"
          accent="#6366f1"
          mono
        >
          {!run.activeRunId && (
            <button
              onClick={() => navigate("/ingestion")}
              style={{
                marginTop: "12px",
                padding: "9px",
                width: "100%",
                borderRadius: "8px",
                border: "none",
                background: "#6366f1",
                color: "#ffffff",
                fontSize: "13px",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Start New Ingestion
            </button>
          )}
        </SummaryCard>

        <SummaryCard
          label="Insights & Dashboards"
          value={totalInsightsAndDashboards.toString()}
          description="Generated from successful ingestions"
          accent="#8b5cf6"
        />

        <SummaryCard
          label="Total Exports"
          value={totalExports.toString()}
          description="Insights and dashboards exported"
          accent="#10b981"
        />
      </div>

      {/* ---------- QUICK ACTIONS ---------- */}
      <h2 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "14px", color: "#374151" }}>
        Quick Actions
      </h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "16px",
        }}
      >
        <ActionCard icon={<FiUpload />} title="Ingestion"
          description="Ingest industrial data files to generate insights."
          onClick={() => navigate("/ingestion")} />
        <ActionCard icon={<FiZap />} title="Insights"
          description="View insights from successful ingestions."
          onClick={() => navigate("/insights")} />
        <ActionCard icon={<FiGrid />} title="Dashboards"
          description="Explore auto-generated dashboards and layouts."
          onClick={() => navigate("/dashboards")} />
        <ActionCard icon={<FiDownload />} title="Exports"
          description="Export insights, dashboards, and reports."
          onClick={() => navigate("/exports")} />
        <ActionCard icon={<FiActivity />} title="Data Health"
          description="Review data quality and ingestion diagnostics."
          onClick={() => navigate("/data-health")} />
        <ActionCard icon={<FiDatabase />} title="Explorer"
          description="Explore raw and processed datasets interactively."
          onClick={() => navigate("/explorer")} />
      </div>
    </section>
  );
};

/* ---------- Summary Card ---------- */

interface SummaryCardProps {
  label: string;
  value: string;
  description: string;
  accent: string;
  mono?: boolean;
  children?: React.ReactNode;
}

const SummaryCard = ({ label, value, description, accent, mono, children }: SummaryCardProps) => (
  <div
    style={{
      background: "#ffffff",
      borderRadius: "12px",
      padding: "20px",
      border: "1px solid #e5e7eb",
      boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
      transition: "all 0.2s ease",
      borderTop: `3px solid ${accent}`,
    }}
  >
    <div style={{ fontSize: "12px", fontWeight: 500, color: "#6b7280", textTransform: "uppercase" as const, letterSpacing: "0.5px", marginBottom: "8px" }}>
      {label}
    </div>
    <div
      style={{
        fontSize: "22px",
        fontWeight: 700,
        color: "#111827",
        marginBottom: "4px",
        fontFamily: mono ? "'JetBrains Mono', Consolas, monospace" : "inherit",
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
      }}
      title={value}
    >
      {value}
    </div>
    <div style={{ fontSize: "12px", color: "#9ca3af" }}>{description}</div>
    {children}
  </div>
);

/* ---------- Action Card ---------- */

interface ActionCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  onClick: () => void;
}

const ActionCard = ({ icon, title, description, onClick }: ActionCardProps) => {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
      style={{
        background: "#ffffff",
        borderRadius: "12px",
        padding: "20px",
        border: `1px solid ${hovered ? "#c7d2fe" : "#e5e7eb"}`,
        boxShadow: hovered
          ? "0 8px 20px rgba(99, 102, 241, 0.1)"
          : "0 1px 3px rgba(0,0,0,0.04)",
        cursor: "pointer",
        transition: "all 0.2s ease",
        transform: hovered ? "translateY(-2px)" : "none",
      }}
    >
      <div
        style={{
          width: "36px",
          height: "36px",
          borderRadius: "10px",
          background: hovered ? "#6366f1" : "#f0f0ff",
          color: hovered ? "#ffffff" : "#6366f1",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "18px",
          marginBottom: "12px",
          transition: "all 0.2s ease",
        }}
      >
        {icon}
      </div>
      <h3 style={{ fontSize: "15px", fontWeight: 600, marginBottom: "4px", color: "#111827" }}>
        {title}
      </h3>
      <p style={{ fontSize: "13px", color: "#6b7280", lineHeight: 1.5 }}>
        {description}
      </p>
    </div>
  );
};

export default Home;