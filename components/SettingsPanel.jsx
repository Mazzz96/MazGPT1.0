import React from "react";
import "./BubbleChat.css";

export default function SettingsPanel({ preferences, setPreferences, onExport, onDelete, onChangePassword }) {
  return (
    <div className="settings-panel" aria-label="Settings panel">
      <h3>Personalization & Settings</h3>
      <div>
        <label htmlFor="theme-select" title="Choose light or dark mode">Theme:</label>
        <select id="theme-select" value={preferences.theme} onChange={e => setPreferences({ ...preferences, theme: e.target.value })} aria-label="Theme selector">
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>
      <div>
        <label htmlFor="lang-select" title="Choose your preferred language">App Language:</label>
        <select id="lang-select" value={preferences.language} onChange={e => setPreferences({ ...preferences, language: e.target.value })} aria-label="Language selector">
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="zh">Chinese</option>
          <option value="ar">Arabic</option>
        </select>
      </div>
      <div>
        <label htmlFor="notif-toggle" title="Enable or disable notifications">Notification Settings:</label>
        <input id="notif-toggle" type="checkbox" checked={preferences.notifications} onChange={e => setPreferences({ ...preferences, notifications: e.target.checked })} aria-label="Enable notifications" />
        <span>Enable notifications</span>
      </div>
      <div>
        <label htmlFor="map-select" title="Choose your map provider">Map Provider:</label>
        <select id="map-select" value={preferences.mapProvider} onChange={e => setPreferences({ ...preferences, mapProvider: e.target.value })} aria-label="Map provider selector">
          <option value="google">Google Maps</option>
          <option value="osm">OpenStreetMap</option>
        </select>
      </div>
      <div>
        <label htmlFor="voice-mode" title="Voice mode coming soon">Voice Mode:</label>
        <span id="voice-mode">Coming soon</span>
      </div>
      <div>
        <button onClick={onExport} aria-label="Export all data" title="Export all your data">Export All Data</button>
        <button onClick={onDelete} aria-label="Delete all data" title="Delete all your data">Delete All Data</button>
      </div>
      <div>
        <button onClick={onChangePassword} aria-label="Change password" title="Change your password">Change Password</button>
      </div>
    </div>
  );
}

// Add this CSS to BubbleChat.css or a global stylesheet:
// @media (max-width: 600px) { .settings-panel { font-size: 14px !important; padding: 8px !important; } }
