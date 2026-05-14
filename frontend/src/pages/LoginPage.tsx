import { useState, FormEvent } from "react";
import { useAuth } from "../context/AuthContext";

type Tab = "login" | "signup";

export default function LoginPage() {
  const { login, signup } = useAuth();
  const [tab, setTab] = useState<Tab>("login");

  // Shared fields
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm]   = useState("");
  const [showPass, setShowPass] = useState(false);

  // State
  const [error,   setError]   = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  function switchTab(t: Tab) {
    setTab(t);
    setError("");
    setSuccess("");
    setUsername("");
    setPassword("");
    setConfirm("");
  }

  function handleLogin(e: FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password) return;
    setLoading(true);
    setError("");
    setTimeout(() => {
      const ok = login(username, password);
      if (!ok) setError("Incorrect username or password.");
      setLoading(false);
    }, 350);
  }

  function handleSignup(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!username.trim() || !password) return;
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    setTimeout(() => {
      const result = signup(username, password);
      if (!result.ok) {
        setError(result.error ?? "Sign-up failed.");
      }
      // On success AuthContext auto-logs in → App redirects away.
      setLoading(false);
    }, 350);
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background orbs */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-violet-600/20 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-5%]  w-[400px] h-[400px] rounded-full bg-indigo-700/20  blur-[100px]" />
      </div>

      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-violet-500/15 border border-violet-500/25 backdrop-blur-xl flex items-center justify-center mx-auto mb-4 text-3xl shadow-lg shadow-violet-500/10">
            🌐
          </div>
          <h1 className="text-2xl font-bold text-white">Polyglot Voice Companion</h1>
          <p className="text-white/35 text-sm mt-1">Multilingual voice agent — runs fully local</p>
        </div>

        {/* Card */}
        <div className="glass-card overflow-hidden">
          {/* Tab bar */}
          <div className="flex border-b border-white/[0.08]">
            {(["login", "signup"] as Tab[]).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => switchTab(t)}
                className={`flex-1 py-3 text-sm font-medium transition-colors ${
                  tab === t
                    ? "text-violet-400 border-b-2 border-violet-400 bg-violet-500/[0.06]"
                    : "text-white/40 hover:text-white/70"
                }`}
              >
                {t === "login" ? "Sign In" : "Sign Up"}
              </button>
            ))}
          </div>

          {/* Form body */}
          <form
            onSubmit={tab === "login" ? handleLogin : handleSignup}
            className="p-6 space-y-4"
          >
            {/* Username */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/55 uppercase tracking-wider">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={tab === "login" ? "admin" : "choose a username"}
                autoComplete="username"
                required
                minLength={3}
                className="input"
                disabled={loading}
              />
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/55 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPass ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete={tab === "login" ? "current-password" : "new-password"}
                  required
                  minLength={6}
                  className="input pr-14"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors text-xs"
                >
                  {showPass ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {/* Confirm password — signup only */}
            {tab === "signup" && (
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-white/55 uppercase tracking-wider">
                  Confirm Password
                </label>
                <input
                  type={showPass ? "text" : "password"}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="new-password"
                  required
                  className="input"
                  disabled={loading}
                />
              </div>
            )}

            {/* Error / success banners */}
            {error && (
              <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                {error}
              </p>
            )}
            {success && (
              <p className="text-green-400 text-sm bg-green-500/10 border border-green-500/20 rounded-xl px-3 py-2">
                {success}
              </p>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={
                loading ||
                !username.trim() ||
                !password ||
                (tab === "signup" && !confirm)
              }
              className="btn-primary w-full py-2.5 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {tab === "login" ? "Signing in…" : "Creating account…"}
                </>
              ) : tab === "login" ? (
                "Sign In"
              ) : (
                "Create Account"
              )}
            </button>

            {/* Footer hint */}
            <p className="text-center text-xs text-white/20">
              {tab === "login" ? (
                <>
                  No account?{" "}
                  <button type="button" onClick={() => switchTab("signup")} className="text-violet-400/70 hover:text-violet-400 underline underline-offset-2">
                    Sign up free
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{" "}
                  <button type="button" onClick={() => switchTab("login")} className="text-violet-400/70 hover:text-violet-400 underline underline-offset-2">
                    Sign in
                  </button>
                </>
              )}
            </p>

            {tab === "login" && (
              <p className="text-center text-[11px] text-white/20">
                Default account: <span className="text-white/35">admin / polyglot123</span>
              </p>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
