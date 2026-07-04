import { BrowserRouter, NavLink, Route, Routes, useLocation } from "react-router-dom";
import { useLang } from "./lib/i18n";
import Studio from "./pages/Studio";
import TraceExplorer from "./pages/TraceExplorer";
import EvalDashboard from "./pages/EvalDashboard";
import Leaderboard from "./pages/Leaderboard";

function navClass({ isActive }: { isActive: boolean }) {
  return `relative px-3 py-1.5 rounded-md text-sm transition-all duration-200 ${
    isActive
      ? "bg-ink-700 text-slate-100 shadow-glow-sm"
      : "text-muted hover:text-slate-200 hover:bg-ink-800"
  }`;
}

function Nav() {
  const { lang, setLang, t } = useLang();
  return (
    <nav className="sticky top-0 z-40 flex items-center gap-2 border-b border-line bg-ink-950/70 px-4 py-3 backdrop-blur-md">
      <span className="mr-1 font-mono text-sm font-semibold tracking-[0.3em] text-accent glow-text">
        HINDSIGHT
      </span>
      <span className="mr-3 hidden font-mono text-[9px] uppercase tracking-[0.2em] text-muted sm:inline">
        time-travel eval
      </span>
      <NavLink to="/" end className={navClass}>
        {t("studio")}
      </NavLink>
      <NavLink to="/runs/_/trace" className={navClass}>
        {t("trace")}
      </NavLink>
      <NavLink to="/runs/_" className={navClass}>
        {t("evals")}
      </NavLink>
      <NavLink to="/leaderboard" className={navClass}>
        {t("leaderboard")}
      </NavLink>
      <button
        type="button"
        onClick={() => setLang(lang === "en" ? "zh" : "en")}
        className="ml-auto rounded-md border border-line px-2 py-1 font-mono text-xs text-muted transition-colors hover:border-accent/60 hover:text-accent"
      >
        {lang === "en" ? "中" : "EN"}
      </button>
    </nav>
  );
}

function PageFrame() {
  const location = useLocation();
  return (
    <div key={location.pathname} className="page-enter">
      <Routes>
        <Route path="/" element={<Studio />} />
        <Route path="/runs/:runId/trace" element={<TraceExplorer />} />
        <Route path="/runs/:runId" element={<EvalDashboard />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <Nav />
        <PageFrame />
      </div>
    </BrowserRouter>
  );
}
