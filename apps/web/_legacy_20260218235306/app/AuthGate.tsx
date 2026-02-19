"use client";

import { useEffect, useState } from "react";
import { getMe } from "@/lib/auth";

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const [ok, setOk] = useState(false);

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        await getMe();
        if (mounted) setOk(true);
      } catch {
        if (!mounted) return;
        // redirect "bruto" (não depende do App Router estar montado)
        if (window.location.pathname !== "/login") {
          window.location.replace("/login");
        }
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  if (!ok) return <div style={{ padding: 24 }}>Verificando sessão...</div>;
  return <>{children}</>;
}
