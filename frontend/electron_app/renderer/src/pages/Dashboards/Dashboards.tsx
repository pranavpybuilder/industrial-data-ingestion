/**
 * Dashboards.tsx — Power BI-style dashboard page
 * ------------------------------------------------
 * Features:
 *  - Left sidebar filter panel (collapsible)
 *  - Section-grouped widget grid (12-col)
 *  - KPI / Chart / Table widget cards
 *  - Drag-and-drop reorder with ghost feedback
 *  - Drill-down side panel (not raw JSON)
 *  - Skeleton loader
 *  - Undo-friendly layout with Save
 *  - lastSaved timestamp shown in header via dashboardsUI.getLastSaved()
 */

import { useEffect, useMemo, useState, useRef, useCallback } from "react";
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
  FiChevronLeft,
  FiChevronRight,
  FiBarChart2,
  FiTrendingUp,
  FiTrendingDown,
  FiMinus,
  FiGrid,
} from "react-icons/fi";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";

import { useRunUI } from "../../state/useRunUI";
import { frontendApi } from "../../services/frontendApi";
// ── CHANGE 1: import dashboardsUI store + useDashboardsUI hook ──────────────
import { dashboardsUI } from "../../state/dashboards_ui_store";
import { useDashboardsUI } from "../../state/useDashboardsUI";

// ─── Types ──────────────────────────────────────────────────────────────────

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
  unit?: string;
  trend?: "up" | "down" | "flat";
  trendValue?: string;
  color?: string;
  icon?: string;
  chart_config?: Record<string, any>;
  columns?: Array<{ key: string; label: string; width?: number }>;
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

type VisualType = "line" | "area" | "bar" | "pie" | "table" | "metric";

type UserLayout = {
  layout_version: number;
  widget_order: string[];
  widget_visuals: Record<string, VisualType>;
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
  slicers: { machine: "all", failureType: "all", timeRange: "all" },
};

const CHART_COLORS = [
  "#6366f1", "#8b5cf6", "#ec4899", "#14b8a6",
  "#f59e0b", "#3b82f6", "#10b981", "#ef4444",
];

const TOOLTIP_STYLE: React.CSSProperties = {
  borderRadius: 10,
  border: "1px solid #e5e7eb",
  boxShadow: "0 8px 24px rgba(0,0,0,0.10)",
  fontSize: 12,
  background: "#fff",
};

const AXIS_STYLE = { fontSize: 11, fill: "#9ca3af" };

// ─── Main Component ──────────────────────────────────────────────────────────

const Dashboards = () => {
  const navigate = useNavigate();
  const run = useRunUI();

  // ── CHANGE 2: subscribe to store so lastSaved re-renders when markSaved() fires
  const uiState = useDashboardsUI();

  const [dashboard, setDashboard] = useState<DashboardState | null>(null);
  const [layout, setLayout] = useState<UserLayout>(DEFAULT_LAYOUT);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);
  const [drillWidgetId, setDrillWidgetId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // ── Load ──────────────────────────────────────────────────────────────────

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

    const nextState: DashboardState = response.data?.dashboard_state || null;
    setDashboard(nextState);
    if (response.message) setMessage(response.message);

    const widgets = extractWidgets(nextState);
    const savedLayout = response.data?.user_layout?.user_saved_layout;
    setLayout(normalizeLayout(savedLayout, widgets.map((w) => w.id)));
  };

  useEffect(() => { loadDashboard(); }, [run.activeRunId]);

  // ── Derived state ─────────────────────────────────────────────────────────

  const allWidgets = useMemo(() => extractWidgets(dashboard), [dashboard]);
  const widgetsById = useMemo(() => {
    const out: Record<string, DashboardWidget> = {};
    for (const w of allWidgets) out[w.id] = w;
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
    for (const w of allWidgets) {
      if (Array.isArray(w.data)) {
        for (const entry of w.data) {
          if (entry && typeof entry === "object") rows.push(entry);
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

  // Group visible widgets into sections
  const sectionGroups = useMemo(() => {
    if (!dashboard?.sections?.length) {
      return [{ id: "__all__", title: "", widgets: visibleWidgetIds }];
    }
    const groups: { id: string; title: string; widgets: string[] }[] = [];
    for (const sec of dashboard.sections) {
      const ids = visibleWidgetIds.filter((id) => {
        const found = allWidgets.find((w) => w.id === id);
        // Try to match section by iterating original sections
        const origSec = dashboard.sections?.find((s) => s.id === sec.id);
        return origSec?.widgets?.some((sw) => String(sw.id) === id);
      });
      if (ids.length) groups.push({ id: sec.id, title: sec.title, widgets: ids });
    }
    // Orphan widgets not matched to any section
    const assignedIds = new Set(groups.flatMap((g) => g.widgets));
    const orphans = visibleWidgetIds.filter((id) => !assignedIds.has(id));
    if (orphans.length) groups.push({ id: "__orphans__", title: "Other", widgets: orphans });
    return groups.length ? groups : [{ id: "__all__", title: "", widgets: visibleWidgetIds }];
  }, [dashboard, visibleWidgetIds, allWidgets]);

  // ── lastSaved: formatted relative timestamp from store ────────────────────

  const lastSavedDisplay = useMemo(() => {
    const ts = uiState.lastSaved;
    if (!ts) return null;
    return formatTimestamp(ts);
  }, [uiState.lastSaved]);

  // ── Actions ───────────────────────────────────────────────────────────────

  const saveLayout = async () => {
    if (!run.activeRunId || !dashboard) return;
    const payload = { ...layout, widget_order: orderedWidgetIds };
    const response = await frontendApi.saveDashboardLayout(
      run.activeRunId,
      dashboard.blueprint_id || "",
      payload
    );
    if (!response.success) {
      setError(response.message || "Failed to save");
      return;
    }
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2500);
    // ── CHANGE 3: mark saved in store → updates lastSaved → re-renders timestamp
    dashboardsUI.markSaved();
  };

  const updateSlicer = (key: keyof UserLayout["slicers"], value: string) => {
    setLayout((prev) => ({ ...prev, slicers: { ...prev.slicers, [key]: value } }));
  };
  const resetSlicers = () => setLayout((prev) => ({ ...prev, slicers: { ...DEFAULT_LAYOUT.slicers } }));

  const toggleHidden = (id: string) => {
    setLayout((prev) => {
      const hidden = prev.hidden_widgets.includes(id)
        ? prev.hidden_widgets.filter((h) => h !== id)
        : [...prev.hidden_widgets, id];
      return { ...prev, hidden_widgets: hidden };
    });
  };

  const setVisual = (id: string, vt: VisualType) => {
    setLayout((prev) => ({ ...prev, widget_visuals: { ...prev.widget_visuals, [id]: vt } }));
  };

  const reorderWidgets = (fromId: string, toId: string) => {
    setLayout((prev) => {
      const order = [...orderedWidgetIds];
      const fromIdx = order.indexOf(fromId);
      const toIdx = order.indexOf(toId);
      if (fromIdx < 0 || toIdx < 0 || fromIdx === toIdx) return prev;
      const [moved] = order.splice(fromIdx, 1);
      order.splice(toIdx, 0, moved);
      return { ...prev, widget_order: order };
    });
  };

  // ── Empty / loading states ────────────────────────────────────────────────

  if (!run.activeRunId) {
    return (
      <section style={s.page}>
        <div style={s.emptyState}>
          <FiGrid size={48} color="#d1d5db" />
          <h2 style={{ margin: "16px 0 8px", color: "#374151" }}>No Active Run</h2>
          <p style={{ color: "#9ca3af", margin: 0 }}>Select a run from the sidebar to view its dashboard.</p>
        </div>
      </section>
    );
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <section style={s.page}>
      {/* ── Top bar ── */}
      <header style={s.topBar}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button style={s.iconBtn} onClick={() => setSidebarOpen((v) => !v)} title="Toggle filters">
            {sidebarOpen ? <FiChevronLeft size={16} /> : <FiSliders size={16} />}
          </button>
          <div>
            <h1 style={s.pageTitle}>{run.activeRunId}</h1>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 2 }}>
              {dashboard?.metadata?.title && (
                <span style={s.pageSubtitle}>{dashboard.metadata.title}</span>
              )}
              {/* ── lastSaved timestamp — only visible after first save ── */}
              {lastSavedDisplay && (
                <span style={s.savedTimestamp}>
                  Saved {lastSavedDisplay}
                </span>
              )}
            </div>
          </div>
        </div>

        <div style={s.actionsRow}>
          <button style={s.btn} onClick={loadDashboard}><FiRefreshCw size={13} /> Refresh</button>
          <button
            style={{ ...s.btn, ...(editMode ? s.btnActive : {}) }}
            onClick={() => setEditMode((v) => !v)}
          >
            <FiMove size={13} /> {editMode ? "Exit Edit" : "Edit Layout"}
          </button>
          <button
            style={{ ...s.btn, ...(saveSuccess ? s.btnSuccess : {}) }}
            onClick={saveLayout}
          >
            <FiSave size={13} /> {saveSuccess ? "Saved!" : "Save"}
          </button>
          <button style={s.btn} onClick={() => navigate("/insights")}><FiEye size={13} /> Insights</button>
          <button style={s.btn} onClick={() => navigate("/exports")}><FiDownload size={13} /> Exports</button>
          <ExportDashboardButton runId={run.activeRunId} />
        </div>
      </header>

      {/* ── Status banners ── */}
      {error && <div style={{ ...s.banner, ...s.bannerError }}>{error}</div>}
      {!error && message && <div style={s.banner}>{message}</div>}

      {/* ── Body (sidebar + canvas) ── */}
      <div style={s.body}>
        {/* Sidebar */}
        {sidebarOpen && (
          <aside style={s.sidebar}>
            <div style={s.sidebarTitle}><FiSliders size={14} /> Filters</div>

            <label style={s.filterLabel}>
              Machine
              <select style={s.select} value={layout.slicers.machine}
                onChange={(e) => updateSlicer("machine", e.target.value)}>
                <option value="all">All Machines</option>
                {machineOptions.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </label>

            <label style={s.filterLabel}>
              Failure Type
              <select style={s.select} value={layout.slicers.failureType}
                onChange={(e) => updateSlicer("failureType", e.target.value)}>
                <option value="all">All Types</option>
                {failureTypeOptions.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </label>

            <label style={s.filterLabel}>
              Time Range
              <select style={s.select} value={layout.slicers.timeRange}
                onChange={(e) => updateSlicer("timeRange", e.target.value as UserLayout["slicers"]["timeRange"])}>
                <option value="all">All Time</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
              </select>
            </label>

            <button style={s.resetBtn} onClick={resetSlicers}>Reset Filters</button>

            {layout.hidden_widgets.length > 0 && (
              <div style={s.hiddenList}>
                <div style={s.hiddenListTitle}>Hidden</div>
                {layout.hidden_widgets.map((id) => (
                  <div key={id} style={s.hiddenChip}>
                    <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}>
                      {widgetsById[id]?.title || id}
                    </span>
                    <button style={s.chipBtn} onClick={() => toggleHidden(id)}>
                      <FiEye size={11} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </aside>
        )}

        {/* Canvas */}
        <main id="dashboard-canvas" data-dashboard-root style={s.canvas}>
          {loading && <SkeletonGrid />}

          {!loading && !error && !dashboard && (
            <div style={s.emptyState}>
              <FiBarChart2 size={48} color="#d1d5db" />
              <h3 style={{ margin: "16px 0 8px", color: "#374151" }}>No Dashboard Found</h3>
              <p style={{ color: "#9ca3af", margin: 0 }}>No blueprint exists for this run yet.</p>
            </div>
          )}

          {!loading && !error && dashboard && sectionGroups.map((group) => (
            <div key={group.id} style={{ marginBottom: 28 }}>
              {group.title && (
                <div style={s.sectionHeader}>
                  <span>{group.title}</span>
                  <div style={s.sectionDivider} />
                </div>
              )}
              <div style={s.widgetGrid}>
                {group.widgets.map((widgetId) => {
                  const widget = widgetsById[widgetId];
                  if (!widget) return null;
                  const visualType = layout.widget_visuals[widgetId] ?? autoVisualType(widget);
                  const filteredData = applySlicers(widget.data, layout.slicers);
                  const isDraggingOver = dragOverId === widgetId && draggingId !== widgetId;

                  return (
                    <div
                      key={widgetId}
                      style={{
                        ...widgetCardStyle(widget),
                        ...(isDraggingOver ? s.cardDragOver : {}),
                        ...(draggingId === widgetId ? s.cardDragging : {}),
                        gridColumn: `span ${widgetGridSpan(widget)}`,
                      }}
                      draggable={editMode}
                      onDragStart={(e) => {
                        setDraggingId(widgetId);
                        e.dataTransfer.effectAllowed = "move";
                      }}
                      onDragOver={(e) => { e.preventDefault(); setDragOverId(widgetId); }}
                      onDragLeave={() => setDragOverId(null)}
                      onDrop={(e) => {
                        e.preventDefault();
                        if (draggingId) reorderWidgets(draggingId, widgetId);
                        setDraggingId(null);
                        setDragOverId(null);
                      }}
                      onDragEnd={() => { setDraggingId(null); setDragOverId(null); }}
                    >
                      {/* Card header */}
                      <div style={s.cardHeader}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 0 }}>
                          {editMode && <FiMove size={13} color="#9ca3af" style={{ flexShrink: 0 }} />}
                          <span style={s.cardTitle}>
                            {widget.title || widget.subtitle || widgetId}
                          </span>
                          {widget.severity && (
                            <span style={severityBadge(widget.severity)}>{widget.severity}</span>
                          )}
                        </div>
                        <div style={s.cardActions}>
                          {canSwitchVisual(widget) && (
                            <select
                              style={s.vizSelect}
                              value={visualType}
                              onChange={(e) => setVisual(widgetId, e.target.value as VisualType)}
                            >
                              {allowedVisuals(widget).map((vt) => (
                                <option key={vt} value={vt}>{vt.toUpperCase()}</option>
                              ))}
                            </select>
                          )}
                          <button style={s.iconBtn} title="Drill down" onClick={() => setDrillWidgetId(widgetId)}>
                            <FiTarget size={13} />
                          </button>
                          {editMode && (
                            <button style={s.iconBtn} title="Hide widget" onClick={() => toggleHidden(widgetId)}>
                              <FiX size={13} />
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Card body */}
                      <div style={s.cardBody}>
                        <WidgetContent
                          widget={widget}
                          visualType={visualType}
                          filteredData={filteredData}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </main>
      </div>

      {/* ── Drill-down panel ── */}
      {drillWidgetId && (
        <DrillPanel
          widget={widgetsById[drillWidgetId]}
          onClose={() => setDrillWidgetId(null)}
        />
      )}
    </section>
  );
};

// ─── Widget Content ───────────────────────────────────────────────────────────

interface WidgetContentProps {
  widget: DashboardWidget;
  visualType: VisualType;
  filteredData: any;
}

const WidgetContent = ({ widget, visualType, filteredData }: WidgetContentProps) => {
  // KPI card: large number with colored accent
  if (widget.type === "kpi") {
    return <KpiCard widget={widget} />;
  }

  if (visualType === "metric") {
    return <MetricCard widget={widget} />;
  }

  // donut_chart: Pie chart with inner radius for donut look
  if (widget.type === "donut_chart" && Array.isArray(widget.data) && widget.data.length > 0) {
    const donutColors = widget.chart_config?.colors || CHART_COLORS;
    const chartData = widget.data.map((d: any) => ({
      name: String(d.label || d.name || ""),
      value: Number(d.value || 0),
    }));
    return (
      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%" cy="50%"
              innerRadius="55%"
              outerRadius="80%"
              strokeWidth={2}
              stroke="#fff"
              label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {chartData.map((_: any, i: number) => (
                <Cell key={i} fill={donutColors[i % donutColors.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 11, color: "#6b7280" }} iconType="circle" iconSize={8} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // bar_chart: horizontal bar chart from data array
  if (widget.type === "bar_chart" && Array.isArray(widget.data) && widget.data.length > 0) {
    const chartData = widget.data.map((d: any) => ({
      label: String(d.label || d.x || ""),
      value: Number(d.value || d.y || 0),
    }));
    return (
      <div style={{ width: "100%", height: Math.max(280, chartData.length * 34) }}>
        <ResponsiveContainer>
          <BarChart data={chartData} layout="vertical" barCategoryGap="16%">
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={false} />
            <XAxis type="number" tick={AXIS_STYLE} axisLine={false} tickLine={false} />
            <YAxis
              dataKey="label" type="category" width={140} tick={AXIS_STYLE}
              axisLine={false} tickLine={false}
            />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "rgba(99,102,241,0.06)" }} />
            <Bar dataKey="value" radius={[0, 5, 5, 0]}>
              {chartData.map((_: any, i: number) => (
                <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (visualType === "table") {
    const rows = Array.isArray(filteredData) ? filteredData : [];
    if (!rows.length) return <EmptyViz />;
    // Use explicit columns from widget if available, otherwise auto-detect
    const explicitCols = widget.columns;
    const cols = explicitCols
      ? explicitCols.map((c: any) => c.key)
      : Object.keys(rows[0]).slice(0, 7);
    const labels: Record<string, string> = {};
    if (explicitCols) {
      for (const c of explicitCols) labels[c.key] = c.label || c.key;
    }
    return (
      <div style={{ overflowX: "auto", maxHeight: 420, overflowY: "auto" }}>
        <table style={s.table}>
          <thead>
            <tr>
              {cols.map((c: string) => (
                <th key={c} style={s.th}>{labels[c] || c.replace(/_/g, " ")}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 50).map((row: any, i: number) => (
              <tr key={i} style={i % 2 === 1 ? { background: "#f9fafb" } : {}}>
                {cols.map((c: string) => (
                  <td key={c} style={s.td}>{formatCell(row[c])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length > 50 && (
          <p style={{ textAlign: "center", color: "#9ca3af", fontSize: 11, margin: "8px 0 0" }}>
            Showing 50 of {rows.length} rows
          </p>
        )}
      </div>
    );
  }

  // Chart types
  const series = buildSeries(widget, filteredData);
  if (!series.length) return <EmptyViz />;

  return (
    <div style={{ width: "100%", height: 260 }}>
      <ResponsiveContainer>
        {renderChart(visualType, series)}
      </ResponsiveContainer>
    </div>
  );
};

function renderChart(type: VisualType, data: Array<{ x: string; y: number }>) {
  switch (type) {
    case "area":
      return (
        <AreaChart data={data}>
          <defs>
            <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS[0]} stopOpacity={0.25} />
              <stop offset="100%" stopColor={CHART_COLORS[0]} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="x" tick={AXIS_STYLE} axisLine={{ stroke: "#e5e7eb" }} tickLine={false} />
          <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Area type="monotone" dataKey="y" stroke={CHART_COLORS[0]} strokeWidth={2} fill="url(#ag)" />
        </AreaChart>
      );
    case "bar":
      return (
        <BarChart data={data} barCategoryGap="20%">
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
          <XAxis dataKey="x" tick={AXIS_STYLE} axisLine={{ stroke: "#e5e7eb" }} tickLine={false} />
          <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "rgba(99,102,241,0.06)" }} />
          <Bar dataKey="y" radius={[5, 5, 0, 0]}>
            {data.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
          </Bar>
        </BarChart>
      );
    case "pie":
      return (
        <PieChart>
          <Pie data={data} dataKey="y" nameKey="x" cx="50%" cy="50%" outerRadius="80%" strokeWidth={2} stroke="#fff">
            {data.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
          </Pie>
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Legend wrapperStyle={{ fontSize: 11, color: "#6b7280" }} iconType="circle" iconSize={8} />
        </PieChart>
      );
    default: // line
      return (
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="x" tick={AXIS_STYLE} axisLine={{ stroke: "#e5e7eb" }} tickLine={false} />
          <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Line
            type="monotone" dataKey="y" stroke={CHART_COLORS[0]} strokeWidth={2.5}
            dot={{ r: 3, fill: CHART_COLORS[0], strokeWidth: 0 }}
            activeDot={{ r: 6, fill: CHART_COLORS[0], stroke: "#fff", strokeWidth: 2 }}
          />
        </LineChart>
      );
  }
}

// ─── Metric Card ──────────────────────────────────────────────────────────────

const MetricCard = ({ widget }: { widget: DashboardWidget }) => {
  const TrendIcon =
    widget.trend === "up" ? FiTrendingUp :
      widget.trend === "down" ? FiTrendingDown :
        FiMinus;

  const trendColor =
    widget.trend === "up" ? "#10b981" :
      widget.trend === "down" ? "#ef4444" :
        "#9ca3af";

  return (
    <div style={s.metricInner}>
      <div style={s.metricValue}>
        {widget.value !== undefined ? String(widget.value) : "—"}
        {widget.unit && <span style={s.metricUnit}>{widget.unit}</span>}
      </div>
      {widget.trendValue && (
        <div style={{ display: "flex", alignItems: "center", gap: 4, color: trendColor, fontSize: 13 }}>
          <TrendIcon size={14} /> {widget.trendValue}
        </div>
      )}
      {widget.description && <p style={s.metricDesc}>{widget.description}</p>}
      {widget.metrics && (
        <div style={s.metricGrid}>
          {Object.entries(widget.metrics).map(([k, v]) => (
            <div key={k} style={s.metricChip}>
              <span style={{ color: "#9ca3af", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.5px" }}>{k}</span>
              <strong style={{ fontSize: 14, color: "#111827" }}>{String(v)}</strong>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── KPI Card (new — rendered by kpi_row sections) ─────────────────────────────

const KpiCard = ({ widget }: { widget: DashboardWidget }) => {
  const accentColor = widget.color || "#6366f1";
  const valueStr = widget.value !== undefined ? String(widget.value) : "—";
  const displayValue =
    typeof widget.value === "number" && widget.value >= 1000
      ? widget.value.toLocaleString()
      : valueStr;

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      justifyContent: "space-between",
      height: "100%",
      position: "relative",
      overflow: "hidden",
      padding: "18px 16px 14px",
      background: `linear-gradient(135deg, ${accentColor}08 0%, ${accentColor}03 100%)`,
      borderTop: `3px solid ${accentColor}`,
      borderRadius: "0 0 12px 12px",
    }}>
      <div style={{
        fontSize: 10,
        fontWeight: 700,
        textTransform: "uppercase" as const,
        letterSpacing: "0.8px",
        color: "#9ca3af",
        marginBottom: 8,
      }}>
        {widget.title || ""}
      </div>
      <div style={{
        fontSize: 28,
        fontWeight: 800,
        color: "#111827",
        lineHeight: 1.1,
        letterSpacing: "-0.03em",
      }}>
        {displayValue}
      </div>
      {widget.subtitle && (
        <div style={{
          fontSize: 11,
          color: accentColor,
          marginTop: 6,
          fontWeight: 600,
        }}>
          {widget.subtitle}
        </div>
      )}
    </div>
  );
};

// ─── Drill Panel ─────────────────────────────────────────────────────────────

const DrillPanel = ({
  widget,
  onClose,
}: {
  widget: DashboardWidget | undefined;
  onClose: () => void;
}) => {
  if (!widget) return null;
  const rows = Array.isArray(widget.data) ? widget.data : null;
  const cols = rows?.length ? Object.keys(rows[0]) : [];

  return (
    <div style={s.drillOverlay}>
      <div style={s.drillPanel}>
        <div style={s.drillHeader}>
          <div>
            <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: "#111827" }}>
              {widget.title || widget.id}
            </h2>
            {widget.subtitle && <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: 13 }}>{widget.subtitle}</p>}
          </div>
          <button style={s.closeBtn} onClick={onClose}><FiX size={18} /></button>
        </div>

        {/* KPI row */}
        {widget.value !== undefined && (
          <div style={s.drillKpi}>
            <div style={s.drillKpiValue}>{String(widget.value)}{widget.unit ? ` ${widget.unit}` : ""}</div>
            {widget.description && <p style={{ color: "#6b7280", fontSize: 13, margin: 0 }}>{widget.description}</p>}
          </div>
        )}

        {/* Metrics grid */}
        {widget.metrics && (
          <div style={s.drillMetricGrid}>
            {Object.entries(widget.metrics).map(([k, v]) => (
              <div key={k} style={s.drillMetricCard}>
                <span style={{ color: "#9ca3af", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.5px" }}>{k}</span>
                <strong style={{ fontSize: 20, color: "#111827", fontWeight: 700 }}>{String(v)}</strong>
              </div>
            ))}
          </div>
        )}

        {/* Data table */}
        {rows && rows.length > 0 && (
          <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: 380 }}>
            <table style={s.table}>
              <thead>
                <tr>{cols.map((c) => <th key={c} style={s.th}>{c.replace(/_/g, " ")}</th>)}</tr>
              </thead>
              <tbody>
                {rows.map((row: any, i: number) => (
                  <tr key={i} style={i % 2 === 1 ? { background: "#f9fafb" } : {}}>
                    {cols.map((c) => <td key={c} style={s.td}>{formatCell(row[c])}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!rows && !widget.value && !widget.metrics && (
          <p style={{ color: "#9ca3af", fontSize: 13 }}>No detailed data available for this widget.</p>
        )}
      </div>
    </div>
  );
};

// ─── Skeleton Loader ──────────────────────────────────────────────────────────

const SkeletonGrid = () => (
  <div style={s.widgetGrid}>
    {Array.from({ length: 6 }).map((_, i) => (
      <div key={i} style={{ ...s.card, gridColumn: `span ${i < 3 ? 4 : 6}`, padding: 20 }}>
        <div style={sk.title} />
        <div style={{ ...sk.bar, width: "60%", marginTop: 12 }} />
        <div style={{ ...sk.bar, width: "80%", marginTop: 8 }} />
        <div style={{ ...sk.bar, width: "50%", marginTop: 8 }} />
      </div>
    ))}
  </div>
);

const sk: Record<string, React.CSSProperties> = {
  title: {
    height: 14, borderRadius: 6, background: "linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%)",
    backgroundSize: "200% 100%", animation: "shimmer 1.4s infinite", width: "45%",
  },
  bar: {
    height: 10, borderRadius: 4, background: "linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%)",
    backgroundSize: "200% 100%", animation: "shimmer 1.4s infinite",
  },
};

const EmptyViz = () => (
  <div style={s.emptyViz}>No data available</div>
);

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractWidgets(state: DashboardState | null): DashboardWidget[] {
  if (!state?.sections || !Array.isArray(state.sections)) return [];
  const widgets: DashboardWidget[] = [];
  for (const section of state.sections) {
    for (const w of (section.widgets || [])) {
      widgets.push({ ...w, id: String((w as any).id || `widget_${widgets.length + 1}`) });
    }
  }
  return widgets;
}

function normalizeLayout(rawLayout: any, widgetIds: string[]): UserLayout {
  if (!rawLayout || typeof rawLayout !== "object") {
    return { ...DEFAULT_LAYOUT, widget_order: [...widgetIds] };
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
    widget_visuals: typeof rawLayout.widget_visuals === "object" ? rawLayout.widget_visuals : {},
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
      const v = row[key];
      if (v !== undefined && v !== null) {
        const n = String(v).trim();
        if (n) values.add(n);
      }
    }
  }
  return Array.from(values).sort((a, b) => a.localeCompare(b));
}

function applySlicers(data: any, slicers: UserLayout["slicers"]): any {
  if (!Array.isArray(data)) return data;
  return data.filter((row) => {
    if (!row || typeof row !== "object") return false;
    const machineVal = String(row.equipment_id || row.resource || row.machine_name || "all");
    const failureVal = String(row.failure_type || row.event_type || row.title || "all");
    if (slicers.machine !== "all" && machineVal !== slicers.machine) return false;
    if (slicers.failureType !== "all" && failureVal !== slicers.failureType) return false;
    if (slicers.timeRange === "all") return true;
    const ts = row.event_time || row.created_at || row.timestamp || row.date;
    if (!ts) return true;
    const t = new Date(ts).getTime();
    if (isNaN(t)) return true;
    const days = slicers.timeRange === "7d" ? 7 : slicers.timeRange === "30d" ? 30 : 90;
    return t >= Date.now() - days * 86400000;
  });
}

function autoVisualType(widget: DashboardWidget): VisualType {
  if (widget.type === "kpi") return "metric";
  if (widget.type === "bar_chart") return "bar";
  if (widget.type === "donut_chart") return "pie";
  if (widget.type === "table") return "table";
  if (widget.type === "metric" || widget.type === "card") return "metric";
  if (Array.isArray(widget.data) && widget.data.length > 0) return "line";
  return "metric";
}

function allowedVisuals(widget: DashboardWidget): VisualType[] {
  if (widget.type === "kpi" || widget.type === "bar_chart" || widget.type === "donut_chart") return ["metric"];
  if (Array.isArray(widget.data) && widget.data.length > 0) {
    return ["line", "area", "bar", "pie", "table", "metric"];
  }
  return ["metric"];
}

function canSwitchVisual(widget: DashboardWidget): boolean {
  if (widget.type === "kpi" || widget.type === "bar_chart" || widget.type === "donut_chart") return false;
  return Array.isArray(widget.data) && widget.data.length > 0;
}

function widgetGridSpan(widget: DashboardWidget): number {
  if (widget.type === "table") return 12;
  if (widget.type === "bar_chart") return 8;   // Takes 8 cols, donut takes 4 → side by side
  if (widget.type === "donut_chart") return 4;  // Companion to bar chart
  if (widget.type === "kpi") return 2;
  if (widget.type === "metric" || widget.type === "card") return 3;
  if (Array.isArray(widget.data)) return 6;
  return 3;
}

function buildSeries(widget: DashboardWidget, filteredData: any): Array<{ x: string; y: number }> {
  if (Array.isArray(filteredData) && filteredData.length > 0) {
    const first = filteredData[0];
    if (Object.prototype.hasOwnProperty.call(first, "x") && Object.prototype.hasOwnProperty.call(first, "y")) {
      return filteredData.map((r: any) => ({ x: String(r.x), y: Number(r.y) })).filter((r: any) => isFinite(r.y));
    }
    const keys = Object.keys(first);
    const numKey = keys.find((k) => isFinite(Number(first[k])));
    const catKey = keys.find((k) => k !== numKey) || keys[0];
    if (numKey) {
      return filteredData.slice(0, 60).map((r: any, i: number) => ({
        x: String(r[catKey] ?? `row_${i + 1}`),
        y: Number(r[numKey]),
      })).filter((r: any) => isFinite(r.y));
    }
  }
  if (isFinite(Number(widget.value))) {
    return [{ x: widget.title || widget.id, y: Number(widget.value) }];
  }
  return [];
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return String(value);
}

// Formats an ISO timestamp as a relative label: "just now", "3m ago", "2h ago", "Jan 5"
function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    const diffMs = Date.now() - d.getTime();
    const diffMins = Math.floor(diffMs / 60_000);
    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHrs = Math.floor(diffMins / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

function widgetCardStyle(widget: DashboardWidget): React.CSSProperties {
  const base = { ...s.card };
  if (widget.type === "metric" || widget.type === "card") {
    return { ...base, ...s.cardMetric };
  }
  return base;
}

function severityBadge(severity: string): React.CSSProperties {
  const n = String(severity).toUpperCase();
  if (n === "CRITICAL") return s.badgeCritical;
  if (n === "WARNING") return s.badgeWarning;
  return s.badgeInfo;
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const s: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", height: "100%", minHeight: 0 },
  topBar: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "14px 20px", borderBottom: "1px solid #e5e7eb", background: "#fff",
    flexShrink: 0, gap: 12, flexWrap: "wrap",
  },
  pageTitle: { margin: 0, fontSize: 18, fontWeight: 700, color: "#111827", lineHeight: 1.2 },
  pageSubtitle: { fontSize: 12, color: "#9ca3af" },
  // "Saved 3m ago" green pill — only shown after first successful save
  savedTimestamp: {
    fontSize: 11,
    fontWeight: 600,
    color: "#065f46",
    background: "#d1fae5",
    border: "1px solid #6ee7b7",
    borderRadius: 6,
    padding: "2px 7px",
    display: "inline-block",
  },
  actionsRow: { display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" },
  btn: {
    display: "inline-flex", alignItems: "center", gap: 5,
    background: "#f9fafb", border: "1px solid #e5e7eb",
    borderRadius: 8, padding: "7px 12px", fontSize: 12, fontWeight: 500,
    color: "#374151", cursor: "pointer",
  },
  btnActive: { background: "#eef2ff", borderColor: "#a5b4fc", color: "#4f46e5" },
  btnSuccess: { background: "#d1fae5", borderColor: "#6ee7b7", color: "#065f46" },
  iconBtn: {
    display: "inline-flex", alignItems: "center", justifyContent: "center",
    background: "transparent", border: "1px solid #e5e7eb",
    borderRadius: 6, padding: "5px 7px", cursor: "pointer", color: "#6b7280",
  },
  banner: {
    margin: "12px 20px 0", padding: "10px 14px", borderRadius: 8,
    background: "#fff", border: "1px solid #e5e7eb", fontSize: 13, color: "#374151",
    flexShrink: 0,
  },
  bannerError: { borderLeft: "4px solid #ef4444", color: "#991b1b", background: "#fef2f2" },
  body: { display: "flex", flex: 1, minHeight: 0, overflow: "hidden" },

  // Sidebar
  sidebar: {
    width: 220, flexShrink: 0, borderRight: "1px solid #e5e7eb",
    background: "#fafafa", padding: "16px 14px",
    overflowY: "auto", display: "flex", flexDirection: "column", gap: 14,
  },
  sidebarTitle: {
    display: "flex", alignItems: "center", gap: 6,
    fontSize: 12, fontWeight: 700, color: "#374151",
    textTransform: "uppercase", letterSpacing: "0.5px",
  },
  filterLabel: {
    display: "flex", flexDirection: "column", gap: 5,
    fontSize: 11, fontWeight: 600, color: "#4b5563",
  },
  select: {
    border: "1px solid #d1d5db", borderRadius: 7,
    padding: "6px 8px", fontSize: 12, color: "#111827", background: "#fff",
  },
  resetBtn: {
    background: "#fff", border: "1px solid #d1d5db", borderRadius: 7,
    padding: "7px 10px", fontSize: 11, color: "#6b7280", cursor: "pointer",
  },
  hiddenList: { borderTop: "1px solid #e5e7eb", paddingTop: 12 },
  hiddenListTitle: { fontSize: 11, fontWeight: 700, color: "#9ca3af", marginBottom: 6, textTransform: "uppercase" },
  hiddenChip: {
    display: "flex", alignItems: "center", gap: 6,
    background: "#fff", border: "1px solid #e5e7eb",
    borderRadius: 6, padding: "4px 8px", fontSize: 11, color: "#374151", marginBottom: 4,
  },
  chipBtn: {
    background: "none", border: "none", cursor: "pointer",
    color: "#9ca3af", display: "flex", padding: 2,
  },

  // Canvas — MUST have explicit background color for html2canvas capture
  canvas: { flex: 1, overflowY: "auto", padding: "20px 24px", backgroundColor: "#f3f4f6" },
  sectionHeader: {
    display: "flex", alignItems: "center", gap: 12, marginBottom: 14,
  },
  sectionDivider: { flex: 1, height: 1, background: "#e5e7eb" },
  widgetGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(12, 1fr)",
    gap: 14,
    alignItems: "start",
  },

  // Card
  card: {
    background: "#fff", borderRadius: 12,
    border: "1px solid #e5e7eb",
    boxShadow: "0 1px 4px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.02)",
    overflow: "hidden", transition: "box-shadow 0.15s ease, transform 0.15s ease",
  },
  cardMetric: {
    background: "#ffffff",
    borderColor: "#e5e7eb",
  },
  cardDragOver: {
    boxShadow: "0 0 0 2px #6366f1",
    borderColor: "#6366f1",
  },
  cardDragging: { opacity: 0.5 },
  cardHeader: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "12px 16px 0", gap: 8,
  },
  cardTitle: { fontSize: 13, fontWeight: 700, color: "#374151", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  cardActions: { display: "flex", gap: 6, alignItems: "center", flexShrink: 0 },
  cardBody: { padding: "12px 16px 16px" },
  vizSelect: {
    border: "1px solid #e5e7eb", borderRadius: 6,
    padding: "4px 6px", fontSize: 11, color: "#374151",
    background: "#f9fafb", cursor: "pointer",
  },

  // Metric
  metricInner: { display: "flex", flexDirection: "column", gap: 6 },
  metricValue: { fontSize: 32, fontWeight: 800, color: "#111827", lineHeight: 1, letterSpacing: "-0.03em" },
  metricUnit: { fontSize: 16, fontWeight: 500, color: "#6b7280", marginLeft: 4 },
  metricDesc: { margin: 0, fontSize: 12, color: "#9ca3af", lineHeight: 1.5 },
  metricGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(90px,1fr))", gap: 8, marginTop: 4 },
  metricChip: {
    border: "1px solid #f3f4f6", borderRadius: 8, padding: "8px 10px",
    display: "flex", flexDirection: "column", gap: 2, background: "#fafafa",
  },

  // Table
  table: { width: "100%", borderCollapse: "collapse", fontSize: 12 },
  th: {
    textAlign: "left", padding: "9px 10px", fontSize: 10, fontWeight: 700,
    color: "#6b7280", borderBottom: "2px solid #e5e7eb", background: "#f9fafb",
    position: "sticky", top: 0, textTransform: "uppercase", letterSpacing: "0.4px",
  },
  td: { padding: "8px 10px", borderBottom: "1px solid #f3f4f6", color: "#374151" },

  // Empty state
  emptyState: {
    display: "flex", flexDirection: "column", alignItems: "center",
    justifyContent: "center", padding: "80px 20px", textAlign: "center",
  },
  emptyViz: {
    display: "flex", alignItems: "center", justifyContent: "center",
    height: 180, color: "#d1d5db", fontSize: 13,
  },

  // Drill panel
  drillOverlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)",
    zIndex: 1000, display: "flex", alignItems: "flex-end", justifyContent: "flex-end",
  },
  drillPanel: {
    width: 520, height: "100vh", background: "#fff", overflowY: "auto",
    padding: 28, display: "flex", flexDirection: "column", gap: 20,
    boxShadow: "-8px 0 32px rgba(0,0,0,0.12)",
  },
  drillHeader: {
    display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12,
  },
  closeBtn: {
    background: "#f3f4f6", border: "none", borderRadius: 8,
    padding: "6px 8px", cursor: "pointer", color: "#374151",
    display: "flex", alignItems: "center",
  },
  drillKpi: {
    background: "linear-gradient(135deg,#f5f3ff,#ede9fe)",
    borderRadius: 12, padding: "18px 20px",
  },
  drillKpiValue: { fontSize: 42, fontWeight: 800, color: "#4f46e5", lineHeight: 1, letterSpacing: "-0.03em" },
  drillMetricGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(120px,1fr))", gap: 10 },
  drillMetricCard: {
    border: "1px solid #e5e7eb", borderRadius: 10, padding: "12px 14px",
    display: "flex", flexDirection: "column", gap: 4, background: "#fafafa",
  },

  // Severity badges
  badgeCritical: {
    display: "inline-block", padding: "2px 8px", borderRadius: 999,
    fontSize: 10, fontWeight: 700, color: "#991b1b", background: "#fee2e2", border: "1px solid #fecaca",
  },
  badgeWarning: {
    display: "inline-block", padding: "2px 8px", borderRadius: 999,
    fontSize: 10, fontWeight: 700, color: "#92400e", background: "#fef3c7", border: "1px solid #fde68a",
  },
  badgeInfo: {
    display: "inline-block", padding: "2px 8px", borderRadius: 999,
    fontSize: 10, fontWeight: 700, color: "#1d4ed8", background: "#dbeafe", border: "1px solid #bfdbfe",
  },
};

// ─── Export Dashboard Button ──────────────────────────────────────────────────

const ExportDashboardButton = ({ runId }: { runId: string }) => {
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);

  const handleExportDashboard = useCallback(async () => {
    if (exporting || !runId) return;
    setExporting(true);
    setExportMsg(null);

    try {
      // Prompt user for save directory first
      const dirRes = await frontendApi.selectDirectory();
      if (!dirRes.success || !dirRes.data) {
        setExportMsg("Export cancelled.");
        setTimeout(() => setExportMsg(null), 2000);
        setExporting(false);
        return;
      }
      const outputDir = String(dirRes.data);

      // Wait for charts to fully render
      await new Promise((r) => setTimeout(r, 2000));

      const html2canvasModule = await import("html2canvas");
      const html2canvas = html2canvasModule.default || html2canvasModule;

      const target =
        document.getElementById("dashboard-canvas") ||
        document.querySelector("[data-dashboard-root]");

      if (!target) {
        setExportMsg("Dashboard not ready. Please wait and try again.");
        setExporting(false);
        return;
      }

      const canvas = await html2canvas(target as HTMLElement, {
        scale: 3,
        useCORS: true,
        backgroundColor: "#f3f4f6",
        logging: false,
        allowTaint: true,
      });

      const imageBase64 = canvas.toDataURL("image/png");
      const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, "");

      const res = await frontendApi.exportDashboardPdf(runId, base64Data, outputDir);

      if (res.success) {
        setExportMsg("Dashboard exported successfully!");
        setTimeout(() => setExportMsg(null), 4000);
      } else {
        setExportMsg(res.message || "Export failed");
      }
    } catch (err) {
      setExportMsg(`Export error: ${err}`);
    } finally {
      setExporting(false);
    }
  }, [exporting, runId]);

  return (
    <>
      <button
        style={{
          ...s.btn,
          background: exporting ? "#e0e7ff" : "#eef2ff",
          color: "#4f46e5",
          borderColor: "#c7d2fe",
          cursor: exporting ? "not-allowed" : "pointer",
          opacity: exporting ? 0.7 : 1,
        }}
        onClick={handleExportDashboard}
        disabled={exporting}
        title="Export current dashboard view as PDF"
      >
        <FiDownload size={13} />
        {exporting ? "Capturing..." : "Export PDF"}
      </button>
      {exportMsg && (
        <span
          style={{
            fontSize: 11,
            color: exportMsg.includes("success") ? "#059669" : "#dc2626",
            fontWeight: 500,
            padding: "4px 8px",
            borderRadius: 6,
            background: exportMsg.includes("success") ? "#ecfdf5" : "#fef2f2",
          }}
        >
          {exportMsg}
        </span>
      )}
    </>
  );
};

export default Dashboards;