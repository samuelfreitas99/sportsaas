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