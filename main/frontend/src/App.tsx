import { Link, NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import RunPrediction from "./pages/RunPrediction";
import RunDetail from "./pages/RunDetail";
import Settings from "./pages/Settings";

function Nav() {
  return (
    <nav className="app-nav">
      <Link to="/" className="app-brand">
        <span className="app-brand-dot" />
        <span>ProcessCompliance Console</span>
      </Link>
      <div className="app-nav-links">
        <NavLink
          to="/"
          className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/run"
          className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
        >
          Run
        </NavLink>
        <NavLink
          to="/settings"
          className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
        >
          Settings
        </NavLink>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <Nav />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/run" element={<RunPrediction />} />
        <Route path="/runs/:runId" element={<RunDetail />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </div>
  );
}
