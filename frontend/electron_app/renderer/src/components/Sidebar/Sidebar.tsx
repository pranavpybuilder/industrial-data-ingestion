import { NavLink } from "react-router-dom";
import { useState } from "react";
import {
  FiHome,
  FiUpload,
  FiZap,
  FiGrid,
  FiDownload,
  FiDatabase,
  FiActivity,
  FiMenu,
  FiChevronLeft,
} from "react-icons/fi";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  collapsed: boolean;
}

const NavItem = ({ to, icon, label, collapsed }: NavItemProps) => {
  const [hovered, setHovered] = useState(false);

  return (
    <NavLink
      to={to}
      end={to === "/"}
      title={label}
      aria-label={label}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={({ isActive }) => ({
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: collapsed ? "10px 0" : "10px 14px",
        justifyContent: collapsed ? "center" : "flex-start",
        borderRadius: "10px",
        marginBottom: "4px",
        textDecoration: "none",
        fontSize: "14px",
        fontWeight: isActive ? 600 : 450,
        color: isActive ? "#ffffff" : "#c7d2fe",
        background: isActive
          ? "rgba(99, 102, 241, 0.25)"
          : hovered
          ? "rgba(255, 255, 255, 0.06)"
          : "transparent",
        borderLeft: isActive
          ? "3px solid #818cf8"
          : "3px solid transparent",
        transition: "all 0.2s ease",
        transform: hovered && !isActive ? "translateX(2px)" : "none",
        whiteSpace: "nowrap" as const,
        overflow: "hidden",
      })}
    >
      <span style={{ fontSize: "17px", flexShrink: 0, display: "flex" }}>
        {icon}
      </span>
      {!collapsed && <span>{label}</span>}
    </NavLink>
  );
};

const Sidebar = ({ collapsed, onToggle }: SidebarProps) => {
  return (
    <nav
      style={{
        width: collapsed ? "64px" : "240px",
        minWidth: collapsed ? "64px" : "240px",
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        background: "linear-gradient(180deg, #15132e 0%, #0f0d24 100%)",
        color: "#ffffff",
        padding: collapsed ? "12px 8px" : "12px",
        overflow: "hidden",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        borderRight: "1px solid rgba(99, 102, 241, 0.1)",
      }}
    >
      {/* TOGGLE BUTTON */}
      <button
        onClick={onToggle}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "flex-end",
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: "10px",
          color: "#c7d2fe",
          padding: "8px",
          cursor: "pointer",
          marginBottom: "20px",
          transition: "all 0.2s ease",
        }}
        title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? <FiMenu size={18} /> : <FiChevronLeft size={18} />}
      </button>

      {/* MAIN NAV */}
      <div style={{ flex: 1 }}>
        <NavItem to="/" icon={<FiHome />} label="Home" collapsed={collapsed} />
        <NavItem to="/ingestion" icon={<FiUpload />} label="Ingestion" collapsed={collapsed} />
        <NavItem to="/insights" icon={<FiZap />} label="Insights" collapsed={collapsed} />
        <NavItem to="/dashboards" icon={<FiGrid />} label="Dashboards" collapsed={collapsed} />
        <NavItem to="/exports" icon={<FiDownload />} label="Exports" collapsed={collapsed} />

        {/* DIVIDER */}
        <div
          style={{
            margin: collapsed ? "16px 4px" : "16px 8px",
            height: "1px",
            background: "rgba(199, 210, 254, 0.12)",
          }}
        />

        {!collapsed && (
          <div
            style={{
              fontSize: "11px",
              fontWeight: 600,
              color: "rgba(199, 210, 254, 0.5)",
              textTransform: "uppercase",
              letterSpacing: "1.2px",
              padding: "0 14px",
              marginBottom: "8px",
            }}
          >
            Advanced
          </div>
        )}

        <NavItem to="/explorer" icon={<FiDatabase />} label="Explorer" collapsed={collapsed} />
        <NavItem to="/data-health" icon={<FiActivity />} label="Data Health" collapsed={collapsed} />
      </div>

      {/* VERSION BADGE */}
      {!collapsed && (
        <div
          style={{
            fontSize: "11px",
            color: "rgba(199, 210, 254, 0.35)",
            textAlign: "center",
            paddingTop: "12px",
            borderTop: "1px solid rgba(199, 210, 254, 0.08)",
          }}
        >
          Offline Intelligence v1.0
        </div>
      )}
    </nav>
  );
};

export default Sidebar;