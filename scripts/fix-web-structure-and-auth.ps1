# scripts/fix-web-structure-and-auth.ps1
# Rodar na raiz do repo (onde está docker-compose.yml)
$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$p) {
  if (!(Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
}

$repoRoot = (Get-Location).Path
$webRoot  = Join-Path $repoRoot "apps\web"
$appRoot  = Join-Path $webRoot "app"

if (!(Test-Path $webRoot)) { throw "Não achei apps\web. Rode na raiz do repo." }
if (!(Test-Path $appRoot)) { throw "Não achei apps\web\app." }

$stamp  = Get-Date -Format "yyyyMMddHHmmss"
$legacy = Join-Path $appRoot ("_legacy_" + $stamp)
Ensure-Dir $legacy

Write-Host "==> Backupando estruturas atuais para $legacy"

$toLegacy = @("app", "dashboard", "test") # pastas dentro de apps/web/app
foreach ($name in $toLegacy) {
  $p = Join-Path $appRoot $name
  if (Test-Path $p) {
    Move-Item $p $legacy
    Write-Host "Movido para legacy: $name"
  }
}

Write-Host "==> Criando estrutura correta"

Ensure-Dir (Join-Path $appRoot "(auth)\login")
Ensure-Dir (Join-Path $appRoot "(auth)\register")
Ensure-Dir (Join-Path $appRoot "(app)\dashboard")

# AuthGate
$authGatePath = Join-Path $appRoot "(app)\AuthGate.tsx"
@'
"use client";

import { useEffect, useState } from "react";
import { getMe } from "@/lib/auth";

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<"checking" | "ok" | "fail">("checking");

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        await getMe();
        if (mounted) setState("ok");
      } catch {
        if (!mounted) return;
        setState("fail");
        if (window.location.pathname !== "/login") {
          window.location.replace("/login");
        }
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  if (state === "checking") return <div style={{ padding: 24 }}>Verificando sessão...</div>;
  if (state === "fail") return <div style={{ padding: 24 }}>Sem sessão. Indo para login…</div>;
  return <>{children}</>;
}
'@ | Set-Content -Encoding UTF8 $authGatePath

# Layout privado
$privateLayoutPath = Join-Path $appRoot "(app)\layout.tsx"
@'
import AuthGate from "./AuthGate";

export default function PrivateLayout({ children }: { children: React.ReactNode }) {
  return <AuthGate>{children}</AuthGate>;
}
'@ | Set-Content -Encoding UTF8 $privateLayoutPath

# /app (grupo privado) -> /dashboard
$privateIndexPath = Join-Path $appRoot "(app)\page.tsx"
@'
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AppIndex() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard");
  }, [router]);

  return <div style={{ padding: 24 }}>Redirecionando…</div>;
}
'@ | Set-Content -Encoding UTF8 $privateIndexPath

# /dashboard
$dashPath = Join-Path $appRoot "(app)\dashboard\page.tsx"
@'
"use client";

import { useEffect, useState } from "react";
import { getMe } from "@/lib/auth";

export default function Dashboard() {
  const [me, setMe] = useState<any>(null);

  useEffect(() => {
    (async () => {
      const data = await getMe();
      setMe(data);
    })();
  }, []);

  return (
    <main style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700 }}>Dashboard</h1>
      <pre style={{ marginTop: 16, background: "#111", color: "#0f0", padding: 12, borderRadius: 8, overflow: "auto" }}>
        {JSON.stringify(me, null, 2)}
      </pre>
    </main>
  );
}
'@ | Set-Content -Encoding UTF8 $dashPath

# Home pública
$publicHome = Join-Path $appRoot "page.tsx"
@'
import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-8">Sport SaaS</h1>
      <div className="flex gap-4">
        <Link href="/login" className="px-4 py-2 bg-blue-500 text-white rounded">Login</Link>
        <Link href="/register" className="px-4 py-2 bg-gray-500 text-white rounded">Register</Link>
        <Link href="/dashboard" className="px-4 py-2 bg-black text-white rounded">Dashboard</Link>
      </div>
    </main>
  );
}
'@ | Set-Content -Encoding UTF8 $publicHome

# Root layout
$rootLayout = Join-Path $appRoot "layout.tsx"
@'
import "./globals.css";

export const metadata = {
  title: "SportSaaS",
  description: "Sport SaaS",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
'@ | Set-Content -Encoding UTF8 $rootLayout

# next.config.js (rewrite pro service api do docker)
$nextConfig = Join-Path $webRoot "next.config.js"
@'
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://api:8000/api/v1/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
'@ | Set-Content -Encoding UTF8 $nextConfig

# lib/api.ts
Ensure-Dir (Join-Path $webRoot "lib")
$apiTs = Join-Path $webRoot "lib\api.ts"
@'
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
'@ | Set-Content -Encoding UTF8 $apiTs

# lib/auth.ts
$authTs = Join-Path $webRoot "lib\auth.ts"
@'
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
'@ | Set-Content -Encoding UTF8 $authTs

Write-Host ""
Write-Host "==> OK!"
Write-Host "Agora rode:"
Write-Host "  docker compose up -d --build web"
Write-Host "E teste: http://10.0.29.107:3000/login  -> login -> /dashboard"
