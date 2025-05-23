// useAuthRefresh.js
// React hook to transparently refresh JWT token on 401 errors
import { useAuth } from "./AuthContext";

export default function useAuthRefresh() {
  const { refresh } = useAuth();

  // Wrap fetch to auto-refresh on 401
  return async function fetchWithRefresh(url, options = {}) {
    let res = await fetch(url, { ...options, credentials: "include" });
    if (res.status === 401) {
      await refresh();
      res = await fetch(url, { ...options, credentials: "include" });
    }
    return res;
  };
}
