import { createBrowserRouter, Navigate } from "react-router-dom";
import AppLayout from "./AppLayout";

import Home from "../pages/Home/Home";
import Ingestion from "../pages/Ingestion/Ingestion";
import Insights from "../pages/Insights/Insights";
import Dashboards from "../pages/Dashboards/Dashboards";
import Exports from "../pages/Exports/Exports";
import Explorer from "../pages/Explorer/Explorer";
import DataHealth from "../pages/DataHealth/DataHealth";

import { RunGuard } from "../components/RunGuard/RunGuard";

export const router = createBrowserRouter([
  {
  path: "/",
  element: <AppLayout />,
  children: [
    { index: true, element: <Home /> },
    { path: "ingestion", element: <Ingestion /> },
    {
      path: "insights",
      element: (
        <RunGuard>
          <Insights />
        </RunGuard>
      ),
    },
    {
      path: "dashboards",
      element: (
        <RunGuard>
          <Dashboards />
        </RunGuard>
      ),
    },
    {
      path: "exports",
      element: (
        <RunGuard>
          <Exports />
        </RunGuard>
      ),
    },
    {
      path: "explorer",
      element: (
        <RunGuard>
          <Explorer />
        </RunGuard>
      ),
    },
    {
      path: "data-health",
      element: (
        <RunGuard>
          <DataHealth />
        </RunGuard>
      ),
    },
  ],
},
]);