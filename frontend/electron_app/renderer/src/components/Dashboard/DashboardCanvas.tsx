/**
 * DashboardCanvas — Power BI-style sectioned grid layout
 * -------------------------------------------------------
 * - Groups widgets by section with labeled headers
 * - 12-column CSS grid, widget spans from blueprint
 * - Respects hiddenWidgets from interaction state
 * - Orphan widgets (no section) rendered at bottom
 * - Empty canvas state when no widgets are visible
 */

import { useMemo } from "react";
import { FiLayout } from "react-icons/fi";
import DashboardSection from "./DashboardSection";
import type {
  DashboardBlueprint,
  InteractionState,
} from "../../state/dashboards_ui_store";

// ─── Types ────────────────────────────────────────────────────────────────────

interface DashboardCanvasProps {
  blueprint: DashboardBlueprint;
  interaction: InteractionState;
  widgetData: Record<string, any>;
}

// ─── Main Component ───────────────────────────────────────────────────────────

const DashboardCanvas = ({
  blueprint,
  interaction,
  widgetData,
}: DashboardCanvasProps) => {
  const sections = useMemo(
    () =>
      blueprint.sections?.length
        ? [...blueprint.sections].sort((a, b) => a.order - b.order)
        : null,
    [blueprint.sections]
  );

  // Visible widget ids (hidden filtered out)
  const visibleWidgets = useMemo(
    () =>
      blueprint.widgets.filter(
        (w) => !interaction.hiddenWidgets.includes(w.widgetId)
      ),
    [blueprint.widgets, interaction.hiddenWidgets]
  );

  const totalVisible = visibleWidgets.length;

  // ── Empty state ────────────────────────────────────────────────────────────
  if (totalVisible === 0) {
    return (
      <div style={emptyCanvasStyle}>
        <FiLayout size={40} color="#d1d5db" />
        <p style={{ margin: "12px 0 4px", fontSize: 14, fontWeight: 600, color: "#374151" }}>
          No widgets visible
        </p>
        <p style={{ margin: 0, fontSize: 12, color: "#9ca3af" }}>
          All widgets are hidden. Use the filter panel to restore them.
        </p>
      </div>
    );
  }

  // ── Sectioned layout ──────────────────────────────────────────────────────
  if (sections) {
    const sectionIds = new Set(sections.map((s) => s.sectionId));

    const orphans = visibleWidgets.filter(
      (w) => !w.sectionId || !sectionIds.has(w.sectionId)
    );

    return (
      <div style={canvasWrap}>
        {sections.map((section) => {
          const sectionWidgets = visibleWidgets.filter(
            (w) => w.sectionId === section.sectionId
          );
          if (sectionWidgets.length === 0) return null;

          return (
            <div key={section.sectionId} style={sectionBlock}>
              <SectionLabel title={section.title} count={sectionWidgets.length} />
              <div style={gridStyle}>
                {sectionWidgets.map((widget) => (
                  <DashboardSection
                    key={widget.widgetId}
                    widget={widget}
                    interaction={interaction}
                    data={widgetData[widget.widgetId] ?? []}
                  />
                ))}
              </div>
            </div>
          );
        })}

        {/* Orphan widgets */}
        {orphans.length > 0 && (
          <div style={sectionBlock}>
            <SectionLabel title="Other" count={orphans.length} muted />
            <div style={gridStyle}>
              {orphans.map((widget) => (
                <DashboardSection
                  key={widget.widgetId}
                  widget={widget}
                  interaction={interaction}
                  data={widgetData[widget.widgetId] ?? []}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── Flat layout (no sections) ──────────────────────────────────────────────
  return (
    <div style={canvasWrap}>
      <div style={gridStyle}>
        {visibleWidgets.map((widget) => (
          <DashboardSection
            key={widget.widgetId}
            widget={widget}
            interaction={interaction}
            data={widgetData[widget.widgetId] ?? []}
          />
        ))}
      </div>
    </div>
  );
};

// ─── Section Label ────────────────────────────────────────────────────────────

interface SectionLabelProps {
  title: string;
  count?: number;
  muted?: boolean;
}

const SectionLabel = ({ title, count, muted }: SectionLabelProps) => (
  <div style={sectionLabelRow}>
    <span style={{
      ...sectionLabelText,
      color: muted ? "#9ca3af" : "#111827",
      fontStyle: muted ? "italic" : "normal",
    }}>
      {title}
    </span>
    {count !== undefined && (
      <span style={sectionCountBadge}>{count}</span>
    )}
    <div style={sectionDivider} />
  </div>
);

// ─── Styles ───────────────────────────────────────────────────────────────────

const canvasWrap: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 32,
};

const sectionBlock: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 14,
};

const sectionLabelRow: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
};

const sectionLabelText: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 700,
  letterSpacing: "-0.01em",
  whiteSpace: "nowrap",
  flexShrink: 0,
};

const sectionCountBadge: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minWidth: 20,
  height: 20,
  borderRadius: 999,
  background: "#f3f4f6",
  border: "1px solid #e5e7eb",
  fontSize: 10,
  fontWeight: 700,
  color: "#6b7280",
  flexShrink: 0,
  padding: "0 5px",
};

const sectionDivider: React.CSSProperties = {
  flex: 1,
  height: 1,
  background: "linear-gradient(to right, #e5e7eb, transparent)",
};

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(12, 1fr)",
  gap: 14,
  alignItems: "start",
};

const emptyCanvasStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  padding: "80px 24px",
  textAlign: "center",
  background: "#fafafa",
  borderRadius: 14,
  border: "2px dashed #e5e7eb",
};

export default DashboardCanvas;