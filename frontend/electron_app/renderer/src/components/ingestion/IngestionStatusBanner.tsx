import { IngestionStatus } from "../../pages/Ingestion/Ingestion";
import { useNavigate } from "react-router-dom";

interface Props {
  status: IngestionStatus;
  error: string | null;
}

const IngestionStatusBanner = ({ status, error }: Props) => {
  const navigate = useNavigate();

  if (status === "idle") return null;

  if (status === "failed") {
    return (
      <div style={{ ...styles.banner, ...styles.failed }}>
        <strong>Ingestion Failed</strong>
        <p>{error}</p>
        <button onClick={() => navigate("/data-health")}>
          Go to Data Health
        </button>
      </div>
    );
  }

  return (
    <div style={{ ...styles.banner, ...styles.success }}>
      <strong>Ingestion Successful</strong>

      <div style={styles.actions}>
        <button onClick={() => navigate("/insights")}>
          Go to Insights
        </button>
        <button onClick={() => navigate("/dashboards")}>
          Go to Dashboards
        </button>
        <button onClick={() => navigate("/data-health")}>
          Data Health
        </button>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  banner: {
    marginTop: "20px",
    padding: "16px",
    borderRadius: "8px",
  },
  success: {
    background: "#ecfdf5",
    border: "1px solid #10b981",
  },
  failed: {
    background: "#fef2f2",
    border: "1px solid #ef4444",
  },
  actions: {
    display: "flex",
    gap: "12px",
    marginTop: "10px",
  },
};

export default IngestionStatusBanner;