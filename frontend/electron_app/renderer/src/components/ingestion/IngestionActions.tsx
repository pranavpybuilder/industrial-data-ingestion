interface Props {
  disabled: boolean;
  onIngest: () => void;
}

const IngestionActions = ({ disabled, onIngest }: Props) => {
  return (
    <div style={styles.actions}>
      <button
        onClick={onIngest}
        disabled={disabled}
        style={{
          ...styles.ingestBtn,
          opacity: disabled ? 0.5 : 1,
        }}
      >
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
    padding: "10px 16px",
    fontSize: "14px",
    cursor: "pointer",
  },
};

export default IngestionActions;