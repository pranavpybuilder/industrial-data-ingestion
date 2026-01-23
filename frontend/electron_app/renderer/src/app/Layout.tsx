import { useState } from "react";
import Sidebar from "../components/Sidebar/Sidebar";

interface Props {
  children: React.ReactNode;
}

const Layout = ({ children }: Props) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        overflow: "hidden",
      }}
    >
      {/* Sidebar */}
      <div
        style={{
          width: sidebarOpen ? "260px" : "48px",
          transition: "width 0.25s ease",
          background: "#1f2933",
        }}
      >
        <Sidebar
          collapsed={!sidebarOpen}
          onToggle={() => setSidebarOpen((v) => !v)}
        />
      </div>

      {/* Main Content */}
      <div
        style={{
          flex: 1,
          overflow: "auto",
          background: "#f3f4f6",
          padding: "1rem",
        }}
      >
        {children}
      </div>
    </div>
  );
};

export default Layout;