import { RouterProvider } from "react-router-dom";
import { router } from "app/Router";

/**
 * Root React application component.
 *
 * Responsibilities:
 * - Bootstraps routing
 * - Acts as the single UI entry point
 *
 * This file contains NO business logic.
 */
const App = () => {
  return <RouterProvider router={router} />;
};

export default App;