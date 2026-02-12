import { useState } from "react";
import { FiCheckCircle, FiAlertCircle } from "react-icons/fi";
import { IngestionStatus } from "../../pages/Ingestion/Ingestion";
import { useNavigate } from "react-router-dom";

interface Props {
  status: IngestionStatus;
  error: string | null;
}

const slideUpKeyframes = `
@keyframes slideUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
`;

const IngestionStatusBanner = ({ status, error }: Props) => {
  const navigate = useNavigate();
  const [hoveredBtn, setHoveredBtn] = useState<string | null>(null);

  if (status === "idle") return null;

  const navBtn = (label: string, path: string): React.ReactElement => (
    <button
      key={path}
      onClick={() => navigate(path)}
      onMouseEnter={() => setHoveredBtn(path)}
      onMouseLeave={() => setHoveredBtn(null)}
      style={{
        ...styles.navBtn,
        background: hoveredBtn === path ? "#f3f4f6" : "#ffffff",
        borderColor: status === "failed" ? "#fca5a5" : "#86efac",
      }}
    >
      {label}
    </button>
  );

  if (status === "failed") {
    return (
      <>
        <style>{slideUpKeyframes}</style>
        <div style={{ ...styles.banner, ...styles.failed }}>
          <div style={styles.headerRow}>
            <FiAlertCircle size={20} color="#ef4444" />
            <strong style={{ color: "#991b1b" }}>Ingestion Failed</strong>
          </div>
          <p style={styles.errorText}>{error}</p>
          {navBtn("Go to Data Health", "/data-health")}
        </div>
      </>
    );
  }

  return (
    <>
      <style>{slideUpKeyframes}</style>
      <div style={{ ...styles.banner, ...styles.success }}>
        <div style={styles.headerRow}>
          <FiCheckCircle size={20} color="#10b981" />
          <strong style={{ color: "#065f46" }}>Ingestion Successful</strong>
        </div>

        <div style={styles.actions}>
          {navBtn("Go to Insights", "/insights")}
          {navBtn("Go to Dashboards", "/dashboards")}
          {navBtn("Data Health", "/data-health")}
        </div>
      </div>
    </>
  );
};

const styles: Record<string, React.CSSProperties> = {
  banner: {
    marginTop: "20px",
    padding: "20px",
    borderRadius: "12px",
    animation: "slideUp 0.3s ease",
  },
  success: {
    background: "#ecfdf5",
    border: "1px solid #10b981",
  },
  failed: {
    background: "#fef2f2",
    border: "1px solid #ef4444",
  },
  headerRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "8px",
  },
  errorText: {
    fontSize: "13px",
    color: "#7f1d1d",
    margin: "4px 0 12px 0",
  },
  actions: {
    display: "flex",
    gap: "12px",
    marginTop: "12px",
  },
  navBtn: {
    padding: "8px 14px",
    borderRadius: "8px",
    border: "1px solid #d1d5db",
    background: "#ffffff",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.2s ease",
    color: "#374151",
  },
};

export default IngestionStatusBanner;