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
const USERS_KEY   = "polyglot_users"; // { [username]: hashedPassword }

// ── Default users seeded on first load ──────────────────────────────────────
const DEFAULT_USERS: Record<string, string> = {
  admin: "polyglot123",
  alice: "alice123",
  bob:   "bob123",
};

// ── User registry helpers ────────────────────────────────────────────────────

function loadUsers(): Record<string, string> {
  try {
    const raw = localStorage.getItem(USERS_KEY);
    const parsed: Record<string, string> = raw ? JSON.parse(raw) : {};
    // Always ensure default users exist (handles first-run and migrations)
    let changed = Object.keys(parsed).length === 0;
    for (const [k, v] of Object.entries(DEFAULT_USERS)) {
      if (!parsed[k]) { parsed[k] = v; changed = true; }
    }
    if (changed) localStorage.setItem(USERS_KEY, JSON.stringify(parsed));
    return parsed;
  } catch {
    localStorage.setItem(USERS_KEY, JSON.stringify(DEFAULT_USERS));
    return { ...DEFAULT_USERS };
  }
}

function saveUsers(users: Record<string, string>) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

// ── Per-user data helpers (exported for use in other components) ─────────────

export function getUserChatsKey(username: string): string {
  return `polyglot_chats_${username}`;
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

