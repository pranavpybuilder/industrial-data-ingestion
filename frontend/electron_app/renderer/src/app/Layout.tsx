import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar/Sidebar";

/**
 * Global application layout.
 *
 * Responsibilities:
 * - Persistent sidebar
 * - Main content container
 * - Stable UI shell across route changes
 *
 * No data access is allowed here.
 */
const Layout = () => {
  return (
    <div style={styles.root}>
      <Sidebar />
      <main style={styles.content}>
        <Outlet />
      </main>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: "flex",
    height: "100vh",
    width: "100vw",
    overflow: "hidden",
    backgroundColor: "#f5f6f8",
  },
  content: {
    flex: 1,
    padding: "16px",
    overflowY: "auto",
    minWidth: 0,
  },
};

export default Layout;