# scripts/fix-web-routing-and-auth.ps1
$ErrorActionPreference = "Stop"

$repo = (Get-Location).Path
$web  = Join-Path $repo "apps\web"
$app  = Join-Path $web "app"

if (!(Test-Path $web)) { throw "Não achei apps\web. Rode na raiz do repo." }
if (!(Test-Path $app)) { throw "Não achei apps\web\app." }

Write-Host "==> Removendo conflito de rotas: app/(app)/page.tsx"
$conflict = Join-Path $app "(app)\page.tsx"
if (Test-Path $conflict) {
  Remove-Item $conflict -Force
  Write-Host "Removido: $conflict"
} else {
  Write-Host "OK: não existe $conflict"
}

Write-Host "==> Garantindo dashboard privado"
$dashDir = Join-Path $app "(app)\dashboard"
if (!(Test-Path $dashDir)) { New-Item -ItemType Directory -Path $dashDir | Out-Null }

$dashPage = Join-Path $dashDir "page.tsx"
@'
"use client";

import { useEffect, useState } from "react";
import { getMe } from "@/lib/auth";

export default function Dashboard() {
  const [me, setMe] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await getMe();
        setMe(data);
      } catch (e: any) {
        setErr(e?.response?.data?.detail ?? e?.message ?? "erro");
      }
    })();
  }, []);

  return (
    <main style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700 }}>Dashboard</h1>
      {err && (
        <pre style={{ marginTop: 16, background: "#300", color: "#fff", padding: 12, borderRadius: 8 }}>
          {String(err)}
        </pre>
      )}
      <pre style={{ marginTop: 16, background: "#111", color: "#0f0", padding: 12, borderRadius: 8, overflow: "auto" }}>
        {JSON.stringify(me, null, 2)}
      </pre>
    </main>
  );
}
'@ | Set-Content -Encoding UTF8 $dashPage

Write-Host "==> Rebuild do web recomendado:"
Write-Host "docker compose up -d --build web"
