import { useEffect, useState } from "react";
import SearchBar from "../SearchBar/SearchBar";
import { runUI } from "../../state/run_ui_store";
import { frontendApi } from "../../services/frontendApi";
import "./RunSelectorModal.css";

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

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const result = await frontendApi.getRuns();
      setRuns(result || []);
    } catch (err) {
      console.error("Failed to fetch runs", err);
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const filteredRuns = runs.filter((run) => {
    if (!search.trim()) return true;
    const searchLower = search.toLowerCase().trim();
    const runIdLower = run.run_id.toLowerCase();
    return runIdLower.includes(searchLower);
  });

  const handleSelectRun = (runId: string) => {
    runUI.setActiveRun(runId);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Select Ingested File</h2>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="search-wrapper">
            <SearchBar
              value={search}
              placeholder="Search run / file..."
              onChange={setSearch}
            />
          </div>

          <div className="runs-list-container">
            {loading && (
              <div className="state-message">
                <div className="spinner"></div>
                <p>Loading runs...</p>
              </div>
            )}

            {!loading && filteredRuns.length === 0 && (
              <div className="state-message empty">
                <p className="empty-text">
                  {search
                    ? `No runs found matching "${search}"`
                    : "No runs available"}
                </p>
                {search && (
                  <button
                    className="clear-search-btn"
                    onClick={() => setSearch("")}
                  >
                    Clear search
                  </button>
                )}
              </div>
            )}

            {!loading &&
              filteredRuns.map((run) => (
                <div
                  key={run.run_id}
                  className="run-item"
                  onClick={() => handleSelectRun(run.run_id)}
                >
                  <div className="run-details">
                    <span className="run-id">{run.run_id}</span>
                  </div>
                  <div className="run-arrow">→</div>
                </div>
              ))}
          </div>
        </div>

        <div className="modal-footer">
          <button className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default RunSelectorModal;