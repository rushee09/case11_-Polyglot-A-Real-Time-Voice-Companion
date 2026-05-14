import { createContext, useContext, useState, ReactNode } from "react";

interface AuthUser {
  username: string;
}

interface AuthContextType {
  user: AuthUser | null;
  login: (username: string, password: string) => boolean;
  signup: (username: string, password: string) => { ok: boolean; error?: string };
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const SESSION_KEY = "polyglot_auth";
const USERS_KEY   = "polyglot_users"; // { [username]: password }

// ── User registry helpers ────────────────────────────────────────────────────

function loadUsers(): Record<string, string> {
  try {
    const raw = localStorage.getItem(USERS_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    // Seed a default admin if the registry is empty
    if (Object.keys(parsed).length === 0) {
      const seed = { admin: "polyglot123" };
      localStorage.setItem(USERS_KEY, JSON.stringify(seed));
      return seed;
    }
    return parsed;
  } catch {
    return { admin: "polyglot123" };
  }
}

function saveUsers(users: Record<string, string>) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

// ── Provider ─────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  function login(username: string, password: string): boolean {
    const key = username.trim().toLowerCase();
    const users = loadUsers();
    if (users[key] === password) {
      const u: AuthUser = { username: key };
      setUser(u);
      localStorage.setItem(SESSION_KEY, JSON.stringify(u));
      return true;
    }
    return false;
  }

  function signup(username: string, password: string): { ok: boolean; error?: string } {
    const key = username.trim().toLowerCase();
    if (key.length < 3) return { ok: false, error: "Username must be at least 3 characters." };
    if (password.length < 6) return { ok: false, error: "Password must be at least 6 characters." };

    const users = loadUsers();
    if (users[key]) return { ok: false, error: "Username is already taken." };

    users[key] = password;
    saveUsers(users);

    // Auto-login after successful signup
    const u: AuthUser = { username: key };
    setUser(u);
    localStorage.setItem(SESSION_KEY, JSON.stringify(u));
    return { ok: true };
  }

  function logout() {
    setUser(null);
    localStorage.removeItem(SESSION_KEY);
  }

  return (
    <AuthContext.Provider value={{ user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}

