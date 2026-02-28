/**
 * DashboardHeader — Power BI-style page header
 * ---------------------------------------------
 * - Dashboard title + run name + last updated
 * - Save / Insights / Export action buttons
 * - Blueprint metadata badge
 * - Matches Dashboards.tsx design language
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FiSave,
  FiBarChart2,
  FiDownload,
  FiRefreshCw,
  FiClock,
  FiLayers,
  FiCheckCircle,
} from "react-icons/fi";

// ─── Types ────────────────────────────────────────────────────────────────────

interface DashboardHeaderProps {
  /** Displayed as the main title (e.g. blueprint title or run name) */
  dashboardTitle: string;
  /** Run ID or run name shown as subtitle */
  runName: string;
  /** Optional: show a "last updated" timestamp */
  lastUpdated?: string | Date;
  /** Optional: number of widgets in the dashboard */
  widgetCount?: number;
  /** Optional: number of sections */
  sectionCount?: number;
  /** Called when Save button is clicked */
  onSave?: () => void | Promise<void>;
  /** Called when Refresh button is clicked */
  onRefresh?: () => void | Promise<void>;
}

// ─── Main Component ───────────────────────────────────────────────────────────

const DashboardHeader = ({
  dashboardTitle,
  runName,
  lastUpdated,
  widgetCount,
  sectionCount,
  onSave,
  onRefresh,
}: DashboardHeaderProps) => {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const handleSave = async () => {
    if (!onSave || saving) return;
    setSaving(true);
    await onSave();
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleRefresh = async () => {
    if (!onRefresh || refreshing) return;
    setRefreshing(true);
    await onRefresh();
    setRefreshing(false);
  };

  const formattedDate = lastUpdated
    ? formatDate(lastUpdated)
    : null;

  return (
    <header style={s.wrapper}>
      {/* ── Left: title block ── */}
      <div style={s.titleBlock}>
        <div style={s.titleRow}>
          <h1 style={s.title}>{dashboardTitle || "Dashboard"}</h1>
          {saved && (
            <span style={s.savedBadge}>
              <FiCheckCircle size={11} /> Saved
            </span>
          )}
        </div>

        <div style={s.metaRow}>
          <span style={s.runBadge}>
            <FiLayers size={10} />
            {runName}
          </span>

          {formattedDate && (
            <span style={s.metaItem}>
              <FiClock size={10} />
              {formattedDate}
            </span>
          )}

          {widgetCount !== undefined && (
            <span style={s.metaItem}>
              {widgetCount} widget{widgetCount !== 1 ? "s" : ""}
              {sectionCount ? ` · ${sectionCount} section${sectionCount !== 1 ? "s" : ""}` : ""}
            </span>
          )}
        </div>
      </div>

      {/* ── Right: actions ── */}
      <div style={s.actions}>
        {onRefresh && (
          <ActionButton
            onClick={handleRefresh}
            disabled={refreshing}
            icon={<FiRefreshCw size={13} style={refreshing ? spinStyle : undefined} />}
            label={refreshing ? "Refreshing…" : "Refresh"}
          />
        )}

        {onSave && (
          <ActionButton
            onClick={handleSave}
            disabled={saving}
            icon={<FiSave size={13} />}
            label={saving ? "Saving…" : saved ? "Saved!" : "Save"}
            variant={saved ? "success" : "default"}
          />
        )}

        <ActionButton
          onClick={() => navigate("/insights")}
          icon={<FiBarChart2 size={13} />}
          label="Insights"
          variant="primary"
        />

        <ActionButton
          onClick={() => navigate("/exports")}
          icon={<FiDownload size={13} />}
          label="Export"
        />
      </div>
    </header>
  );
};

// ─── Action Button ────────────────────────────────────────────────────────────

interface ActionButtonProps {
  onClick?: () => void;
  icon: React.ReactNode;
  label: string;
  disabled?: boolean;
  variant?: "default" | "primary" | "success";
}

const ActionButton = ({
  onClick,
  icon,
  label,
  disabled,
  variant = "default",
}: ActionButtonProps) => {
  const variantStyle =
    variant === "primary"
      ? s.btnPrimary
      : variant === "success"
      ? s.btnSuccess
      : {};

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        ...s.btn,
        ...variantStyle,
        ...(disabled ? s.btnDisabled : {}),
      }}
    >
      {icon}
      {label}
    </button>
  );
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(d: string | Date): string {
  const date = typeof d === "string" ? new Date(d) : d;
  if (isNaN(date.getTime())) return String(d);
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const spinStyle: React.CSSProperties = {
  animation: "spin 1s linear infinite",
};

// ─── Styles ───────────────────────────────────────────────────────────────────

const s: Record<string, React.CSSProperties> = {
  wrapper: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    padding: "16px 20px",
    borderBottom: "1px solid #e5e7eb",
    background: "#ffffff",
    flexWrap: "wrap",
    gap: 12,
    flexShrink: 0,
  },

  // Title block
  titleBlock: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    minWidth: 0,
    flex: 1,
  },
  titleRow: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    flexWrap: "wrap",
  },
  title: {
    margin: 0,
    fontSize: 20,
    fontWeight: 800,
    color: "#111827",
    letterSpacing: "-0.03em",
    lineHeight: 1.1,
  },
  savedBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: 4,
    fontSize: 11,
    fontWeight: 700,
    color: "#065f46",
    background: "#d1fae5",
    border: "1px solid #6ee7b7",
    borderRadius: 999,
    padding: "2px 8px",
  },

  // Meta row
  metaRow: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    flexWrap: "wrap",
  },
  runBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: 4,
    fontSize: 11,
    fontWeight: 600,
    color: "#4f46e5",
    background: "#eef2ff",
    border: "1px solid #c7d2fe",
    borderRadius: 6,
    padding: "2px 8px",
  },
  metaItem: {
    display: "inline-flex",
    alignItems: "center",
    gap: 4,
    fontSize: 11,
    color: "#9ca3af",
    fontWeight: 500,
  },

  // Actions
  actions: {
    display: "flex",
    alignItems: "center",
    gap: 7,
    flexWrap: "wrap",
    flexShrink: 0,
  },
  btn: {
    display: "inline-flex",
    alignItems: "center",
    gap: 5,
    background: "#f9fafb",
    border: "1px solid #e5e7eb",
    borderRadius: 8,
    padding: "7px 13px",
    fontSize: 12,
    fontWeight: 600,
    color: "#374151",
    cursor: "pointer",
    transition: "all 0.12s ease",
    whiteSpace: "nowrap",
  },
  btnPrimary: {
    background: "#eef2ff",
    borderColor: "#a5b4fc",
    color: "#4f46e5",
  },
  btnSuccess: {
    background: "#d1fae5",
    borderColor: "#6ee7b7",
    color: "#065f46",
  },
  btnDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
    pointerEvents: "none",
  },
};

export default DashboardHeader;