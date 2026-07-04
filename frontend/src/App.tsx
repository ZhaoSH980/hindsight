import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { useLang } from "./lib/i18n";
import Studio from "./pages/Studio";
import TraceExplorer from "./pages/TraceExplorer";
import EvalDashboard from "./pages/EvalDashboard";

function navClass({ isActive }: { isActive: boolean }) {
  return `px-3 py-1.5 rounded-md text-sm transition-colors ${
    isActive ? "bg-ink-700 text-slate-100" : "text-muted hover:text-slate-200"
  }`;
}

function Nav() {
  const { lang, setLang, t } = useLang();
  return (
    <nav className="flex items-center gap-2 border-b border-line bg-ink-950 px-4 py-3">
      <span className="mr-4 font-mono text-sm font-semibold tracking-widest text-accent">
        HINDSIGHT
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
      <button
        type="button"
        onClick={() => setLang(lang === "en" ? "zh" : "en")}
        className="ml-auto rounded-md border border-line px-2 py-1 font-mono text-xs text-muted hover:text-slate-200"
      >
        {lang === "en" ? "中" : "EN"}
      </button>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-ink-900">
        <Nav />
        <Routes>
          <Route path="/" element={<Studio />} />
          <Route path="/runs/:runId/trace" element={<TraceExplorer />} />
          <Route path="/runs/:runId" element={<EvalDashboard />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
