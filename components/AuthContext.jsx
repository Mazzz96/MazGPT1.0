// --- MazGPT AuthContext: JWT, session, and persistent chat/project state ---
import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";

const AuthContext = createContext();
const LOCAL_KEY = "mazgpt_user_data";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [userData, setUserData] = useState(null); // { projects, projectMessages, preferences }
  const navigate = useNavigate();
  const [refreshTimer, setRefreshTimer] = useState(null);

  // --- Persistence helpers ---
  // Save userData to localStorage
  const saveUserData = (data) => {
    if (user?.email) {
      localStorage.setItem(LOCAL_KEY + ":" + user.email, JSON.stringify(data));
    }
  };
  // Load userData from localStorage
  const loadUserData = (email) => {
    const raw = localStorage.getItem(LOCAL_KEY + ":" + email);
    return raw ? JSON.parse(raw) : null;
  };
  // Clear userData from localStorage
  const clearUserData = (email) => {
    localStorage.removeItem(LOCAL_KEY + ":" + email);
  };

  // --- Token refresh scheduling ---
  const scheduleRefresh = useCallback(() => {
    if (refreshTimer) clearTimeout(refreshTimer);
    const timer = setTimeout(() => refresh(), 25 * 60 * 1000);
    setRefreshTimer(timer);
  }, [refreshTimer]);

  // --- On mount: check session, load userData ---
  useEffect(() => {
    fetch("/auth/me", { credentials: "include" })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        setUser(data?.email ? data : null);
        setLoading(false);
        if (data?.email) {
          scheduleRefresh();
          setUserData(loadUserData(data.email));
        }
      })
      .catch(() => setLoading(false));
    return () => refreshTimer && clearTimeout(refreshTimer);
  }, []);

  // --- Login handler ---
  const login = useCallback(async (email, password) => {
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password })
      });
      if (!res.ok) {
        const msg = (await res.json())?.detail || "Invalid credentials";
        setError(msg);
        throw new Error(msg);
      }
      const data = await res.json();
      setUser(data.user);
      scheduleRefresh();
      setUserData(loadUserData(data.user.email));
      setLoading(false);
      return data.user;
    } catch (err) {
      setLoading(false);
      throw err;
    }
  }, [scheduleRefresh]);

  // --- Logout handler ---
  const logout = useCallback(async () => {
    setLoading(true);
    await fetch("/auth/logout", { method: "POST", credentials: "include" });
    if (user?.email) saveUserData(userData); // Save before logout
    setUser(null);
    setUserData(null);
    setError("");
    if (refreshTimer) clearTimeout(refreshTimer);
    setLoading(false);
    navigate("/login");
  }, [refreshTimer, navigate, user, userData]);

  // --- Token refresh (auto) ---
  const refresh = useCallback(async () => {
    setLoading(true);
    await fetch("/auth/refresh-token", { method: "POST", credentials: "include" });
    const res = await fetch("/auth/me", { credentials: "include" });
    setUser(res.ok ? await res.json() : null);
    scheduleRefresh();
    setLoading(false);
  }, [scheduleRefresh]);

  // --- Save userData on change ---
  useEffect(() => {
    if (user?.email && userData) saveUserData(userData);
  }, [user, userData]);

  // --- Expose helpers to update userData (projects, messages, preferences) ---
  const updateUserData = (patch) => {
    setUserData(prev => ({ ...prev, ...patch }));
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout, refresh, userData, setUserData, updateUserData }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
