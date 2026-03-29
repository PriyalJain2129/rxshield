import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { User, getCurrentUser, login as apiLogin, signup as apiSignup, logout as apiLogout } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("rxshield_session");
    if (stored) {
      getCurrentUser().then(setUser).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const u = await apiLogin(email, password);
    setUser(u);
    localStorage.setItem("rxshield_session", "true");
  };

  const signup = async (name: string, email: string, password: string) => {
    const u = await apiSignup(name, email, password);
    setUser(u);
    localStorage.setItem("rxshield_session", "true");
  };

  const logout = async () => {
    await apiLogout();
    setUser(null);
    localStorage.removeItem("rxshield_session");
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
