import { useEffect, useState } from "react";
import SearchBar from "../SearchBar/SearchBar";
import { onRunChange } from "../../state/state_reset";
import { frontendApi } from "../../services/frontendApi";

interface RunMeta {
  run_id: string;
}

interface Props {
  onClose: () => void;
}

const RunSelectorModal = ({ onClose }: Props) => {
  const [runs, setRuns] = useState<RunMeta[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchRuns = async (query: string) => {
    setLoading(true);
    try {
      const result = await frontendApi.getRuns();
      setRuns(result || []);
    } catch (err) {
      console.error("Search failed", err);
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns("");
  }, []);

  useEffect(() => {
    const t = setTimeout(() => fetchRuns(search), 250);
    return () => clearTimeout(t);
  }, [search]);

  return (
    <div
      style={{
        background: "#ffffff",
        borderRadius: "12px",
        padding: "20px",
        width: "420px",
        boxShadow: "0 10px 25px rgba(0,0,0,0.12)",
      }}
    >
      <h2 style={{ marginBottom: "12px" }}>Select Ingested File</h2>

      <SearchBar
        value={search}
        placeholder="Search run / file..."
        onChange={setSearch}
      />

      <div style={{ maxHeight: "260px", overflowY: "auto" }}>
        {loading && <p style={{ color: "#6b7280" }}>Searching…</p>}

        {!loading && runs.length === 0 && (
          <p style={{ color: "#6b7280" }}>No matching runs found</p>
        )}

        {runs.map((run) => (
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
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "#f9fafb")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "#ffffff")
            }
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