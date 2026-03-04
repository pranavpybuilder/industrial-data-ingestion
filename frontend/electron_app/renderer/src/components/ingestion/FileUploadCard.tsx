import { useRef, useState } from "react";
import { FiFile, FiUploadCloud } from "react-icons/fi";

import { frontendApi } from "../../services/frontendApi";

/* ---------------------------------------------------------------
   Accepted extensions shown in the helper text
--------------------------------------------------------------- */
const ACCEPTED = ".csv, .xlsx, .xls";

interface Props {
  fileName: string | null;
  fileExt: string | null;
  onFileSelected: (filePath: string, fileName: string, ext?: string) => void;
}

const FileUploadCard = ({ fileName, fileExt, onFileSelected }: Props) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDropHover, setIsDropHover] = useState(false);
  const [selectionError, setSelectionError] = useState<string | null>(null);

  /* ---------- Desktop native dialog (primary) ---------- */
  const handleBrowse = async () => {
    setSelectionError(null);

    const picked = await frontendApi.selectFile();
    if (picked.success && picked.data?.file_path) {
      const ext = picked.data.file_name?.split(".").pop()?.toLowerCase() || "";
      onFileSelected(picked.data.file_path, picked.data.file_name, ext);
      return;
    }

    // Browser fallback for local UI testing.
    fileInputRef.current?.click();
  };

  const onFallbackPicked = (file: File) => {
    const fallbackPath = (file as any).path || "";
    if (!fallbackPath) {
      setSelectionError(
        "Browser mode can't expose absolute paths. Run inside the desktop shell.",
      );
      return;
    }
    const ext = file.name.split(".").pop()?.toLowerCase() || "";
    onFileSelected(fallbackPath, file.name, ext);
  };

  /* ---------- Badge shown after file selection ---------- */
  const renderExtBadge = () => {
    if (!fileExt) return null;
    const label = fileExt.toUpperCase();
    const color =
      fileExt === "xlsx" || fileExt === "xls" ? "#059669" : "#6366f1";
    return (
      <span
        style={{
          fontSize: "11px",
          fontWeight: 600,
          color,
          background: color + "14",
          padding: "2px 8px",
          borderRadius: "6px",
          marginLeft: "8px",
        }}
      >
        {label}
      </span>
    );
  };

  return (
    <div style={styles.card}>
      <h3 style={styles.heading}>Select Data File</h3>

      {/* hidden fallback input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED}
        aria-label="Upload file"
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFallbackPicked(file);
        }}
      />

      {/* clickable drop-zone */}
      <button
        type="button"
        style={{
          ...styles.dropZone,
          borderColor: isDropHover ? "#818cf8" : "#6366f1",
          background: isDropHover ? "#eef2ff" : "#ffffff",
        }}
        onClick={handleBrowse}
        onMouseEnter={() => setIsDropHover(true)}
        onMouseLeave={() => setIsDropHover(false)}
      >
        {fileName ? (
          <div style={styles.fileInfo}>
            <FiFile size={22} color="#6366f1" />
            <span style={styles.fileName}>
              {fileName}
              {renderExtBadge()}
            </span>
          </div>
        ) : (
          <div style={styles.dropContent}>
            <FiUploadCloud size={34} color="#6366f1" />
            <span style={styles.dropText}>
              Click to select a data file
            </span>
            <span style={styles.dropHint}>
              Supports {ACCEPTED} &mdash; source type is auto-detected
            </span>
          </div>
        )}
      </button>

      {selectionError && <p style={styles.error}>{selectionError}</p>}
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
  dropZone: {
    border: "2px dashed #6366f1",
    borderRadius: "12px",
    padding: "36px",
    width: "100%",
    cursor: "pointer",
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
