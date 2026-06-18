"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { Session, User } from "@supabase/supabase-js";

interface LocalAuthError {
  message: string;
}

interface AuthContextValue {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signInWithEmail: (email: string, password: string) => Promise<{ error: LocalAuthError | null }>;
  signUpWithEmail: (email: string, password: string) => Promise<{ error: LocalAuthError | null }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// Helper to generate a mock JWT token that can be parsed by the backend
function generateMockJwt(userId: string, email: string): string {
  const header = { alg: "HS256", typ: "JWT" };
  const payload = { sub: userId, email: email, aud: "authenticated" };
  
  const base64Header = btoa(JSON.stringify(header))
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
  const base64Payload = btoa(JSON.stringify(payload))
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
    
  return `${base64Header}.${base64Payload}.dummy_signature`;
}

interface LocalUser {
  id: string;
  email: string;
  password?: string;
}

/**
 * Mock Auth Provider that runs 100% locally using LocalStorage.
 * Mimics Supabase authentication and session logic.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  /* ── Hydrate session on mount ───────────────────────────── */
  useEffect(() => {
    const saved = localStorage.getItem("promethicc_session");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setUser(parsed.user);
        setSession(parsed);
      } catch {
        localStorage.removeItem("promethicc_session");
      }
    }
    setLoading(false);
  }, []);

  /* ── Auth actions ────────────────────────────────────────── */
  const signInWithEmail = useCallback(async (email: string, password: string) => {
    // Read all local users
    const usersRaw = localStorage.getItem("promethicc_users");
    const users: LocalUser[] = usersRaw ? JSON.parse(usersRaw) : [];

    const matchedUser = users.find(
      (u: LocalUser) => u.email.toLowerCase() === email.toLowerCase() && u.password === password
    );

    if (!matchedUser) {
      return { error: { message: "Invalid email or password." } };
    }

    const mockUser: User = {
      id: matchedUser.id,
      email: matchedUser.email,
      aud: "authenticated",
      role: "authenticated",
      created_at: new Date().toISOString(),
      app_metadata: {},
      user_metadata: {},
    };

    const token = generateMockJwt(mockUser.id, mockUser.email!);

    const mockSession: Session = {
      access_token: token,
      refresh_token: "mock-refresh",
      expires_in: 3600,
      token_type: "bearer",
      user: mockUser,
    };

    localStorage.setItem("promethicc_session", JSON.stringify(mockSession));
    setUser(mockUser);
    setSession(mockSession);

    return { error: null };
  }, []);

  const signUpWithEmail = useCallback(async (email: string, password: string) => {
    // Read all local users
    const usersRaw = localStorage.getItem("promethicc_users");
    const users: LocalUser[] = usersRaw ? JSON.parse(usersRaw) : [];

    const exists = users.some((u: LocalUser) => u.email.toLowerCase() === email.toLowerCase());
    if (exists) {
      return { error: { message: "A user with this email already exists." } };
    }

    const newUser: LocalUser = {
      id: crypto.randomUUID(),
      email,
      password,
    };

    users.push(newUser);
    localStorage.setItem("promethicc_users", JSON.stringify(users));

    // Sign in immediately
    const mockUser: User = {
      id: newUser.id,
      email: newUser.email,
      aud: "authenticated",
      role: "authenticated",
      created_at: new Date().toISOString(),
      app_metadata: {},
      user_metadata: {},
    };

    const token = generateMockJwt(mockUser.id, mockUser.email || "");

    const mockSession: Session = {
      access_token: token,
      refresh_token: "mock-refresh",
      expires_in: 3600,
      token_type: "bearer",
      user: mockUser,
    };

    localStorage.setItem("promethicc_session", JSON.stringify(mockSession));
    setUser(mockUser);
    setSession(mockSession);

    return { error: null };
  }, []);

  const signOut = useCallback(async () => {
    localStorage.removeItem("promethicc_session");
    setUser(null);
    setSession(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, session, loading, signInWithEmail, signUpWithEmail, signOut }),
    [user, session, loading, signInWithEmail, signUpWithEmail, signOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
