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
