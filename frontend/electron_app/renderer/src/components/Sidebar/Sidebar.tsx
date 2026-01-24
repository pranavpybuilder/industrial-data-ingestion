import { NavLink } from "react-router-dom";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const Sidebar = ({ collapsed, onToggle }: SidebarProps) => {
  return (
    <nav
      style={{
        width: collapsed ? "56px" : "240px",
        transition: "width 0.2s ease",
        background: "linear-gradient(180deg, #18163a 0%, #14122e 100%)",
        color: "#ffffff",
        padding: "12px",
        overflow: "hidden",
        height: "100%",
        /* ❌ removed borderRight completely */
      }}
    >
      {/* TOGGLE */}
      <button
        onClick={onToggle}
        style={{
          background: "transparent",
          border: "none",
          color: "#ffffff",
          fontSize: "18px",
          cursor: "pointer",
          marginBottom: "20px",
        }}
        title="Toggle sidebar"
      >
        ☰
      </button>

      {!collapsed && (
        <>
          <NavLink to="/" style={link}>Home</NavLink>
          <NavLink to="/ingestion" style={link}>Ingestion</NavLink>
          <NavLink to="/insights" style={link}>Insights</NavLink>
          <NavLink to="/dashboards" style={link}>Dashboards</NavLink>
          <NavLink to="/exports" style={link}>Exports</NavLink>

          <div
            style={{
              marginTop: "18px",
              marginBottom: "8px",
              fontSize: "12px",
              color: "#c7d2fe",
              opacity: 0.9,
              textAlign:"center",
            }}
          >
            Advanced
          </div>

          <NavLink to="/explorer" style={subLink}>Explorer</NavLink>
          <NavLink to="/data-health" style={subLink}>Data Health</NavLink>
        </>
      )}
    </nav>
  );
};

/* STYLES */
const link: React.CSSProperties = {
  display: "block",
  color: "#ffffff",
  textDecoration: "none",
  marginBottom: "12px",
  fontSize: "14px",
  fontWeight: 500,
  textAlign:"center"
};

const subLink: React.CSSProperties = {
  ...link,
  fontSize: "13px",
  color: "#c7d2fe",
  fontWeight: 400,
};

export default Sidebar;