import { useEffect, useState } from "react";
import SearchBar from "../SearchBar/SearchBar";
import { onRunChange } from "../../state/state_reset";

interface RunMeta {
  run_id: string;
}

interface Props {
  onClose: () => void;
}

const RunSelectorModal = ({ onClose }: Props) => {
  const [runs, setRuns] = useState<RunMeta[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadRuns = async () => {
      try {
        const result = await window.frontendAPI.get_runs();
        setRuns(result || []);
      } catch (err) {
        console.error("Failed to load runs", err);
        setRuns([]);
      } finally {
        setLoading(false);
      }
    };

    loadRuns();
  }, []);

  const filteredRuns = runs.filter((r) =>
    r.run_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div
      style={{
        background: "#ffffff",
        borderRadius: "12px",
        padding: "20px",
        width: "420px",
      }}
    >
      <h2 style={{ marginBottom: "12px" }}>Select Ingested File</h2>

      <SearchBar
        value={search}
        placeholder="Search run / file..."
        onChange={setSearch}
      />

      <div style={{ maxHeight: "260px", overflowY: "auto" }}>
        {loading && <p>Loading runs...</p>}

        {!loading && filteredRuns.length === 0 && (
          <p style={{ color: "#6b7280" }}>No matching runs found</p>
        )}

        {filteredRuns.map((run) => (
          <div
            key={run.run_id}
            onClick={() => {
              onRunChange(run.run_id);
              onClose();
            }}
            style={{
              padding: "10px",
              marginBottom: "8px",
              borderRadius: "8px",
              border: "1px solid #e5e7eb",
              cursor: "pointer",
            }}
          >
            {run.run_id}
          </div>
        ))}
      </div>

      <button
        onClick={onClose}
        style={{
          marginTop: "12px",
          background: "transparent",
          border: "none",
          color: "#2563eb",
          cursor: "pointer",
        }}
      >
        Cancel
      </button>
    </div>
  );
};

export default RunSelectorModal;