import { createContext, useContext, useEffect, useMemo, useState } from "react";
import api, { clearTokens, getAccessToken, getRefreshToken, setTokens } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = async () => {
    try {
      const response = await api.get("/me");
      setUser(response.data);
    } catch (error) {
      setUser(null);
      clearTokens();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (getAccessToken()) {
      fetchMe();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (identifier, password) => {
    const response = await api.post("/login", { identifier, password });
    setTokens(response.data);
    setUser(response.data.user);
    return response.data.user;
  };

  const logout = async () => {
    try {
      const refresh = getRefreshToken();
      if (refresh) {
        await api.post("/logout", { refresh });
      }
    } catch (error) {
      // Ignore backend logout errors, clear local session anyway.
    } finally {
      clearTokens();
      setUser(null);
    }
  };

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      logout,
      fetchMe
    }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
