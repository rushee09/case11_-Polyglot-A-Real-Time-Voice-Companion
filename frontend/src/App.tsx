import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import LandingPage from "./pages/LandingPage";
import VoiceAgentPage from "./pages/VoiceAgentPage";
import ScenarioTestPage from "./pages/ScenarioTestPage";
import LogsPage from "./pages/LogsPage";
import { downloadChatCsv } from "./api/client";

function Nav() {
  const loc = useLocation();
  const { user, logout } = useAuth();
  const links = [
    { to: "/", label: "Home" },
    { to: "/agent", label: "Voice Agent" },
    { to: "/scenarios", label: "Scenarios" },
    { to: "/logs", label: "Logs" },
  ];
  return (
    <nav className="glass-nav px-6 py-3 flex items-center justify-between sticky top-0 z-50">
      <Link to="/" className="font-semibold text-violet-400 text-sm tracking-wide flex items-center gap-2">
        🌐 <span>Polyglot</span>
      </Link>
      <div className="flex gap-1">
        {links.map((l) => (
          <Link
            key={l.to}
            to={l.to}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              loc.pathname === l.to
                ? "bg-violet-500/15 text-violet-400 border border-violet-500/20"
                : "text-white/50 hover:text-white hover:bg-white/[0.06]"
            }`}
          >
            {l.label}
          </Link>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={downloadChatCsv}
          title="Export chat history as CSV"
          className="px-3 py-1.5 rounded-lg text-xs text-white/40 hover:text-white hover:bg-white/[0.06] transition-colors border border-transparent hover:border-white/10"
        >
          ⬇ CSV
        </button>
        {user && (
          <>
            <span className="text-xs text-white/30 hidden sm:block">{user.username}</span>
            <button
              onClick={logout}
              className="px-3 py-1.5 rounded-lg text-xs text-white/40 hover:text-red-400 hover:bg-red-500/10 transition-colors border border-transparent hover:border-red-500/20"
            >
              Sign out
            </button>
          </>
        )}
      </div>
    </nav>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  return user ? <>{children}</> : <Navigate to="/login" replace />;
}

function AppRoutes() {
  const { user } = useAuth();
  return (
    <>
      {user && <Nav />}
      {/* Ambient background orbs */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute top-[-15%] left-[-10%] w-[600px] h-[600px] rounded-full bg-violet-700/10 blur-[140px]" />
        <div className="absolute bottom-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full bg-indigo-700/10 blur-[120px]" />
        <div className="absolute top-[40%] left-[50%] w-[300px] h-[300px] rounded-full bg-violet-500/5 blur-[100px]" />
      </div>
      <main className="flex-1">
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
          <Route path="/" element={<RequireAuth><LandingPage /></RequireAuth>} />
          <Route path="/agent" element={<RequireAuth><VoiceAgentPage key={user?.username} /></RequireAuth>} />
          <Route path="/scenarios" element={<RequireAuth><ScenarioTestPage /></RequireAuth>} />
          <Route path="/logs" element={<RequireAuth><LogsPage /></RequireAuth>} />
        </Routes>
      </main>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col">
          <AppRoutes />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
