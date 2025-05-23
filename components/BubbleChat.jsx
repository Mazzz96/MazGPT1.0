import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "./AuthContext";
import "./BubbleChat.css";
import QRCode from "qrcode.react"; // For TOTP QR code display (install with npm if needed)

const defaultProjects = [
  { id: "default", name: "Default" }
];

export default function BubbleChat({ projectId, setProjectId, projects, setProjects, messages, setMessages, preferences, setPreferences }) {
  const { user, refresh, logout } = useAuth();
  const [expanded, setExpanded] = useState(false);
  const [input, setInput] = useState("");
  const [newProjectName, setNewProjectName] = useState("");
  const [renaming, setRenaming] = useState(null);
  const [renameValue, setRenameValue] = useState("");
  const [showPrefs, setShowPrefs] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [importing, setImporting] = useState(false);
  const [importText, setImportText] = useState("");
  const [archivedProjects, setArchivedProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [aiTyping, setAiTyping] = useState(false);
  const [show2FA, setShow2FA] = useState(false);
  const [twofaStatus, setTwofaStatus] = useState(null); // {enabled, type}
  const [twofaType, setTwofaType] = useState("totp");
  const [twofaSecret, setTwofaSecret] = useState("");
  const [twofaQr, setTwofaQr] = useState("");
  const [twofaCode, setTwofaCode] = useState("");
  const [twofaMsg, setTwofaMsg] = useState("");
  const [twofaLogin, setTwofaLogin] = useState(null); // {email, type}
  const scrollRef = useRef(null);

  // --- Helper: Read CSRF token from cookie ---
  function getCSRFToken() {
    const match = document.cookie.match(/(?:^|; )mazgpt-csrf=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  // --- Helper: Authenticated fetch with CSRF support ---
  const fetchWithAuth = async (url, options = {}) => {
    const method = (options.method || "GET").toUpperCase();
    const isStateChanging = ["POST", "PUT", "DELETE", "PATCH"].includes(method);
    const headers = { ...(options.headers || {}) };
    if (isStateChanging) {
      headers["x-csrf-token"] = getCSRFToken();
    }
    let res = await fetch(url, { ...options, headers, credentials: "include" });
    if (res.status === 401) {
      await refresh();
      res = await fetch(url, { ...options, headers, credentials: "include" });
      if (res.status === 401) {
        logout();
        throw new Error("Session expired. Please log in again.");
      }
    }
    return res;
  };

  // --- Fetch chat history for current project on mount or project change ---
  useEffect(() => {
    if (!user) return;
    setLoading(true);
    setError("");
    fetchWithAuth(`/user/export-data`)
      .then(res => res.ok ? res.json() : Promise.reject(res))
      .then(data => {
        const chat = data.chats?.find(c => c.project_id === projectId);
        setMessages(chat ? chat.messages : []);
        setLoading(false);
      })
      .catch(err => {
        setError("Failed to load chat history.");
        setLoading(false);
      });
    // eslint-disable-next-line
  }, [projectId, user]);

  // --- Send message to backend and get AI response ---
  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setError("");
    setMessages([...messages, { sender: "user", text: input }]);
    setInput("");
    setAiTyping(true);
    setLoading(true);
    try {
      // Example: POST to /chat/send (replace with your actual endpoint)
      const res = await fetchWithAuth(`/chat/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId, message: input })
      });
      if (!res.ok) throw new Error("Failed to send message");
      const data = await res.json();
      setMessages([...messages, { sender: "user", text: input }, { sender: "ai", text: data.reply }]);
    } catch (err) {
      setError(err.message || "Failed to send message");
    } finally {
      setAiTyping(false);
      setLoading(false);
    }
  };

  // --- Project management handlers (add API calls as needed) ---
  const handleProjectChange = (e) => setProjectId(e.target.value);
  const handleCreateProject = () => {
    const name = newProjectName.trim();
    if (!name) return;
    const id = name.toLowerCase().replace(/[^a-z0-9]+/g, "-");
    if (projects.some(p => p.id === id)) return;
    setProjects([...projects, { id, name }]);
    setProjectId(id);
    setNewProjectName("");
  };
  const handleDeleteProject = (id) => {
    if (id === "default") return;
    setProjects(projects.filter(p => p.id !== id));
    if (projectId === id) setProjectId("default");
  };
  const handleRenameProject = (id) => {
    setRenaming(id);
    setRenameValue(projects.find(p => p.id === id)?.name || "");
  };
  const handleRenameSubmit = (id) => {
    setProjects(projects.map(p => p.id === id ? { ...p, name: renameValue } : p));
    setRenaming(null);
    setRenameValue("");
  };

  // New chat: clears messages for current project
  const handleNewChat = () => setMessages([]);

  // Archive project: move to archived list and switch to default
  const handleArchiveProject = (id) => {
    if (id === "default") return;
    setArchivedProjects([...archivedProjects, id]);
    setProjects(projects.filter(p => p.id !== id));
    if (projectId === id) setProjectId("default");
  };

  // Export chat: download messages as JSON
  const handleExport = () => {
    const data = JSON.stringify(messages, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${projectId}-chat.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Import chat: parse JSON and replace messages
  const handleImport = () => {
    try {
      const parsed = JSON.parse(importText);
      if (Array.isArray(parsed)) setMessages(parsed);
      setImporting(false);
      setImportText("");
    } catch {
      alert("Invalid JSON");
    }
  };

  // Search messages in current chat
  const filteredMessages = showSearch && searchTerm.trim()
    ? messages.filter(m => m.text.toLowerCase().includes(searchTerm.toLowerCase()))
    : messages;

  // --- Smooth scroll to latest message ---
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, aiTyping]);

  // --- UI logic for opacity and background overlay ---
  const chatOpacity = expanded ? 0.95 : 0.5;
  const bgOverlay = expanded ? "bubblechat-modal" : "";

  // --- 2FA: Fetch status on mount or user change ---
  useEffect(() => {
    if (!user) return;
    fetchWithAuth("/auth/2fa/status")
      .then(res => res.ok ? res.json() : Promise.reject(res))
      .then(setTwofaStatus)
      .catch(() => setTwofaStatus(null));
  }, [user]);

  // --- 2FA: Enable ---
  const handleEnable2FA = async () => {
    setTwofaMsg("");
    setTwofaSecret("");
    setTwofaQr("");
    try {
      const res = await fetchWithAuth("/auth/2fa/enable", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: twofaType })
      });
      const data = await res.json();
      if (data.type === "totp") {
        setTwofaSecret(data.secret);
        setTwofaQr(data.otpauth_url);
        setTwofaMsg("Scan QR with your authenticator app, then enter a code to verify.");
      } else if (data.type === "email") {
        setTwofaMsg("A code was sent to your email. Enter it below to verify.");
      }
    } catch (e) {
      setTwofaMsg("Failed to enable 2FA");
    }
  };

  // --- 2FA: Verify (for setup) ---
  const handleVerify2FA = async () => {
    setTwofaMsg("");
    try {
      const res = await fetchWithAuth("/auth/2fa/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: twofaCode, type: twofaType })
      });
      if (res.ok) {
        setTwofaMsg("2FA enabled and verified!");
        setTwofaStatus({ enabled: true, type: twofaType });
        setTwofaSecret(""); setTwofaQr(""); setTwofaCode("");
      } else {
        setTwofaMsg("Invalid code. Try again.");
      }
    } catch {
      setTwofaMsg("Failed to verify 2FA");
    }
  };

  // --- 2FA: Disable ---
  const handleDisable2FA = async () => {
    setTwofaMsg("");
    try {
      const res = await fetchWithAuth("/auth/2fa/disable", { method: "POST" });
      if (res.ok) {
        setTwofaMsg("2FA disabled.");
        setTwofaStatus({ enabled: false });
      } else {
        setTwofaMsg("Failed to disable 2FA");
      }
    } catch {
      setTwofaMsg("Failed to disable 2FA");
    }
  };

  // --- 2FA: Login flow ---
  // Patch login logic: if backend returns {ok: false, 2fa_required: true}, show 2FA code prompt
  // (Assume login logic is in AuthContext or similar; here is a sample handler)
  // Example usage: setTwofaLogin({ email, type }) and show 2FA code input
  const handle2FALogin = async () => {
    setTwofaMsg("");
    try {
      const res = await fetch("/auth/2fa/login-verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: twofaLogin.email, code: twofaCode, type: twofaLogin.type })
      });
      if (res.ok) {
        setTwofaMsg("2FA login successful!");
        setTwofaLogin(null);
        // Optionally refresh user/session here
        window.location.reload();
      } else {
        setTwofaMsg("Invalid 2FA code.");
      }
    } catch {
      setTwofaMsg("2FA login failed");
    }
  };

  // --- 2FA UI panel (for settings/profile) ---
  const render2FAPanel = () => (
    <div style={{ background: "#f8f8ff", borderRadius: 10, padding: 16, margin: 8, maxWidth: 400 }}>
      <h3>Two-Factor Authentication (2FA)</h3>
      {twofaStatus?.enabled ? (
        <>
          <div>2FA is <b>enabled</b> ({twofaStatus.type})</div>
          <button onClick={handleDisable2FA} style={{ marginTop: 8 }}>Disable 2FA</button>
        </>
      ) : (
        <>
          <div>2FA is <b>not enabled</b>.</div>
          <select value={twofaType} onChange={e => setTwofaType(e.target.value)} style={{ marginTop: 8 }}>
            <option value="totp">Authenticator App (TOTP)</option>
            <option value="email">Email Code</option>
          </select>
          <button onClick={handleEnable2FA} style={{ marginLeft: 8 }}>Enable 2FA</button>
        </>
      )}
      {twofaQr && (
        <div style={{ marginTop: 12 }}>
          <div>Scan this QR code in your authenticator app:</div>
          <QRCode value={twofaQr} size={160} />
          <div style={{ fontSize: 12, marginTop: 4 }}>Or enter secret: <b>{twofaSecret}</b></div>
        </div>
      )}
      {(twofaQr || twofaType === "email") && (
        <div style={{ marginTop: 12 }}>
          <input
            type="text"
            value={twofaCode}
            onChange={e => setTwofaCode(e.target.value)}
            placeholder="Enter 2FA code"
            style={{ fontSize: 16, borderRadius: 6, padding: "4px 10px", width: 140 }}
          />
          <button onClick={handleVerify2FA} style={{ marginLeft: 8 }}>Verify</button>
        </div>
      )}
      {twofaMsg && <div style={{ color: twofaMsg.includes("success") ? "green" : "#c00", marginTop: 8 }}>{twofaMsg}</div>}
    </div>
  );

  // --- 2FA login prompt (if required) ---
  const render2FALogin = () => (
    <div style={{ background: "#fffbe6", borderRadius: 10, padding: 16, margin: 8, maxWidth: 400 }}>
      <h3>2FA Verification Required</h3>
      <div>Enter the code from your {twofaLogin?.type === "totp" ? "authenticator app" : "email"}:</div>
      <input
        type="text"
        value={twofaCode}
        onChange={e => setTwofaCode(e.target.value)}
        placeholder="2FA code"
        style={{ fontSize: 16, borderRadius: 6, padding: "4px 10px", width: 140, marginTop: 8 }}
      />
      <button onClick={handle2FALogin} style={{ marginLeft: 8 }}>Verify</button>
      {twofaMsg && <div style={{ color: twofaMsg.includes("success") ? "green" : "#c00", marginTop: 8 }}>{twofaMsg}</div>}
    </div>
  );

  return (
    <div className={`bubblechat-container ${bgOverlay} ${preferences.theme === "dark" ? "bubblechat-dark" : ""}`}> 
      {/* Project selector UI */}
      <div className="bubblechat-projectbar" style={{ display: expanded ? "flex" : "none", alignItems: "center", gap: 8, padding: 8, background: "rgba(255,255,255,0.85)", borderRadius: 12, marginBottom: 4 }}>
        <span style={{ fontWeight: 600, color: "#222" }}>Project:</span>
        <select value={projectId} onChange={handleProjectChange} style={{ fontSize: 15, borderRadius: 6, padding: "2px 8px" }}>
          {projects.map(p => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
        <input type="text" value={newProjectName} onChange={e => setNewProjectName(e.target.value)} placeholder="New project name" style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px" }} />
        <button onClick={handleCreateProject} style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px", background: "#00bfff", color: "#fff", border: "none" }}>Create</button>
        <button onClick={handleNewChat} style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px", marginLeft: 4, background: "#eee", color: "#222", border: "none" }}>New Chat</button>
        <button onClick={() => setShowSearch(v => !v)} style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px", marginLeft: 4, background: showSearch ? "#00bfff" : "#eee", color: showSearch ? "#fff" : "#222", border: "none" }}>Search</button>
        <button onClick={handleExport} style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px", marginLeft: 4, background: "#eee", color: "#222", border: "none" }}>Export</button>
        <button onClick={() => setImporting(v => !v)} style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px", marginLeft: 4, background: importing ? "#00bfff" : "#eee", color: importing ? "#fff" : "#222", border: "none" }}>Import</button>
        <button onClick={() => handleArchiveProject(projectId)} style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px", marginLeft: 4, background: "#eee", color: "#c00", border: "none" }}>Archive</button>
        <button onClick={() => setShowPrefs((v) => !v)} style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px", marginLeft: 8, background: preferences.theme === "dark" ? "#333" : "#eee", color: preferences.theme === "dark" ? "#fff" : "#222", border: "none" }}>⚙️ Settings</button>
        {projects.map(p => p.id !== "default" && (
          <span key={p.id} style={{ marginLeft: 6 }}>
            {renaming === p.id ? (
              <>
                <input value={renameValue} onChange={e => setRenameValue(e.target.value)} style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px" }} />
                <button onClick={() => handleRenameSubmit(p.id)} style={{ fontSize: 13, marginLeft: 2 }}>OK</button>
                <button onClick={() => setRenaming(null)} style={{ fontSize: 13, marginLeft: 2 }}>Cancel</button>
              </>
            ) : (
              <>
                <button onClick={() => handleRenameProject(p.id)} style={{ fontSize: 13, marginLeft: 2 }}>Rename</button>
                <button onClick={() => handleDeleteProject(p.id)} style={{ fontSize: 13, marginLeft: 2, color: "#c00" }}>Delete</button>
              </>
            )}
          </span>
        ))}
      </div>
      {/* Error and loading indicators */}
      {error && <div className="bubblechat-error">{error}</div>}
      {loading && <div className="bubblechat-loading">Loading...</div>}
      {/* Import panel */}
      {importing && expanded && (
        <div style={{ background: "#fffbe6", color: "#222", borderRadius: 10, padding: 10, marginBottom: 8 }}>
          <textarea value={importText} onChange={e => setImportText(e.target.value)} rows={4} style={{ width: "100%", fontSize: 14, borderRadius: 6, marginBottom: 4 }} placeholder="Paste exported chat JSON here..." />
          <button onClick={handleImport} style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px", background: "#00bfff", color: "#fff", border: "none" }}>Import</button>
          <button onClick={() => setImporting(false)} style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px", marginLeft: 4, background: "#eee", color: "#222", border: "none" }}>Cancel</button>
        </div>
      )}
      {/* Search bar */}
      {showSearch && expanded && (
        <div style={{ background: "#eef", color: "#222", borderRadius: 10, padding: 8, marginBottom: 8 }}>
          <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="Search messages..." style={{ fontSize: 14, borderRadius: 6, padding: "2px 8px", width: "80%" }} />
        </div>
      )}
      <div
        className={`ai-face${expanded ? " expanded" : ""}`}
        onClick={handleFaceClick}
        title={expanded ? "Minimize" : "Open chat"}
        style={{
          opacity: expanded ? 1 : 0.5,
          transition: "all 0.4s cubic-bezier(.72,1.53,.63,1.08)"
        }}
      >
        {/* WALL-E-inspired SVG face */}
        <svg width={expanded ? 140 : 56} height={expanded ? 70 : 28} viewBox="0 0 180 90">
          <rect x="20" y="20" rx="30" ry="30" width="140" height="60" fill="#c0c0c0" stroke="#999" strokeWidth="3"/>
          <ellipse cx="60" cy="55" rx="28" ry="28" fill="#444"/>
          <ellipse cx="120" cy="55" rx="28" ry="28" fill="#444"/>
          <ellipse cx="60" cy="55" rx="18" ry="18" fill="#fff"/>
          <ellipse cx="120" cy="55" rx="18" ry="18" fill="#fff"/>
          <ellipse cx="60" cy="55" rx="7" ry="7" fill="#00bfff"/>
          <ellipse cx="120" cy="55" rx="7" ry="7" fill="#00bfff"/>
          <ellipse cx="63" cy="52" rx="2" ry="4" fill="#fff" opacity="0.8"/>
          <ellipse cx="123" cy="52" rx="2" ry="4" fill="#fff" opacity="0.8"/>
          <path d="M75,80 Q90,90 105,80" stroke="#777" strokeWidth="3" fill="none"/>
        </svg>
      </div>

      {/* Chat bubble/message area */}
      <div
        className={`bubblechat-bubbles${expanded ? " expanded" : ""}`}
        style={{ opacity: chatOpacity, fontSize: preferences.fontSize }}
        aria-label="Chat messages area"
      >
        <div className="bubblechat-scroll" ref={scrollRef}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`bubblechat-bubble ${msg.sender === "ai" ? "left" : "right"}${expanded ? " vivid" : ""}`}
              aria-label={msg.sender === "ai" ? "MazGPT reply" : "Your message"}
            >
              {msg.text}
            </div>
          ))}
          {aiTyping && <div className="bubblechat-bubble left typing" role="status" aria-live="polite">MazGPT is typing…</div>}
        </div>
        {error && <div className="bubblechat-error" role="alert" aria-live="assertive">{error}</div>}
        {/* Message input bar */}
        <form className="bubblechat-inputbar" onSubmit={handleSend} style={{
          opacity: 0.8,
          background: "rgba(0,0,0,0.45)",
        }} aria-label="Send a message">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Type your message…"
            style={{
              background: "rgba(255,255,255,0.85)",
              color: "#222",
              borderRadius: 20,
              border: "none",
              padding: "10px 18px",
              width: "85%",
              fontSize: 16,
            }}
            disabled={loading || aiTyping}
            aria-label="Message input"
            aria-disabled={loading || aiTyping}
            title={loading || aiTyping ? "Please wait for MazGPT to finish responding" : "Type your message"}
          />
          <button type="submit" style={{
            marginLeft: 10,
            padding: "10px 20px",
            borderRadius: 16,
            border: "none",
            background: "#00bfff",
            color: "#fff",
            fontWeight: 600,
            cursor: loading || aiTyping ? "not-allowed" : "pointer"
          }} disabled={loading || aiTyping} aria-disabled={loading || aiTyping} aria-label="Send message" title="Send message">
            {aiTyping || loading ? <span className="spinner" aria-label="Loading" style={{ marginRight: 8 }} /> : null}
            Send
          </button>
        </form>
      </div>
      {/* 2FA Panel (show in settings/profile area) */}
      {show2FA && render2FAPanel()}
      {/* 2FA Login Prompt (show if login requires 2FA) */}
      {twofaLogin && render2FALogin()}
    </div>
  );
}
// ---
// Changes:
// - Added fetchWithAuth for authenticated API calls with auto-refresh and logout on 401.
// - Added loading/error/typing indicators and smooth scroll.
// - All chat/project API calls use credentials: 'include' for secure cookie auth.
// - Comments and structure for clarity.
// - Added CSRF protection for state-changing API calls (POST, PUT, DELETE, PATCH).
// - Added 2FA UI: setup, verify, disable, and status. Update login flow to prompt for 2FA code if required. Add comments and test instructions.
// - Polish BubbleChat.jsx: Add loading/disabled states, error feedback, tooltips, accessible labels, and ensure mobile/widget responsiveness. Add aria attributes, tooltips, and error display. Disable input/button while loading or AI is typing. Add role and aria-live for error and typing feedback. Add simple responsive tweaks.
