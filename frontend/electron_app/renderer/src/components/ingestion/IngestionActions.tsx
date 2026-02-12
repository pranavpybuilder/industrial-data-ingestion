import { useState } from "react";
import { FiPlay } from "react-icons/fi";

interface Props {
  disabled: boolean;
  onIngest: () => void;
}

const IngestionActions = ({ disabled, onIngest }: Props) => {
  const [hovered, setHovered] = useState(false);

  return (
    <div style={styles.actions}>
      <button
        onClick={onIngest}
        disabled={disabled}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          ...styles.ingestBtn,
          opacity: disabled ? 0.45 : 1,
          cursor: disabled ? "not-allowed" : "pointer",
          background: hovered && !disabled ? "#4f46e5" : "#6366f1",
          transform: hovered && !disabled ? "translateY(-1px)" : "none",
          boxShadow:
            hovered && !disabled
              ? "0 4px 12px rgba(99,102,241,0.35)"
              : "0 1px 3px rgba(0,0,0,0.08)",
        }}
      >
        <FiPlay size={14} style={{ marginRight: "8px", verticalAlign: "middle" }} />
        Ingest Data
      </button>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  actions: {
    marginTop: "16px",
  },
  ingestBtn: {
    padding: "12px 24px",
    fontSize: "14px",
    fontWeight: 600,
    color: "#ffffff",
    background: "#6366f1",
    border: "none",
    borderRadius: "8px",
    display: "inline-flex",
    alignItems: "center",
    transition: "all 0.2s ease",
  },
};

export default IngestionActions;