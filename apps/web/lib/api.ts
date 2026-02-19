import axios from "axios";

export const STORAGE_KEYS = {
  currentOrgId: "currentOrgId",
} as const;

let didForceLogout = false;

export async function forceLogout() {
  if (didForceLogout) return;
  didForceLogout = true;

  if (typeof window !== "undefined") {
    localStorage.removeItem(STORAGE_KEYS.currentOrgId);
  }

  try {
    await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
  } catch {}

  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
});

let isRefreshing = false;
let pendingQueue: Array<{
  resolve: (value: any) => void;
  reject: (reason?: any) => void;
  original: any;
}> = [];

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const status = err?.response?.status;
    const original = err?.config;

    if (status === 401 && original && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => pendingQueue.push({ resolve, reject, original }));
      }

      isRefreshing = true;

      try {
        const r = await fetch("/api/v1/auth/refresh", { method: "POST", credentials: "include" });
        if (!r.ok) throw new Error("refresh failed");

        original._retry = true;

        const queued = pendingQueue;
        pendingQueue = [];
        queued.forEach(({ resolve, reject, original }) => {
          original._retry = true;
          api.request(original).then(resolve).catch(reject);
        });

        return api.request(original);
      } catch (e) {
        const queued = pendingQueue;
        pendingQueue = [];
        queued.forEach(({ reject }) => reject(e));
        void forceLogout();
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(err);
  }
);

export default api;
