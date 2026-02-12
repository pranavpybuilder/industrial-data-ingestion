import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home/Home";
import Ingestion from "./pages/Ingestion/Ingestion";
import Insights from "./pages/Insights/Insights";
import Dashboards from "./pages/Dashboards/Dashboards";
import Exports from "./pages/Exports/Exports";
import Explorer from "./pages/Explorer/Explorer";
import DataHealth from "./pages/DataHealth/DataHealth";

function App() {
  return (
    <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/ingestion" element={<Ingestion />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="/dashboards" element={<Dashboards />} />
          <Route path="/exports" element={<Exports />} />
          <Route path="/explorer" element={<Explorer />} />
          <Route path="/data-health" element={<DataHealth />} />
        </Routes>
    </Router>
  );
}

export default App;