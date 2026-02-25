import { useRef, useState } from "react";
import { FiFile, FiUploadCloud } from "react-icons/fi";

import { frontendApi } from "../../services/frontendApi";
import { IngestionSource } from "../../pages/Ingestion/Ingestion";

interface Props {
  source: IngestionSource | null;
  onSourceChange: (s: IngestionSource) => void;
  fileName: string | null;
  onFileSelected: (filePath: string, fileName: string) => void;
}

const SOURCES: IngestionSource[] = ["SAP", "RFID", "PLC", "EXCEL", "ENERGY"];

const FileUploadCard = ({
  source,
  onSourceChange,
  fileName,
  onFileSelected,
}: Props) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [hoveredSource, setHoveredSource] = useState<string | null>(null);
  const [selectionError, setSelectionError] = useState<string | null>(null);

  const handleBrowse = async () => {
    if (!source) return;
    setSelectionError(null);

    // Desktop mode: use native dialog so backend receives a real absolute path.
    const picked = await frontendApi.selectFile();
    if (picked.success && picked.data?.file_path) {
      onFileSelected(picked.data.file_path, picked.data.file_name);
      return;
    }

    // Browser fallback for local UI testing.
    fileInputRef.current?.click();
  };

  const onFallbackPicked = (file: File) => {
    const fallbackPath = (file as any).path || "";
    if (!fallbackPath) {
      setSelectionError(
        "Browser mode does not expose absolute file paths. Run in desktop shell."
      );
      return;
    }

    onFileSelected(fallbackPath, file.name);
  };

  return (
    <div style={styles.card}>
      <h3 style={styles.heading}>Select Source</h3>

      <div style={styles.sources}>
        {SOURCES.map((s) => {
          const isSelected = source === s;
          const isHovered = hoveredSource === s;
          return (
            <button
              key={s}
              onClick={() => onSourceChange(s)}
              onMouseEnter={() => setHoveredSource(s)}
              onMouseLeave={() => setHoveredSource(null)}
              style={{
                ...styles.sourceBtn,
                background: isSelected
                  ? "#6366f1"
                  : isHovered
                    ? "#e0e7ff"
                    : "#f3f4f6",
                color: isSelected ? "#ffffff" : "#111827",
                boxShadow: isSelected ? "0 2px 8px rgba(99,102,241,0.3)" : "none",
              }}
            >
              {s}
            </button>
          );
        })}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        aria-label="Upload file"
        disabled={!source}
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            onFallbackPicked(file);
          }
        }}
      />

      <button
        type="button"
        style={{
          ...styles.dropZone,
          borderColor: !source ? "#d1d5db" : "#6366f1",
          opacity: !source ? 0.5 : 1,
          cursor: !source ? "not-allowed" : "pointer",
        }}
        disabled={!source}
        onClick={handleBrowse}
      >
        {fileName ? (
          <div style={styles.fileInfo}>
            <FiFile size={22} color="#6366f1" />
            <span style={styles.fileName}>{fileName}</span>
          </div>
        ) : (
          <div style={styles.dropContent}>
            <FiUploadCloud size={32} color="#6366f1" />
            <span style={styles.dropText}>Click to select a data file</span>
            <span style={styles.dropHint}>
              {source ? `Source: ${source}` : "Select a source first"}
            </span>
          </div>
        )}
      </button>

      {selectionError && (
        <p style={styles.error}>{selectionError}</p>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  card: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    marginTop: "20px",
    border: "1px solid #e5e7eb",
  },
  heading: {
    fontSize: "15px",
    fontWeight: 600,
    color: "#111827",
    marginTop: 0,
    marginBottom: "16px",
  },
  sources: {
    display: "flex",
    gap: "10px",
    marginBottom: "20px",
    flexWrap: "wrap",
  },
  sourceBtn: {
    padding: "8px 16px",
    borderRadius: "8px",
    border: "none",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: 500,
    transition: "all 0.2s ease",
  },
  dropZone: {
    border: "2px dashed #e5e7eb",
    borderRadius: "12px",
    padding: "32px",
    width: "100%",
    background: "#ffffff",
    transition: "all 0.2s ease",
  },
  dropContent: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "8px",
  },
  dropText: {
    fontSize: "14px",
    fontWeight: 500,
    color: "#374151",
  },
  dropHint: {
    fontSize: "12px",
    color: "#9ca3af",
  },
  fileInfo: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
  },
  fileName: {
    fontSize: "14px",
    fontWeight: 500,
    color: "#111827",
  },
  error: {
    color: "#b91c1c",
    fontSize: "12px",
    marginTop: "10px",
  },
};

export default FileUploadCard;
