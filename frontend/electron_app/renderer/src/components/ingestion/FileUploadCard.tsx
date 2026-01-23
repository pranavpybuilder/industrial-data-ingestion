import { IngestionSource } from "../../pages/Ingestion/Ingestion";

interface Props {
  source: IngestionSource | null;
  onSourceChange: (s: IngestionSource) => void;
  file: File | null;
  onFileChange: (f: File) => void;
}

const SOURCES: IngestionSource[] = [
  "SAP",
  "RFID",
  "PLC",
  "EXCEL",
  "ENERGY",
];

const FileUploadCard = ({
  source,
  onSourceChange,
  file,
  onFileChange,
}: Props) => {
  return (
    <div style={styles.card}>
      <h3>Select Source</h3>

      <div style={styles.sources}>
        {SOURCES.map((s) => (
          <button
            key={s}
            onClick={() => onSourceChange(s)}
            style={{
              ...styles.sourceBtn,
              background: source === s ? "#2563eb" : "#f3f4f6",
              color: source === s ? "#ffffff" : "#111827",
            }}
          >
            {s}
          </button>
        ))}
      </div>

      <div style={styles.upload}>
        <input
          type="file"
          disabled={!source}
          onChange={(e) =>
            e.target.files && onFileChange(e.target.files[0])
          }
        />
        {file && <p>Selected file: {file.name}</p>}
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  card: {
    background: "#ffffff",
    borderRadius: "8px",
    padding: "20px",
    marginTop: "20px",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },
  sources: {
    display: "flex",
    gap: "10px",
    marginBottom: "16px",
    flexWrap: "wrap",
  },
  sourceBtn: {
    padding: "8px 14px",
    borderRadius: "6px",
    border: "none",
    cursor: "pointer",
    fontSize: "13px",
  },
  upload: {
    marginTop: "12px",
    fontSize: "13px",
  },
};

export default FileUploadCard;