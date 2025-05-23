import React, { useState, useEffect } from "react";
import BubbleChat from "./components/BubbleChat";
import "./components/BubbleChat.css";
import { AuthProvider, useAuth } from "./components/AuthContext";
import Auth from "./components/Auth";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";

// Simple error boundary for debugging
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    // You can log errorInfo here
  }
  render() {
    if (this.state.hasError) {
      return <div style={{ color: 'red', padding: 20 }}>Frontend Error: {this.state.error && this.state.error.toString()}</div>;
    }
    return this.props.children;
  }
}

function ProtectedApp() {
  const { user, loading, logout, userData, updateUserData } = useAuth();
  const defaultProjects = [{ id: "default", name: "Default" }];
  const [projects, setProjects] = useState(userData?.projects || defaultProjects);
  const [projectId, setProjectId] = useState(projects[0]?.id || "default");
  const [projectMessages, setProjectMessages] = useState(userData?.projectMessages || { default: [
    { sender: "ai", text: "Hello! I'm MazGPT 👋" },
    { sender: "user", text: "Hi! You look cute." },
    { sender: "ai", text: "Thank you! Tap my face to chat with me." }
  ] });
  const [preferences, setPreferences] = useState(userData?.preferences || {
    theme: "light", language: "en", tone: "friendly", fontSize: 16
  });

  // --- Sync userData to AuthContext on change ---
  useEffect(() => {
    updateUserData({ projects, projectMessages, preferences });
  }, [projects, projectMessages, preferences]);

  // --- Sync from userData on login ---
  useEffect(() => {
    if (userData) {
      setProjects(userData.projects || defaultProjects);
      setProjectMessages(userData.projectMessages || { default: [] });
      setPreferences(userData.preferences || { theme: "light", language: "en", tone: "friendly", fontSize: 16 });
      setProjectId(userData.projects?.[0]?.id || "default");
    }
  }, [userData]);

  // --- Message helpers ---
  const messages = projectMessages[projectId] || [];
  const setMessages = (msgs) => setProjectMessages(prev => ({ ...prev, [projectId]: msgs }));

  // --- Project management helpers ---
  const handleSetProjects = (newProjects) => {
    setProjects(newProjects);
    newProjects.forEach((p) => {
      if (!(p.id in projectMessages)) {
        setProjectMessages((prev) => ({ ...prev, [p.id]: [] }));
      }
    });
    const validIds = new Set(newProjects.map((p) => p.id));
    setProjectMessages((prev) => {
      const next = {};
      for (const id of Object.keys(prev)) {
        if (validIds.has(id)) next[id] = prev[id];
      }
      return next;
    });
    if (!newProjects.some(p => p.id === projectId)) setProjectId(newProjects[0]?.id || "default");
  };

  if (loading) return <div>Loading...</div>;
  if (!user) return <Auth />;
  // Always show the floating robot face/chat UI
  return (
    <>
      <button style={{ position: "absolute", top: 10, right: 10, zIndex: 1000 }} onClick={logout}>Logout</button>
      <BubbleChat
        projectId={projectId}
        setProjectId={setProjectId}
        projects={projects}
        setProjects={handleSetProjects}
        messages={messages}
        setMessages={setMessages}
        preferences={preferences}
        setPreferences={setPreferences}
      />
    </>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Auth />} />
            <Route path="/" element={<ProtectedRoute><ProtectedApp /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
