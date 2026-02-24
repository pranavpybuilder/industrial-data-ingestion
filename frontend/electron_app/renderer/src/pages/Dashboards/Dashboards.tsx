import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FiDownload,
  FiEye,
  FiMove,
  FiRefreshCw,
  FiSave,
  FiSliders,
  FiTarget,
  FiX,
} from "react-icons/fi";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

import { useRunUI } from "../../state/useRunUI";
import { frontendApi } from "../../services/frontendApi";

type DashboardWidget = {
  id: string;
  type?: string;
  title?: string;
  subtitle?: string;
  value?: number | string;
  severity?: string;
  description?: string;
  metrics?: Record<string, any>;
  data?: any;
};

type DashboardSection = {
  id: string;
  title: string;
  type: string;
  widgets: DashboardWidget[];
};

type DashboardState = {
  blueprint_id?: string;
  run_id?: string;
  sections?: DashboardSection[];
  metadata?: Record<string, any>;
};

type UserLayout = {
  layout_version: number;
  widget_order: string[];
  widget_visuals: Record<string, string>;
  hidden_widgets: string[];
  slicers: {
    machine: string;
    failureType: string;
    timeRange: "all" | "7d" | "30d" | "90d";
  };
};

const DEFAULT_LAYOUT: UserLayout = {
  layout_version: 1,
  widget_order: [],
  widget_visuals: {},
  hidden_widgets: [],
  slicers: {
    machine: "all",
    failureType: "all",
    timeRange: "all",
  },
};

const Dashboards = () => {
  const navigate = useNavigate();
  const run = useRunUI();

  const [dashboard, setDashboard] = useState<DashboardState | null>(null);
  const [layout, setLayout] = useState<UserLayout>(DEFAULT_LAYOUT);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [draggingWidgetId, setDraggingWidgetId] = useState<string | null>(null);
  const [drillWidgetId, setDrillWidgetId] = useState<string | null>(null);

  const loadDashboard = async () => {
    if (!run.activeRunId) return;
    setLoading(true);
    setError(null);
    setMessage(null);

    const response = await frontendApi.getDashboard(run.activeRunId);
    setLoading(false);

    if (!response.success) {
      setError(response.message || "Failed to load dashboard");
      setDashboard(null);
      setLayout(DEFAULT_LAYOUT);
      return;
    }

    const nextState = response.data?.dashboard_state || null;
    setDashboard(nextState);
    if (response.message) {
      setMessage(response.message);
    }

    const widgets = extractWidgets(nextState);
    const savedLayout = response.data?.user_layout?.user_saved_layout;
    const normalized = normalizeLayout(savedLayout, widgets.map((w) => w.id));
    setLayout(normalized);
  };

  useEffect(() => {
    loadDashboard();
  }, [run.activeRunId]);

  const allWidgets = useMemo(() => extractWidgets(dashboard), [dashboard]);

  const widgetsById = useMemo(() => {
    const out: Record<string, DashboardWidget> = {};
    for (const widget of allWidgets) {
      out[widget.id] = widget;
    }
    return out;
  }, [allWidgets]);

  const orderedWidgetIds = useMemo(() => {
    const seen = new Set(layout.widget_order);
    const missing = allWidgets.map((w) => w.id).filter((id) => !seen.has(id));
    return [...layout.widget_order, ...missing].filter((id) => widgetsById[id]);
  }, [layout.widget_order, allWidgets, widgetsById]);

  const visibleWidgetIds = useMemo(
    () => orderedWidgetIds.filter((id) => !layout.hidden_widgets.includes(id)),
    [orderedWidgetIds, layout.hidden_widgets]
  );

  const rowsForSlicers = useMemo(() => {
    const rows: Record<string, any>[] = [];
    for (const widget of allWidgets) {
      if (Array.isArray(widget.data)) {
        for (const entry of widget.data) {
          if (entry && typeof entry === "object") {
            rows.push(entry as Record<string, any>);
          }
        }
      }
    }
    return rows;
  }, [allWidgets]);

  const machineOptions = useMemo(
    () => uniqueValues(rowsForSlicers, ["equipment_id", "resource", "machine_name"]),
    [rowsForSlicers]
  );

  const failureTypeOptions = useMemo(
    () => uniqueValues(rowsForSlicers, ["failure_type", "event_type", "title"]),
    [rowsForSlicers]
  );

  const saveLayout = async () => {
    if (!run.activeRunId || !dashboard) return;

    const payload: UserLayout = {
      ...layout,
      widget_order: orderedWidgetIds,
    };
    const response = await frontendApi.saveDashboardLayout(
      run.activeRunId,
      dashboard.blueprint_id || "",
      payload
    );
    if (!response.success) {
      setError(response.message || "Failed to save dashboard layout");
      return;
    }
    setMessage(response.message || "Dashboard layout saved");
  };

  const updateSlicer = (
    key: keyof UserLayout["slicers"],
    value: string
  ) => {
    setLayout((prev) => ({
      ...prev,
      slicers: { ...prev.slicers, [key]: value },
    }));
  };

  const resetSlicers = () => {
    setLayout((prev) => ({
      ...prev,
      slicers: { ...DEFAULT_LAYOUT.slicers },
    }));
  };

  const toggleHidden = (widgetId: string) => {
    setLayout((prev) => {
      const hidden = prev.hidden_widgets.includes(widgetId)
        ? prev.hidden_widgets.filter((id) => id !== widgetId)
        : [...prev.hidden_widgets, widgetId];
      return { ...prev, hidden_widgets: hidden };
    });
  };

  const setVisual = (widgetId: string, visualType: string) => {
    setLayout((prev) => ({
      ...prev,
      widget_visuals: {
        ...prev.widget_visuals,
        [widgetId]: visualType,
      },
    }));
  };

  const reorderWidgets = (fromId: string, toId: string) => {
    setLayout((prev) => {
      const order = [...orderedWidgetIds];
      const fromIndex = order.indexOf(fromId);
      const toIndex = order.indexOf(toId);
      if (fromIndex < 0 || toIndex < 0 || fromIndex === toIndex) {
        return prev;
      }
      const [moved] = order.splice(fromIndex, 1);
      order.splice(toIndex, 0, moved);
      return { ...prev, widget_order: order };
    });
  };

  if (!run.activeRunId) {
    return (
      <section>
        <h1>Dashboards</h1>
        <p>No active run selected.</p>
      </section>
    );
  }

  return (
    <section style={styles.page}>
      <div style={styles.headerRow}>
        <div>
          <h1 style={styles.title}>{run.activeRunId}</h1>
          <span style={styles.subtitle}>Blueprint + saved user layout</span>
        </div>

        <div style={styles.actionsRow}>
          <button style={styles.btn} onClick={loadDashboard}>
            <FiRefreshCw size={14} /> Refresh
          </button>
          <button
            style={styles.btn}
            onClick={() => setEditMode((prev) => !prev)}
          >
            <FiMove size={14} /> {editMode ? "Exit Edit" : "Edit Layout"}
          </button>
          <button style={styles.btn} onClick={saveLayout}>
            <FiSave size={14} /> Save Dashboard
          </button>
          <button style={styles.btn} onClick={() => navigate("/insights")}>
            <FiEye size={14} /> Show Insights
          </button>
          <button style={styles.btn} onClick={() => navigate("/exports")}>
            <FiDownload size={14} /> Export
          </button>
        </div>
      </div>

      {loading && <div style={styles.infoCard}>Loading dashboard...</div>}
      {error && <div style={{ ...styles.infoCard, ...styles.errorCard }}>{error}</div>}
      {!error && message && <div style={styles.infoCard}>{message}</div>}

      {!loading && !error && !dashboard && (
        <div style={styles.infoCard}>
          No dashboard blueprint found for this run.
        </div>
      )}

      {!loading && !error && dashboard && (
        <>
          <div style={styles.filterPanel}>
            <div style={styles.filterTitle}>
              <FiSliders size={15} /> Filter Panel / Slicers
            </div>
            <div style={styles.filterGrid}>
              <label style={styles.filterLabel}>
                Machine
                <select
                  title="Machine slicer"
                  value={layout.slicers.machine}
                  onChange={(event) => updateSlicer("machine", event.target.value)}
                  style={styles.select}
                >
                  <option value="all">All Machines</option>
                  {machineOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>

              <label style={styles.filterLabel}>
                Failure Type
                <select
                  title="Failure type slicer"
                  value={layout.slicers.failureType}
                  onChange={(event) => updateSlicer("failureType", event.target.value)}
                  style={styles.select}
                >
                  <option value="all">All Failure Types</option>
                  {failureTypeOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>

              <label style={styles.filterLabel}>
                Time Range
                <select
                  title="Time range slicer"
                  value={layout.slicers.timeRange}
                  onChange={(event) =>
                    updateSlicer(
                      "timeRange",
                      event.target.value as UserLayout["slicers"]["timeRange"]
                    )
                  }
                  style={styles.select}
                >
                  <option value="all">All Time</option>
                  <option value="7d">Last 7 Days</option>
                  <option value="30d">Last 30 Days</option>
                  <option value="90d">Last 90 Days</option>
                </select>
              </label>
            </div>
            <button style={styles.smallBtn} onClick={resetSlicers}>
              Reset Filters
            </button>
          </div>

          <div style={styles.widgetGrid}>
            {visibleWidgetIds.map((widgetId) => {
              const widget = widgetsById[widgetId];
              const visualType = layout.widget_visuals[widgetId] || defaultVisual(widget);
              const filteredData = applySlicers(
                widget?.data,
                layout.slicers
              );
              return (
                <article
                  key={widgetId}
                  style={styles.widgetCard}
                  draggable={editMode}
                  onDragStart={(event) => {
                    if (!editMode) return;
                    setDraggingWidgetId(widgetId);
                    event.dataTransfer.effectAllowed = "move";
                  }}
                  onDragOver={(event) => {
                    if (!editMode) return;
                    event.preventDefault();
                  }}
                  onDrop={(event) => {
                    if (!editMode || !draggingWidgetId) return;
                    event.preventDefault();
                    reorderWidgets(draggingWidgetId, widgetId);
                    setDraggingWidgetId(null);
                  }}
                >
                  <div style={styles.widgetHeader}>
                    <div>
                      <h3 style={styles.widgetTitle}>
                        {widget?.title || widget?.subtitle || widget?.id || "Widget"}
                      </h3>
                      {widget?.severity && (
                        <span style={severityBadge(widget.severity)}>{widget.severity}</span>
                      )}
                    </div>
                    <div style={styles.widgetActions}>
                      <select
                        title="Chart type switcher"
                        value={visualType}
                        onChange={(event) => setVisual(widgetId, event.target.value)}
                        style={styles.select}
                      >
                        {allowedVisuals(widget).map((option) => (
                          <option key={option} value={option}>
                            {option.toUpperCase()}
                          </option>
                        ))}
                      </select>
                      <button
                        style={styles.smallBtn}
                        onClick={() => setDrillWidgetId(widgetId)}
                      >
                        <FiTarget size={13} /> Drill
                      </button>
                      {editMode && (
                        <>
                          <button style={styles.smallBtn}>
                            <FiMove size={13} />
                          </button>
                          <button
                            style={styles.smallBtn}
                            onClick={() => toggleHidden(widgetId)}
                          >
                            <FiX size={13} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {renderWidgetContent(widget, visualType, filteredData)}
                </article>
              );
            })}
          </div>

          {layout.hidden_widgets.length > 0 && (
            <div style={styles.infoCard}>
              Hidden widgets: {layout.hidden_widgets.join(", ")}
            </div>
          )}

          {drillWidgetId && (
            <div style={styles.drillPanel}>
              <div style={styles.drillHeader}>
                <h3 style={styles.widgetTitle}>
                  Drill-Down: {widgetsById[drillWidgetId]?.title || drillWidgetId}
                </h3>
                <button style={styles.smallBtn} onClick={() => setDrillWidgetId(null)}>
                  Close
                </button>
              </div>
              <pre style={styles.pre}>
                {JSON.stringify(widgetsById[drillWidgetId], null, 2)}
              </pre>
            </div>
          )}
        </>
      )}
    </section>
  );
};

function extractWidgets(state: DashboardState | null): DashboardWidget[] {
  if (!state?.sections || !Array.isArray(state.sections)) {
    return [];
  }

  const widgets: DashboardWidget[] = [];
  for (const section of state.sections) {
    const items = Array.isArray(section.widgets) ? section.widgets : [];
    for (const widget of items) {
      widgets.push({
        ...widget,
        id: String(widget.id || `widget_${widgets.length + 1}`),
      });
    }
  }
  return widgets;
}

function normalizeLayout(rawLayout: any, widgetIds: string[]): UserLayout {
  const base = { ...DEFAULT_LAYOUT };
  if (!rawLayout || typeof rawLayout !== "object") {
    return {
      ...base,
      widget_order: [...widgetIds],
    };
  }

  const order = Array.isArray(rawLayout.widget_order)
    ? rawLayout.widget_order.map(String).filter((id: string) => widgetIds.includes(id))
    : [];

  const hidden = Array.isArray(rawLayout.hidden_widgets)
    ? rawLayout.hidden_widgets.map(String).filter((id: string) => widgetIds.includes(id))
    : [];

  return {
    layout_version: Number(rawLayout.layout_version || 1),
    widget_order: [...order, ...widgetIds.filter((id) => !order.includes(id))],
    widget_visuals: typeof rawLayout.widget_visuals === "object" && rawLayout.widget_visuals
      ? rawLayout.widget_visuals
      : {},
    hidden_widgets: hidden,
    slicers: {
      machine: String(rawLayout.slicers?.machine || "all"),
      failureType: String(rawLayout.slicers?.failureType || "all"),
      timeRange: (rawLayout.slicers?.timeRange as UserLayout["slicers"]["timeRange"]) || "all",
    },
  };
}

function uniqueValues(rows: Record<string, any>[], keys: string[]): string[] {
  const values = new Set<string>();
  for (const row of rows) {
    for (const key of keys) {
      const value = row[key];
      if (value === undefined || value === null) continue;
      const normalized = String(value).trim();
      if (normalized) values.add(normalized);
    }
  }
  return Array.from(values).sort((a, b) => a.localeCompare(b));
}

function applySlicers(data: any, slicers: UserLayout["slicers"]): any {
  if (!Array.isArray(data)) return data;

  return data.filter((row) => {
    if (!row || typeof row !== "object") return false;
    const machineValue = String(row.equipment_id || row.resource || row.machine_name || "all");
    const failureValue = String(row.failure_type || row.event_type || row.title || "all");

    if (slicers.machine !== "all" && machineValue !== slicers.machine) {
      return false;
    }
    if (slicers.failureType !== "all" && failureValue !== slicers.failureType) {
      return false;
    }

    if (slicers.timeRange === "all") {
      return true;
    }

    const timestampCandidate = row.event_time || row.created_at || row.timestamp || row.date;
    if (!timestampCandidate) {
      return true;
    }
    const timestamp = new Date(timestampCandidate).getTime();
    if (Number.isNaN(timestamp)) {
      return true;
    }

    const now = Date.now();
    const lookbackDays = slicers.timeRange === "7d" ? 7 : slicers.timeRange === "30d" ? 30 : 90;
    return timestamp >= now - lookbackDays * 24 * 60 * 60 * 1000;
  });
}

function defaultVisual(widget: DashboardWidget): string {
  if (widget.type === "table") return "table";
  if (widget.type === "metric" || widget.type === "card") return "metric";
  if (Array.isArray(widget.data)) return "table";
  return "metric";
}

function allowedVisuals(widget: DashboardWidget): string[] {
  if (Array.isArray(widget.data)) {
    return ["table", "line", "bar", "metric"];
  }
  return ["metric", "table"];
}

function renderWidgetContent(
  widget: DashboardWidget,
  visualType: string,
  filteredData: any
) {
  if (visualType === "table") {
    if (!Array.isArray(filteredData) || filteredData.length === 0) {
      return <p style={styles.mutedText}>No tabular data available for this widget.</p>;
    }
    const columns = Object.keys(filteredData[0]).slice(0, 6);
    return (
      <div style={styles.tableWrap}>
        <table style={styles.table}>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column} style={styles.th}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredData.slice(0, 8).map((row, idx) => (
              <tr key={idx}>
                {columns.map((column) => (
                  <td key={column} style={styles.td}>{String(row[column] ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (visualType === "line" || visualType === "bar") {
    const series = buildChartSeries(widget, filteredData);
    if (!series.length) {
      return <p style={styles.mutedText}>No numeric series available for charting.</p>;
    }
    return (
      <div style={{ width: "100%", height: 220 }}>
        <ResponsiveContainer>
          {visualType === "line" ? (
            <LineChart data={series}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="x" tick={{ fontSize: 12, fill: "#64748b" }} />
              <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
              <Tooltip />
              <Line type="monotone" dataKey="y" stroke="#6366f1" strokeWidth={2} dot={false} />
            </LineChart>
          ) : (
            <BarChart data={series}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="x" tick={{ fontSize: 12, fill: "#64748b" }} />
              <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
              <Tooltip />
              <Bar dataKey="y" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div>
      {widget.value !== undefined && (
        <div style={styles.metricValue}>{String(widget.value)}</div>
      )}
      {widget.description && <p style={styles.mutedText}>{widget.description}</p>}
      {widget.metrics && (
        <div style={styles.metricGrid}>
          {Object.entries(widget.metrics).map(([key, value]) => (
            <div key={key} style={styles.metricChip}>
              <span>{key}</span>
              <strong>{String(value)}</strong>
            </div>
          ))}
        </div>
      )}
      {!widget.metrics && widget.value === undefined && (
        <pre style={styles.pre}>{JSON.stringify(filteredData ?? widget.data ?? {}, null, 2)}</pre>
      )}
    </div>
  );
}

function buildChartSeries(widget: DashboardWidget, filteredData: any): Array<{ x: string; y: number }> {
  if (Array.isArray(filteredData) && filteredData.length > 0) {
    if (
      filteredData[0] &&
      Object.prototype.hasOwnProperty.call(filteredData[0], "x") &&
      Object.prototype.hasOwnProperty.call(filteredData[0], "y")
    ) {
      return filteredData
        .map((row) => ({
          x: String(row.x),
          y: Number(row.y),
        }))
        .filter((row) => Number.isFinite(row.y));
    }

    const keys = Object.keys(filteredData[0]);
    const numericKey = keys.find((key) => Number.isFinite(Number(filteredData[0][key])));
    const categoryKey = keys.find((key) => key !== numericKey) || keys[0];
    if (numericKey) {
      return filteredData
        .slice(0, 50)
        .map((row, idx) => ({
          x: String(row[categoryKey] ?? `row_${idx + 1}`),
          y: Number(row[numericKey]),
        }))
        .filter((row) => Number.isFinite(row.y));
    }
  }

  if (Number.isFinite(Number(widget.value))) {
    return [{ x: widget.title || widget.id, y: Number(widget.value) }];
  }

  return [];
}

function severityBadge(severity: string): React.CSSProperties {
  const normalized = String(severity).toUpperCase();
  if (normalized === "CRITICAL") {
    return styles.criticalBadge;
  }
  if (normalized === "WARNING") {
    return styles.warningBadge;
  }
  return styles.infoBadge;
}

const styles: Record<string, React.CSSProperties> = {
  page: {},
  headerRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
    gap: "12px",
    flexWrap: "wrap",
  },
  title: {
    fontSize: "22px",
    fontWeight: 700,
    color: "#111827",
    margin: 0,
    marginBottom: 4,
  },
  subtitle: { color: "#6b7280", fontSize: 13 },
  actionsRow: { display: "flex", gap: 8, flexWrap: "wrap" },
  btn: {
    background: "#f3f4f6",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    padding: "8px 14px",
    fontSize: 13,
    fontWeight: 500,
    color: "#111827",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  smallBtn: {
    background: "#ffffff",
    border: "1px solid #d1d5db",
    borderRadius: "8px",
    padding: "6px 10px",
    fontSize: "12px",
    color: "#374151",
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
  },
  infoCard: {
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: "12px",
    padding: "16px",
    color: "#374151",
    marginBottom: "14px",
  },
  errorCard: {
    borderLeft: "4px solid #ef4444",
    color: "#991b1b",
  },
  filterPanel: {
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: "12px",
    padding: "14px",
    marginBottom: "14px",
  },
  filterTitle: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    color: "#111827",
    fontWeight: 600,
    marginBottom: "10px",
  },
  filterGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
    gap: "10px",
    marginBottom: "8px",
  },
  filterLabel: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    fontSize: "12px",
    color: "#4b5563",
    fontWeight: 600,
  },
  select: {
    border: "1px solid #d1d5db",
    borderRadius: "8px",
    padding: "6px 8px",
    fontSize: "12px",
    color: "#111827",
    background: "#fff",
  },
  widgetGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
    gap: "12px",
  },
  widgetCard: {
    border: "1px solid #e5e7eb",
    borderRadius: "10px",
    padding: "12px",
    background: "#ffffff",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },
  widgetHeader: {
    display: "flex",
    justifyContent: "space-between",
    gap: "8px",
    marginBottom: "10px",
    alignItems: "flex-start",
  },
  widgetTitle: {
    margin: 0,
    fontSize: "14px",
    color: "#111827",
  },
  widgetActions: {
    display: "flex",
    gap: "6px",
    alignItems: "center",
    flexWrap: "wrap",
    justifyContent: "flex-end",
  },
  metricValue: {
    fontSize: "26px",
    fontWeight: 700,
    color: "#111827",
    marginBottom: "8px",
  },
  mutedText: {
    margin: 0,
    color: "#6b7280",
    fontSize: "13px",
    lineHeight: 1.5,
  },
  metricGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
    gap: "8px",
  },
  metricChip: {
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    padding: "8px",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    fontSize: "12px",
    color: "#4b5563",
    background: "#fafafa",
  },
  tableWrap: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse" },
  th: {
    textAlign: "left",
    fontSize: "11px",
    color: "#6b7280",
    borderBottom: "1px solid #e5e7eb",
    padding: "8px",
    textTransform: "uppercase",
    letterSpacing: "0.4px",
  },
  td: { fontSize: "12px", color: "#111827", borderBottom: "1px solid #f3f4f6", padding: "8px" },
  pre: {
    margin: 0,
    fontSize: "11px",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    background: "#f8fafc",
    borderRadius: "8px",
    border: "1px solid #e5e7eb",
    padding: "8px",
    maxHeight: "220px",
    overflow: "auto",
  },
  drillPanel: {
    marginTop: "14px",
    background: "#ffffff",
    borderRadius: "12px",
    border: "1px solid #dbeafe",
    padding: "14px",
  },
  drillHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "8px",
  },
  criticalBadge: {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: "999px",
    fontSize: "11px",
    fontWeight: 700,
    color: "#991b1b",
    background: "#fee2e2",
    border: "1px solid #fecaca",
  },
  warningBadge: {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: "999px",
    fontSize: "11px",
    fontWeight: 700,
    color: "#92400e",
    background: "#fef3c7",
    border: "1px solid #fde68a",
  },
  infoBadge: {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: "999px",
    fontSize: "11px",
    fontWeight: 700,
    color: "#1d4ed8",
    background: "#dbeafe",
    border: "1px solid #bfdbfe",
  },
};

export default Dashboards;
