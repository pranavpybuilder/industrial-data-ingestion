import { useState } from "react";
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
    <section style={styles.page}>
      <header>
        <h1>Data Ingestion</h1>
        <p>Ingest datasets from industrial sources.</p>
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
  );
};

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: "24px",
    maxWidth: "900px",
  },
};

export default Ingestion;