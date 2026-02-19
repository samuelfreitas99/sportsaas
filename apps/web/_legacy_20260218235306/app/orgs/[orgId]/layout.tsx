"use client"

import { useEffect, useMemo, useState } from "react"
import api from "@/lib/api"

type FinanceSummary = {
  income: number
  expense: number
  balance: number
}

type ChargeItem = {
  id: string
  status: "PENDING" | "PAID" | "CANCELED"
  charge_type: string
  amount: number
  cycle_key: string | null
  due_date: string | null
  paid_at: string | null
  member_id: string | null
  game_id: string | null
  created_at: string
}

type LedgerItem = {
  id: string
  entry_type: "INCOME" | "EXPENSE"
  amount: number
  description: string | null
  happened_at: string
  created_at: string
}

type FinanceRecent = {
  ledger: LedgerItem[]
  charges: ChargeItem[]
}

type FinanceDashboard = {
  summary: FinanceSummary
  pending_total: number
  paid_total: number
  recent: FinanceRecent
  // se no backend tiver timeseries, a gente pluga depois
}

function fmtMoney(v: number) {
  return (v ?? 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function toISODate(d: Date) {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, "0")
  const dd = String(d.getDate()).padStart(2, "0")
  return `${yyyy}-${mm}-${dd}`
}

function startOfMonthISO() {
  const d = new Date()
  d.setDate(1)
  return toISODate(d)
}

function todayISO() {
  return toISODate(new Date())
}

export default function OrgFinancePage({ params }: { params: { orgId: string } }) {
  const orgId = params.orgId

  const [start, setStart] = useState<string>(startOfMonthISO())
  const [end, setEnd] = useState<string>(todayISO())

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [data, setData] = useState<FinanceDashboard | null>(null)

  const hasRange = useMemo(() => Boolean(start && end), [start, end])

  async function load() {
    setLoading(true)
    setError(null)

    try {
      const qs = new URLSearchParams()
      if (start) qs.set("start", start)
      if (end) qs.set("end", end)

      const res = await api.get(
        `/orgs/${orgId}/finance/dashboard?${qs.toString()}`
      )

      setData(res.data as FinanceDashboard)
    } catch (e: any) {
      const msg =
        e?.response?.data?.detail ||
        e?.response?.data?.message ||
        e?.message ||
        "Erro ao carregar dashboard financeiro."
      setError(String(msg))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId])

  const summary = data?.summary
  const recentLedger = data?.recent?.ledger ?? []
  const recentCharges = data?.recent?.charges ?? []

  return (
    <div style={{ padding: 24, maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 16, justifyContent: "space-between", flexWrap: "wrap" }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 6 }}>
            Financeiro da Organização
          </h1>
          <div style={{ opacity: 0.8 }}>
            Org: <code>{orgId}</code>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontSize: 12, opacity: 0.75 }}>Início</label>
            <input
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              style={{ padding: "8px 10px", borderRadius: 10, border: "1px solid rgba(0,0,0,0.15)" }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontSize: 12, opacity: 0.75 }}>Fim</label>
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              style={{ padding: "8px 10px", borderRadius: 10, border: "1px solid rgba(0,0,0,0.15)" }}
            />
          </div>

          <button
            onClick={load}
            disabled={loading || !hasRange}
            style={{
              padding: "10px 14px",
              borderRadius: 12,
              border: "1px solid rgba(0,0,0,0.2)",
              background: loading ? "rgba(0,0,0,0.05)" : "white",
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            {loading ? "Carregando..." : "Aplicar filtro"}
          </button>
        </div>
      </div>

      {error && (
        <div
          style={{
            marginTop: 16,
            padding: 12,
            borderRadius: 12,
            background: "rgba(255,0,0,0.06)",
            border: "1px solid rgba(255,0,0,0.25)",
          }}
        >
          <b>Erro:</b> {error}
        </div>
      )}

      {/* Cards */}
      <div
        style={{
          marginTop: 18,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 12,
        }}
      >
        <Card title="Receitas" value={fmtMoney(summary?.income ?? 0)} />
        <Card title="Despesas" value={fmtMoney(summary?.expense ?? 0)} />
        <Card title="Saldo" value={fmtMoney(summary?.balance ?? 0)} />
        <Card title="Pendentes" value={fmtMoney(data?.pending_total ?? 0)} />
        <Card title="Pagas" value={fmtMoney(data?.paid_total ?? 0)} />
      </div>

      {/* Recent */}
      <div style={{ marginTop: 22, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: 14 }}>
        <div style={panelStyle}>
          <h2 style={h2Style}>Lançamentos recentes (Ledger)</h2>
          {recentLedger.length === 0 ? (
            <div style={{ opacity: 0.75 }}>Sem lançamentos recentes.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {recentLedger.slice(0, 12).map((it) => (
                <div key={it.id} style={rowStyle}>
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <div style={{ fontWeight: 700 }}>
                      {it.entry_type === "INCOME" ? "Entrada" : "Saída"} •{" "}
                      {fmtMoney(it.amount)}
                    </div>
                    <div style={{ opacity: 0.8, fontSize: 13 }}>
                      {it.description ?? "-"}
                    </div>
                  </div>
                  <div style={{ fontSize: 12, opacity: 0.75, textAlign: "right" }}>
                    {new Date(it.happened_at).toLocaleString("pt-BR")}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={panelStyle}>
          <h2 style={h2Style}>Cobranças recentes (Charges)</h2>
          {recentCharges.length === 0 ? (
            <div style={{ opacity: 0.75 }}>Sem cobranças recentes.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {recentCharges.slice(0, 12).map((it) => (
                <div key={it.id} style={rowStyle}>
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <div style={{ fontWeight: 700 }}>
                      {it.charge_type} • {fmtMoney(it.amount)}
                    </div>
                    <div style={{ fontSize: 12, opacity: 0.75 }}>
                      Status:{" "}
                      <b>{it.status}</b>
                      {it.cycle_key ? <> • ciclo: <code>{it.cycle_key}</code></> : null}
                    </div>
                  </div>

                  <div style={{ fontSize: 12, opacity: 0.75, textAlign: "right" }}>
                    {it.due_date ? <>Vence: {new Date(it.due_date).toLocaleDateString("pt-BR")}</> : <>—</>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Placeholder gráfico */}
      <div style={{ marginTop: 16, ...panelStyle }}>
        <h2 style={h2Style}>Gráfico (próximo passo)</h2>
        <div style={{ opacity: 0.75 }}>
          Aqui a gente pluga um gráfico simples quando o backend expor séries por dia
          (income/expense/balance) ou a gente calcula via endpoint dedicado.
        </div>
      </div>
    </div>
  )
}

function Card({ title, value }: { title: string; value: string }) {
  return (
    <div
      style={{
        padding: 14,
        borderRadius: 14,
        border: "1px solid rgba(0,0,0,0.12)",
        background: "white",
      }}
    >
      <div style={{ fontSize: 12, opacity: 0.75, marginBottom: 6 }}>{title}</div>
      <div style={{ fontSize: 20, fontWeight: 800 }}>{value}</div>
    </div>
  )
}

const panelStyle: React.CSSProperties = {
  padding: 14,
  borderRadius: 14,
  border: "1px solid rgba(0,0,0,0.12)",
  background: "white",
}

const h2Style: React.CSSProperties = {
  fontSize: 16,
  fontWeight: 800,
  marginBottom: 10,
}

const rowStyle: React.CSSProperties = {
  display: "flex",
  gap: 12,
  justifyContent: "space-between",
  alignItems: "flex-start",
  padding: 10,
  borderRadius: 12,
  border: "1px solid rgba(0,0,0,0.08)",
}
