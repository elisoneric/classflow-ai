import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import axios from "axios";
import { apiClient, API_BASE_URL } from "@/lib/api-client";
import { setAccessToken } from "@/lib/token-store";

interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Silent refresh on load — relies on the httpOnly refresh cookie set by
    // a previous /auth/login. No cookie (or an expired one) just means
    // "not logged in", not an error worth surfacing.
    axios
      .post<{ access_token: string }>(
        `${API_BASE_URL}/auth/refresh`,
        {},
        { withCredentials: true },
      )
      .then((res) => {
        setAccessToken(res.data.access_token);
        setIsAuthenticated(true);
      })
      .catch(() => {
        setAccessToken(null);
        setIsAuthenticated(false);
      })
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const res = await apiClient.post<{ access_token: string }>("/auth/login", {
      email,
      password,
    });
    setAccessToken(res.data.access_token);
    setIsAuthenticated(true);
  }

  async function logout() {
    try {
      await apiClient.post("/auth/logout");
    } finally {
      setAccessToken(null);
      setIsAuthenticated(false);
    }
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
