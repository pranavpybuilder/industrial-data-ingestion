import { useEffect, useState } from "react";
import { onRunChange } from "../../state/state_reset";
import { useRunUI } from "../../state/useRunUI";
import { frontendApi, RunMeta } from "../../services/frontendApi";

const RunSelector = () => {
  const { activeRunId } = useRunUI();

  const [runs, setRuns] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        const result: RunMeta[] = await frontendApi.getRuns();
        setRuns(result.map((r: RunMeta) => r.run_id));
      } catch (err) {
        console.error("Failed to fetch runs", err);
        setRuns([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRuns();
  }, []);

  const filteredRuns = runs.filter((runId) =>
    runId.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ padding: "12px" }}>
      <p style={{ fontSize: "13px", marginBottom: "8px" }}>
        {activeRunId ?? "No run selected"}
      </p>

      <input
        type="text"
        placeholder="Search runs..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        disabled={loading}
        style={{
          width: "100%",
          padding: "6px 8px",
          marginBottom: "8px",
          borderRadius: "6px",
          border: "1px solid #d1d5db",
          fontSize: "12px",
        }}
      />

      <div style={{ maxHeight: "120px", overflowY: "auto" }}>
        {loading && <p>Loading runs...</p>}

        {!loading && filteredRuns.length === 0 && (
          <p>No runs found</p>
        )}

        {filteredRuns.map((runId) => (
          <button
            key={runId}
            onClick={() => onRunChange(runId)}
            style={{
              width: "100%",
              textAlign: "left",
              padding: "6px 8px",
              marginBottom: "4px",
              borderRadius: "6px",
              border: "1px solid #e5e7eb",
              background:
                runId === activeRunId ? "#e0f2fe" : "#ffffff",
            }}
          >
            {runId}
          </button>
        ))}
      </div>

      {activeRunId && (
        <button
          onClick={() => onRunChange("")}
          style={{
            width: "100%",
            marginTop: "6px",
            padding: "6px",
            borderRadius: "6px",
            border: "1px solid #ef4444",
            background: "#fee2e2",
          }}
        >
          Clear Active Run
        </button>
      )}
    </div>
  );
};

export default RunSelector;