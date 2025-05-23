import React from "react";
import "./BubbleChat.css";

export default function AboutTab() {
  return (
    <div className="about-tab">
      <h3>About MazGPT for Windows</h3>
      <p>Version: 1.0.0</p>
      <p>Branding: MazGPT for Windows</p>
      <p><a href="#help">Help Center</a></p>
      <p><a href="#terms">Terms of Use</a></p>
      <p><a href="#privacy">Privacy Policy</a></p>
      <p>All data is stored securely and is GDPR-compliant.</p>
    </div>
  );
}
