import api from "./api";

export async function login(email: string, password: string) {
  const res = await api.post("/auth/login", { email, password });
  return res.data;
}

export async function register(payload: any) {
  const res = await api.post("/auth/register", payload);
  return res.data;
}

export async function getMe() {
  const res = await api.get("/auth/me");
  return res.data;
}

export async function logout() {
  const res = await api.post("/auth/logout");
  return res.data;
}
