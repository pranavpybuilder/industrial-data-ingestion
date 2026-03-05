import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import SearchBar from "../SearchBar/SearchBar";
import { runUI } from "../../state/run_ui_store";
import { frontendApi } from "../../services/frontendApi";
import { clearActiveRunContext, onRunChange } from "../../state/state_reset";
import "./RunSelectorModal.css";

interface RunMeta {
  run_id: string;
  run_name?: string;
  file_name?: string;
  source_type?: string;
  status?: string;
  created_at?: string;
}

interface Props {
  onClose: () => void;
}

const RunSelectorModal = ({ onClose }: Props) => {
  const runState = useSyncExternalStore(runUI.subscribe, runUI.getSnapshot);
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

  const filteredRuns = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return runs;
    return runs.filter((run) => {
      return (
        run.run_id.toLowerCase().includes(needle) ||
        (run.file_name || "").toLowerCase().includes(needle) ||
        (run.run_name || "").toLowerCase().includes(needle) ||
        (run.source_type || "").toLowerCase().includes(needle)
      );
    });
  }, [runs, search]);

  const handleSelectRun = (run: RunMeta) => {
    onRunChange(run.run_id, run.file_name);
    onClose();
  };

  const handleClearRun = () => {
    clearActiveRunContext();
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Select Ingested Run</h2>
          <button className="close-btn" onClick={onClose} aria-label="Close" title="Close">
            x
          </button>
        </div>

        <div className="modal-body">
          <div className="search-wrapper">
            <SearchBar
              value={search}
              placeholder="Search run / file..."
              onChange={setSearch}
            />
            {runState.activeRunId && (
              <button
                className="clear-run-btn"
                onClick={handleClearRun}
              >
                Clear Run
              </button>
            )}
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
              filteredRuns.map((run) => {
                const displayName = run.file_name || run.run_id;
                const dateStr = run.created_at
                  ? new Date(run.created_at).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })
                  : "";
                return (
                <div
                  key={run.run_id}
                  className="run-item"
                  onClick={() => handleSelectRun(run)}
                >
                  <div className="run-details">
                    <span className="run-id">{displayName}</span>
                    {dateStr && (
                      <span className="run-meta">
                        {dateStr}
                      </span>
                    )}
                  </div>
                  <div className="run-arrow">-&gt;</div>
                </div>
              );
              })}
          </div>
        </div>

        <div className="modal-footer">
          <div>
            {runState.activeRunId && (
              <button className="clear-run-footer-btn" onClick={handleClearRun}>
                Clear Run
              </button>
            )}
          </div>
          <button className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default RunSelectorModal;
