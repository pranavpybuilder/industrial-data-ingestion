/* ═══════════════════════════════════════════════════════════════
   OFFLINE INTELLIGENCE  ·  Design System  ·  v1.0
   ═══════════════════════════════════════════════════════════════ */

/* ---------- Color Palette ---------- */

export const colors = {
  /* Brand */
  primary:    "#6366f1",      // Indigo-500
  primaryDk:  "#4f46e5",      // Indigo-600
  primaryLt:  "#818cf8",      // Indigo-400
  accent:     "#8b5cf6",      // Violet-500

  /* Surfaces */
  bgApp:      "#f0f1f5",      // overall app canvas
  bgCard:     "#ffffff",
  bgSidebar:  "#111024",      // deep navy
  bgTopbar:   "linear-gradient(90deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%)",

  /* Text */
  textPrimary:   "#111827",
  textSecondary: "#6b7280",
  textMuted:     "#9ca3af",
  textOnDark:    "#e0e7ff",
  textWhite:     "#ffffff",

  /* Borders */
  border:     "#e5e7eb",
  borderFocus:"#6366f1",

  /* Semantic */
  success:    "#10b981",
  successBg:  "#ecfdf5",
  error:      "#ef4444",
  errorBg:    "#fef2f2",
  warning:    "#f59e0b",
  warningBg:  "#fffbeb",
  info:       "#3b82f6",
  infoBg:     "#eff6ff",
} as const;

/* ---------- Spacing ---------- */

export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "12px",
  lg: "16px",
  xl: "20px",
  xxl: "24px",
  xxxl: "32px",
} as const;

/* ---------- Radius ---------- */

export const radius = {
  sm:   "6px",
  md:   "8px",
  lg:   "12px",
  xl:   "16px",
  full: "9999px",
} as const;

/* ---------- Shadows ---------- */

export const shadows = {
  sm:   "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
  md:   "0 4px 12px rgba(0,0,0,0.08)",
  lg:   "0 10px 25px rgba(0,0,0,0.10)",
  xl:   "0 20px 50px rgba(0,0,0,0.15)",
  glow: "0 0 20px rgba(99,102,241,0.25)",
} as const;

/* ---------- Typography ---------- */

export const fonts = {
  sans: "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace",
} as const;

/* ---------- Transitions ---------- */

export const transitions = {
  fast:     "all 0.15s ease",
  normal:   "all 0.2s ease",
  smooth:   "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
  spring:   "all 0.35s cubic-bezier(0.16, 1, 0.3, 1)",
} as const;

/* ---------- Sidebar constants ---------- */

export const sidebar = {
  widthOpen:     "240px",
  widthCollapsed:"64px",
} as const;

/* ---------- Z-index layers ---------- */

export const zIndex = {
  sidebar:   100,
  topbar:    200,
  dropdown:  500,
  modal:     9999,
  toast:     10000,
} as const;

/* ---------- Reusable card style ---------- */

export const cardStyle: React.CSSProperties = {
  background: colors.bgCard,
  borderRadius: radius.lg,
  padding: spacing.xl,
  boxShadow: shadows.md,
  border: `1px solid ${colors.border}`,
  transition: transitions.normal,
};

/* ---------- Button base ---------- */

export const btnPrimary: React.CSSProperties = {
  background: colors.primary,
  color: colors.textWhite,
  border: "none",
  borderRadius: radius.md,
  padding: "10px 18px",
  fontSize: "14px",
  fontWeight: 500,
  cursor: "pointer",
  transition: transitions.fast,
};

export const btnSecondary: React.CSSProperties = {
  background: "transparent",
  color: colors.textPrimary,
  border: `1px solid ${colors.border}`,
  borderRadius: radius.md,
  padding: "10px 18px",
  fontSize: "14px",
  fontWeight: 500,
  cursor: "pointer",
  transition: transitions.fast,
};
