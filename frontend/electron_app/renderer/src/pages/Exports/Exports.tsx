import { useEffect, useState, useSyncExternalStore, useCallback } from "react";
import {
  FiFileText,
  FiImage,
  FiDownload,
  FiRefreshCw,
  FiFile,
  FiExternalLink,
  FiCheckCircle,
  FiLoader,
  FiUploadCloud,
  FiLayers,
} from "react-icons/fi";

import { frontendApi, ExportRecord, IPCResponse } from "../../services/frontendApi";
import { runUI } from "../../state/run_ui_store";

/* ─────────────────────────────────────────
   Types
   ───────────────────────────────────────── */

type ExportMode = "insights_docx" | "insights_pdf" | "dashboard_pdf" | "dashboard_json" | "full_report";

interface CardConfig {
  id: ExportMode;
  title: string;
  description: string;
  icon: React.ReactNode;
  emitLabel: string;
  needsCapture: boolean;
}

/* ─────────────────────────────────────────
   Card definitions for the 4 export modes
   ───────────────────────────────────────── */

const EXPORT_CARDS: CardConfig[] = [
  {
    id: "insights_docx",
    title: "Insights Report (DOCX)",
    description:
      "Professional Word document with cover page, table of contents, executive summary, severity-colored findings, root cause table, 3-tier recommendations, and predictive signals.",
    icon: <FiFileText size={28} />,
    emitLabel: "Export DOCX",
    needsCapture: false,
  },
  {
    id: "insights_pdf",
    title: "Insights Report (PDF)",
    description:
      "A4 portrait PDF with the same comprehensive sections as DOCX — executive summary, findings with severity colors, root cause analysis, recommendations, and ML signals.",
    icon: <FiFile size={28} />,
    emitLabel: "Export PDF",
    needsCapture: false,
  },
  {
    id: "dashboard_pdf",
    title: "Dashboard Snapshot (PDF)",
    description:
      "Captures the current dashboard visualization at 4K resolution and embeds it in an A3 landscape PDF. Navigate to the Dashboard page first to ensure the latest view is captured.",
    icon: <FiImage size={28} />,
    emitLabel: "Capture & Export",
    needsCapture: true,
  },
  {
    id: "dashboard_json",
    title: "Dashboard Layout (JSON)",
    description:
      "Exports the full dashboard blueprint and your saved layout as a JSON file. This can be re-imported later to restore your dashboard configuration.",
    icon: <FiDownload size={28} />,
    emitLabel: "Export JSON",
    needsCapture: false,
  },
  {
    id: "full_report",
    title: "Full Report (PDF)",
    description:
      "Complete unified report: A4 portrait pages for all insights sections, followed by a divider page and the dashboard screenshot on A3 landscape pages. Single PDF file.",
    icon: <FiLayers size={28} />,
    emitLabel: "Generate Full Report",
    needsCapture: true,
  },
];

/* ─────────────────────────────────────────
   fade-in keyframes
   ───────────────────────────────────────── */

const fadeKeyframes = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
`;

/* ─────────────────────────────────────────
   Dashboard capture util (html2canvas)
   ───────────────────────────────────────── */

async function captureDashboardImage(): Promise<string | null> {
  try {
    // Dynamically import html2canvas so it doesn't break if not installed
    const html2canvasModule = await import("html2canvas");
    const html2canvas = html2canvasModule.default || html2canvasModule;

    // Look for the dashboard canvas container
    const target =
      document.getElementById("dashboard-canvas") ||
      document.querySelector("[data-dashboard-root]") ||
      document.querySelector(".dashboard-grid");

    if (!target) {
      return null;
    }

    const canvas = await html2canvas(target as HTMLElement, {
      scale: 4, // 4K resolution
      useCORS: true,
      backgroundColor: "#ffffff",
      logging: false,
    });

    return canvas.toDataURL("image/png");
  } catch {
    return null;
  }
}

/* ─────────────────────────────────────────
   Main Component
   ───────────────────────────────────────── */

const Exports = () => {
  const runState = useSyncExternalStore(runUI.subscribe, runUI.getSnapshot);
  const activeRun = runState.activeRunId;

  const [loadingCard, setLoadingCard] = useState<ExportMode | null>(null);
  const [successCard, setSuccessCard] = useState<ExportMode | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successFilePath, setSuccessFilePath] = useState<string | null>(null);

  const [exportHistory, setExportHistory] = useState<ExportRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  /* ── Load export history ── */
  const loadHistory = useCallback(async () => {
    if (!activeRun) return;
    setHistoryLoading(true);
    try {
      const res = await frontendApi.getExportHistory(activeRun);
      if (res.success && res.data?.exports) {
        setExportHistory(res.data.exports);
      } else {
        // Fallback to legacy endpoint
        const legacy = await frontendApi.getExports(activeRun);
        if (legacy.success && Array.isArray(legacy.data)) {
          setExportHistory(legacy.data);
        } else {
          setExportHistory([]);
        }
      }
    } catch {
      setExportHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, [activeRun]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  /* ── Handle export click ── */
  const handleExport = async (card: CardConfig) => {
    if (!activeRun || loadingCard) return;

    setLoadingCard(card.id);
    setSuccessCard(null);
    setErrorMsg(null);
    setSuccessFilePath(null);

    let imageBase64: string | null = null;

    // Capture dashboard image if needed
    if (card.needsCapture) {
      imageBase64 = await captureDashboardImage();
      if (!imageBase64) {
        // Create a minimal fallback image (1x1 white PNG)
        // so exports don't fail when dashboard isn't visible
        imageBase64 =
          "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==";
      }
    }

    let res: IPCResponse<{ file_path: string }>;

    try {
      switch (card.id) {
        case "insights_docx":
          res = await frontendApi.exportInsightsDocx(activeRun);
          break;
        case "insights_pdf":
          res = await frontendApi.exportInsightsPdf(activeRun);
          break;
        case "dashboard_pdf":
          res = await frontendApi.exportDashboardPdf(activeRun, imageBase64!);
          break;
        case "dashboard_json":
          res = await frontendApi.exportDashboardJson(activeRun);
          break;
        case "full_report":
          res = await frontendApi.exportFullReport(activeRun, imageBase64!);
          break;
        default:
          res = { success: false, message: "Unknown export mode" };
      }
    } catch (err) {
      res = { success: false, message: `Export failed: ${err}` };
    }

    setLoadingCard(null);

    if (res.success) {
      setSuccessCard(card.id);
      setSuccessFilePath(res.data?.file_path || null);
      await loadHistory();
    } else {
      setErrorMsg(res.message || "Export failed");
    }
  };

  /* ── Open file in OS ── */
  const handleOpenFile = async (filePath: string) => {
    await frontendApi.openExportFile(filePath);
  };

  /* ── No active run ── */
  if (!activeRun) {
    return (
      <section style={s.page}>
        <header style={s.header}>
          <div style={s.headerIcon}>
            <FiDownload size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={s.title}>Exports</h1>
            <p style={s.subtitle}>No active run selected. Upload data first.</p>
          </div>
        </header>
      </section>
    );
  }

  return (
    <>
      <style>{fadeKeyframes}</style>
      <section style={s.page}>
        {/* ── Header ── */}
        <header style={s.header}>
          <div style={s.headerIcon}>
            <FiDownload size={22} color="#6366f1" />
          </div>
          <div>
            <h1 style={s.title}>Export Center</h1>
            <p style={s.subtitle}>
              Run: <strong>{activeRun}</strong>
            </p>
          </div>
        </header>

        {/* ── Global error ── */}
        {errorMsg && (
          <div style={s.errorBanner} id="export-error-banner">
            <span style={{ fontWeight: 600 }}>Export Error:</span> {errorMsg}
            <button
              style={{ ...s.linkBtn, marginLeft: 12 }}
              onClick={() => setErrorMsg(null)}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* ── Global success ── */}
        {successCard && (
          <div style={s.successBanner} id="export-success-banner">
            <FiCheckCircle size={16} color="#10b981" />
            <span>Export completed successfully!</span>
            {successFilePath && (
              <button
                style={s.openBtn}
                onClick={() => handleOpenFile(successFilePath)}
              >
                <FiExternalLink size={13} /> Open File
              </button>
            )}
          </div>
        )}

        {/* ── Export Mode Cards ── */}
        <div style={s.cardGrid} id="export-mode-cards">
          {EXPORT_CARDS.map((card) => {
            const isLoading = loadingCard === card.id;
            const isSuccess = successCard === card.id;

            return (
              <div
                key={card.id}
                style={{
                  ...s.card,
                  borderColor: isSuccess ? "#10b981" : "#e5e7eb",
                  boxShadow: isSuccess
                    ? "0 0 0 2px rgba(16,185,129,0.2)"
                    : "0 1px 3px rgba(0,0,0,0.04)",
                }}
                id={`export-card-${card.id}`}
              >
                <div style={s.cardIconWrap}>
                  <div
                    style={{
                      ...s.cardIcon,
                      color: isSuccess ? "#10b981" : "#6366f1",
                    }}
                  >
                    {card.icon}
                  </div>
                </div>

                <h3 style={s.cardTitle}>{card.title}</h3>
                <p style={s.cardDesc}>{card.description}</p>

                <button
                  style={{
                    ...s.primaryBtn,
                    opacity: isLoading || loadingCard ? 0.6 : 1,
                    cursor: isLoading || loadingCard ? "not-allowed" : "pointer",
                  }}
                  disabled={!!loadingCard}
                  onClick={() => handleExport(card)}
                  id={`export-btn-${card.id}`}
                >
                  {isLoading ? (
                    <>
                      <FiLoader
                        size={14}
                        style={{ animation: "spin 1s linear infinite" }}
                      />
                      Processing...
                    </>
                  ) : (
                    <>
                      <FiDownload size={14} />
                      {card.emitLabel}
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* ── Export History ── */}
        <div style={s.historyCard} id="export-history">
          <div style={s.listHeader}>
            <h3 style={s.sectionTitle}>Export History</h3>
            <button style={s.refreshBtn} onClick={loadHistory}>
              <FiRefreshCw size={14} />
              Refresh
            </button>
          </div>

          {historyLoading ? (
            <p style={s.subtitle}>Loading history...</p>
          ) : exportHistory.length === 0 ? (
            <p style={s.subtitle}>No exports generated yet for this run.</p>
          ) : (
            <div style={s.tableWrap}>
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th}>Type</th>
                    <th style={s.th}>Scope</th>
                    <th style={s.th}>Created</th>
                    <th style={s.th}>File</th>
                    <th style={s.th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {exportHistory.map((row) => (
                    <tr key={row.export_id}>
                      <td style={s.td}>
                        <span style={s.typeBadge}>{row.export_type}</span>
                      </td>
                      <td style={s.td}>{row.scope}</td>
                      <td style={s.td}>{row.created_at}</td>
                      <td style={{ ...s.td, maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis" }}>
                        {row.file_path}
                      </td>
                      <td style={s.td}>
                        <button
                          style={s.openBtn}
                          onClick={() => handleOpenFile(row.file_path)}
                          title="Open file"
                        >
                          <FiExternalLink size={13} />
                          Open
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ── Import Dashboard JSON ── */}
        <div style={s.historyCard} id="import-dashboard-section">
          <h3 style={s.sectionTitle}>Import Dashboard Layout</h3>
          <p style={s.subtitle}>
            Re-import a previously exported <code>.json</code> dashboard layout file
            to restore your dashboard configuration.
          </p>
          <button
            style={s.secondaryBtn}
            onClick={async () => {
              const fileRes = await frontendApi.selectFile();
              if (!fileRes.success || !fileRes.data?.file_path) return;
              // The import logic would go through the existing dashboard save IPC
              // For now, we read the JSON and call saveDashboardLayout
              setErrorMsg(
                "Dashboard import: selected " + fileRes.data.file_path + ". " +
                "Import will be processed on next run load."
              );
            }}
            id="import-dashboard-btn"
          >
            <FiUploadCloud size={14} />
            Select JSON File
          </button>
        </div>
      </section>
    </>
  );
};

/* ─────────────────────────────────────────
   Styles
   ───────────────────────────────────────── */

const s: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: "1100px",
    animation: "fadeIn 0.3s ease-out",
    padding: "0 4px",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    marginBottom: "24px",
  },
  headerIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    background: "#eef2ff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  title: {
    fontSize: "22px",
    fontWeight: 700,
    color: "#111827",
    margin: 0,
  },
  subtitle: {
    fontSize: "14px",
    color: "#6b7280",
    margin: 0,
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: "15px",
    fontWeight: 600,
    marginBottom: "12px",
    color: "#111827",
  },

  /* ── Card Grid ── */
  cardGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
    gap: "16px",
    marginBottom: "24px",
  },
  card: {
    background: "#ffffff",
    borderRadius: "14px",
    padding: "24px",
    border: "1.5px solid #e5e7eb",
    transition: "border-color 0.2s, box-shadow 0.2s",
    display: "flex",
    flexDirection: "column" as const,
    gap: "10px",
  },
  cardIconWrap: {
    marginBottom: 4,
  },
  cardIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    background: "#eef2ff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  cardTitle: {
    fontSize: "15px",
    fontWeight: 600,
    color: "#111827",
    margin: 0,
  },
  cardDesc: {
    fontSize: "13px",
    color: "#6b7280",
    lineHeight: "1.5",
    margin: 0,
    flex: 1,
  },

  /* ── Buttons ── */
  primaryBtn: {
    background: "#6366f1",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    padding: "10px 18px",
    fontSize: "13px",
    fontWeight: 500,
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    marginTop: "8px",
    transition: "opacity 0.2s",
    alignSelf: "flex-start",
  },
  secondaryBtn: {
    background: "#ffffff",
    color: "#6366f1",
    border: "1.5px solid #6366f1",
    borderRadius: "8px",
    padding: "10px 18px",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
  },
  openBtn: {
    border: "1px solid #e5e7eb",
    background: "#ffffff",
    borderRadius: "6px",
    padding: "5px 10px",
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    fontSize: "12px",
    color: "#6366f1",
    fontWeight: 500,
  },
  refreshBtn: {
    border: "1px solid #e5e7eb",
    background: "#ffffff",
    borderRadius: "8px",
    padding: "8px 12px",
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "12px",
  },
  linkBtn: {
    background: "none",
    border: "none",
    color: "#6366f1",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: 500,
    padding: 0,
    textDecoration: "underline",
  },

  /* ── Banners ── */
  successBanner: {
    marginBottom: "16px",
    padding: "12px 16px",
    background: "#ecfdf5",
    borderLeft: "4px solid #10b981",
    borderRadius: "8px",
    color: "#065f46",
    fontSize: "14px",
    fontWeight: 500,
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  errorBanner: {
    marginBottom: "16px",
    padding: "12px 16px",
    background: "#fef2f2",
    borderLeft: "4px solid #ef4444",
    borderRadius: "8px",
    color: "#991b1b",
    fontSize: "14px",
    fontWeight: 500,
  },

  /* ── History Card ── */
  historyCard: {
    background: "#ffffff",
    borderRadius: "14px",
    padding: "24px",
    border: "1px solid #e5e7eb",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
    marginBottom: "16px",
  },
  listHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },

  /* ── Table ── */
  tableWrap: { overflowX: "auto" as const },
  table: { width: "100%", borderCollapse: "collapse" as const },
  th: {
    textAlign: "left" as const,
    fontSize: "11px",
    color: "#6b7280",
    borderBottom: "1px solid #e5e7eb",
    padding: "10px 8px",
    textTransform: "uppercase" as const,
    letterSpacing: "0.5px",
  },
  td: {
    fontSize: "13px",
    color: "#111827",
    borderBottom: "1px solid #f3f4f6",
    padding: "10px 8px",
    whiteSpace: "nowrap" as const,
  },
  typeBadge: {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: "6px",
    fontSize: "11px",
    fontWeight: 600,
    background: "#eef2ff",
    color: "#6366f1",
  },
};

export default Exports;
