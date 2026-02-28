/**
 * DashboardToolBar — Undo/Redo + layout action bar
 * -------------------------------------------------
 * - Undo / Redo with keyboard shortcut hints
 * - Widget visibility toggle panel
 * - Time granularity switcher (day/month/year)
 * - Matches Dashboards.tsx design language
 */

import { useState } from "react";
import {
  FiRotateCcw,
  FiRotateCw,
  FiCalendar,
  FiEye,
  FiEyeOff,
  FiChevronDown,
} from "react-icons/fi";
import { dashboardsUI } from "../../state/dashboards_ui_store";
import { useDashboardsUI } from "../../state/useDashboardsUI";
import type { InteractionState } from "../../state/dashboards_ui_store";

// ─── Types ────────────────────────────────────────────────────────────────────

type Granularity = InteractionState["timeGranularity"];

// ─── Main Component ───────────────────────────────────────────────────────────

const DashboardToolBar = () => {
  const state = useDashboardsUI();
  const [showWidgets, setShowWidgets] = useState(false);

  const interaction = state.interactionState;
  const blueprint = state.blueprint;

  const canUndo = state.undoStack.length > 0;
  const canRedo = state.redoStack.length > 0;

  const currentGranularity: Granularity =
    interaction?.timeGranularity ?? "day";

  const setGranularity = (g: Granularity) => {
    dashboardsUI.updateInteraction((prev) => ({
      ...prev,
      timeGranularity: g,
    }));
  };

  const toggleWidget = (widgetId: string) => {
    dashboardsUI.updateInteraction((prev) => {
    // hiddenWidgets is string[] — use array ops, not Set
      const isHidden = prev.hiddenWidgets.includes(widgetId);
      return {
        ...prev,
        hiddenWidgets: isHidden
          ? prev.hiddenWidgets.filter((id) => id !== widgetId)
          : [...prev.hiddenWidgets, widgetId],
      };
    });
  };
  
  const widgets = blueprint?.widgets ?? [];
  const hiddenCount = interaction?.hiddenWidgets.length ?? 0;

  return (
    <div style={toolbarWrap}>
      {/* ── Undo / Redo ── */}
      <div style={group}>
        <ToolButton
          onClick={() => dashboardsUI.undo()}
          disabled={!canUndo}
          title="Undo (Ctrl+Z)"
          aria-label="Undo"
        >
          <FiRotateCcw size={13} />
          <span>Undo</span>
        </ToolButton>

        <ToolButton
          onClick={() => dashboardsUI.redo()}
          disabled={!canRedo}
          title="Redo (Ctrl+Y)"
          aria-label="Redo"
        >
          <FiRotateCw size={13} />
          <span>Redo</span>
        </ToolButton>

        {/* Undo stack depth indicator */}
        {canUndo && (
          <span style={stackBadge} title={`${state.undoStack.length} changes`}>
            {state.undoStack.length}
          </span>
        )}
      </div>

      <div style={divider} />

      {/* ── Time granularity ── */}
      <div style={group}>
        <span style={groupLabel}><FiCalendar size={11} /> Granularity</span>
        {(["day", "month", "year"] as Granularity[]).map((g) => (
          <button
            key={g}
            onClick={() => setGranularity(g)}
            style={{
              ...granularityBtn,
              ...(currentGranularity === g ? granularityActive : {}),
            }}
          >
            {g.charAt(0).toUpperCase() + g.slice(1)}
          </button>
        ))}
      </div>

      <div style={divider} />

      {/* ── Widget visibility ── */}
      {widgets.length > 0 && (
        <div style={{ position: "relative" }}>
          <ToolButton
            onClick={() => setShowWidgets((v) => !v)}
            title="Toggle widget visibility"
          >
            <FiEye size={13} />
            <span>Widgets</span>
            {hiddenCount > 0 && (
              <span style={hiddenBadge}>{hiddenCount} hidden</span>
            )}
            <FiChevronDown
              size={11}
              style={{
                transform: showWidgets ? "rotate(180deg)" : "none",
                transition: "transform 0.15s ease",
              }}
            />
          </ToolButton>

          {showWidgets && (
            <div style={widgetPanel}>
              <div style={widgetPanelTitle}>Widget Visibility</div>
              {widgets.map((w) => {
                const isHidden = interaction?.hiddenWidgets.includes(w.widgetId) ?? false;
                const label = (w.title || w.widgetId).replace(/_/g, " ");
                return (
                  <button
                    key={w.widgetId}
                    onClick={() => toggleWidget(w.widgetId)}
                    style={{
                      ...widgetRow,
                      ...(isHidden ? widgetRowHidden : {}),
                    }}
                  >
                    <span style={{ flex: 1, textAlign: "left", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {label}
                    </span>
                    {isHidden
                      ? <FiEyeOff size={12} color="#9ca3af" />
                      : <FiEye size={12} color="#6366f1" />
                    }
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Tool Button ──────────────────────────────────────────────────────────────

interface ToolButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

const ToolButton = ({ children, disabled, style, ...rest }: ToolButtonProps) => (
  <button
    {...rest}
    disabled={disabled}
    style={{
      ...toolBtn,
      ...(disabled ? toolBtnDisabled : {}),
      ...style,
    }}
  >
    {children}
  </button>
);

// ─── Styles ───────────────────────────────────────────────────────────────────

const toolbarWrap: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "8px 20px",
  background: "#ffffff",
  borderBottom: "1px solid #f3f4f6",
  flexWrap: "wrap",
};

const group: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 4,
};

const groupLabel: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 4,
  fontSize: 10,
  fontWeight: 700,
  color: "#9ca3af",
  textTransform: "uppercase",
  letterSpacing: "0.5px",
  marginRight: 2,
};

const divider: React.CSSProperties = {
  width: 1,
  height: 20,
  background: "#e5e7eb",
  flexShrink: 0,
  margin: "0 4px",
};

const toolBtn: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 5,
  background: "#f9fafb",
  border: "1px solid #e5e7eb",
  borderRadius: 7,
  padding: "5px 10px",
  fontSize: 12,
  fontWeight: 500,
  color: "#374151",
  cursor: "pointer",
  transition: "all 0.12s ease",
  whiteSpace: "nowrap",
};

const toolBtnDisabled: React.CSSProperties = {
  opacity: 0.35,
  cursor: "not-allowed",
  pointerEvents: "none",
};

const stackBadge: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minWidth: 18,
  height: 18,
  borderRadius: 999,
  background: "#eef2ff",
  border: "1px solid #c7d2fe",
  fontSize: 10,
  fontWeight: 700,
  color: "#4f46e5",
  padding: "0 4px",
};

const granularityBtn: React.CSSProperties = {
  background: "#fff",
  border: "1px solid #e5e7eb",
  borderRadius: 6,
  padding: "4px 9px",
  fontSize: 11,
  fontWeight: 600,
  color: "#6b7280",
  cursor: "pointer",
  transition: "all 0.1s ease",
};

const granularityActive: React.CSSProperties = {
  background: "#eef2ff",
  borderColor: "#a5b4fc",
  color: "#4f46e5",
};

const hiddenBadge: React.CSSProperties = {
  background: "#fef3c7",
  border: "1px solid #fde68a",
  borderRadius: 999,
  padding: "1px 6px",
  fontSize: 10,
  fontWeight: 700,
  color: "#92400e",
};

// Widget panel dropdown
const widgetPanel: React.CSSProperties = {
  position: "absolute",
  top: "calc(100% + 6px)",
  left: 0,
  zIndex: 200,
  background: "#fff",
  border: "1px solid #e5e7eb",
  borderRadius: 10,
  boxShadow: "0 8px 24px rgba(0,0,0,0.10)",
  padding: "8px",
  minWidth: 220,
  maxWidth: 300,
  maxHeight: 340,
  overflowY: "auto",
};

const widgetPanelTitle: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  color: "#9ca3af",
  textTransform: "uppercase",
  letterSpacing: "0.5px",
  padding: "4px 8px 8px",
  borderBottom: "1px solid #f3f4f6",
  marginBottom: 4,
};

const widgetRow: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  width: "100%",
  padding: "7px 10px",
  borderRadius: 7,
  border: "none",
  background: "none",
  fontSize: 12,
  color: "#374151",
  cursor: "pointer",
  transition: "background 0.1s ease",
};

const widgetRowHidden: React.CSSProperties = {
  color: "#9ca3af",
  background: "#f9fafb",
};

export default DashboardToolBar;