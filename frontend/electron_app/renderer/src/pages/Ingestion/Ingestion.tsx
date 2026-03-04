import { useState } from "react";
import { FiUploadCloud } from "react-icons/fi";

import FileUploadCard from "../../components/ingestion/FileUploadCard";
import IngestionActions from "../../components/ingestion/IngestionActions";
import IngestionStatusBanner from "../../components/ingestion/IngestionStatusBanner";
import { frontendApi } from "../../services/frontendApi";
import { clearActiveRunContext, onRunChange } from "../../state/state_reset";

export type IngestionStatus = "idle" | "success" | "failed";

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

const Ingestion = () => {
  const [filePath, setFilePath] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileExt, setFileExt] = useState<string | null>(null);
  const [status, setStatus] = useState<IngestionStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleIngest = async () => {
    if (!filePath) return;

    setStatus("idle");
    setError(null);
    setIsRunning(true);
    clearActiveRunContext();

    // Pass no source_type — let the backend auto-detect everything
    const result = await frontendApi.uploadFile(filePath);
    setIsRunning(false);

    if (!result.success) {
      setStatus("failed");
      setError(result.message || "Pipeline failed");
      const failedRunId = result.data?.run_id;
      if (failedRunId) {
        onRunChange(String(failedRunId));
      }
      return;
    }

    const runId = result.data?.run_id;
    if (!runId) {
      setStatus("failed");
      setError("Backend did not return run_id");
      return;
    }

    onRunChange(runId);
    setStatus("success");
  };

  return (
    <>
      <style>{fadeKeyframes}</style>
      <section style={styles.page}>
        <header style={styles.header}>
          <div style={styles.headerIcon}>
            <FiUploadCloud size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={styles.title}>Data Ingestion</h1>
            <p style={styles.subtitle}>
              Upload any CSV or Excel file. Source type, schema, and domain are
              auto-detected. Multi-sheet workbooks are fully processed.
            </p>
          </div>
        </header>

        <FileUploadCard
          fileName={fileName}
          fileExt={fileExt}
          onFileSelected={(selectedPath, selectedName, ext) => {
            setFilePath(selectedPath);
            setFileName(selectedName);
            setFileExt(ext || null);
            setStatus("idle");
            setError(null);
          }}
        />

        <IngestionActions
          disabled={!filePath || isRunning}
          onIngest={handleIngest}
        />

        <IngestionStatusBanner status={status} error={error} />
      </section>
    </>
  );
};

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: "24px",
    maxWidth: "900px",
    animation: "fadeIn 0.3s ease-out",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    marginBottom: "28px",
  },
  headerIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    background: "#eef2ff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  title: {
    fontSize: "22px",
    fontWeight: 700,
    color: "#111827",
    margin: 0,
  },
  subtitle: {
    fontSize: "14px",
    color: "#6b7280",
    margin: 0,
    marginTop: 2,
  },
};

export default Ingestion;
