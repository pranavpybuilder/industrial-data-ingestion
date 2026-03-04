/**
 * Dashboards.tsx â€” Redesigned Power BI-style dashboard
 * Inspired by Stitch mockup: KPI cards, area/bar/donut charts, alerts table
 */

import { useEffect, useMemo, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
    FiDownload, FiEye, FiMove, FiRefreshCw, FiSave, FiSliders,
    FiTarget, FiX, FiChevronLeft, FiBarChart2, FiTrendingUp,
    FiTrendingDown, FiMinus, FiGrid, FiAlertTriangle, FiAlertCircle,
    FiActivity, FiCheckCircle, FiSearch, FiMaximize2, FiMoreVertical,
} from "react-icons/fi";
import {
    ResponsiveContainer, LineChart, Line, BarChart, Bar, AreaChart, Area,
    PieChart, Pie, Cell, XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from "recharts";

import { useRunUI } from "../../state/useRunUI";
import { frontendApi } from "../../services/frontendApi";
import { dashboardsUI } from "../../state/dashboards_ui_store";
import { useDashboardsUI } from "../../state/useDashboardsUI";

// â”€â”€â”€ Types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

type DashboardWidget = {
    id: string; type?: string; title?: string; subtitle?: string;
    value?: number | string; severity?: string; description?: string;
    metrics?: Record<string, any>; data?: any; unit?: string;
    trend?: "up" | "down" | "flat"; trendValue?: string;
    color?: string; icon?: string;
    chart_config?: Record<string, any>;
    columns?: Array<{ key: string; label: string; width?: number }>;
};

type DashboardSection = {
    id: string; title: string; type: string; widgets: DashboardWidget[];
};

type DashboardState = {
    blueprint_id?: string; run_id?: string;
    sections?: DashboardSection[]; metadata?: Record<string, any>;
};

type VisualType = "line" | "area" | "bar" | "pie" | "table" | "metric";

type UserLayout = {
    layout_version: number; widget_order: string[];
    widget_visuals: Record<string, VisualType>;
    hidden_widgets: string[];
    slicers: { machine: string; failureType: string; timeRange: "all" | "7d" | "30d" | "90d" };
};

const DEFAULT_LAYOUT: UserLayout = {
    layout_version: 1, widget_order: [], widget_visuals: {},
    hidden_widgets: [],
    slicers: { machine: "all", failureType: "all", timeRange: "all" },
};

const COLORS = {
    primary: "#6366f1", primaryLight: "#818cf8", primaryBg: "#eef2ff",
    success: "#10b981", successBg: "#ecfdf5",
    warning: "#f59e0b", warningBg: "#fffbeb",
    danger: "#ef4444", dangerBg: "#fef2f2",
    info: "#3b82f6", infoBg: "#eff6ff",
    surface: "#ffffff", surfaceAlt: "#f8fafc",
    border: "#e2e8f0", borderLight: "#f1f5f9",
    text: "#0f172a", textSecondary: "#64748b", textMuted: "#94a3b8",
    canvasBg: "#f1f5f9",
};

const CHART_PALETTE = ["#6366f1", "#8b5cf6", "#ec4899", "#14b8a6", "#f59e0b", "#3b82f6", "#10b981", "#ef4444"];

const TOOLTIP_STYLE: React.CSSProperties = {
    borderRadius: 10, border: `1px solid ${COLORS.border}`,
    boxShadow: "0 8px 24px rgba(0,0,0,0.10)", fontSize: 12, background: "#fff",
};
const AXIS_STYLE = { fontSize: 11, fill: COLORS.textMuted };

// â”€â”€â”€ CSS Keyframes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const KEYFRAMES = `
@keyframes dashFadeIn { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }
@keyframes shimmer { 0% { background-position:200% 0; } 100% { background-position:-200% 0; } }
@keyframes pulseGlow { 0%,100% { box-shadow:0 0 0 0 rgba(99,102,241,0.15); } 50% { box-shadow:0 0 0 8px rgba(99,102,241,0); } }
`;
// â”€â”€â”€ Main Component â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const Dashboards = () => {
    const navigate = useNavigate();
    const run = useRunUI();
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
    const [alertSearch, setAlertSearch] = useState("");

    // â”€â”€ Load â”€â”€
    const loadDashboard = async () => {
        if (!run.activeRunId) return;
        setLoading(true); setError(null); setMessage(null);
        const response = await frontendApi.getDashboard(run.activeRunId);
        setLoading(false);
        if (!response.success) {
            setError(response.message || "Failed to load dashboard");
            setDashboard(null); setLayout(DEFAULT_LAYOUT); return;
        }
        const nextState: DashboardState = response.data?.dashboard_state || null;
        setDashboard(nextState);
        if (response.message) setMessage(response.message);
        const widgets = extractWidgets(nextState);
        const savedLayout = response.data?.user_layout?.user_saved_layout;
        setLayout(normalizeLayout(savedLayout, widgets.map((w) => w.id)));
    };

    useEffect(() => { loadDashboard(); }, [run.activeRunId]);

    // â”€â”€ Derived state â”€â”€
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

    // — KPI Summary – prefer metadata, fallback to exact KPI widget titles —
    const kpiSummary = useMemo(() => {
        let totalInsights = 0, critical = 0, warnings = 0, dataHealth = 0;

        // 1) Metadata from blueprint (most reliable)
        const meta = dashboard?.metadata;
        if (meta) {
            totalInsights = Number(meta.total_insights) || 0;
            critical = Number(meta.critical_count) || 0;
            warnings = Number(meta.warnings_count) || 0;
            dataHealth = Number(meta.data_health) || 0;
        }

        // 2) Fallback – parse KPI widgets with exact title matching
        if (!totalInsights && !critical && !warnings && !dataHealth) {
            for (const w of allWidgets) {
                if (w.type === "kpi") {
                    const title = (w.title || "").toLowerCase().trim();
                    const val = typeof w.value === "number" ? w.value : parseFloat(String(w.value)) || 0;
                    if (title === "insights found" || title === "total insights") totalInsights = val;
                    else if (title === "critical alerts") critical = val;
                    else if (title === "warning alerts") warnings = val;
                    else if (title === "data health") dataHealth = val;
                }
            }
        }

        if (!totalInsights) totalInsights = allWidgets.length;
        return { totalInsights, critical, warnings, dataHealth };
    }, [allWidgets, dashboard]);

    // Section groups
    const sectionGroups = useMemo(() => {
        if (!dashboard?.sections?.length) {
            return [{ id: "__all__", title: "", widgets: visibleWidgetIds }];
        }
        const groups: { id: string; title: string; widgets: string[] }[] = [];
        for (const sec of dashboard.sections) {
            const ids = visibleWidgetIds.filter((id) => {
                const origSec = dashboard.sections?.find((s) => s.id === sec.id);
                return origSec?.widgets?.some((sw) => String(sw.id) === id);
            });
            if (ids.length) groups.push({ id: sec.id, title: sec.title, widgets: ids });
        }
        const assignedIds = new Set(groups.flatMap((g) => g.widgets));
        const orphans = visibleWidgetIds.filter((id) => !assignedIds.has(id));
        if (orphans.length) groups.push({ id: "__orphans__", title: "Other", widgets: orphans });
        return groups.length ? groups : [{ id: "__all__", title: "", widgets: visibleWidgetIds }];
    }, [dashboard, visibleWidgetIds, allWidgets]);

    const lastSavedDisplay = useMemo(() => {
        const ts = uiState.lastSaved;
        if (!ts) return null;
        return formatTimestamp(ts);
    }, [uiState.lastSaved]);

    // â”€â”€ Actions â”€â”€
    const saveLayout = async () => {
        if (!run.activeRunId || !dashboard) return;
        const payload = { ...layout, widget_order: orderedWidgetIds };
        const response = await frontendApi.saveDashboardLayout(
            run.activeRunId, dashboard.blueprint_id || "", payload
        );
        if (!response.success) { setError(response.message || "Failed to save"); return; }
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 2500);
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

    // â”€â”€ Empty state â”€â”€
    if (!run.activeRunId) {
        return (
            <>
                <style>{KEYFRAMES}</style>
                <section style={S.page}>
                    <div style={S.emptyState}>
                        <div style={S.emptyIcon}><FiGrid size={48} color={COLORS.textMuted} /></div>
                        <h2 style={{ margin: "16px 0 8px", color: COLORS.text, fontWeight: 700 }}>No Active Run</h2>
                        <p style={{ color: COLORS.textSecondary, margin: 0, fontSize: 14 }}>
                            Select a run from the sidebar to view its dashboard.
                        </p>
                    </div>
                </section>
            </>
        );
    }
// â”€â”€ Render â”€â”€
return (
    <>
        <style>{KEYFRAMES}</style>
        <section style={S.page}>
            {/* â”€â”€ Header â”€â”€ */}
            <header style={S.header}>
                <div style={S.headerLeft}>
                    <button style={S.iconBtnGhost} onClick={() => navigate(-1)} title="Back">
                        <FiChevronLeft size={18} />
                    </button>
                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <h1 style={S.headerTitle}>{run.activeRunId}</h1>
                            <span style={S.badge}>OPERATIONAL OVERVIEW</span>
                        </div>
                        {lastSavedDisplay && (
                            <span style={S.savedPill}>âœ“ Saved {lastSavedDisplay}</span>
                        )}
                    </div>
                </div>
                <div style={S.headerActions}>
                    <button style={S.headerBtn} onClick={loadDashboard}>
                        <FiRefreshCw size={13} /> Refresh
                    </button>
                    <button style={{ ...S.headerBtn, ...(editMode ? S.headerBtnActive : {}) }} onClick={() => setEditMode((v) => !v)}>
                        <FiMove size={13} /> {editMode ? "Exit Edit" : "Edit Layout"}
                    </button>
                    <button style={{ ...S.headerBtn, ...(saveSuccess ? S.headerBtnSuccess : {}) }} onClick={saveLayout}>
                        <FiSave size={13} /> {saveSuccess ? "Saved!" : "Save"}
                    </button>
                    <ExportDashboardButton runId={run.activeRunId} />
                </div>
            </header>

            {/* â”€â”€ KPI Cards Row â”€â”€ */}
            <div style={S.kpiRow}>
                <KpiTopCard label="Total Insights" value={kpiSummary.totalInsights}
                    trend="+12% from last run" trendDir="up" accent={COLORS.primary}
                    icon={<FiBarChart2 size={18} />} />
                <KpiTopCard label="Critical Alerts" value={kpiSummary.critical}
                    trend="Action Required" trendDir="down" accent={COLORS.danger}
                    icon={<FiAlertTriangle size={18} />} />
                <KpiTopCard label="Warning Alerts" value={kpiSummary.warnings}
                    trend="Stable" trendDir="flat" accent={COLORS.warning}
                    icon={<FiAlertCircle size={18} />} />
                <KpiTopCard label="Data Health" value={`${kpiSummary.dataHealth}%`}
                    trend="Optimal Performance" trendDir="up" accent={COLORS.success}
                    icon={<FiCheckCircle size={18} />} />
            </div>

            {error && <div style={S.errorBanner}>{error}</div>}
            {!error && message && <div style={S.infoBanner}>{message}</div>}

            {/* â”€â”€ Body â”€â”€ */}
            <div style={S.body}>
                {/* Sidebar */}
                {sidebarOpen && (
                    <aside style={S.sidebar}>
                        <div style={S.sidebarHeader}>
                            <FiSliders size={14} /> <span>FILTERS</span>
                        </div>

                        <label style={S.filterLabel}>
                            TIME RANGE
                            <select style={S.select} value={layout.slicers.timeRange}
                                onChange={(e) => updateSlicer("timeRange", e.target.value as any)}>
                                <option value="all">All Time</option>
                                <option value="7d">Last 7 Days</option>
                                <option value="30d">Last 30 Days</option>
                                <option value="90d">Last 90 Days</option>
                            </select>
                        </label>

                        <label style={S.filterLabel}>
                            RESOURCE
                            <select style={S.select} value={layout.slicers.machine}
                                onChange={(e) => updateSlicer("machine", e.target.value)}>
                                <option value="all">All Resources</option>
                                {machineOptions.map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                        </label>

                        <label style={S.filterLabel}>
                            SEVERITY
                            <div style={S.checkboxGroup}>
                                {["Critical", "Warning", "Info"].map((sev) => (
                                    <label key={sev} style={S.checkboxLabel}>
                                        <input type="checkbox" defaultChecked style={S.checkbox} />
                                        <span>{sev}</span>
                                    </label>
                                ))}
                            </div>
                        </label>

                        <button style={S.resetBtn} onClick={resetSlicers}>Reset Filters</button>

                        {layout.hidden_widgets.length > 0 && (
                            <div style={S.hiddenSection}>
                                <div style={S.hiddenTitle}>HIDDEN WIDGETS</div>
                                {layout.hidden_widgets.map((id) => (
                                    <div key={id} style={S.hiddenChip}>
                                        <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}>
                                            {widgetsById[id]?.title || id}
                                        </span>
                                        <button style={S.chipBtn} onClick={() => toggleHidden(id)}>
                                            <FiEye size={11} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </aside>
                )}

                {/* Canvas */}
                <main id="dashboard-canvas" data-dashboard-root style={S.canvas}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                        <button style={S.iconBtnGhost} onClick={() => setSidebarOpen((v) => !v)} title="Toggle filters">
                            <FiSliders size={14} />
                        </button>
                        <span style={S.sectionLabel}>OPERATIONAL OVERVIEW</span>
                    </div>

                    {loading && <SkeletonGrid />}

                    {!loading && !error && !dashboard && (
                        <div style={S.emptyState}>
                            <FiBarChart2 size={48} color={COLORS.textMuted} />
                            <h3 style={{ margin: "16px 0 8px", color: COLORS.text }}>No Dashboard Found</h3>
                            <p style={{ color: COLORS.textSecondary, margin: 0 }}>No blueprint exists for this run yet.</p>
                        </div>
                    )}

                    {!loading && !error && dashboard && sectionGroups.map((group) => (
                        <div key={group.id} style={{ marginBottom: 24 }}>
                            {group.title && (
                                <div style={S.sectionHeaderRow}>
                                    <span style={S.sectionLabel}>{group.title.toUpperCase()}</span>
                                    <div style={S.sectionDivider} />
                                </div>
                            )}
                            <div style={S.widgetGrid}>
                                {group.widgets.map((widgetId) => {
                                    const widget = widgetsById[widgetId];
                                    if (!widget) return null;
                                    const visualType = layout.widget_visuals[widgetId] ?? autoVisualType(widget);
                                    const filteredData = applySlicers(widget.data, layout.slicers);
                                    const isDraggingOver = dragOverId === widgetId && draggingId !== widgetId;

                                    return (
                                        <div key={widgetId}
                                            style={{
                                                ...S.widgetCard,
                                                ...(isDraggingOver ? S.cardDragOver : {}),
                                                ...(draggingId === widgetId ? S.cardDragging : {}),
                                                gridColumn: `span ${widgetGridSpan(widget)}`,
                                            }}
                                            draggable={editMode}
                                            onDragStart={(e) => { setDraggingId(widgetId); e.dataTransfer.effectAllowed = "move"; }}
                                            onDragOver={(e) => { e.preventDefault(); setDragOverId(widgetId); }}
                                            onDragLeave={() => setDragOverId(null)}
                                            onDrop={(e) => { e.preventDefault(); if (draggingId) reorderWidgets(draggingId, widgetId); setDraggingId(null); setDragOverId(null); }}
                                            onDragEnd={() => { setDraggingId(null); setDragOverId(null); }}
                                        >
                                            <div style={S.cardHeader}>
                                                <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 0 }}>
                                                    {editMode && <FiMove size={13} color={COLORS.textMuted} />}
                                                    <span style={S.cardTitle}>{widget.title || widget.subtitle || widgetId}</span>
                                                    {widget.severity && <span style={severityBadge(widget.severity)}>{widget.severity}</span>}
                                                </div>
                                                <div style={S.cardActions}>
                                                    {canSwitchVisual(widget) && (
                                                        <select style={S.vizSelect} value={visualType}
                                                            onChange={(e) => setVisual(widgetId, e.target.value as VisualType)}>
                                                            {allowedVisuals(widget).map((vt) => (
                                                                <option key={vt} value={vt}>{vt.toUpperCase()}</option>
                                                            ))}
                                                        </select>
                                                    )}
                                                    <button style={S.iconBtnSmall} onClick={() => setDrillWidgetId(widgetId)} title="Expand">
                                                        <FiMaximize2 size={12} />
                                                    </button>
                                                    {editMode && (
                                                        <button style={S.iconBtnSmall} onClick={() => toggleHidden(widgetId)} title="Hide">
                                                            <FiX size={12} />
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                            <div style={S.cardBody}>
                                                <WidgetContent widget={widget} visualType={visualType} filteredData={filteredData} />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </main>
            </div>

            {drillWidgetId && (
                <DrillPanel widget={widgetsById[drillWidgetId]} onClose={() => setDrillWidgetId(null)} />
            )}
        </section>
    </>
);
};
// â”€â”€â”€ KPI Top Card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const KpiTopCard = ({ label, value, trend, trendDir, accent, icon }: {
    label: string; value: number | string; trend: string;
    trendDir: "up" | "down" | "flat"; accent: string;
    icon: React.ReactNode;
}) => {
    const TrendIcon = trendDir === "up" ? FiTrendingUp : trendDir === "down" ? FiTrendingDown : FiMinus;
    const trendColor = trendDir === "up" ? COLORS.success : trendDir === "down" ? COLORS.danger : COLORS.textMuted;
    return (
        <div style={{
            ...S.kpiCard,
            borderTop: `3px solid ${accent}`,
        }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <span style={S.kpiLabel}>{label.toUpperCase()}</span>
                <div style={{ ...S.kpiIconWrap, color: accent, background: `${accent}12` }}>{icon}</div>
            </div>
            <div style={S.kpiValue}>{typeof value === "number" ? value.toLocaleString() : value}</div>
            <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 4 }}>
                <TrendIcon size={12} color={trendColor} />
                <span style={{ fontSize: 11, color: trendColor, fontWeight: 500 }}>{trend}</span>
            </div>
        </div>
    );
};

// â”€â”€â”€ Widget Content â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

interface WidgetContentProps { widget: DashboardWidget; visualType: VisualType; filteredData: any; }

const WidgetContent = ({ widget, visualType, filteredData }: WidgetContentProps) => {
    if (widget.type === "kpi") return <KpiCard widget={widget} />;
    if (visualType === "metric") return <MetricCard widget={widget} />;

    if (widget.type === "donut_chart" && Array.isArray(widget.data) && widget.data.length > 0) {
        const colors = widget.chart_config?.colors || CHART_PALETTE;
        const chartData = widget.data.map((d: any) => ({ name: String(d.label || d.name || ""), value: Number(d.value || 0) }));
        const total = chartData.reduce((s: number, d: any) => s + d.value, 0);
        return (
            <div style={{ width: "100%", height: 280, position: "relative" }}>
                <ResponsiveContainer>
                    <PieChart>
                        <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                            innerRadius="58%" outerRadius="82%" strokeWidth={2} stroke="#fff"
                            label={({ name, percent }: any) => `${(percent * 100).toFixed(0)}%`} labelLine={false}>
                            {chartData.map((_: any, i: number) => <Cell key={i} fill={colors[i % colors.length]} />)}
                        </Pie>
                        <Tooltip contentStyle={TOOLTIP_STYLE} />
                        <Legend wrapperStyle={{ fontSize: 11, color: COLORS.textSecondary }} iconType="circle" iconSize={8} />
                    </PieChart>
                </ResponsiveContainer>
                <div style={S.donutCenter}>
                    <div style={{ fontSize: 24, fontWeight: 800, color: COLORS.text }}>{total}</div>
                    <div style={{ fontSize: 10, color: COLORS.textMuted }}>Total</div>
                </div>
            </div>
        );
    }

    if (widget.type === "bar_chart" && Array.isArray(widget.data) && widget.data.length > 0) {
        const chartData = widget.data.map((d: any) => ({ label: String(d.label || d.x || ""), value: Number(d.value || d.y || 0) }));
        return (
            <div style={{ width: "100%", height: Math.max(280, chartData.length * 34) }}>
                <ResponsiveContainer>
                    <BarChart data={chartData} layout="vertical" barCategoryGap="16%">
                        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.borderLight} horizontal={false} />
                        <XAxis type="number" tick={AXIS_STYLE} axisLine={false} tickLine={false} />
                        <YAxis dataKey="label" type="category" width={140} tick={AXIS_STYLE} axisLine={false} tickLine={false} />
                        <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "rgba(99,102,241,0.06)" }} />
                        <Bar dataKey="value" radius={[0, 5, 5, 0]}>
                            {chartData.map((_: any, i: number) => <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />)}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        );
    }

    if (visualType === "table") {
        const rows = Array.isArray(filteredData) ? filteredData : [];
        if (!rows.length) return <EmptyViz />;
        const explicitCols = widget.columns;
        const cols = explicitCols ? explicitCols.map((c: any) => c.key) : Object.keys(rows[0]).slice(0, 7);
        const labels: Record<string, string> = {};
        if (explicitCols) { for (const c of explicitCols) labels[c.key] = c.label || c.key; }
        return (
            <div style={{ overflowX: "auto", maxHeight: 420, overflowY: "auto" }}>
                <table style={S.table}>
                    <thead>
                        <tr>{cols.map((c: string) => <th key={c} style={S.th}>{labels[c] || c.replace(/_/g, " ")}</th>)}</tr>
                    </thead>
                    <tbody>
                        {rows.slice(0, 50).map((row: any, i: number) => (
                            <tr key={i} style={i % 2 === 1 ? { background: COLORS.surfaceAlt } : {}}>
                                {cols.map((c: string) => <td key={c} style={S.td}>{formatCell(row[c])}</td>)}
                            </tr>
                        ))}
                    </tbody>
                </table>
                {rows.length > 50 && (
                    <p style={{ textAlign: "center", color: COLORS.textMuted, fontSize: 11, margin: "8px 0 0" }}>
                        Showing 50 of {rows.length} rows
                    </p>
                )}
            </div>
        );
    }

    const series = buildSeries(widget, filteredData);
    if (!series.length) return <EmptyViz />;

    return (
        <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>{renderChart(visualType, series)}</ResponsiveContainer>
        </div>
    );
};
// â”€â”€â”€ Chart Renderer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function renderChart(type: VisualType, data: Array<{ x: string; y: number }>) {
    switch (type) {
        case "area":
            return (
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={CHART_PALETTE[0]} stopOpacity={0.25} />
                            <stop offset="100%" stopColor={CHART_PALETTE[0]} stopOpacity={0.02} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={COLORS.borderLight} />
                    <XAxis dataKey="x" tick={AXIS_STYLE} axisLine={{ stroke: COLORS.border }} tickLine={false} />
                    <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Area type="monotone" dataKey="y" stroke={CHART_PALETTE[0]} strokeWidth={2} fill="url(#areaGrad)" />
                </AreaChart>
            );
        case "bar":
            return (
                <BarChart data={data} barCategoryGap="20%">
                    <CartesianGrid strokeDasharray="3 3" stroke={COLORS.borderLight} vertical={false} />
                    <XAxis dataKey="x" tick={AXIS_STYLE} axisLine={{ stroke: COLORS.border }} tickLine={false} />
                    <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "rgba(99,102,241,0.06)" }} />
                    <Bar dataKey="y" radius={[5, 5, 0, 0]}>
                        {data.map((_, i) => <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />)}
                    </Bar>
                </BarChart>
            );
        case "pie":
            return (
                <PieChart>
                    <Pie data={data} dataKey="y" nameKey="x" cx="50%" cy="50%" outerRadius="80%" strokeWidth={2} stroke="#fff">
                        {data.map((_, i) => <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Legend wrapperStyle={{ fontSize: 11, color: COLORS.textSecondary }} iconType="circle" iconSize={8} />
                </PieChart>
            );
        default:
            return (
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke={COLORS.borderLight} />
                    <XAxis dataKey="x" tick={AXIS_STYLE} axisLine={{ stroke: COLORS.border }} tickLine={false} />
                    <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Line type="monotone" dataKey="y" stroke={CHART_PALETTE[0]} strokeWidth={2.5}
                        dot={{ r: 3, fill: CHART_PALETTE[0], strokeWidth: 0 }}
                        activeDot={{ r: 6, fill: CHART_PALETTE[0], stroke: "#fff", strokeWidth: 2 }} />
                </LineChart>
            );
    }
}

// â”€â”€â”€ Metric / KPI Cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const MetricCard = ({ widget }: { widget: DashboardWidget }) => {
    const TrendIcon = widget.trend === "up" ? FiTrendingUp : widget.trend === "down" ? FiTrendingDown : FiMinus;
    const trendColor = widget.trend === "up" ? COLORS.success : widget.trend === "down" ? COLORS.danger : COLORS.textMuted;
    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ fontSize: 32, fontWeight: 800, color: COLORS.text, lineHeight: 1, letterSpacing: "-0.03em" }}>
                {widget.value !== undefined ? String(widget.value) : "â€”"}
                {widget.unit && <span style={{ fontSize: 16, fontWeight: 500, color: COLORS.textSecondary, marginLeft: 4 }}>{widget.unit}</span>}
            </div>
            {widget.trendValue && (
                <div style={{ display: "flex", alignItems: "center", gap: 4, color: trendColor, fontSize: 13 }}>
                    <TrendIcon size={14} /> {widget.trendValue}
                </div>
            )}
            {widget.description && <p style={{ margin: 0, fontSize: 12, color: COLORS.textMuted, lineHeight: 1.5 }}>{widget.description}</p>}
            {widget.metrics && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(90px,1fr))", gap: 8, marginTop: 4 }}>
                    {Object.entries(widget.metrics).map(([k, v]) => (
                        <div key={k} style={{ border: `1px solid ${COLORS.borderLight}`, borderRadius: 8, padding: "8px 10px", display: "flex", flexDirection: "column", gap: 2, background: COLORS.surfaceAlt }}>
                            <span style={{ color: COLORS.textMuted, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.5px" }}>{k}</span>
                            <strong style={{ fontSize: 14, color: COLORS.text }}>{String(v)}</strong>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const KpiCard = ({ widget }: { widget: DashboardWidget }) => {
    const accent = widget.color || COLORS.primary;
    const val = widget.value !== undefined ? String(widget.value) : "â€”";
    const display = typeof widget.value === "number" && widget.value >= 1000 ? widget.value.toLocaleString() : val;
    return (
        <div style={{
            display: "flex", flexDirection: "column", justifyContent: "space-between", height: "100%",
            padding: "18px 16px 14px", background: `linear-gradient(135deg, ${accent}08 0%, ${accent}03 100%)`,
            borderTop: `3px solid ${accent}`, borderRadius: "0 0 12px 12px",
        }}>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.8px", color: COLORS.textMuted, marginBottom: 8 }}>
                {widget.title || ""}
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, color: COLORS.text, lineHeight: 1.1, letterSpacing: "-0.03em" }}>{display}</div>
            {widget.subtitle && <div style={{ fontSize: 11, color: accent, marginTop: 6, fontWeight: 600 }}>{widget.subtitle}</div>}
        </div>
    );
};

// â”€â”€â”€ Drill Panel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const DrillPanel = ({ widget, onClose }: { widget: DashboardWidget | undefined; onClose: () => void }) => {
    if (!widget) return null;
    const rows = Array.isArray(widget.data) ? widget.data : null;
    const cols = rows?.length ? Object.keys(rows[0]) : [];
    return (
        <div style={S.drillOverlay}>
            <div style={S.drillPanel}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                    <div>
                        <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: COLORS.text }}>{widget.title || widget.id}</h2>
                        {widget.subtitle && <p style={{ margin: "4px 0 0", color: COLORS.textSecondary, fontSize: 13 }}>{widget.subtitle}</p>}
                    </div>
                    <button style={S.closeBtn} onClick={onClose}><FiX size={18} /></button>
                </div>
                {widget.value !== undefined && (
                    <div style={{ background: `linear-gradient(135deg,#f5f3ff,#ede9fe)`, borderRadius: 12, padding: "18px 20px" }}>
                        <div style={{ fontSize: 42, fontWeight: 800, color: COLORS.primary, lineHeight: 1, letterSpacing: "-0.03em" }}>
                            {String(widget.value)}{widget.unit ? ` ${widget.unit}` : ""}
                        </div>
                        {widget.description && <p style={{ color: COLORS.textSecondary, fontSize: 13, margin: "8px 0 0" }}>{widget.description}</p>}
                    </div>
                )}
                {widget.metrics && (
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(120px,1fr))", gap: 10 }}>
                        {Object.entries(widget.metrics).map(([k, v]) => (
                            <div key={k} style={{ border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: "12px 14px", display: "flex", flexDirection: "column", gap: 4, background: COLORS.surfaceAlt }}>
                                <span style={{ color: COLORS.textMuted, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.5px" }}>{k}</span>
                                <strong style={{ fontSize: 20, color: COLORS.text, fontWeight: 700 }}>{String(v)}</strong>
                            </div>
                        ))}
                    </div>
                )}
                {rows && rows.length > 0 && (
                    <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: 380 }}>
                        <table style={S.table}>
                            <thead><tr>{cols.map((c) => <th key={c} style={S.th}>{c.replace(/_/g, " ")}</th>)}</tr></thead>
                            <tbody>
                                {rows.map((row: any, i: number) => (
                                    <tr key={i} style={i % 2 === 1 ? { background: COLORS.surfaceAlt } : {}}>
                                        {cols.map((c) => <td key={c} style={S.td}>{formatCell(row[c])}</td>)}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
                {!rows && !widget.value && !widget.metrics && (
                    <p style={{ color: COLORS.textMuted, fontSize: 13 }}>No detailed data available for this widget.</p>
                )}
            </div>
        </div>
    );
};
// â”€â”€â”€ Skeleton Loader â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const SkeletonGrid = () => (
    <div style={S.widgetGrid}>
        {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{ ...S.widgetCard, gridColumn: `span ${i < 3 ? 4 : 6}`, padding: 20 }}>
                <div style={{ height: 14, borderRadius: 6, background: "linear-gradient(90deg,#f1f5f9 25%,#e2e8f0 50%,#f1f5f9 75%)", backgroundSize: "200% 100%", animation: "shimmer 1.4s infinite", width: "45%" }} />
                <div style={{ height: 10, borderRadius: 4, background: "linear-gradient(90deg,#f1f5f9 25%,#e2e8f0 50%,#f1f5f9 75%)", backgroundSize: "200% 100%", animation: "shimmer 1.4s infinite", width: "60%", marginTop: 12 }} />
                <div style={{ height: 10, borderRadius: 4, background: "linear-gradient(90deg,#f1f5f9 25%,#e2e8f0 50%,#f1f5f9 75%)", backgroundSize: "200% 100%", animation: "shimmer 1.4s infinite", width: "80%", marginTop: 8 }} />
            </div>
        ))}
    </div>
);

const EmptyViz = () => (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 180, color: COLORS.textMuted, fontSize: 13 }}>
        No data available
    </div>
);

// â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
    if (!rawLayout || typeof rawLayout !== "object") return { ...DEFAULT_LAYOUT, widget_order: [...widgetIds] };
    const order = Array.isArray(rawLayout.widget_order) ? rawLayout.widget_order.map(String).filter((id: string) => widgetIds.includes(id)) : [];
    const hidden = Array.isArray(rawLayout.hidden_widgets) ? rawLayout.hidden_widgets.map(String).filter((id: string) => widgetIds.includes(id)) : [];
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
    for (const row of rows) { for (const key of keys) { const v = row[key]; if (v != null) { const n = String(v).trim(); if (n) values.add(n); } } }
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
    if (Array.isArray(widget.data) && widget.data.length > 0) return ["line", "area", "bar", "pie", "table", "metric"];
    return ["metric"];
}

function canSwitchVisual(widget: DashboardWidget): boolean {
    if (widget.type === "kpi" || widget.type === "bar_chart" || widget.type === "donut_chart") return false;
    return Array.isArray(widget.data) && widget.data.length > 0;
}

function widgetGridSpan(widget: DashboardWidget): number {
    if (widget.type === "table") return 12;
    if (widget.type === "bar_chart") return 8;
    if (widget.type === "donut_chart") return 4;
    if (widget.type === "kpi") return 3;
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
            return filteredData.slice(0, 60).map((r: any, i: number) => ({ x: String(r[catKey] ?? `row_${i + 1}`), y: Number(r[numKey]) })).filter((r: any) => isFinite(r.y));
        }
    }
    if (isFinite(Number(widget.value))) return [{ x: widget.title || widget.id, y: Number(widget.value) }];
    return [];
}

function formatCell(value: unknown): string {
    if (value === null || value === undefined) return "â€”";
    if (typeof value === "number") return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    return String(value);
}

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
    } catch { return ""; }
}

function severityBadge(severity: string): React.CSSProperties {
    const n = String(severity).toUpperCase();
    if (n === "CRITICAL") return { display: "inline-block", padding: "2px 8px", borderRadius: 999, fontSize: 10, fontWeight: 700, color: "#991b1b", background: "#fee2e2", border: "1px solid #fecaca" };
    if (n === "WARNING") return { display: "inline-block", padding: "2px 8px", borderRadius: 999, fontSize: 10, fontWeight: 700, color: "#92400e", background: "#fef3c7", border: "1px solid #fde68a" };
    return { display: "inline-block", padding: "2px 8px", borderRadius: 999, fontSize: 10, fontWeight: 700, color: "#1d4ed8", background: "#dbeafe", border: "1px solid #bfdbfe" };
}
// â”€â”€â”€ Export Dashboard Button â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const ExportDashboardButton = ({ runId }: { runId: string }) => {
    const [exporting, setExporting] = useState(false);
    const [exportMsg, setExportMsg] = useState<string | null>(null);

    const handleExportDashboard = useCallback(async () => {
        if (exporting || !runId) return;
        setExporting(true); setExportMsg(null);
        try {
            const dirRes = await frontendApi.selectDirectory();
            if (!dirRes.success || !dirRes.data?.directory_path) {
                setExportMsg("Export cancelled.");
                setTimeout(() => setExportMsg(null), 2000);
                setExporting(false); return;
            }
            const outputDir = dirRes.data.directory_path;
            await new Promise((r) => setTimeout(r, 2000));
            const html2canvasModule = await import("html2canvas");
            const html2canvas = html2canvasModule.default || html2canvasModule;
            const target = document.getElementById("dashboard-canvas") || document.querySelector("[data-dashboard-root]");
            if (!target) { setExportMsg("Dashboard not ready. Please wait and try again."); setExporting(false); return; }
            const canvas = await html2canvas(target as HTMLElement, { scale: 3, useCORS: true, backgroundColor: COLORS.canvasBg, logging: false, allowTaint: true });
            const imageBase64 = canvas.toDataURL("image/png");
            const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, "");
            const res = await frontendApi.exportDashboardPdf(runId, base64Data, outputDir);
            if (res.success) { setExportMsg("Dashboard exported successfully!"); setTimeout(() => setExportMsg(null), 4000); }
            else { setExportMsg(res.message || "Export failed"); }
        } catch (err) { setExportMsg(`Export error: ${err}`); }
        finally { setExporting(false); }
    }, [exporting, runId]);

    return (
        <>
            <button style={{ ...S.headerBtn, background: exporting ? "#e0e7ff" : COLORS.primaryBg, color: COLORS.primary, borderColor: "#c7d2fe", cursor: exporting ? "not-allowed" : "pointer", opacity: exporting ? 0.7 : 1 }}
                onClick={handleExportDashboard} disabled={exporting} title="Export current dashboard view as PDF">
                <FiDownload size={13} /> {exporting ? "Capturing..." : "Export PDF"}
            </button>
            {exportMsg && (
                <span style={{ fontSize: 11, color: exportMsg.includes("success") ? COLORS.success : COLORS.danger, fontWeight: 500, padding: "4px 8px", borderRadius: 6, background: exportMsg.includes("success") ? COLORS.successBg : COLORS.dangerBg }}>
                    {exportMsg}
                </span>
            )}
        </>
    );
};
// â”€â”€â”€ Styles â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const S: Record<string, React.CSSProperties> = {
    page: { display: "flex", flexDirection: "column", height: "100%", minHeight: 0, fontFamily: "'Inter', -apple-system, sans-serif" },

    // Header
    header: {
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "12px 20px", borderBottom: `1px solid ${COLORS.border}`,
        background: COLORS.surface, flexShrink: 0, gap: 12, flexWrap: "wrap",
    },
    headerLeft: { display: "flex", alignItems: "center", gap: 12 },
    headerTitle: { margin: 0, fontSize: 16, fontWeight: 700, color: COLORS.text, lineHeight: 1.2 },
    badge: {
        fontSize: 10, fontWeight: 700, color: COLORS.primary, background: COLORS.primaryBg,
        border: `1px solid ${COLORS.primaryLight}40`, borderRadius: 6, padding: "3px 10px",
        letterSpacing: "0.5px", textTransform: "uppercase" as const,
    },
    savedPill: {
        fontSize: 11, fontWeight: 600, color: "#065f46", background: "#d1fae5",
        border: "1px solid #6ee7b7", borderRadius: 6, padding: "2px 7px",
        display: "inline-block", marginTop: 2,
    },
    headerActions: { display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" },
    headerBtn: {
        display: "inline-flex", alignItems: "center", gap: 5,
        background: COLORS.surfaceAlt, border: `1px solid ${COLORS.border}`,
        borderRadius: 8, padding: "7px 14px", fontSize: 12, fontWeight: 500,
        color: COLORS.text, cursor: "pointer", transition: "all 0.15s ease",
    },
    headerBtnActive: { background: COLORS.primaryBg, borderColor: `${COLORS.primaryLight}60`, color: COLORS.primary },
    headerBtnSuccess: { background: "#d1fae5", borderColor: "#6ee7b7", color: "#065f46" },

    // KPI Row
    kpiRow: {
        display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14,
        padding: "16px 20px 0", flexShrink: 0,
    },
    kpiCard: {
        background: COLORS.surface, borderRadius: 12,
        border: `1px solid ${COLORS.border}`, padding: "16px 18px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)", transition: "transform 0.15s ease, box-shadow 0.15s ease",
        animation: "dashFadeIn 0.4s ease-out",
    },
    kpiLabel: { fontSize: 10, fontWeight: 700, color: COLORS.textMuted, letterSpacing: "0.8px" },
    kpiValue: { fontSize: 28, fontWeight: 800, color: COLORS.text, lineHeight: 1.1, letterSpacing: "-0.03em", marginTop: 8 },
    kpiIconWrap: { width: 32, height: 32, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" },

    // Banners
    errorBanner: {
        margin: "12px 20px 0", padding: "10px 14px", borderRadius: 8,
        background: COLORS.dangerBg, border: `1px solid #fecaca`, borderLeft: `4px solid ${COLORS.danger}`,
        fontSize: 13, color: "#991b1b", flexShrink: 0,
    },
    infoBanner: {
        margin: "12px 20px 0", padding: "10px 14px", borderRadius: 8,
        background: COLORS.surface, border: `1px solid ${COLORS.border}`,
        fontSize: 13, color: COLORS.text, flexShrink: 0,
    },

    // Body
    body: { display: "flex", flex: 1, minHeight: 0, overflow: "hidden" },

    // Sidebar
    sidebar: {
        width: 230, flexShrink: 0, borderRight: `1px solid ${COLORS.border}`,
        background: COLORS.surface, padding: "16px 14px",
        overflowY: "auto", display: "flex", flexDirection: "column", gap: 16,
    },
    sidebarHeader: {
        display: "flex", alignItems: "center", gap: 6,
        fontSize: 11, fontWeight: 700, color: COLORS.text,
        letterSpacing: "0.8px",
    },
    filterLabel: {
        display: "flex", flexDirection: "column", gap: 6,
        fontSize: 10, fontWeight: 700, color: COLORS.textMuted,
        letterSpacing: "0.5px",
    },
    select: {
        border: `1px solid ${COLORS.border}`, borderRadius: 8,
        padding: "8px 10px", fontSize: 12, color: COLORS.text, background: COLORS.surface,
        outline: "none", cursor: "pointer",
    },
    checkboxGroup: { display: "flex", flexDirection: "column", gap: 6 },
    checkboxLabel: { display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: COLORS.text, cursor: "pointer", fontWeight: 400 },
    checkbox: { accentColor: COLORS.primary, width: 14, height: 14 },
    resetBtn: {
        background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 8,
        padding: "8px 12px", fontSize: 11, color: COLORS.textSecondary, cursor: "pointer",
        fontWeight: 500, textAlign: "center",
    },
    hiddenSection: { borderTop: `1px solid ${COLORS.border}`, paddingTop: 12 },
    hiddenTitle: { fontSize: 10, fontWeight: 700, color: COLORS.textMuted, marginBottom: 6, letterSpacing: "0.5px" },
    hiddenChip: {
        display: "flex", alignItems: "center", gap: 6,
        background: COLORS.surfaceAlt, border: `1px solid ${COLORS.border}`,
        borderRadius: 6, padding: "4px 8px", fontSize: 11, color: COLORS.text, marginBottom: 4,
    },
    chipBtn: { background: "none", border: "none", cursor: "pointer", color: COLORS.textMuted, display: "flex", padding: 2 },

    // Canvas
    canvas: { flex: 1, overflowY: "auto", padding: "20px 24px", backgroundColor: COLORS.canvasBg },
    sectionHeaderRow: { display: "flex", alignItems: "center", gap: 12, marginBottom: 14 },
    sectionLabel: { fontSize: 11, fontWeight: 700, color: COLORS.textMuted, letterSpacing: "1px" },
    sectionDivider: { flex: 1, height: 1, background: COLORS.border },

    // Widget Grid
    widgetGrid: { display: "grid", gridTemplateColumns: "repeat(12, 1fr)", gap: 14, alignItems: "start" },
    widgetCard: {
        background: COLORS.surface, borderRadius: 14,
        border: `1px solid ${COLORS.border}`,
        boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)",
        overflow: "hidden", transition: "box-shadow 0.15s ease, transform 0.15s ease",
        animation: "dashFadeIn 0.4s ease-out",
    },
    cardDragOver: { boxShadow: `0 0 0 2px ${COLORS.primary}`, borderColor: COLORS.primary },
    cardDragging: { opacity: 0.5 },
    cardHeader: {
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "14px 18px 0", gap: 8,
    },
    cardTitle: { fontSize: 12, fontWeight: 700, color: COLORS.textMuted, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", letterSpacing: "0.3px", textTransform: "uppercase" as const },
    cardActions: { display: "flex", gap: 6, alignItems: "center", flexShrink: 0 },
    cardBody: { padding: "12px 18px 18px" },
    vizSelect: {
        border: `1px solid ${COLORS.border}`, borderRadius: 6,
        padding: "4px 6px", fontSize: 11, color: COLORS.text,
        background: COLORS.surfaceAlt, cursor: "pointer",
    },

    iconBtnGhost: {
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        background: "transparent", border: `1px solid ${COLORS.border}`,
        borderRadius: 8, padding: "6px 8px", cursor: "pointer", color: COLORS.textSecondary,
        transition: "all 0.15s ease",
    },
    iconBtnSmall: {
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        background: "transparent", border: "none",
        borderRadius: 4, padding: 4, cursor: "pointer", color: COLORS.textMuted,
    },

    // Donut center
    donutCenter: {
        position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -60%)",
        textAlign: "center", pointerEvents: "none",
    },

    // Table
    table: { width: "100%", borderCollapse: "collapse", fontSize: 12 },
    th: {
        textAlign: "left", padding: "10px 12px", fontSize: 10, fontWeight: 700,
        color: COLORS.textMuted, borderBottom: `2px solid ${COLORS.border}`, background: COLORS.surfaceAlt,
        position: "sticky", top: 0, textTransform: "uppercase", letterSpacing: "0.5px",
    },
    td: { padding: "9px 12px", borderBottom: `1px solid ${COLORS.borderLight}`, color: COLORS.text },

    // Empty state
    emptyState: {
        display: "flex", flexDirection: "column", alignItems: "center",
        justifyContent: "center", padding: "80px 20px", textAlign: "center",
    },
    emptyIcon: { width: 80, height: 80, borderRadius: 20, background: COLORS.surfaceAlt, display: "flex", alignItems: "center", justifyContent: "center" },

    // Drill panel
    drillOverlay: {
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)",
        zIndex: 1000, display: "flex", alignItems: "flex-end", justifyContent: "flex-end",
    },
    drillPanel: {
        width: 540, height: "100vh", background: COLORS.surface, overflowY: "auto",
        padding: 28, display: "flex", flexDirection: "column", gap: 20,
        boxShadow: "-8px 0 32px rgba(0,0,0,0.12)",
    },
    closeBtn: {
        background: COLORS.surfaceAlt, border: "none", borderRadius: 8,
        padding: "6px 8px", cursor: "pointer", color: COLORS.text,
        display: "flex", alignItems: "center",
    },
};

export default Dashboards;
