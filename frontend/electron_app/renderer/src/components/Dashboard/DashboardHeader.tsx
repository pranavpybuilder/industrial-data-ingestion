import { FiSave, FiBarChart2, FiDownload } from "react-icons/fi";
import { useNavigate } from "react-router-dom";

interface Props {
  dashboardTitle: string;
  runName: string;
}

const DashboardHeader = ({ dashboardTitle, runName }: Props) => {
  const navigate = useNavigate();

  return (
    <header style={styles.wrapper}>
      <div>
        <h1 style={styles.run}>{runName}</h1>
        <p style={styles.subtitle}>{dashboardTitle}</p>
      </div>

      <div style={styles.actions}>
        <button><FiSave /> Save</button>
        <button onClick={() => navigate("/insights")}>
          <FiBarChart2 /> Show Insights
        </button>
        <button onClick={() => navigate("/exports")}>
          <FiDownload /> Export
        </button>
      </div>
    </header>
  );
};

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "1.25rem",
  },
  run: { fontSize: "22px", fontWeight: 700 },
  subtitle: { fontSize: "13px", color: "#6b7280" },
  actions: { display: "flex", gap: "0.75rem" },
};

export default DashboardHeader;