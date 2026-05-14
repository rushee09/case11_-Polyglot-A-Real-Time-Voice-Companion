import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import VoiceAgentPage from "./pages/VoiceAgentPage";
import ScenarioTestPage from "./pages/ScenarioTestPage";
import LogsPage from "./pages/LogsPage";

function Nav() {
  const loc = useLocation();
  const links = [
    { to: "/", label: "Home" },
    { to: "/agent", label: "Voice Agent" },
    { to: "/scenarios", label: "Scenarios" },
    { to: "/logs", label: "Logs" },
  ];
  return (
    <nav className="border-b border-white/[0.06] px-6 py-3 flex items-center justify-between">
      <Link to="/" className="font-semibold text-violet-400 text-sm tracking-wide">
        🌐 Polyglot
      </Link>
      <div className="flex gap-1">
        {links.map((l) => (
          <Link
            key={l.to}
            to={l.to}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              loc.pathname === l.to
                ? "bg-violet-500/10 text-violet-400"
                : "text-white/50 hover:text-white hover:bg-white/5"
            }`}
          >
            {l.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Nav />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/agent" element={<VoiceAgentPage />} />
            <Route path="/scenarios" element={<ScenarioTestPage />} />
            <Route path="/logs" element={<LogsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
