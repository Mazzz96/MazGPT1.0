import React from "react";
import "./BubbleChat.css";

export default function UserProfile({ user, onLogout, onUpgrade }) {
  return (
    <div className="user-profile-panel">
      <div className="user-profile-header">
        <img src={user.picture || "/default-avatar.png"} alt="avatar" className="user-profile-avatar" />
        <div>
          <div className="user-profile-name">{user.name}</div>
          <div className="user-profile-email">{user.email}</div>
        </div>
      </div>
      <div className="user-profile-tier">Subscription: {user.tier || "Free"}</div>
      <button onClick={onUpgrade} className="user-profile-upgrade">Upgrade</button>
      <button onClick={onLogout} className="user-profile-logout">Log Out</button>
    </div>
  );
}
