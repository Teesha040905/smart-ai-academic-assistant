"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { api, clearToken, getToken, setToken } from "./api";
import { TokenResponse, User } from "./types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshUser = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      return;
    }
    const me = await api.get<User>("/auth/me");
    setUser(me);
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        if (getToken()) await refreshUser();
      } catch {
        clearToken();
        setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.post<TokenResponse>(
        "/auth/login",
        { email, password },
        false
      );
      setToken(res.access_token);
      await refreshUser();
      router.replace("/dashboard");
    },
    [refreshUser, router]
  );

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      await api.post<User>(
        "/auth/register",
        { email, password, full_name: fullName },
        false
      );
      await login(email, password);
    },
    [login]
  );

  const logout = useCallback(async () => {
    try {
      if (getToken()) await api.post("/auth/logout");
    } catch {
      /* ignore */
    }
    clearToken();
    setUser(null);
    router.replace("/login");
  }, [router]);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
