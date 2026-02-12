import { useState } from "react";
import { FiUploadCloud } from "react-icons/fi";
import FileUploadCard from "../../components/ingestion/FileUploadCard";
import IngestionActions from "../../components/ingestion/IngestionActions";
import IngestionStatusBanner from "../../components/ingestion/IngestionStatusBanner";
import { runUI } from "../../state/run_ui_store";

export type IngestionSource =
  | "SAP"
  | "RFID"
  | "PLC"
  | "EXCEL"
  | "ENERGY";

export type IngestionStatus = "idle" | "success" | "failed";

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
`;

const Ingestion = () => {
  const [source, setSource] = useState<IngestionSource | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<IngestionStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const handleIngest = async () => {
    if (!file || !source) return;

    setStatus("idle");
    setError(null);

    try {
      /**
       * 🔌 BACKEND HOOK (future)
       * ipc.ingest({ source, file })
       */
      await new Promise((res) => setTimeout(res, 900));

      // ✅ Mock success
      runUI.setActiveRun(file.name);
      setStatus("success");
    } catch (err) {
      setStatus("failed");
      setError("Invalid schema or unsupported columns");
    }
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
            <p style={styles.subtitle}>Ingest datasets from industrial sources.</p>
          </div>
        </header>

        <FileUploadCard
          source={source}
          onSourceChange={setSource}
          file={file}
          onFileChange={setFile}
        />

        <IngestionActions
          disabled={!file || !source}
          onIngest={handleIngest}
        />

        <IngestionStatusBanner
          status={status}
          error={error}
        />
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