import { useEffect, useState } from "react";
import { runUI } from "../../state/run_ui_store";
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
      <p style={{ fontSize: "13px", marginBottom: "8px", color: "#4b5563", fontWeight: 500 }}>
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
          padding: "8px 10px",
          marginBottom: "8px",
          borderRadius: "8px",
          border: "1px solid #d1d5db",
          fontSize: "13px",
          outline: "none",
        }}
      />

      <div style={{ maxHeight: "120px", overflowY: "auto" }}>
        {loading && <p style={{ fontSize: "12px", color: "#6b7280" }}>Loading...</p>}

        {!loading && filteredRuns.length === 0 && (
          <p style={{ fontSize: "12px", color: "#6b7280" }}>
            {search ? `No matching runs for "${search}"` : "No runs found"}
          </p>
        )}

        {filteredRuns.map((runId) => (
          <button
            key={runId}
            onClick={() => runUI.setActiveRun(runId)}
            style={{
              width: "100%",
              textAlign: "left",
              padding: "8px 10px",
              marginBottom: "4px",
              borderRadius: "8px",
              border: "1px solid #e5e7eb",
              background: runId === activeRunId ? "#eff6ff" : "#ffffff",
              cursor: "pointer",
              fontSize: "12px",
              fontFamily: "monospace",
              color: runId === activeRunId ? "#1d4ed8" : "#374151",
              fontWeight: runId === activeRunId ? 600 : 400,
            }}
          >
            {runId}
          </button>
        ))}
      </div>

      {activeRunId && (
        <button
          onClick={() => runUI.clearRun()}
          style={{
            width: "100%",
            marginTop: "8px",
            padding: "8px",
            borderRadius: "8px",
            border: "1px solid #ef4444",
            background: "#fee2e2",
            color: "#b91c1c",
            fontSize: "12px",
            fontWeight: 500,
            cursor: "pointer",
          }}
        >
          Clear Active Run
        </button>
      )}
    </div>
  );
};

export default RunSelector;