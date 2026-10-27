import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { api, getTokens, onTokens, setTokens, type Role, type Tokens } from "../api/client";
import { setPreview } from "../api/preview";
import type { User } from "../api/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  preview: (role: Role) => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const [tokens, setLocal] = useState(getTokens());
  useEffect(() => onTokens(setLocal), []);

  const me = useQuery({
    queryKey: ["me", tokens?.access_token ? "auth" : "anon"],
    queryFn: () => api<User>("/auth/me"),
    enabled: Boolean(tokens),
    retry: false,
  });

  const login = async (email: string, password: string) => {
    setTokens(await api<Tokens>("/auth/login", { json: { email, password } }));
    await qc.invalidateQueries();
  };
  const register = async (email: string, password: string, fullName: string) => {
    setTokens(
      await api<Tokens>("/auth/register", { json: { email, password, full_name: fullName } }),
    );
    await qc.invalidateQueries();
  };
  const preview = async (role: Role) => {
    setPreview(role);
    setTokens({ access_token: "preview", refresh_token: "preview", role });
    await qc.invalidateQueries();
  };
  const logout = () => {
    setPreview(null);
    setTokens(null);
    qc.clear();
  };

  const value: AuthState = {
    user: tokens ? (me.data ?? null) : null,
    loading: Boolean(tokens) && me.isPending,
    login,
    register,
    logout,
    preview,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}
