import React, { useState } from "react";
import "./BubbleChat.css";
import { useAuth } from "./AuthContext";

export default function Auth() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [step, setStep] = useState("signin");
  const { login, error, loading } = useAuth();
  const [localError, setLocalError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");
    setSuccess("");
    if (!email || (!password && step !== "reset") || (step === "signup" && !name)) {
      setLocalError("All fields are required.");
      return;
    }
    try {
      if (step === "signin") {
        await login(email, password);
      } else if (step === "signup") {
        const res = await fetch("/auth/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, name }),
        });
        if (!res.ok) throw new Error("Signup failed");
        await login(email, password);
      } else if (step === "reset") {
        const res = await fetch("/auth/reset-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        if (!res.ok) throw new Error("Reset failed");
        setSuccess("Reset link sent (check your email)");
        return;
      }
    } catch (err) {
      setLocalError(err.message || "Auth failed");
    }
  };

  return (
    <div className="auth-container">
      <form className="auth-form" onSubmit={handleSubmit} aria-label="Authentication form">
        <h2>
          {step === "signup"
            ? "Sign Up"
            : step === "reset"
            ? "Reset Password"
            : "Sign In"}
        </h2>
        {step === "signup" && (
          <label htmlFor="auth-name" title="Enter your full name">
            Name
            <input
              id="auth-name"
              type="text"
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={loading}
              aria-required="true"
            />
          </label>
        )}
        <label htmlFor="auth-email" title="Enter your email address">
          Email
          <input
            id="auth-email"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
            aria-required="true"
          />
        </label>
        {step !== "reset" && (
          <label htmlFor="auth-password" title="Enter your password">
            Password
            <input
              id="auth-password"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              aria-required="true"
            />
          </label>
        )}
        {(localError || error) && (
          <div className="auth-error" role="alert">{localError || error}</div>
        )}
        {success && <div className="auth-success" role="status">{success}</div>}
        <button type="submit" disabled={loading} aria-busy={loading} aria-label={step === "signup" ? "Sign Up" : step === "reset" ? "Send Reset Link" : "Sign In"}>
          {loading ? (
            <span className="spinner" aria-label="Loading" style={{ marginRight: 8 }} />
          ) : null}
          {step === "signup"
            ? "Sign Up"
            : step === "reset"
            ? "Send Reset Link"
            : "Sign In"}
        </button>
        <div className="auth-links">
          {step !== "signin" && (
            <span
              tabIndex={0}
              role="button"
              aria-label="Switch to Sign In"
              onClick={() => {
                setStep("signin");
                setLocalError("");
                setSuccess("");
              }}
              title="Already have an account? Sign in"
            >
              Sign In
            </span>
          )}
          {step !== "signup" && (
            <span
              tabIndex={0}
              role="button"
              aria-label="Switch to Sign Up"
              onClick={() => {
                setStep("signup");
                setLocalError("");
                setSuccess("");
              }}
              title="Create a new account"
            >
              Sign Up
            </span>
          )}
          {step !== "reset" && (
            <span
              tabIndex={0}
              role="button"
              aria-label="Reset Password"
              onClick={() => {
                setStep("reset");
                setLocalError("");
                setSuccess("");
              }}
              title="Forgot your password?"
            >
              Forgot Password?
            </span>
          )}
        </div>
        {loading && (
          <div className="auth-loading" aria-live="polite" style={{ marginTop: 12 }}>
            <span className="spinner" aria-label="Loading" />
            Processing…
          </div>
        )}
      </form>
    </div>
  );
}
// Add this CSS to BubbleChat.css or a global stylesheet:
// .spinner { display: inline-block; width: 1em; height: 1em; border: 2px solid #ccc; border-top: 2px solid #00bfff; border-radius: 50%; animation: spin 0.7s linear infinite; vertical-align: middle; }
// @keyframes spin { 100% { transform: rotate(360deg); } }
